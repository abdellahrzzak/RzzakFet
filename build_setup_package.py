# -*- coding: utf-8 -*-
import os, sys, io, base64, zipfile, shutil, subprocess

INSTALLER_FOOTER = '''
def create_shortcut(target, link_path, icon_path=None, desc=""):
    try:
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(link_path)
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.Description = desc
        if icon_path and os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        else:
            shortcut.IconLocation = f"{target},0"
        shortcut.save()
        return
    except Exception:
        pass

    try:
        ico = f"{icon_path},0" if (icon_path and os.path.exists(icon_path)) else f"{target},0"
        ps_cmd = f'$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\\"{link_path}\\"); $Shortcut.TargetPath = \\"{target}\\"; $Shortcut.WorkingDirectory = \\"{os.path.dirname(target)}\\"; $Shortcut.IconLocation = \\"{ico}\\"; $Shortcut.Description = \\"{desc}\\"; $Shortcut.Save()'
        subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd], capture_output=True)
    except Exception:
        pass

def install_app(progress_var, status_var, root):
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'RzzakFet.exe'], capture_output=True)
        
        status_var.set("جاري بدء التثبيت واستخراج الملفات...")
        progress_var.set(20)
        root.update()
        
        dest_dir = os.path.expandvars(r'%LOCALAPPDATA%\\Programs\\RzzakFet')
        os.makedirs(dest_dir, exist_ok=True)
        
        raw_zip = base64.b64decode(ZIP_DATA)
        with zipfile.ZipFile(io.BytesIO(raw_zip), 'r') as zf:
            total = len(zf.namelist())
            for i, name in enumerate(zf.namelist()):
                zf.extract(name, dest_dir)
                if i % 15 == 0:
                    pct = 20 + int((i / total) * 60)
                    progress_var.set(pct)
                    root.update()
        
        progress_var.set(85)
        status_var.set("جاري تسجيل الاختصارات وأيقونة التطبيق...")
        root.update()
        
        exe_path = os.path.join(dest_dir, 'RzzakFet.exe')
        icon_path = os.path.join(dest_dir, 'assets', 'icon.ico')
        if not os.path.exists(icon_path):
            alt_icon = os.path.join(dest_dir, '_internal', 'assets', 'icon.ico')
            if os.path.exists(alt_icon):
                icon_path = alt_icon
                try:
                    os.makedirs(os.path.join(dest_dir, 'assets'), exist_ok=True)
                    shutil.copy2(alt_icon, os.path.join(dest_dir, 'assets', 'icon.ico'))
                    shutil.copy2(alt_icon, os.path.join(dest_dir, 'icon.ico'))
                except Exception:
                    pass
            else:
                icon_path = exe_path
        
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        create_shortcut(exe_path, os.path.join(desktop, 'RzzakFet.lnk'), icon_path, 'RzzakFet - برنامج إسناد وتوليد الجداول المدرسية')
        
        programs = os.path.expandvars(r'%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs')
        create_shortcut(exe_path, os.path.join(programs, 'RzzakFet.lnk'), icon_path, 'RzzakFet - برنامج إسناد وتوليد الجداول المدرسية')

        # Refresh Windows Shell Icon Cache immediately
        try:
            import ctypes
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        except Exception:
            pass
        
        progress_var.set(100)
        status_var.set("تم اكتمال التثبيت بنجاح! جاري فتح البرنامج...")
        root.update()
        
        subprocess.Popen([exe_path], cwd=dest_dir)
        root.after(1200, root.destroy)
        
    except Exception as e:
        status_var.set(f"خطأ أثناء التثبيت: {e}")

def main():
    root = tk.Tk()
    root.title("تثبيت برنامج RzzakFet v2.0 (النسخة الثانية)")
    root.geometry("490x290")
    root.resizable(False, False)
    root.configure(bg="#0f172a")
    root.eval('tk::PlaceWindow . center')
    
    title_lbl = tk.Label(root, text="برنامج RzzakFet المكتبي v2.0", font=("Segoe UI", 16, "bold"), fg="#38bdf8", bg="#0f172a")
    title_lbl.pack(pady=(28, 6))
    
    sub_lbl = tk.Label(root, text="النسخة الثانية المتقدمة - بنك القيود الشامل (68 قيداً وتخصيص فردي وجماعي)", font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a")
    sub_lbl.pack(pady=(0, 20))
    
    progress_var = tk.DoubleVar(value=0)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Horizontal.TProgressbar", foreground='#0ea5e9', background='#0ea5e9', troughcolor='#1e293b', thickness=10)
    
    pb = ttk.Progressbar(root, variable=progress_var, maximum=100, style="Horizontal.TProgressbar", length=390)
    pb.pack(pady=10)
    
    status_var = tk.StringVar(value="جاري التحضير...")
    status_lbl = tk.Label(root, textvariable=status_var, font=("Segoe UI", 10), fg="#e2e8f0", bg="#0f172a")
    status_lbl.pack(pady=8)
    
    root.after(400, lambda: threading.Thread(target=install_app, args=(progress_var, status_var, root), daemon=True).start())
    root.mainloop()

if __name__ == '__main__':
    main()
'''

def build_setup():
    dist_dir = os.path.join(os.getcwd(), "dist", "RzzakFet")
    if not os.path.exists(dist_dir):
        print(f"Error: {dist_dir} does not exist.")
        return False

    # Ensure icon is present in dist_dir root and assets/
    src_icon = os.path.join(os.getcwd(), "assets", "icon.ico")
    if os.path.exists(src_icon):
        os.makedirs(os.path.join(dist_dir, "assets"), exist_ok=True)
        shutil.copy2(src_icon, os.path.join(dist_dir, "assets", "icon.ico"))
        shutil.copy2(src_icon, os.path.join(dist_dir, "icon.ico"))

    print("1. Creating in-memory zip of dist/RzzakFet...")
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dist_dir)
                zf.write(full_path, rel_path)

    raw_zip = zip_buf.getvalue()
    print(f"   Zip size: {len(raw_zip) / (1024*1024):.2f} MB")
    
    print("2. Base64 encoding...")
    b64_data = base64.b64encode(raw_zip).decode("ascii")

    print("3. Writing updated installer_src.py...")
    with open("installer_src.py", "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write("import os\nimport sys\nimport base64\nimport zipfile\nimport io\nimport subprocess\n")
        f.write("import tkinter as tk\nfrom tkinter import ttk\nimport threading\n\n")
        f.write('ZIP_DATA = """' + b64_data + '"""\n\n')
        f.write(INSTALLER_FOOTER.strip() + "\n")

    print("4. Running PyInstaller on RzzakFet_v2.0_Setup.spec...")
    res = subprocess.run(["pyinstaller", "RzzakFet_v2.0_Setup.spec", "--noconfirm"], capture_output=True, text=True)
    if res.returncode != 0:
        print("PyInstaller failed:", res.stderr[-500:])
        return False

    setup_exe = os.path.join("dist", "RzzakFet_v2.0_Setup.exe")
    if os.path.exists(setup_exe):
        desktop_dest = os.path.join(os.path.expanduser("~"), "Desktop", "RzzakFet_v2.0_Setup.exe")
        shutil.copy2(setup_exe, desktop_dest)
        print(f"5. Successfully copied {setup_exe} to {desktop_dest} (size: {os.path.getsize(desktop_dest)/(1024*1024):.2f} MB)")
        return True
    else:
        print("Setup.exe not found in dist/")
        return False

if __name__ == "__main__":
    build_setup()
