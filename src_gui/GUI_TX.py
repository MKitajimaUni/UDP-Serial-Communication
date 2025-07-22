import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from PythonTX import PythonTX


def select_file():
    filepath = filedialog.askopenfilename()
    if filepath:
        file_path_var.set(filepath)


def show_help_ipaddr():
    messagebox.showinfo("IP-Address", "IP Address must be in ordinal IPv4 Address form.")


def send_file():
    filepath = file_path_var.get()
    dest_ip = ip_address_var.get()

    if not filepath or not dest_ip:
        messagebox.showerror("Input Error", "Please provide both file path and destination IP.")
        return

    def run_transfer():
        try:
            send_button.config(state="disabled")
            root.config(cursor="watch")
            update_loading_message("Sending file. This may take a while...")

            tx = PythonTX(dest_ip, filepath)
            tx.send_file(progress_callback=update_loading_message)

            update_loading_message("Transfer complete.")
            messagebox.showinfo("Success", f"File sent to {dest_ip} successfully.")

        except FileNotFoundError as e:
            messagebox.showerror("File Error", message=str(e))
            update_loading_message("Error: File not found.")
        except TimeoutError as e:
            messagebox.showerror("Timeout Error", message=str(e))
            update_loading_message("Error: Timeout. Make sure that RX program is active.")
        except ConnectionError as e:
            messagebox.showerror("Transmission Error", message=str(e))
            update_loading_message("Error: Connection error.")
        except OSError as e:
            messagebox.showerror("Network Error", message=str(e))
            update_loading_message("Error: Network issue.")
        except Exception as e:
            messagebox.showerror("Unexpected Error", message=str(e))
            update_loading_message("Error: Unexpected issue.")
        finally:
            send_button.config(state="normal")
            root.config(cursor="")
            root.after(lambda: update_loading_message(""))  # Clear after 3s

    threading.Thread(target=run_transfer, daemon=True).start()


def update_loading_message(text):
    loading_label.config(text=text)


# GUI setup
root = tk.Tk()
root.title("UDP File Sender")

file_path_var = tk.StringVar()
ip_address_var = tk.StringVar()

tk.Label(root, text="File to Send:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=file_path_var, width=40).grid(row=0, column=1, padx=5)
tk.Button(root, text="Browse", command=select_file).grid(row=0, column=2, padx=5)
tk.Label(root, text="Enter a filepath or browse the file.", fg="gray").grid(row=1, column=1, sticky="w", padx=5)

tk.Label(root, text="").grid(row=2, column=0)

tk.Label(root, text="Destination IP Address:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=ip_address_var, width=40).grid(row=3, column=1, padx=5)
tk.Button(root, text="Help", command=show_help_ipaddr).grid(row=3, column=2, padx=5)
tk.Label(root, text="Enter a destination IP address.", fg="gray").grid(row=4, column=1, sticky="w", padx=5)

send_button = tk.Button(root, text="Send File", command=send_file)
send_button.grid(row=5, column=1, pady=10)

# Loading / status message label
loading_label = tk.Label(root, text="", fg="orange")
loading_label.grid(row=6, column=1)

root.mainloop()
