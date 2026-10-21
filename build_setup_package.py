# -*- coding: utf-8 -*-
import os, sys, zipfile, shutil, subprocess

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
        
        status_var.set("جاري بدء التثبيت واستخراج ملفات البرنامج...")
        progress_var.set(10)
        root.update()
        
        dest_dir = os.path.expandvars(r'%LOCALAPPDATA%\\Programs\\RzzakFet')
        os.makedirs(dest_dir, exist_ok=True)

        if getattr(sys, 'frozen', False):
            base_p = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_p = os.path.dirname(os.path.abspath(__file__))

        zip_cand = os.path.join(base_p, 'app.zip')
        if not os.path.exists(zip_cand):
            zip_cand = os.path.join(os.path.dirname(sys.executable), 'app.zip')

        if not os.path.exists(zip_cand):
            raise FileNotFoundError(f"لم يتم العثور على حزمة البرنامج: {zip_cand}")

        with zipfile.ZipFile(zip_cand, 'r') as zf:
            namelist = zf.namelist()
            total = len(namelist)
            for i, name in enumerate(namelist):
                zf.extract(name, dest_dir)
                if i % 25 == 0:
                    pct = 10 + int((i / total) * 70)
                    progress_var.set(pct)
                    root.update()
        
        progress_var.set(85)
        status_var.set("جاري إنشاء الاختصارات وتحديث الأيقونة الرسمية...")
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

        # Seed user data directory with state files
        user_data = os.path.expandvars(r'%LOCALAPPDATA%\\RzzakFet\\data')
        os.makedirs(user_data, exist_ok=True)
        for s_file in ['attendance_mobile_db.json', 'students_attendance_state.json', 'student_mobility_state.json', 'app_state.json']:
            for src_cand in [os.path.join(dest_dir, 'data', s_file), os.path.join(dest_dir, '_internal', 'data', s_file)]:
                if os.path.exists(src_cand):
                    tgt = os.path.join(user_data, s_file)
                    if not os.path.exists(tgt) or os.path.getsize(tgt) < 10:
                        try:
                            shutil.copy2(src_cand, tgt)
                        except Exception:
                            pass
                    break

        # Always update ui/index.html in user_data/ui to ensure fresh UI
        for ui_cand in [os.path.join(dest_dir, 'ui', 'index.html'), os.path.join(dest_dir, '_internal', 'ui', 'index.html')]:
            if os.path.exists(ui_cand):
                try:
                    os.makedirs(os.path.join(user_data, 'ui'), exist_ok=True)
                    shutil.copy2(ui_cand, os.path.join(user_data, 'ui', 'index.html'))
                except Exception:
                    pass
                break

        # Refresh Windows Shell Icon Cache immediately
        try:
            import ctypes
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        except Exception:
            pass
        
        progress_var.set(100)
        status_var.set("تم اكتمال التثبيت بنجاح! جاري تشغيل RzzakFet...")
        root.update()
        
        subprocess.Popen([exe_path], cwd=dest_dir)
        root.after(1200, root.destroy)
        
    except Exception as e:
        status_var.set(f"خطأ أثناء التثبيت: {e}")

def main():
    root = tk.Tk()
    root.title("تثبيت برنامج RzzakFet v2.0 (النسخة المتطورة)")
    root.geometry("490x290")
    root.resizable(False, False)
    root.configure(bg="#0f172a")
    root.eval('tk::PlaceWindow . center')
    
    title_lbl = tk.Label(root, text="برنامج RzzakFet المعتمد v2.0", font=("Segoe UI", 16, "bold"), fg="#38bdf8", bg="#0f172a")
    title_lbl.pack(pady=(28, 6))
    
    sub_lbl = tk.Label(root, text="التثبيت والتحديث الشامل (إصلاح النوافذ وتتبع الغياب)", font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a")
    sub_lbl.pack(pady=(0, 20))
    
    progress_var = tk.DoubleVar(value=0)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Horizontal.TProgressbar", foreground='#0ea5e9', background='#0ea5e9', troughcolor='#1e293b', thickness=10)
    
    pb = ttk.Progressbar(root, variable=progress_var, maximum=100, style="Horizontal.TProgressbar", length=390)
    pb.pack(pady=10)
    
    status_var = tk.StringVar(value="جاري فحص الحزمة والملفات...")
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

    # Check essential files in dist_dir
    pydll = os.path.join(dist_dir, "_internal", "python311.dll")
    tcldll = os.path.join(dist_dir, "_internal", "tcl86t.dll")
    mainexe = os.path.join(dist_dir, "RzzakFet.exe")
    if not os.path.exists(pydll) or not os.path.exists(tcldll) or not os.path.exists(mainexe):
        print("ERROR: dist/RzzakFet is missing critical binaries:")
        print(f"  python311.dll: {os.path.exists(pydll)}")
        print(f"  tcl86t.dll:    {os.path.exists(tcldll)}")
        print(f"  RzzakFet.exe:  {os.path.exists(mainexe)}")
        return False

    # Ensure all assets and ui are synced into dist_dir and dist_dir/_internal
    src_assets_dir = os.path.join(os.getcwd(), "assets")
    src_ui_file = os.path.join(os.getcwd(), "ui", "index.html")
    if os.path.exists(src_assets_dir):
        for target_assets in [os.path.join(dist_dir, "assets"), os.path.join(dist_dir, "_internal", "assets")]:
            os.makedirs(target_assets, exist_ok=True)
            for a_item in os.listdir(src_assets_dir):
                shutil.copy2(os.path.join(src_assets_dir, a_item), os.path.join(target_assets, a_item))
    src_icon = os.path.join(os.getcwd(), "assets", "icon.ico")
    if os.path.exists(src_icon):
        shutil.copy2(src_icon, os.path.join(dist_dir, "icon.ico"))
    if os.path.exists(src_ui_file):
        for target_ui in [os.path.join(dist_dir, "ui"), os.path.join(dist_dir, "_internal", "ui")]:
            os.makedirs(target_ui, exist_ok=True)
            shutil.copy2(src_ui_file, os.path.join(target_ui, "index.html"))

    print("1. Creating app.zip from dist/RzzakFet...")
    zip_path = os.path.join(os.getcwd(), "app.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dist_dir)
                zf.write(full_path, rel_path)

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"   app.zip created successfully! Size: {zip_size_mb:.2f} MB")
    if zip_size_mb < 30.0:
        print(f"WARNING: app.zip is suspiciously small ({zip_size_mb:.2f} MB)!")
        return False

    print("2. Writing installer_src.py...")
    with open("installer_src.py", "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write("import os\nimport sys\nimport zipfile\nimport subprocess\n")
        f.write("import tkinter as tk\nfrom tkinter import ttk\nimport threading\n\n")
        f.write(INSTALLER_FOOTER.strip() + "\n")

    print("3. Running PyInstaller on RzzakFet_v2.0_Setup.spec...")
    res = subprocess.run(["pyinstaller", "RzzakFet_v2.0_Setup.spec", "--noconfirm"])
    if res.returncode != 0:
        print("PyInstaller failed for setup.")
        return False

    setup_exe = os.path.join("dist", "RzzakFet_v2.0_Setup.exe")
    if os.path.exists(setup_exe):
        desktop_dest = os.path.join(os.path.expanduser("~"), "Desktop", "RzzakFet_v2.0_Setup.exe")
        shutil.copy2(setup_exe, desktop_dest)
        dest_size_mb = os.path.getsize(desktop_dest) / (1024 * 1024)
        print(f"4. Successfully copied {setup_exe} to {desktop_dest} (size: {dest_size_mb:.2f} MB)")
        return True
    else:
        print("Setup.exe not found in dist/")
        return False

if __name__ == "__main__":
    build_setup()
