import os
import sys
import threading
from tkinter import filedialog
import customtkinter as ctk
import yt_dlp

# Ensure bundled binaries (ffmpeg.exe, deno.exe) are on PATH when running as a PyInstaller .exe
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    os.environ["PATH"] = sys._MEIPASS + os.pathsep + os.environ.get("PATH", "")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MinimalYTDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("snd-yt")
        self.geometry("500x365")
        self.resizable(False, False)

        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self.cookie_file = None

        # Main container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=28, pady=24)

        # Header
        self.header = ctk.CTkLabel(
            self.container,
            text="YouTube Downloader",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
        )
        self.header.pack(anchor="w", pady=(0, 14))

        # URL Input
        self.url_entry = ctk.CTkEntry(
            self.container,
            placeholder_text="Paste YouTube link here...",
            height=40,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.url_entry.pack(fill="x", pady=(0, 14))

        # Format, Resolution & Cookies Row
        self.controls_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.controls_frame.pack(fill="x", pady=(0, 14))

        # MP4 / MP3 Segmented Toggle
        self.format_var = ctk.StringVar(value="MP4")
        self.format_switch = ctk.CTkSegmentedButton(
            self.controls_frame,
            values=["MP4", "MP3"],
            variable=self.format_var,
            command=self.on_format_change,
            height=34,
            width=130,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        self.format_switch.pack(side="left")

        # Resolution Dropdown
        self.res_var = ctk.StringVar(value="1080p")
        self.res_menu = ctk.CTkOptionMenu(
            self.controls_frame,
            values=["Best", "2160p (4K)", "1440p", "1080p", "720p", "480p"],
            variable=self.res_var,
            height=34,
            width=130,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.res_menu.pack(side="left", padx=(10, 0))

        # Cookies File Button (Click to load cookies.txt, click again to unload)
        self.cookie_btn = ctk.CTkButton(
            self.controls_frame,
            text="Cookies: None",
            width=130,
            height=34,
            fg_color="#2B2D31",
            hover_color="#383A40",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.toggle_cookies_file,
        )
        self.cookie_btn.pack(side="right")

        # Save Folder Row
        self.folder_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.folder_frame.pack(fill="x", pady=(0, 16))

        self.folder_label = ctk.CTkLabel(
            self.folder_frame,
            text=f"Save to: {self.download_dir}",
            text_color="#9CA3AF",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            anchor="w",
        )
        self.folder_label.pack(side="left", fill="x", expand=True)

        self.folder_btn = ctk.CTkButton(
            self.folder_frame,
            text="Folder",
            width=68,
            height=26,
            fg_color="#2B2D31",
            hover_color="#383A40",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.choose_folder,
        )
        self.folder_btn.pack(side="right")

        # Download Button
        self.download_btn = ctk.CTkButton(
            self.container,
            text="Download",
            height=42,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.start_download,
        )
        self.download_btn.pack(fill="x", pady=(0, 14))

        # Progress Bar & Status
        self.progress = ctk.CTkProgressBar(self.container, height=6)
        self.progress.set(0)
        self.progress.pack(fill="x", pady=(0, 8))

        self.status_label = ctk.CTkLabel(
            self.container,
            text="Ready",
            text_color="#9CA3AF",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.status_label.pack(anchor="w")

    def on_format_change(self, choice):
        if choice == "MP3":
            self.res_menu.configure(state="disabled")
        else:
            self.res_menu.configure(state="normal")

    def toggle_cookies_file(self):
        if self.cookie_file:
            # Clear loaded cookies
            self.cookie_file = None
            self.cookie_btn.configure(text="Cookies: None", fg_color="#2B2D31")
            self.status_label.configure(text="Cookies cleared.", text_color="#9CA3AF")
        else:
            # Pick a cookies.txt file
            selected = filedialog.askopenfilename(
                title="Select cookies.txt",
                filetypes=[("Cookie Files", "*.txt"), ("All Files", "*.*")],
            )
            if selected:
                self.cookie_file = selected
                self.cookie_btn.configure(text="Cookies: Loaded", fg_color="#1F6AA5")
                self.status_label.configure(
                    text=f"Loaded {os.path.basename(selected)}", text_color="#9CA3AF"
                )

    def choose_folder(self):
        selected = filedialog.askdirectory(initialdir=self.download_dir)
        if selected:
            self.download_dir = selected
            self.folder_label.configure(text=f"Save to: {self.download_dir}")

    def progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                ratio = downloaded / total
                self.after(0, lambda: self.progress.set(ratio))
                self.after(
                    0,
                    lambda: self.status_label.configure(
                        text=f"Downloading... {ratio * 100:.1f}%"
                    ),
                )
        elif d["status"] == "finished":
            self.after(0, lambda: self.progress.set(1.0))
            self.after(
                0,
                lambda: self.status_label.configure(
                    text="Processing audio/video with FFmpeg..."
                ),
            )

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(
                text="Please paste a valid YouTube link first.", text_color="#F87171"
            )
            return

        self.download_btn.configure(state="disabled", text="Downloading...")
        self.progress.set(0)
        self.status_label.configure(text="Fetching video info...", text_color="#9CA3AF")
        threading.Thread(target=self.run_ytdlp, args=(url,), daemon=True).start()

    def run_ytdlp(self, url):
        fmt = self.format_var.get()
        res = self.res_var.get()

        ydl_opts = {
            "outtmpl": os.path.join(self.download_dir, "%(title)s.%(ext)s"),
            "progress_hooks": [self.progress_hook],
            "noplaylist": True,
            "extractor_args": {"youtube": {"player_client": ["default", "-web_embedded"]}},
        }

        if fmt == "MP3":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
        else:
            height_map = {
                "2160p (4K)": "2160",
                "1440p": "1440",
                "1080p": "1080",
                "720p": "720",
                "480p": "480",
            }
            if res == "Best":
                ydl_opts["format"] = "bv*+ba/b"
            else:
                h = height_map[res]
                ydl_opts["format"] = f"bv*[height<={h}]+ba/b[height<={h}]/best"
            ydl_opts["merge_output_format"] = "mp4"

        if self.cookie_file and os.path.exists(self.cookie_file):
            ydl_opts["cookiefile"] = self.cookie_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(
                0,
                lambda: self.status_label.configure(
                    text="Download complete!", text_color="#34D399"
                ),
            )
            self.after(0, lambda: self.url_entry.delete(0, "end"))
        except Exception as e:
            err_msg = str(e).splitlines()[-1] if str(e) else "Unknown error"
            self.after(
                0,
                lambda: self.status_label.configure(
                    text=f"Error: {err_msg[:65]}", text_color="#F87171"
                ),
            )
        finally:
            self.after(
                0, lambda: self.download_btn.configure(state="normal", text="Download")
            )


if __name__ == "__main__":
    app = MinimalYTDownloader()
    app.mainloop()
