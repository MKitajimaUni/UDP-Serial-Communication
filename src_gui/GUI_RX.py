import tkinter as tk
from tkinter import messagebox
import threading
from PythonRX import PythonRX


class GUI_RX:
    def __init__(self, root):
        self.root = root
        self.root.title("UDP File Receiver")
        self.status_var = tk.StringVar(value="")

        self.output_filename_var = tk.StringVar()
        self._build_widgets()

    def _build_widgets(self):
        tk.Label(self.root, text="UDP Receiver", font=("Arial", 14, "bold")).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(pady=5)

        tk.Label(frame, text="Save As:").grid(row=0, column=0, padx=5)
        tk.Entry(frame, textvariable=self.output_filename_var, width=40).grid(row=0, column=1, padx=5)
        tk.Label(frame, text="Enter a filepath with extension type.", fg="gray").grid(row=1, column=1, sticky="w", padx=5)

        tk.Button(self.root, text="Start Receiving", command=self.start_receiving).pack(pady=10)
        tk.Label(self.root, textvariable=self.status_var, fg="orange").pack(pady=10)

    def start_receiving(self):
        filename = self.output_filename_var.get().strip()
        if not filename:
            messagebox.showerror("Input Error", "Please specify an output filename.")
            return

        def listen():
            self.status_var.set("Listening for incoming file.")
            rx = PythonRX(filename)
            success = rx.receive_file(progress_callback=self.status_var.set)
            if success:
                self.status_var.set("File received successfully.")
            else:
                self.status_var.set("Receiving failed.")

        threading.Thread(target=listen, daemon=True).start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    GUI_RX(tk.Tk()).run()