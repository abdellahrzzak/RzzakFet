# -*- coding: utf-8 -*-
"""
RzzakFet Native Splash Screen with live progress percentage and visual identity
"""

import tkinter as tk
from tkinter import ttk
import os
import sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class RzzakFetSplashScreen:
    def __init__(self):
        self.root = None
        self.progress_val = 0
        self.status_text = None
        self.pct_text = None
        self.progress_bar = None
        self.is_running = False

    def show(self):
        try:
            self.root = tk.Tk()
            self.root.overrideredirect(True) # Borderless window
            
            width = 560
            height = 350
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            self.root.configure(bg="#0f172a") # Dark slate
            self.root.attributes('-topmost', True)

            # Outer border frame
            border_frame = tk.Frame(self.root, bg="#2563eb", bd=2)
            border_frame.pack(fill="both", expand=True, padx=2, pady=2)

            main_frame = tk.Frame(border_frame, bg="#0f172a")
            main_frame.pack(fill="both", expand=True, padx=1, pady=1)

            # Official RF logo
            logo_path = os.path.join(get_base_dir(), "assets", "icon.png")
            if os.path.exists(logo_path):
                try:
                    from PIL import Image, ImageTk
                    pil_img = Image.open(logo_path).resize((62, 62), Image.Resampling.LANCZOS)
                    self.logo_photo = ImageTk.PhotoImage(pil_img)
                    logo_lbl = tk.Label(main_frame, image=self.logo_photo, bg="#0f172a")
                    logo_lbl.pack(pady=(16, 2))
                except Exception:
                    pass

            # Header Title
            title_lbl = tk.Label(
                main_frame,
                text="برنامج RzzakFet المكتبي",
                font=("Segoe UI", 17, "bold"),
                fg="#ffffff",
                bg="#0f172a"
            )
            title_lbl.pack(pady=(4, 2))

            # Subtitle
            sub_lbl = tk.Label(
                main_frame,
                text="المعين في إعداد البنية التربوية وجداول الحصص الرسمية",
                font=("Segoe UI", 9.5),
                fg="#94a3b8",
                bg="#0f172a"
            )
            sub_lbl.pack(pady=(0, 6))

            # Version Badge v1.0
            badge_lbl = tk.Label(
                main_frame,
                text=" الإصدار الرسمي v1.0 ",
                font=("Segoe UI", 9, "bold"),
                fg="#38bdf8",
                bg="#1e293b",
                bd=1,
                relief="solid"
            )
            badge_lbl.pack(pady=(0, 12))

            # Status text & percentage frame
            info_frame = tk.Frame(main_frame, bg="#0f172a")
            info_frame.pack(fill="x", padx=45, pady=(5, 5))

            self.status_text = tk.Label(
                info_frame,
                text="جاري تهيئة بيئة العمل ومحرك الجداول...",
                font=("Segoe UI", 10),
                fg="#38bdf8",
                bg="#0f172a",
                anchor="w"
            )
            self.status_text.pack(side="left")

            self.pct_text = tk.Label(
                info_frame,
                text="15%",
                font=("Segoe UI", 10, "bold"),
                fg="#60a5fa",
                bg="#0f172a",
                anchor="e"
            )
            self.pct_text.pack(side="right")

            # Custom ttk progress style
            style = ttk.Style()
            style.theme_use('clam')
            style.configure(
                "Rzzak.Horizontal.TProgressbar",
                troughcolor="#1e293b",
                background="#2563eb",
                darkcolor="#1d4ed8",
                lightcolor="#60a5fa",
                bordercolor="#334155",
                thickness=12
            )

            self.progress_bar = ttk.Progressbar(
                main_frame,
                style="Rzzak.Horizontal.TProgressbar",
                orient="horizontal",
                length=450,
                mode="determinate"
            )
            self.progress_bar.pack(padx=45, pady=(4, 12))
            self.progress_bar["value"] = 15

            # Footer copyright
            ft_lbl = tk.Label(
                main_frame,
                text="RzzakFet Timetable Solver • جميع الحقوق محفوظة",
                font=("Segoe UI", 8),
                fg="#475569",
                bg="#0f172a"
            )
            ft_lbl.pack(side="bottom", pady=(0, 10))

            self.is_running = True
            self.root.update()
        except Exception as e:
            print("Splash error:", e)

    def update_progress(self, val, msg=""):
        if not self.root or not self.is_running:
            return
        try:
            self.progress_val = val
            if self.progress_bar:
                self.progress_bar["value"] = val
            if self.pct_text:
                self.pct_text.config(text=f"{int(val)}%")
            if msg and self.status_text:
                self.status_text.config(text=msg)
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            pass

    def close(self):
        if self.root and self.is_running:
            try:
                self.is_running = False
                self.root.destroy()
            except Exception:
                pass
