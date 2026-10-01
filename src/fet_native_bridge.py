# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import glob
import json
import time
import shutil
from typing import Dict, Any, Optional, List

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_dir():
    if getattr(sys, 'frozen', False):
        app_data = os.path.join(os.path.expanduser("~"), "AppData", "Local", "RzzakFet")
        os.makedirs(app_data, exist_ok=True)
        return os.path.join(app_data, "data")
    return os.path.join(get_base_dir(), "data")

BASE_DIR = get_base_dir()
DATA_DIR = get_data_dir()
FET_OFFICIAL_DIR = r"C:\fet-5.27.3-morocco40\fet-5.27.3-morocco40"

class FetNativeBridge:
    def __init__(self, fet_dir: Optional[str] = None):
        bin_dir = os.path.join(BASE_DIR, "bin")
        if fet_dir and os.path.exists(fet_dir):
            self.fet_dir = fet_dir
        elif os.path.exists(bin_dir) and os.path.exists(os.path.join(bin_dir, "fet.exe")):
            self.fet_dir = bin_dir
        elif os.path.exists(FET_OFFICIAL_DIR):
            self.fet_dir = FET_OFFICIAL_DIR
        else:
            self.fet_dir = bin_dir
        self.fet_exe = os.path.join(self.fet_dir, "fet.exe")
        self.fet_cl_exe = os.path.join(self.fet_dir, "fet-cl.exe")
        self.timetables_dir = os.path.join(self.fet_dir, "timetables")
        os.makedirs(DATA_DIR, exist_ok=True)

    def is_installed(self) -> bool:
        return os.path.exists(self.fet_exe)

    def get_status(self) -> Dict[str, Any]:
        return {
            "installed": self.is_installed(),
            "fet_dir": self.fet_dir,
            "fet_exe": self.fet_exe,
            "has_gui": os.path.exists(self.fet_exe),
            "has_cli": os.path.exists(self.fet_cl_exe),
            "timetables_dir_exists": os.path.exists(self.timetables_dir)
        }

    def prepare_fet_file(self, xml_content: str, filename_prefix: str = "RzzakFet_Institution") -> str:
        """Saves .fet file in both data/ and inside FET working directory for instant loading."""
        safe_prefix = "".join([c if c.isalnum() or c in "_-" else "_" for c in filename_prefix])
        filename = f"{safe_prefix}.fet"
        
        # 1. Save in local data dir
        local_path = os.path.join(DATA_DIR, filename)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        
        # 2. Also copy directly to FET installation directory for seamless access
        if os.path.exists(self.fet_dir):
            try:
                fet_root_path = os.path.join(self.fet_dir, filename)
                with open(fet_root_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)
                return fet_root_path
            except Exception as e:
                print("Note: could not write to FET root dir:", e)

        return local_path

    def launch_fet_gui(self, xml_content: Optional[str] = None, institution_name: str = "Institution") -> Dict[str, Any]:
        """Launches official Moroccan FET 5.27.3 with pre-loaded XML file."""
        if not os.path.exists(self.fet_exe):
            return {
                "success": False,
                "error": f"برنامج FET غير موجود بالمسار: {self.fet_exe}"
            }

        target_fet_path = None
        if xml_content:
            target_fet_path = self.prepare_fet_file(xml_content, f"RzzakFet_{institution_name}")

        try:
            cmd = [self.fet_exe]
            if target_fet_path and os.path.exists(target_fet_path):
                cmd.append(target_fet_path)

            # Launch detached process so Python server remains free
            if sys.platform == "win32":
                subprocess.Popen(
                    cmd,
                    cwd=self.fet_dir,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                subprocess.Popen(cmd, cwd=self.fet_dir)

            return {
                "success": True,
                "message": "تم تشغيل برنامج FET المغربي الرسمي بنجاح.",
                "loaded_file": target_fet_path,
                "fet_exe": self.fet_exe
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ أثناء تشغيل برنامج FET: {str(e)}"
            }

    def open_working_directory(self) -> Dict[str, Any]:
        """Opens FET directory in Windows File Explorer."""
        try:
            target_dir = self.fet_dir if os.path.exists(self.fet_dir) else DATA_DIR
            if sys.platform == "win32":
                os.startfile(target_dir)
            return {"success": True, "path": target_dir}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_latest_generated_xml(self) -> Optional[str]:
        """Scans FET directories for the latest timetable XML file."""
        search_dirs = [
            os.path.join(self.fet_dir, "timetables"),
            self.timetables_dir,
            os.path.join(DATA_DIR, "generated_output"),
            DATA_DIR
        ]

        xml_files = []
        for d in search_dirs:
            if os.path.exists(d):
                for f in glob.glob(os.path.join(d, "**", "*_timetable.xml"), recursive=True):
                    xml_files.append(f)
                for f in glob.glob(os.path.join(d, "**", "*_data_and_timetable.xml"), recursive=True):
                    xml_files.append(f)

        if not xml_files:
            return None

        # Sort by modification time descending
        xml_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return xml_files[0]
