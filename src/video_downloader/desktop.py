"""A quiet Tkinter interface. All widget access stays on the main thread."""

import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .core import QUALITY_OPTIONS, DownloadOptions, parse_urls, source_type
from .engine import DownloadEngine
from .settings import load_settings, save_settings
from .tools import diagnostics, find_tools

BG = "#0c0e11"
CARD = "#15181d"
FIELD = "#1b1f25"
BORDER = "#2c323b"
TEXT = "#f4f6f8"
MUTED = "#a8b0bb"


class VideoDownloader(tk.Tk):
    def __init__(self, preferences_path: Path | None = None):
        super().__init__()
        self.preferences_path = preferences_path
        self.preferences = load_settings(preferences_path)
        self.title("Video Downloader")
        self.geometry("920x760")
        self.minsize(760, 560)
        self.configure(bg=BG)
        self.engine = None
        self.worker = None
        self.ui_queue = queue.Queue()
        self.progress_by_job = {}
        self.total = 0
        self.closing = False
        self._destroyed = False
        self.tools = find_tools()
        self.build_ui()
        self.refresh_tools()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self.process_ui_queue)

    def label(self, parent, text, *, size=10, color=MUTED):
        return tk.Label(parent, text=text, bg=parent["bg"], fg=color, font=("Segoe UI", size))

    def button(self, parent, text, command, *, primary=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=TEXT if primary else FIELD,
            fg=BG if primary else TEXT,
            activebackground="#dfe3e7" if primary else BORDER,
            activeforeground=BG if primary else TEXT,
            relief="flat",
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
            font=("Segoe UI", 10),
            disabledforeground="#737d89",
            takefocus=True,
        )

    def card(self, parent, title):
        border = tk.Frame(parent, bg=BORDER)
        border.pack(fill="x", pady=(0, 12))
        body = tk.Frame(border, bg=CARD)
        body.pack(fill="both", expand=True, padx=1, pady=1)
        inner = tk.Frame(body, bg=CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=14)
        self.label(inner, title, size=9).pack(anchor="w", pady=(0, 9))
        return inner

    def build_ui(self):
        footer = tk.Frame(self, bg=BG)
        footer.pack(side="bottom", fill="x", padx=28, pady=(8, 18))
        self.download_btn = self.button(footer, "Download", self.start_downloads, primary=True)
        self.download_btn.pack(side="left", fill="x", expand=True)
        self.cancel_btn = self.button(footer, "Cancel", self.cancel_all)
        self.cancel_btn.pack(side="left", padx=(10, 0))
        self.cancel_btn.configure(state="disabled")

        holder = tk.Frame(self, bg=BG)
        holder.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(holder, bg=BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        shell = tk.Frame(self.canvas, bg=BG)
        window = self.canvas.create_window((0, 0), window=shell, anchor="nw")
        shell.bind(
            "<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>", lambda event: self.canvas.itemconfigure(window, width=event.width)
        )
        self.bind("<MouseWheel>", self.on_mousewheel)
        content = tk.Frame(shell, bg=BG)
        content.pack(fill="both", expand=True, padx=28, pady=(22, 0))

        title = tk.Frame(content, bg=BG)
        title.pack(fill="x", pady=(0, 4))
        self.label(title, "Video Downloader", size=25, color=TEXT).pack(side="left")
        self.button(title, "About", self.show_about).pack(side="right")
        self.label(content, "Video and audio from YouTube, Instagram, cloud links, and more.").pack(
            anchor="w", pady=(0, 18)
        )

        body = self.card(content, "LINKS")
        self.urls_text = tk.Text(
            body,
            height=4,
            bg=FIELD,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            font=("Segoe UI", 10),
            padx=12,
            pady=10,
            wrap="word",
            undo=True,
        )
        self.urls_text.pack(fill="x")
        self.urls_text.bind("<<Modified>>", self.on_text_modified)
        row = tk.Frame(body, bg=CARD)
        row.pack(fill="x", pady=(8, 0))
        self.button(row, "Paste", self.paste_links).pack(side="left")
        self.button(row, "Clear", lambda: self.urls_text.delete("1.0", "end")).pack(
            side="left", padx=(8, 0)
        )
        self.count_var = tk.StringVar(value="0 links")
        tk.Label(row, textvariable=self.count_var, bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(
            side="right"
        )

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Dark.TCombobox",
            fieldbackground=FIELD,
            background=FIELD,
            foreground=TEXT,
            arrowcolor=MUTED,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=7,
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", FIELD)],
            foreground=[("readonly", TEXT), ("disabled", MUTED)],
            selectbackground=[("readonly", FIELD)],
            selectforeground=[("readonly", TEXT)],
        )
        style.configure(
            "Dark.Horizontal.TProgressbar",
            background=TEXT,
            troughcolor=BORDER,
            borderwidth=0,
            lightcolor=TEXT,
            darkcolor=TEXT,
        )
        self.option_add("*TCombobox*Listbox.background", FIELD)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", BORDER)
        body = self.card(content, "OPTIONS")
        settings = tk.Frame(body, bg=CARD)
        settings.pack(fill="x")
        self.quality_var = tk.StringVar(value=self.preferences["quality"])
        self.mode_var = tk.StringVar(
            value={1: "One at a time", 2: "2 at a time", 3: "4 at a time", 4: "4 at a time"}[
                self.preferences["workers"]
            ]
        )
        self.cookies_var = tk.StringVar(value=self.preferences["cookies"])
        self.selects = []
        for column, (label, variable, values, width) in enumerate(
            [
                ("Quality", self.quality_var, QUALITY_OPTIONS, 33),
                ("Downloads", self.mode_var, ["4 at a time", "2 at a time", "One at a time"], 16),
                ("Browser cookies", self.cookies_var, ["None", "Chrome", "Edge", "Firefox"], 13),
            ]
        ):
            settings.columnconfigure(column, weight=1)
            frame = tk.Frame(settings, bg=CARD)
            frame.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 12, 0))
            self.label(frame, label, size=9).pack(anchor="w", pady=(0, 5))
            select = ttk.Combobox(
                frame,
                textvariable=variable,
                values=values,
                width=width,
                state="readonly",
                style="Dark.TCombobox",
                font=("Segoe UI", 9),
            )
            select.pack(fill="x")
            self.selects.append(select)
        self.label(body, "Save to", size=9).pack(anchor="w", pady=(12, 5))
        row = tk.Frame(body, bg=CARD)
        row.pack(fill="x")
        self.folder_var = tk.StringVar(value=self.preferences["folder"])
        self.folder_entry = tk.Entry(
            row,
            textvariable=self.folder_var,
            bg=FIELD,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10),
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.folder_btn = self.button(row, "Choose folder", self.choose_folder)
        self.folder_btn.pack(side="left", padx=(8, 0))

        body = self.card(content, "PROGRESS")
        row = tk.Frame(body, bg=CARD)
        row.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready")
        self.percent_var = tk.StringVar(value="0%")
        tk.Label(row, textvariable=self.status_var, bg=CARD, fg=TEXT, font=("Segoe UI", 10)).pack(
            side="left"
        )
        tk.Label(row, textvariable=self.percent_var, bg=CARD, fg=TEXT, font=("Segoe UI", 10)).pack(
            side="right"
        )
        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(
            body, variable=self.progress_var, maximum=100, style="Dark.Horizontal.TProgressbar"
        ).pack(fill="x", pady=(10, 8))
        self.detail_var = tk.StringVar(value="Paste one or more links to get started.")
        tk.Label(body, textvariable=self.detail_var, bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(
            anchor="w"
        )

        body = self.card(content, "ACTIVITY")
        self.log_text = tk.Text(
            body,
            height=4,
            bg=BG,
            fg=MUTED,
            relief="flat",
            font=("Consolas", 9),
            padx=10,
            pady=8,
            wrap="word",
            state="disabled",
        )
        self.log_text.pack(fill="x")
        self.button(body, "Clear activity", self.clear_log).pack(anchor="e", pady=(7, 0))
        row = tk.Frame(content, bg=BG)
        row.pack(fill="x", pady=(0, 10))
        self.tools_var = tk.StringVar()
        tk.Label(row, textvariable=self.tools_var, bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(
            side="left"
        )
        self.button(row, "Check tools", self.show_diagnostics).pack(side="right")

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def parse_urls(self):
        return parse_urls(self.urls_text.get("1.0", "end"))

    def on_text_modified(self, event=None):
        if self.urls_text.edit_modified():
            self.urls_text.edit_modified(False)
            count = len(self.parse_urls())
            self.count_var.set(f"{count} link" + ("" if count == 1 else "s"))

    def paste_links(self):
        try:
            value = self.clipboard_get().strip()
            if value:
                self.urls_text.insert(
                    "end", ("\n" if self.urls_text.get("1.0", "end").strip() else "") + value
                )
        except tk.TclError:
            messagebox.showinfo("Clipboard", "The clipboard does not contain text.", parent=self)

    def choose_folder(self):
        folder = filedialog.askdirectory(
            initialdir=self.folder_var.get()
            if Path(self.folder_var.get()).is_dir()
            else str(Path.home()),
            parent=self,
        )
        if folder:
            self.folder_var.set(folder)

    def refresh_tools(self):
        self.tools = find_tools()
        self.tools_var.set(
            "   ·   ".join(
                f"{name}: {'ready' if path else 'missing'}"
                for name, path in [
                    ("yt-dlp", self.tools.ytdlp),
                    ("FFmpeg", self.tools.ffmpeg),
                    ("Deno", self.tools.deno),
                ]
            )
        )

    def show_diagnostics(self):
        self.refresh_tools()
        self.log(
            "Tool paths and versions are local to your computer. Do not share private paths unnecessarily."
        )
        for name, value in diagnostics().items():
            self.log(f"{name}: {value}")

    def show_about(self):
        messagebox.showinfo(
            "About",
            f"Video Downloader {__version__}\n\nFree and open source. Own code: MIT.\nUses separately installed yt-dlp, FFmpeg and Deno.\n\nDownload only material you are allowed to save.\nFollow the source's terms and applicable law.\nNo availability guarantee. Mandatory user rights remain.\n\nDesign inspired by Emil Kowalski's principles.\nSee LICENSE and THIRD_PARTY_NOTICES for details.",
            parent=self,
        )

    def snapshot(self):
        workers = {"One at a time": 1, "2 at a time": 2, "4 at a time": 4}[self.mode_var.get()]
        return DownloadOptions(self.quality_var.get(), workers, self.cookies_var.get())

    def save_preferences(self):
        options = self.snapshot()
        try:
            save_settings(
                {
                    "folder": self.folder_var.get(),
                    "quality": options.quality,
                    "workers": options.workers,
                    "cookies": options.cookies,
                },
                self.preferences_path,
            )
        except OSError as error:
            self.log(f"Could not save settings: {error}")

    def set_controls(self, enabled):
        state = "normal" if enabled else "disabled"
        for widget in (self.download_btn, self.folder_btn, self.folder_entry, self.urls_text):
            widget.configure(state=state)
        for widget in self.selects:
            widget.configure(state="readonly" if enabled else "disabled")
        self.cancel_btn.configure(state="disabled" if enabled else "normal")

    def start_downloads(self):
        if self.worker and self.worker.is_alive():
            return
        urls = self.parse_urls()
        if not urls:
            messagebox.showinfo("Video Downloader", "Paste at least one video link.", parent=self)
            return
        self.refresh_tools()
        if not self.tools.ytdlp:
            messagebox.showerror(
                "Missing tool",
                "Install yt-dlp first.\nSee docs/windows.md or use scripts/install-tools.ps1.\nThen click Check tools.",
                parent=self,
            )
            return
        options = self.snapshot()
        needs_ffmpeg = options.quality == "Audio only · M4A" or any(
            source_type(url) not in ("Google Drive", "Yandex Disk") for url in urls
        )
        if needs_ffmpeg and not (self.tools.ffmpeg and self.tools.ffprobe):
            messagebox.showerror(
                "Missing tool",
                "Install FFmpeg with ffprobe to combine video and audio.\nSee docs/windows.md, then click Check tools.",
                parent=self,
            )
            return
        folder_value = self.folder_var.get().strip()
        if not folder_value:
            messagebox.showinfo("Save folder", "Choose a folder for your downloads.", parent=self)
            return
        folder = Path(folder_value).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror("Save folder", str(error), parent=self)
            return
        self.save_preferences()
        self.total = len(urls)
        self.progress_by_job = dict.fromkeys(range(self.total), 0.0)
        self.set_controls(False)
        self.status_var.set("Downloading")
        self.detail_var.set(f"{self.total} links, up to {options.workers} downloads at a time")
        self.update_progress()
        self.engine = DownloadEngine(options, self.tools, self.ui_queue.put)
        self.worker = threading.Thread(target=self.engine.run, args=(urls, folder), daemon=False)
        self.worker.start()

    def cancel_all(self):
        if self.engine:
            self.engine.stop.set()
            self.status_var.set("Cancelling")
            self.cancel_btn.configure(state="disabled")
            threading.Thread(target=self.engine.cancel, daemon=True).start()

    def update_progress(self):
        pct = sum(self.progress_by_job.values()) / max(1, self.total)
        self.progress_var.set(pct)
        self.percent_var.set(f"{pct:.0f}%")

    def process_ui_queue(self):
        try:
            while True:
                event = self.ui_queue.get_nowait()
                if event.kind == "log":
                    self.log(event.value)
                elif event.kind == "progress":
                    self.progress_by_job[event.job] = event.value
                    self.update_progress()
                elif event.kind == "speed":
                    self.detail_var.set(f"Link {event.job + 1}: {event.value}")
                elif event.kind == "state" and event.value == "processing":
                    self.status_var.set("Processing files")
                elif event.kind == "counts":
                    self.detail_var.set(
                        f"Saved {event.value['completed']}/{self.total} · Failed {event.value['failed']}"
                    )
                elif event.kind == "batch_done":
                    self.finish_batch(event.value)
        except queue.Empty:
            pass
        if not self.closing:
            self.after(100, self.process_ui_queue)

    def finish_batch(self, result):
        self.status_var.set(
            "Cancelled"
            if result["cancelled"]
            else "Finished with errors"
            if result["failed"]
            else "Done"
        )
        self.detail_var.set(
            f"Saved {result['completed']}/{self.total} · Failed {len(result['failed'])}"
        )
        if result["failed"]:
            self.log("Failed links are listed in failed_downloads.txt when the folder is writable.")
        self.update_progress()
        self.set_controls(True)

    def on_close(self):
        if self.closing:
            return
        self.save_preferences()
        self.closing = True
        if self.worker and self.worker.is_alive():
            self.cancel_all()
            self.after(100, self.wait_for_close)
        else:
            self.destroy()

    def wait_for_close(self):
        if self.worker and self.worker.is_alive():
            self.after(100, self.wait_for_close)
        else:
            self.destroy()

    def destroy(self):
        if self._destroyed:
            return
        self.closing = True
        for timer in self.tk.call("after", "info"):
            self.after_cancel(timer)
        self._destroyed = True
        super().destroy()
