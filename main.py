# -*- coding: utf-8 -*-
"""
RzzakFet Desktop Application Launcher
Runs as a true embedded Native Windows Desktop Application Window via pywebview (Edge WebView2)
"""

import sys
import os
import threading
import time
import multiprocessing
import urllib.request
import webbrowser
import ctypes
from http.server import ThreadingHTTPServer
from src.desktop_server import RzzakFetHandler

APP_PORT = 8765
APP_ID = "rzzakfet.timetable.desktop.2.0"
APP_TITLE = "RzzakFet v2.0 - برنامج إسناد وتوليد الجداول المدرسية (النسخة الثانية المتقدمة)"

# 1. Set explicit Windows AppUserModelID before any GUI creation
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
except Exception:
    pass

def get_app_icon_path():
    """Finds the high-resolution application icon path across development and frozen environments."""
    candidates = []
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', '')
        exe_dir = os.path.dirname(sys.executable)
        candidates.extend([
            os.path.join(meipass, 'assets', 'icon.ico'),
            os.path.join(exe_dir, '_internal', 'assets', 'icon.ico'),
            os.path.join(exe_dir, 'assets', 'icon.ico'),
            os.path.join(exe_dir, 'icon.ico'),
        ])
    else:
        base = os.path.dirname(os.path.abspath(__file__))
        candidates.extend([
            os.path.join(base, 'assets', 'icon.ico'),
            os.path.join(base, 'assets', 'icon.png'),
        ])
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    return None

def apply_taskbar_icon(title, icon_path):
    """Directly sends Win32 WM_SETICON to guarantee taskbar and titlebar icon display."""
    if not icon_path or not os.path.isfile(icon_path):
        return
    try:
        from ctypes import wintypes
        hwnd = ctypes.windll.user32.FindWindowW(None, title)
        if not hwnd:
            return
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040

        LoadImageW = ctypes.windll.user32.LoadImageW
        LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        LoadImageW.restype = wintypes.HANDLE

        SendMessageW = ctypes.windll.user32.SendMessageW

        hicon_big = LoadImageW(None, icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
        hicon_small = LoadImageW(None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)

        if hicon_big:
            SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
        if hicon_small:
            SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
    except Exception:
        pass

def is_server_alive(port=APP_PORT, timeout=0.25):
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=timeout)
        if req.status == 200:
            return True
    except Exception:
        pass
    return False

def start_server(port=APP_PORT):
    try:
        ThreadingHTTPServer.allow_reuse_address = True
        server = ThreadingHTTPServer(('127.0.0.1', port), RzzakFetHandler)
        server.serve_forever()
    except Exception as e:
        print(f"[RzzakFet Server Notice]: {e}")

def wait_for_server(port=APP_PORT, timeout=5.0):
    start = time.time()
    while time.time() - start < timeout:
        if is_server_alive(port, timeout=0.15):
            return True
        time.sleep(0.02)
    return False

def dismiss_splash():
    """Safely closes PyInstaller bootloader splash screen without any blank delay."""
    try:
        import pyi_splash
        if pyi_splash.is_alive():
            pyi_splash.close()
    except Exception:
        pass

def main():
    multiprocessing.freeze_support()

    # 1. Start local background server
    if not is_server_alive(APP_PORT):
        t = threading.Thread(target=start_server, args=(APP_PORT,), daemon=True)
        t.start()
        wait_for_server(APP_PORT)

    url = f"http://127.0.0.1:{APP_PORT}/?v={int(time.time())}"
    icon_path = get_app_icon_path()

    # Failsafe timer: ensures splash is closed even if webview takes unusually long
    failsafe = threading.Timer(8.0, dismiss_splash)
    failsafe.daemon = True
    failsafe.start()

    # 2. Launch Native Windows Desktop Window using pywebview
    try:
        import webview
        window = webview.create_window(
            title=APP_TITLE,
            url=url,
            width=1320,
            height=880,
            min_size=(1050, 680),
            confirm_close=False,
            easy_drag=False,
            background_color="#020617"
        )

        def on_ui_ready():
            dismiss_splash()
            apply_taskbar_icon(APP_TITLE, icon_path)

        window.events.shown += on_ui_ready
        window.events.loaded += on_ui_ready

        def on_gui_ready(w):
            on_ui_ready()

        webview.start(on_gui_ready, window, gui="edgechromium", icon=icon_path, debug=False)
        return
    except Exception as e:
        dismiss_splash()
        print(f"[Native Window Notice]: {e}")

    # 3. Fallback to default browser
    dismiss_splash()
    webbrowser.open(url)
    while True:
        try:
            time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            break

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

