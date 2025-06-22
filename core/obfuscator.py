import ast
import os
import shutil
import random
import string
import astor
import builtins

BUILTINS = set(dir(builtins))
RESERVED = {"self", "cls", "__init__", "__name__", "__file__", "__main__"}


class SafeObfuscator(ast.NodeTransformer):
    def __init__(self):
        self.global_name_map = {}  # Tracks global renaming
        self.imports = set()
        self.scopes = []  # Stack to track variable names in each function scope

    def random_name(self):
        name = ''.join(random.choices(string.ascii_letters, k=8))
        while name in self.global_name_map.values():
            name = ''.join(random.choices(string.ascii_letters, k=8))
        return name

    def obfuscate_name(self, name):
        if (
            name in self.imports or
            name in RESERVED or
            name in BUILTINS or
            name.startswith("__") and name.endswith("__")
        ):
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

        # Enter a new scope
        local_scope = {}
        for arg in node.args.args:
            obfuscated = self.random_name()
            local_scope[arg.arg] = obfuscated
            arg.arg = obfuscated
        self.scopes.append(local_scope)

        self.generic_visit(node)
        self.scopes.pop()  # Leave scope
        return node

    def visit_arg(self, node):
        # Already handled it in visit_FunctionDef
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
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            if hasattr(node, 'body') and isinstance(node.body, list):
                if node.body and isinstance(node.body[0], ast.Expr):
                    if isinstance(node.body[0].value, ast.Str):
                        node.body.pop(0)
    return astor.to_source(tree)


def obfuscate_file(src_path, output_dir):
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