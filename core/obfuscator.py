import os
import ast
import random
import string
import builtins
import subprocess
import sys
import importlib.util
import pkg_resources

BUILTINS = set(dir(builtins))
RESERVED = {"self", "cls", "__init__", "__name__", "__file__", "__main__"}

def check_package_installed(package_name):
    """Check if package is installed using both importlib and pkg_resources"""
    try:
        spec = importlib.util.find_spec(package_name)
        pkg_resources.get_distribution(package_name)
        return spec is not None
    except (ImportError, pkg_resources.DistributionNotFound):
        return False

def check_astor_installed():
    if not check_package_installed('astor'):
        raise ImportError("astor package is required but not installed. Please install it first.")

def check_pyinstaller_installed():
    if not check_package_installed('pyinstaller'):
        raise ImportError("PyInstaller is required but not installed. Please install it first.")

def check_pyarmor_installed():
    if not check_package_installed('pyarmor'):
        raise ImportError("PyArmor is required but not installed. Please install it first.")

class SafeObfuscator(ast.NodeTransformer):
    def __init__(self):
        self.global_name_map = {}
        self.imports = set()
        self.scopes = []

    def random_name(self):
        while True:
            name = ''.join(random.choices(string.ascii_letters, k=8))
            if name not in self.global_name_map.values():
                return name

    def obfuscate_name(self, name):
        if (name in self.imports or name in RESERVED or name in BUILTINS
                or (name.startswith("__") and name.endswith("__"))):
            return name

        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        if name not in self.global_name_map:
            self.global_name_map[name] = self.random_name()
        return self.global_name_map[name]

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.asname or alias.name)
        return node

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.add(alias.asname or alias.name)
        return node

    def visit_FunctionDef(self, node):
        node.name = self.obfuscate_name(node.name)

        local_scope = {}
        for arg in node.args.args:
            obfuscated = self.random_name()
            local_scope[arg.arg] = obfuscated
            arg.arg = obfuscated
        self.scopes.append(local_scope)

        self.generic_visit(node)
        self.scopes.pop()
        return node

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Load, ast.Store, ast.Del)):
            node.id = self.obfuscate_name(node.id)
        return node

    def visit_ClassDef(self, node):
        node.name = self.obfuscate_name(node.name)
        self.generic_visit(node)
        return node


def strip_comments_and_docstrings(source):
    check_astor_installed()
    import astor
    
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            if hasattr(node, 'body') and isinstance(node.body, list):
                if node.body and isinstance(node.body[0], ast.Expr):
                    if isinstance(node.body[0].value, ast.Str):
                        node.body.pop(0)
    return astor.to_source(tree)


def obfuscate_file(src_path, output_dir):
    check_astor_installed()
    import astor
    
    with open(src_path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        source = strip_comments_and_docstrings(source)
        tree = ast.parse(source)
        obfuscator = SafeObfuscator()
        obfuscator.visit(tree)
        obfuscated_code = astor.to_source(tree)
    except Exception as e:
        raise RuntimeError(f"Failed to process {src_path}: {str(e)}")

    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(src_path)
    output_path = os.path.join(output_dir, filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(obfuscated_code)


def obfuscate_directory(path, output_dir):
    if os.path.isfile(path):
        obfuscate_file(path, output_dir)
    else:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    src_file = os.path.join(root, file)
                    relative_path = os.path.relpath(src_file, path)
                    target_path = os.path.join(output_dir, relative_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    obfuscate_file(src_file, os.path.dirname(target_path))


def run_pyarmor_encrypt(input_path, output_path, logger=print):
    check_pyarmor_installed()
    
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)

    logger(f"🧩 Running: pyarmor gen --output {output_path} {input_path}")

    try:
        result = subprocess.run(
            ["pyarmor", "gen", "--output", output_path, input_path],
            capture_output=True,
            text=True,
            shell=True
        )

        if result.stdout:
            logger("➡️ PyArmor stdout:\n" + result.stdout.strip())

        if result.stderr:
            logger("🛑 PyArmor stderr:\n" + result.stderr.strip())

        if result.returncode != 0:
            raise RuntimeError("PyArmor encoding failed.")

        logger("✅ PyArmor encryption complete.")

    except Exception as e:
        logger(f"❌ Exception during PyArmor run: {e}")
        raise


def run_pyinstaller(input_path, output_dir, icon_path=None, cleanup=False, logger=print):
    check_pyinstaller_installed()
    
    input_path = os.path.abspath(input_path)
    output_dir = os.path.abspath(output_dir)

    command = [
        "pyinstaller",
        "--onefile",
        "--distpath", output_dir
    ]

    if icon_path and os.path.isfile(icon_path) and icon_path.endswith(".ico"):
        command.extend(["--icon", icon_path])
        logger(f"🎨 Using icon: {icon_path}")

    command.append(input_path)

    logger(f"📦 Running: {' '.join(command)}")
    logger(f"⏳ Creating .exe file... please wait, this may take a moment.")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True
        )

        if result.stdout:
            logger("➡️ PyInstaller stdout:\n" + result.stdout.strip())
        if result.stderr:
            logger("🛑 PyInstaller stderr:\n" + result.stderr.strip())

        if result.returncode != 0:
            raise RuntimeError("PyInstaller failed to build executable.")

        logger("✅ Executable built with PyInstaller.")

    except Exception as e:
        logger(f"❌ Exception during PyInstaller run: {e}")
        raise

    if cleanup:
        spec_file = os.path.splitext(os.path.basename(input_path))[0] + ".spec"
        try:
            if os.path.isdir("build"):
                os.system("rmdir /s /q build") if os.name == 'nt' else os.system("rm -rf build")
                logger("🧹 Deleted 'build' folder.")
            if os.path.isfile(spec_file):
                os.remove(spec_file)
                logger(f"🧹 Deleted '{spec_file}' file.")
        except Exception as e:
            logger(f"⚠️ Cleanup error: {e}")
