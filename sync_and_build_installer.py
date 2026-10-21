# -*- coding: utf-8 -*-
import os, sys, time, shutil, subprocess

def main():
    print("1. Terminating any running instances of RzzakFet.exe...")
    os.system('taskkill /F /IM RzzakFet.exe 2>nul')
    os.system('taskkill /F /IM fet-cl.exe 2>nul')
    time.sleep(2)

    print("0. Syncing entire ui/ folder and assets...")
    src_ui = os.path.abspath('ui')
    src_assets = os.path.abspath('assets')

    for dest_ui in [
        os.path.abspath('data/ui'),
        os.path.abspath('dist/RzzakFet/ui'),
        os.path.abspath('dist/RzzakFet/_internal/ui'),
        os.path.expandvars(r'%LOCALAPPDATA%\RzzakFet\data\ui'),
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\RzzakFet\ui'),
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\RzzakFet\_internal\ui'),
    ]:
        if os.path.exists(os.path.dirname(dest_ui)):
            try:
                os.makedirs(dest_ui, exist_ok=True)
                for item in os.listdir(src_ui):
                    s_file = os.path.join(src_ui, item)
                    d_file = os.path.join(dest_ui, item)
                    if os.path.isfile(s_file):
                        shutil.copy2(s_file, d_file)
                print(f"   Synced ui/ -> {dest_ui}")
            except Exception as e:
                print(f"   Skip ui {dest_ui}: {e}")

    # Sync assets
    for a_dest in [
        os.path.abspath('dist/RzzakFet/assets'),
        os.path.abspath('dist/RzzakFet/_internal/assets'),
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\RzzakFet\assets'),
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\RzzakFet\_internal\assets'),
    ]:
        if os.path.exists(os.path.dirname(a_dest)):
            try:
                os.makedirs(a_dest, exist_ok=True)
                for item in os.listdir(src_assets):
                    shutil.copy2(os.path.join(src_assets, item), os.path.join(a_dest, item))
                print(f"   Synced assets -> {a_dest}")
            except Exception as e:
                print(f"   Skip assets {a_dest}: {e}")

    # Sync state files to user AppData and dist data folders
    user_data_dir = os.path.expandvars(r'%LOCALAPPDATA%\RzzakFet\data')
    os.makedirs(user_data_dir, exist_ok=True)
    state_files = ['attendance_mobile_db.json', 'students_attendance_state.json', 'student_mobility_state.json', 'app_state.json']
    for state_filename in state_files:
        src_state = os.path.abspath(os.path.join('data', state_filename))
        if os.path.exists(src_state) and os.path.getsize(src_state) > 10:
            target_user_file = os.path.join(user_data_dir, state_filename)
            shutil.copy2(src_state, target_user_file)
            print(f"   Seeded {state_filename} -> {target_user_file}")
            for d_target in [
                os.path.abspath(os.path.join('dist/RzzakFet/data', state_filename)),
                os.path.abspath(os.path.join('dist/RzzakFet/_internal/data', state_filename))
            ]:
                if os.path.exists(os.path.dirname(d_target)):
                    os.makedirs(os.path.dirname(d_target), exist_ok=True)
                    shutil.copy2(src_state, d_target)

    dist = os.path.abspath('dist/RzzakFet')
    target = os.path.expandvars(r'%LOCALAPPDATA%\Programs\RzzakFet')

    print("2. Syncing dist/RzzakFet to LocalAppData...")
    if os.path.exists(target):
        for attempt in range(5):
            try:
                for item in os.listdir(dist):
                    s = os.path.join(dist, item)
                    d = os.path.join(target, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d, ignore_errors=True)
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
                print("   SUCCESS: Synced to LocalAppData successfully!")
                break
            except Exception as e:
                print(f"   Attempt {attempt+1} failed: {e}")
                time.sleep(2)

    print("3. Building setup installer via build_setup_package.py...")
    res = subprocess.run([sys.executable, 'build_setup_package.py'])
    if res.returncode == 0:
        print("   SUCCESS: Desktop Setup Package built successfully!")
    else:
        print(f"   ERROR: build_setup_package.py failed with code {res.returncode}")

if __name__ == '__main__':
    main()
