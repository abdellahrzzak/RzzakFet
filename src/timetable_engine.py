# -*- coding: utf-8 -*-
import os
import subprocess
import glob
import json
import time
import xml.etree.ElementTree as ET
import shutil
from typing import Dict, List, Any, Optional

import sys

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
BIN_DIR = os.path.join(BASE_DIR, "bin")
DATA_DIR = get_data_dir()
CACHE_FILE = os.path.join(DATA_DIR, "timetable_result.json")

DAYS_12 = [
    "الاثنين ص", "الاثنين م",
    "الثلاثاء ص", "الثلاثاء م",
    "الاربعاء ص", "الاربعاء م",
    "الخميس ص", "الخميس م",
    "الجمعة ص", "الجمعة م",
    "السبت ص", "السبت م"
]
HOURS_4 = ["ح 1", "ح 2", "ح 3", "ح 4"]

class TimetableEngine:
    def __init__(self):
        bundled_fet = os.path.join(BIN_DIR, "fet-cl.exe")
        official_fet = r"C:\fet-5.27.3-morocco40\fet-5.27.3-morocco40\fet-cl.exe"
        if os.path.exists(bundled_fet):
            self.fet_cl_exe = bundled_fet
        elif os.path.exists(official_fet):
            self.fet_cl_exe = official_fet
        else:
            self.fet_cl_exe = bundled_fet
        self.active_process = None
        self.is_aborted = False

    def stop_generation(self) -> bool:
        self.is_aborted = True
        try:
            if self.active_process:
                self.active_process.terminate()
                self.active_process.kill()
        except Exception as e:
            print("Error terminating active fet process:", e)
        if os.name == 'nt':
            try:
                subprocess.run(["taskkill", "/F", "/IM", "fet-cl.exe"], capture_output=True)
            except Exception:
                pass
        return True

    def get_cached_timetable(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("Error loading cached timetable:", e)
        return None

    def generate_timetable(self, xml_data: str, institution_data: Any, rooms_list: List[Any] = None, timeout: int = 900) -> Dict[str, Any]:
        start_time = time.time()
        self.is_aborted = False
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Build teacher-to-room fallback map from room allocation
        teacher_to_room_map = {}
        if rooms_list:
            for r in rooms_list:
                if r.morning_teacher and "شاغر" not in r.morning_teacher and r.morning_teacher != "-":
                    teacher_to_room_map[r.morning_teacher] = r.room_name
                if r.afternoon_teacher and "شاغر" not in r.afternoon_teacher and r.afternoon_teacher != "-":
                    if r.afternoon_teacher not in teacher_to_room_map:
                        teacher_to_room_map[r.afternoon_teacher] = r.room_name

        temp_input = os.path.join(DATA_DIR, "current_input.fet")
        with open(temp_input, "w", encoding="utf-8") as f:
            f.write(xml_data)

        out_dir = os.path.join(DATA_DIR, "generated_output")
        shutil.rmtree(os.path.join(out_dir, "timetables"), ignore_errors=True)
        os.makedirs(out_dir, exist_ok=True)

        if not os.path.exists(self.fet_cl_exe):
            return {
                "success": False,
                "error": "لم يتم العثور على محرك الحساب fet-cl.exe داخل مجلد bin للتطبيق.",
                "duration_seconds": 0
            }

        cmd = [
            self.fet_cl_exe,
            f"--inputfile={temp_input}",
            f"--outputdir={out_dir}"
        ]
        
        fet_bin_dir = os.path.dirname(os.path.abspath(self.fet_cl_exe))
        try:
            self.active_process = subprocess.Popen(
                cmd,
                cwd=fet_bin_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            stdout, stderr = self.active_process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.stop_generation()
            return {
                "success": False,
                "error": "انتهت المهلة الزمنية المحددة لتوليد الجدول.",
                "duration_seconds": round(time.time() - start_time, 2)
            }
        except Exception as e:
            if self.is_aborted:
                return {
                    "success": False,
                    "aborted": True,
                    "error": "تم توقيف عملية الإنتاج بواسطة المستخدم.",
                    "duration_seconds": round(time.time() - start_time, 2)
                }
            return {
                "success": False,
                "error": f"خطأ أثناء تشغيل محرك الحساب: {str(e)}",
                "duration_seconds": round(time.time() - start_time, 2)
            }
        finally:
            self.active_process = None

        if self.is_aborted:
            return {
                "success": False,
                "aborted": True,
                "error": "تم توقيف عملية الإنتاج بواسطة المستخدم.",
                "duration_seconds": round(time.time() - start_time, 2)
            }

        search_pattern = os.path.join(out_dir, "timetables", "*", "*_activities.xml")
        matches = glob.glob(search_pattern)
        if not matches:
            if self.is_aborted:
                return {
                    "success": False,
                    "aborted": True,
                    "error": "تم توقيف عملية الإنتاج بواسطة المستخدم.",
                    "duration_seconds": round(time.time() - start_time, 2)
                }
            engine_msg = stderr.strip() if stderr and stderr.strip() else (stdout.strip() if stdout else "")
            return {
                "success": False,
                "error": f"تعذر إيجاد ملفات النتائج الصادرة من محرك FET. رسالة المحرك:\n{engine_msg[:600]}",
                "duration_seconds": round(time.time() - start_time, 2)
            }

        latest_xml = max(matches, key=os.path.getmtime)

        input_tree = ET.fromstring(xml_data)
        activities_dict = {}
        for act in input_tree.find("Activities_List").findall("Activity"):
            aid = act.find("Id").text
            activities_dict[aid] = {
                "id": aid,
                "teacher": act.find("Teacher").text if act.find("Teacher") is not None else "",
                "subject": act.find("Subject").text if act.find("Subject") is not None else "",
                "students": act.find("Students").text if act.find("Students") is not None else "",
                "duration": int(act.find("Duration").text) if act.find("Duration") is not None else 1,
                "total_duration": int(act.find("Total_Duration").text) if act.find("Total_Duration") is not None else 1,
            }

        res_tree = ET.parse(latest_xml).getroot()
        
        def get_occupied_hours(start_h, dur):
            try:
                idx = HOURS_4.index(start_h)
                return HOURS_4[idx:idx+dur]
            except ValueError:
                return [start_h]

        teacher_timetables: Dict[str, Dict[str, Dict[str, Any]]] = {}
        student_timetables: Dict[str, Dict[str, Dict[str, Any]]] = {}
        room_timetables: Dict[str, Dict[str, Dict[str, Any]]] = {}
        all_activities_list: List[Dict[str, Any]] = []

        gen_rooms = [r.room_name for r in rooms_list if r.room_type == "عامة"] if rooms_list else [f"S {i}" for i in range(1, 15)]
        svt_rooms = [r.room_name for r in rooms_list if "SVT" in r.room_name or "علوم" in r.assigned_subject] if rooms_list else ["S-SVT 1", "S-SVT 2"]
        pc_rooms = [r.room_name for r in rooms_list if "PC" in r.room_name or "فيزياء" in r.assigned_subject] if rooms_list else ["S-PC 1", "S-PC 2"]
        it_rooms = [r.room_name for r in rooms_list if "INFO" in r.room_name or "إعلام" in r.assigned_subject or "معلوم" in r.assigned_subject] if rooms_list else ["S-INFO"]
        sport_rooms = [r.room_name for r in rooms_list if "Terrain" in r.room_name or "رياض" in r.assigned_subject or "بدن" in r.assigned_subject] if rooms_list else ["Terrain 1", "Terrain  2"]

        m_teacher_to_room = {}
        e_teacher_to_room = {}
        if rooms_list:
            for r in rooms_list:
                if r.morning_teacher and "شاغر" not in r.morning_teacher and r.morning_teacher != "-":
                    m_teacher_to_room[r.morning_teacher] = r.room_name
                if r.afternoon_teacher and "شاغر" not in r.afternoon_teacher and r.afternoon_teacher != "-":
                    e_teacher_to_room[r.afternoon_teacher] = r.room_name

        room_slot_occupied = {}

        for act in res_tree.findall("Activity"):
            aid = act.find("Id").text
            day = act.find("Day").text
            start_hour = act.find("Hour").text
            
            info = activities_dict.get(aid, {})
            teacher = info.get("teacher", "")
            subject = info.get("subject", "")
            students = info.get("students", "")
            dur = info.get("duration", 1)

            occupied_hours = get_occupied_hours(start_hour, dur)
            is_morning = ("ص" in day)

            raw_room = act.find("Room")
            fet_room = raw_room.text.strip() if (raw_room is not None and raw_room.text and raw_room.text.strip() and raw_room.text.strip() != "null") else None

            # Resolve room candidate pool
            if any(k in subject for k in ["علوم الحياة", "SVT"]):
                pool = svt_rooms + gen_rooms
            elif any(k in subject for k in ["الفيزياء", "PC", "الكيمياء"]):
                pool = pc_rooms + gen_rooms
            elif any(k in subject for k in ["معلوميات", "إعلاميات", "INFO"]):
                pool = it_rooms + gen_rooms
            elif any(k in subject for k in ["بدنية", "رياضة", "EPS", "Terrain"]):
                pool = sport_rooms
            else:
                primary = m_teacher_to_room.get(teacher) if is_morning else e_teacher_to_room.get(teacher)
                if not primary:
                    primary = m_teacher_to_room.get(teacher) or e_teacher_to_room.get(teacher)
                if primary:
                    pool = [primary] + [r for r in gen_rooms if r != primary]
                else:
                    pool = gen_rooms

            chosen_room = None
            if fet_room and all((fet_room, day, h) not in room_slot_occupied for h in occupied_hours):
                chosen_room = fet_room
            else:
                for r_cand in pool:
                    if all((r_cand, day, h) not in room_slot_occupied for h in occupied_hours):
                        chosen_room = r_cand
                        break
                if not chosen_room:
                    for r_cand in gen_rooms:
                        if all((r_cand, day, h) not in room_slot_occupied for h in occupied_hours):
                            chosen_room = r_cand
                            break
                if not chosen_room:
                    chosen_room = pool[0] if pool else "قاعة عامة"

            for h in occupied_hours:
                room_slot_occupied[(chosen_room, day, h)] = (teacher, subject, students)

            room = chosen_room

            all_activities_list.append({
                "id": aid,
                "teacher": teacher,
                "subject": subject,
                "students": students,
                "room": room,
                "day": day,
                "start_hour": start_hour,
                "duration": dur,
                "hours": occupied_hours
            })

            # Teacher Timetable
            if teacher:
                if teacher not in teacher_timetables:
                    teacher_timetables[teacher] = {d: {h: None for h in HOURS_4} for d in DAYS_12}
                for h in occupied_hours:
                    teacher_timetables[teacher][day][h] = {
                        "subject": subject,
                        "students": students,
                        "room": room,
                        "duration": dur,
                        "is_first": (h == start_hour)
                    }

            # Student / Class Timetable
            if students:
                if students not in student_timetables:
                    student_timetables[students] = {d: {h: None for h in HOURS_4} for d in DAYS_12}
                for h in occupied_hours:
                    student_timetables[students][day][h] = {
                        "subject": subject,
                        "teacher": teacher,
                        "room": room,
                        "duration": dur,
                        "is_first": (h == start_hour)
                    }

            # Room Timetable
            if room:
                if room not in room_timetables:
                    room_timetables[room] = {d: {h: None for h in HOURS_4} for d in DAYS_12}
                for h in occupied_hours:
                    room_timetables[room][day][h] = {
                        "subject": subject,
                        "teacher": teacher,
                        "students": students,
                        "duration": dur,
                        "is_first": (h == start_hour)
                    }

        elapsed = round(time.time() - start_time, 2)

        # Master Teachers Matrix structure
        teachers_list = sorted(list(teacher_timetables.keys()))
        master_teachers_data = []
        for t in teachers_list:
            # find subject
            t_subj = ""
            for d in DAYS_12:
                for h in HOURS_4:
                    cell = teacher_timetables[t][d][h]
                    if cell:
                        t_subj = cell["subject"]
                        break
                if t_subj: break

            t_row = {
                "teacher": t,
                "subject": t_subj,
                "room": teacher_to_room_map.get(t, "عامة"),
                "schedule": teacher_timetables[t]
            }
            master_teachers_data.append(t_row)

        result = {
            "success": True,
            "error": None,
            "duration_seconds": elapsed,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_activities": len(all_activities_list),
            "teachers_count": len(teacher_timetables),
            "classes_count": len(student_timetables),
            "rooms_count": len(room_timetables),
            "days": DAYS_12,
            "hours": HOURS_4,
            "teachers_list": teachers_list,
            "classes_list": sorted(list(student_timetables.keys())),
            "rooms_list": sorted(list(room_timetables.keys())),
            "teacher_timetables": teacher_timetables,
            "student_timetables": student_timetables,
            "room_timetables": room_timetables,
            "master_teachers_data": master_teachers_data,
            "institution_info": {
                "name": getattr(institution_data, "institution_name", "المؤسسة التعليمية"),
                "province": getattr(institution_data, "province", "المديرية الإقليمية"),
                "academy": getattr(institution_data, "academy", "الأكاديمية الجهوية"),
                "year": getattr(institution_data, "academic_year", "2026-2027"),
                "gresa": getattr(institution_data, "gresa_code", ""),
                "principal": getattr(institution_data, "principal_name", ""),
                "pe_wednesday_label": getattr(institution_data, "pe_wednesday_label", "أنشطة الجمعية الرياضية المدرسية (ASS)"),
                "general_wednesday_label": getattr(institution_data, "general_wednesday_label", "الأنشطة الموازية والدعم التربوي"),
                "enable_wednesday_labels": getattr(institution_data, "enable_wednesday_labels", True)
            }
        }

        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error saving timetable cache:", e)

        return result
