import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
from core.obfuscator import obfuscate_directory

class BlackBoxPyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ BlackBoxPy - Python Obfuscator")
        self.root.geometry("800x600")
        self.root.configure(bg="#121212")
        self.root.resizable(False, False)

        self.selected_path = tk.StringVar()
        self.output_path = tk.StringVar()

        self.build_gui()

    def build_gui(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Dark theme styling
        style.configure(".", background="#121212", foreground="#FFFFFF", font=("Segoe UI", 10))
        style.configure("TButton", background="#1f1f1f", foreground="#FFFFFF", borderwidth=1)
        style.map("TButton",
                  background=[("active", "#333333")],
                  relief=[("pressed", "sunken")])

        style.configure("TLabel", background="#121212", foreground="#FFFFFF")
        style.configure("TLabelframe", background="#1c1c1c", foreground="#FFFFFF", font=("Segoe UI Semibold", 10))
        style.configure("TLabelframe.Label", background="#1c1c1c", font=("Segoe UI Bold", 11))

        # Title
        title_label = ttk.Label(self.root, text="🛡️ BlackBoxPy", font=("Segoe UI Black", 20))
        title_label.pack(pady=20)

        # Frame for input/output selectors
        io_frame = ttk.Frame(self.root)
        io_frame.pack(padx=20, pady=10, fill="x")

        # Source Selector
        self.build_path_row(io_frame, "📄 Source File", self.selected_path, self.browse_path).pack(fill="x", pady=5)

        # Output Selector
        self.build_path_row(io_frame, "📁 Output Folder", self.output_path, self.select_output_folder).pack(fill="x", pady=5)

        # Run Button
        run_btn = ttk.Button(self.root, text="🔒 Start Obfuscation", command=self.run_obfuscation)
        run_btn.pack(pady=15, ipadx=10, ipady=5)

        # Log Area
        log_frame = ttk.LabelFrame(self.root, text="📝 Log Output")
        log_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self.log_area = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=12,
            font=("Consolas", 10), bg="#1a1a1a", fg="#d4d4d4",
            insertbackground="#ffffff", borderwidth=0, relief="flat"
        )
        self.log_area.pack(fill="both", expand=True)

    def build_path_row(self, parent, label_text, var, browse_cmd):
        frame = ttk.LabelFrame(parent, text=label_text)
        entry = ttk.Entry(frame, textvariable=var, width=70)
        entry.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="ew")

        browse_button = ttk.Button(frame, text="Browse", command=browse_cmd)
        browse_button.grid(row=0, column=1, padx=(0, 10), pady=10)

        frame.columnconfigure(0, weight=1)
        return frame

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

    def run_obfuscation(self):
        input_path = self.selected_path.get()
        output_path = self.output_path.get()

        if not input_path:
            messagebox.showerror("Error", "❗ Please select a source file or folder.")
            return
        if not output_path:
            messagebox.showerror("Error", "❗ Please select an output folder.")
            return

        self.log("🔍 Starting obfuscation...")
        self.log(f"📁 Input: {input_path}")
        self.log(f"📂 Output: {output_path}")

        try:
            obfuscate_directory(input_path, output_path)
            self.log("✅ Obfuscation complete!")
        except Exception as e:
            self.log(f"❌ Error occurred: {str(e)}")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = BlackBoxPyGUI(root)
    root.mainloop()
