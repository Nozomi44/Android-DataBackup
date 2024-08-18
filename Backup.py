import subprocess
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk, scrolledtext, font
import threading
from tkinter import Toplevel

class AndroidBackupApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("600x400")
        self.root.overrideredirect(True)  # Menghilangkan border default window
        self.root.attributes("-alpha", 0.9)  # Menambahkan efek transparansi

        # Mendeteksi direktori home pengguna dan menyesuaikan path instalasi
        user_home = os.path.expanduser("~")
        self.install_path = os.path.join(user_home, "AppData", "Local", "Programs", "Android Data Backuper")
        self.adb_path = os.path.join(self.install_path, "adb.exe")

        # Mengatur tampilan header
        self.header_frame = tk.Frame(root, bg="#2C3E50", height=40)
        self.header_frame.pack(side="top", fill="x")

        # Tambahkan judul aplikasi di header
        self.app_title = tk.Label(self.header_frame, text="Android Backup App", bg="#2C3E50", fg="white",
                                  font=font.Font(family="UD Digi Kyokasho NP R", size=12, weight="bold"))
        self.app_title.pack(side="left", padx=10)

        # Tambahkan tombol minimize
        self.minimize_button = tk.Button(self.header_frame, text="_", bg="#2C3E50", fg="white", bd=0, 
                                         font=font.Font(family="UD Digi Kyokasho NP R", size=12, weight="bold"), 
                                         command=self.minimize_app)
        self.minimize_button.pack(side="right", padx=5)

        # Tambahkan tombol close
        self.close_button = tk.Button(self.header_frame, text="X", bg="#2C3E50", fg="white", bd=0, 
                                      font=font.Font(family="UD Digi Kyokasho NP R", size=12, weight="bold"), 
                                      command=self.close_app)
        self.close_button.pack(side="right")

        # Membuat draggable window
        self.header_frame.bind("<Button-1>", self.start_move)
        self.header_frame.bind("<ButtonRelease-1>", self.stop_move)
        self.header_frame.bind("<B1-Motion>", self.on_move)

        # Tambahkan konten aplikasi di bawah header
        self.content_frame = tk.Frame(root, bg="#ECF0F1")
        self.content_frame.pack(expand=True, fill="both")

        self.label = tk.Label(self.content_frame, text="Select backup folder:", bg="#ECF0F1")
        self.label.pack(pady=10)

        self.browse_button = tk.Button(self.content_frame, text="Browse", command=self.browse_folder)
        self.browse_button.pack(pady=5)

        self.start_button = tk.Button(self.content_frame, text="Start Backup", command=self.start_backup, state=tk.DISABLED)
        self.start_button.pack(pady=20)

        # Add button to detect ADB devices
        self.detect_button = tk.Button(self.content_frame, text="Detect Devices", command=self.detect_devices)
        self.detect_button.pack(pady=5)

        # Progress bar setup
        self.progress_label = tk.Label(self.content_frame, text="Backup Progress:", bg="#ECF0F1")
        self.progress_label.pack(pady=5)
        self.progress = ttk.Progressbar(self.content_frame, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack(pady=10)

        # Log text area
        self.log_area = scrolledtext.ScrolledText(self.content_frame, width=60, height=15, wrap=tk.WORD, state=tk.DISABLED)
        self.log_area.pack(pady=10)

        # Menambahkan kontrol untuk pause dan resume
        self.pause_button = tk.Button(self.content_frame, text="Pause", command=self.pause_backup, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=10)

        self.resume_button = tk.Button(self.content_frame, text="Resume", command=self.resume_backup, state=tk.DISABLED)
        self.resume_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(self.content_frame, text="Stop", command=self.stop_backup, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)

        self.backup_folder = ""
        self.backup_process = None
        self.paused = False

    def start_move(self, event):
        self.root.x = event.x
        self.root.y = event.y

    def stop_move(self, event):
        self.root.x = None
        self.root.y = None

    def on_move(self, event):
        delta_x = event.x - self.root.x
        delta_y = event.y - self.root.y
        x = self.root.winfo_x() + delta_x
        y = self.root.winfo_y() + delta_y
        self.root.geometry(f"+{x}+{y}")

    def minimize_app(self):
        self.root.iconify()

    def close_app(self):
        self.root.destroy()

    def browse_folder(self):
        self.backup_folder = filedialog.askdirectory()
        if self.backup_folder:
            self.start_button.config(state=tk.NORMAL)

    def run_adb_command(self, command):
        """Run adb command and capture the output."""
        full_command = f'"{self.adb_path}" {command}'
        self.log_output(f"Running command: {full_command}")
        try:
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.log_output(f"Error: {result.stderr}")
            else:
                self.log_output(result.stdout)
            return result.stdout
        except FileNotFoundError:
            self.log_output("ADB command not found. Ensure ADB is installed and added to PATH.")
            return ""
        except Exception as e:
            self.log_output(f"An error occurred: {str(e)}")
            return ""

    def detect_devices(self):
        """Detect connected ADB devices and display in log."""
        devices = self.run_adb_command("devices")
        self.log_output(devices)
        if "device" not in devices:
            messagebox.showerror("Error", "No devices connected. Make sure USB Debugging is enabled and the device is connected.")
            self.start_button.config(state=tk.DISABLED)
        else:
            self.start_button.config(state=tk.NORMAL)

    def get_device_model(self):
        """Get the connected device model name."""
        model = self.run_adb_command("shell getprop ro.product.model").strip()
        return model if model else "android_backup"

    def start_backup(self):
        if not self.backup_folder:
            messagebox.showwarning("Warning", "Please select a backup folder.")
            return

        # Check for devices again before starting the backup
        devices = self.run_adb_command("devices")
        if "device" not in devices:
            messagebox.showerror("Error", "No devices connected. Make sure USB Debugging is enabled and the device is connected.")
            return

        # Get device model to name the backup folder
        device_model = self.get_device_model()

        # Define the source and destination paths
        backup_path = os.path.join(self.backup_folder, device_model)

        # Disable start button and enable pause and stop buttons
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)

        # Start backup in a new thread to avoid blocking the GUI
        self.backup_process = threading.Thread(target=self.perform_backup, args=(backup_path,))
        self.backup_process.start()

    def perform_backup(self, backup_path):
        # Create backup directory if it does not exist
        if not os.path.exists(backup_path):
            try:
                os.makedirs(backup_path)
                self.log_output(f"Created backup directory: {backup_path}")
            except Exception as e:
                self.log_output(f"Error creating directory: {str(e)}")
                return

        # Start backup process
        self.log_output("Starting backup...")

        # Use adb pull command and update progress
        pull_command = f"pull /storage/emulated/0/ \"{backup_path}\""
        process = subprocess.Popen(f'"{self.adb_path}" {pull_command}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        self.progress.config(mode="indeterminate")  # Start indeterminate progress bar
        self.progress.start(10)  # Animation starts
        for line in iter(process.stdout.readline, ''):
            if self.paused:
                break
            output = line.strip()
            self.log_output(output)
            if "bytes transferred" in output:
                self.update_progress_bar(output)

        process.wait()
        error_output = process.stderr.read().strip()

        # Check if the stderr output is just informational and not an actual error
        if "files pulled" in error_output and "bytes transferred" in error_output:
            self.log_output(f"Backup completed. Data saved to {backup_path}")
            self.show_completion_window(backup_path)  # Panggil fungsi baru untuk menampilkan jendela notifikasi
        else:
            self.log_output(f"Backup completed. Data saved to {backup_path}")
            self.show_completion_window(backup_path)  # Panggil fungsi baru untuk menampilkan jendela notifikasi

        # Reset buttons
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

        # Stop progress bar
        self.progress.stop()

    def pause_backup(self):
        if self.backup_process and self.backup_process.is_alive():
            self.paused = True
            self.pause_button.config(state=tk.DISABLED)
            self.resume_button.config(state=tk.NORMAL)
            self.log_output("Backup paused.")

    def resume_backup(self):
        if self.paused:
            self.paused = False
            self.pause_button.config(state=tk.NORMAL)
            self.resume_button.config(state=tk.DISABLED)
            self.log_output("Backup resumed.")
            self.start_backup()

    def stop_backup(self):
        if self.backup_process and self.backup_process.is_alive():
            self.backup_process = None  # Stop the thread
            self.log_output("Backup stopped by user.")
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.resume_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)

    def update_progress_bar(self, output):
        # Simple logic to simulate progress based on the output
        if "files pulled" in output and "bytes transferred" in output:
            parts = output.split(",")
            if len(parts) >= 3:
                try:
                    transferred = int(parts[2].strip().split()[0].replace(",", ""))
                    total = int(parts[1].strip().split()[0].replace(",", ""))
                    if total > 0:
                        percent = (transferred / total) * 100
                        self.progress.config(value=percent)
                except ValueError:
                    pass

    def log_output(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.yview(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def show_completion_window(self, backup_path):
        # Jendela notifikasi untuk memberitahu bahwa backup sudah selesai
        completion_window = Toplevel(self.root)
        completion_window.title("Backup Complete")
        completion_window.geometry("300x150")
        completion_window.overrideredirect(True)  # Hilangkan border default window
        completion_window.attributes("-topmost", True)  # Membuat jendela selalu berada di atas

        # Tambahkan label notifikasi
        label = tk.Label(completion_window, text=f"Backup completed!\nData saved to:\n{backup_path}", padx=10, pady=10)
        label.pack(expand=True)

        # Tambahkan tombol untuk menutup jendela notifikasi
        close_button = tk.Button(completion_window, text="Close", command=completion_window.destroy)
        close_button.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = AndroidBackupApp(root)
    root.mainloop()
