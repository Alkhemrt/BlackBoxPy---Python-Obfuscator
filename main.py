import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import threading
import sys
import subprocess
import importlib.util
import pkg_resources

from core.obfuscator import (
    run_pyarmor_encrypt,
    obfuscate_file,
    obfuscate_directory,
    run_pyinstaller
)

def check_and_install_dependencies():
    required_packages = {
        'pyarmor': 'pyarmor',
        'pyinstaller': 'pyinstaller',
        'astor': 'astor',
    }
    
    missing_packages = []
    total_size = 0
    
    # Check which packages are missing using both methods
    for name, package in required_packages.items():
        spec = importlib.util.find_spec(name)
        try:
            pkg_resources.get_distribution(name)
        except pkg_resources.DistributionNotFound:
            spec = None
        
        if not spec:
            missing_packages.append(package)
    
    if not missing_packages:
        return True
    
    # Estimate download size (approximate sizes in KB)
    size_estimates = {
        'pyarmor': 5000,
        'pyinstaller': 15000,
        'astor': 100,
    }
    
    total_size = sum(size_estimates.get(pkg, 1000) for pkg in missing_packages)
    
    # Ask user for permission to install
    root = tk.Tk()
    root.withdraw()
    
    response = messagebox.askyesno(
        "Missing Dependencies",
        f"The following packages are required but not installed:\n\n"
        f"{', '.join(missing_packages)}\n\n"
        f"Total download size: ~{total_size/1024:.1f} MB\n\n"
        "Would you like to install them now?",
        parent=root
    )
    root.destroy()
    
    if not response:
        return False
    
    # Install missing packages
    for package in missing_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError as e:
            messagebox.showerror(
                "Installation Failed",
                f"Failed to install {package}. Please install it manually.\n\n"
                f"Error: {str(e)}"
            )
            return False
    
    return True

class BlackBoxPyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BlackBoxPy - Python Obfuscator")
        self.root.geometry("800x600")
        self.root.configure(bg="#1a1a1a")
        self.root.resizable(False, False)

        self.selected_path = tk.StringVar()
        self.output_path = tk.StringVar()

        self.use_ast = tk.BooleanVar(value=True)
        self.use_pyarmor = tk.BooleanVar(value=True)
        self.use_pyinstaller = tk.BooleanVar(value=False)
        self.icon_path = tk.StringVar()
        self.clean_pyinstaller = tk.BooleanVar(value=True)

        self.build_gui()

    def build_gui(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background="#1a1a1a", foreground="#cccccc", font=("Segoe UI", 10))
        style.configure("TButton", background="#222222", foreground="#ffffff", borderwidth=1)
        style.map("TButton", background=[("active", "#2e2e2e")], relief=[("pressed", "sunken")])
        style.configure("TLabel", background="#1a1a1a", foreground="#ffffff")
        style.configure("TLabelframe", background="#212121", foreground="#ffffff", font=("Segoe UI Semibold", 10))
        style.configure("TLabelframe.Label", background="#212121", font=("Segoe UI Bold", 11))

        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", pady=10, padx=20)

        title_label = ttk.Label(top_frame, text="🛡 BlackBoxPy", font=("Segoe UI Black", 20))
        title_label.pack(side="left")

        settings_btn = ttk.Button(top_frame, text="⚙️ Settings", command=self.open_settings)
        settings_btn.pack(side="right")

        io_frame = ttk.Frame(self.root)
        io_frame.pack(padx=20, pady=10, fill="x")

        self.build_path_row(io_frame, "📄 Source File", self.selected_path, self.browse_path).pack(fill="x", pady=5)
        self.build_path_row(io_frame, "📁 Output Folder", self.output_path, self.select_output_folder).pack(fill="x", pady=5)

        run_btn = ttk.Button(self.root, text="🔒 Start Obfuscation", command=self.run_obfuscation_threaded)
        run_btn.pack(pady=15, ipadx=10, ipady=5)

        log_frame = ttk.LabelFrame(self.root, text="📝 Log Output")
        log_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self.log_area = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=12,
            font=("Consolas", 10), bg="#2a2a2a", fg="#e0e0e0",
            insertbackground="#ffffff", borderwidth=0, relief="flat"
        )
        self.log_area.pack(fill="both", expand=True)

    def build_path_row(self, parent, label_text, var, browse_cmd):
        frame = ttk.LabelFrame(parent, text=label_text)
        entry = tk.Entry(frame, textvariable=var, width=70, bg="#2a2a2a", fg="#ffffff", insertbackground="#ffffff")
        entry.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="ew")

        browse_button = ttk.Button(frame, text="Browse", command=browse_cmd)
        browse_button.grid(row=0, column=1, padx=(0, 10), pady=10)

        frame.columnconfigure(0, weight=1)
        return frame

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("⚙️ Settings")
        settings_win.geometry("400x300")
        settings_win.configure(bg="#212121")
        settings_win.resizable(False, False)

        container = tk.Frame(settings_win, bg="#272727", bd=0, relief="flat")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            container,
            text="🔧 Obfuscation Options",
            font=("Segoe UI Semibold", 13),
            fg="#ffffff",
            bg="#272727",
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        style = ttk.Style(settings_win)
        style.configure("Settings.TCheckbutton", background="#272727", foreground="#ffffff", font=("Segoe UI", 10))
        style.map("Settings.TCheckbutton", background=[("active", "#3a3a3a")])

        ttk.Checkbutton(container, text="🔄 Enable AST Obfuscation", variable=self.use_ast,
                        style="Settings.TCheckbutton").pack(anchor="w", padx=10, pady=5)
        ttk.Checkbutton(container, text="🛡 Enable PyArmor Encryption", variable=self.use_pyarmor,
                        style="Settings.TCheckbutton").pack(anchor="w", padx=10, pady=5)
        ttk.Checkbutton(container, text="📦 Build .EXE with PyInstaller", variable=self.use_pyinstaller,
                        style="Settings.TCheckbutton").pack(anchor="w", padx=10, pady=5)
        ttk.Checkbutton(container, text="🧹 Auto-delete build folder and .spec file after .exe creation",
                        variable=self.clean_pyinstaller, style="Settings.TCheckbutton").pack(anchor="w", padx=10,
                                                                                             pady=5)

        # Icon selector
        icon_frame = ttk.LabelFrame(container, text="🖼️ EXE Icon (.ico)")
        icon_frame.pack(fill="x", padx=10, pady=(15, 5))

        icon_entry = tk.Entry(icon_frame, textvariable=self.icon_path, width=32, bg="#2a2a2a", fg="#ffffff",
                              insertbackground="#ffffff")
        icon_entry.grid(row=0, column=0, padx=(10, 5), pady=8, sticky="ew")

        icon_btn = ttk.Button(icon_frame, text="Browse", command=self.browse_icon)
        icon_btn.grid(row=0, column=1, padx=(0, 10), pady=8)

        icon_frame.columnconfigure(0, weight=1)

        save_btn = tk.Button(
            container, text="✓ Save & Close", font=("Segoe UI Semibold", 10),
            bg="#3a3a3a", fg="#ffffff", activebackground="#505050", activeforeground="#ffffff",
            relief="flat", command=settings_win.destroy, height=1, width=20
        )
        save_btn.pack(pady=15)

    def browse_icon(self):
        path = filedialog.askopenfilename(title="Select Icon File", filetypes=[("ICO Files", "*.ico")])
        if path:
            self.icon_path.set(path)

    def browse_path(self):
        path = filedialog.askopenfilename(title="Select Python File", filetypes=[("Python Files", "*.py")])
        if not path:
            path = filedialog.askdirectory(title="Select Folder")
        if path:
            self.selected_path.set(path)

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_path.set(folder)

    def run_obfuscation_threaded(self):
        threading.Thread(target=self.run_obfuscation).start()

    def run_obfuscation(self):
        input_path = self.selected_path.get()
        output_path = self.output_path.get()

        if not input_path:
            messagebox.showerror("Error", "❗ Please select a source file or folder.")
            return
        if not output_path:
            messagebox.showerror("Error", "❗ Please select an output folder.")
            return

        self.log("🔍 Starting...")
        self.log(f"📁 Input: {input_path}")
        self.log(f"📂 Output: {output_path}")

        if self.use_ast.get():
            self.log("🔄 AST Obfuscation: ON")
            try:
                if os.path.isfile(input_path):
                    self.log(f"🧹 Stripping docstrings in {os.path.basename(input_path)}")
                    obfuscate_file(input_path, output_path)
                else:
                    obfuscate_directory(input_path, output_path)
                self.log(f"✅ AST-obfuscated: {os.path.basename(input_path)}")
            except Exception as e:
                self.log(f"❌ AST error: {input_path} - {str(e)}")

        if self.use_pyarmor.get():
            self.log("🛡️ PyArmor Encryption: ON")
            try:
                run_pyarmor_encrypt(input_path, output_path, logger=self.log)
            except Exception as e:
                self.log(f"❌ PyArmor error: {str(e)}")

        if self.use_pyinstaller.get():
            self.log("📦 PyInstaller Build: ON")
            try:
                run_pyinstaller(input_path, output_path, icon_path=self.icon_path.get(),
                                cleanup=self.clean_pyinstaller.get(), logger=self.log)
            except Exception as e:
                self.log(f"❌ PyInstaller error: {str(e)}")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

if __name__ == "__main__":
    if not check_and_install_dependencies():
        sys.exit(1)
    
    root = tk.Tk()
    app = BlackBoxPyGUI(root)
    root.mainloop()
