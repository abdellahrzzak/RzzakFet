
def _get_server_fn(fn_name: str, fallback=None):
    """Safely retrieves a function from desktop_server without circular import errors."""
    import sys
    for mod_name in ('src.desktop_server', 'desktop_server', '__main__'):
        mod = sys.modules.get(mod_name)
        if mod and hasattr(mod, fn_name):
            return getattr(mod, fn_name)
    try:
        import desktop_server
        if hasattr(desktop_server, fn_name):
            return getattr(desktop_server, fn_name)
    except Exception:
        pass
    try:
        from . import desktop_server as ds
        if hasattr(ds, fn_name):
            return getattr(ds, fn_name)
    except Exception:
        pass
    return fallback

# -*- coding: utf-8 -*-
"""
Master Timetable Engine (القاعدة البيانية الأساسية المعتمدة لجدول الحصص)
------------------------------------------------------------------------
This engine serves as the ABSOLUTE SINGLE SOURCE OF TRUTH for:
- Timetable views and distribution (Tab 10)
- Teaching assignment sheet / ورقة الإسناد (Tab 11)
- Teachers list and assigned rooms / هيئة التدريس والقاعات (Tab 4 & 5)
- Mobile Attendance PWA and teacher login codes / مسك وتتبع غياب التلاميذ
- General surveillance daily reports / تقارير الحراسة العامة والمواظبة
- Exam planning & availability engine / برمجة وتتبع الفروض المحروسة
- Cloud Firestore 24/7 synchronization

Any official timetable uploaded via the prominent Master Timetable button (.xml, .fet, .xlsx, .json, .zip)
or adopted from the current FET generation is parsed here and propagated across all subsystems.
"""

import os
import sys
import json
import glob
import time
import zipfile
import secrets
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

DAYS_12 = [
    "الاثنين ص", "الاثنين م",
    "الثلاثاء ص", "الثلاثاء م",
    "الاربعاء ص", "الاربعاء م",
    "الخميس ص", "الخميس م",
    "الجمعة ص", "الجمعة م",
    "السبت ص", "السبت م"
]
HOURS_4 = ["ح 1", "ح 2", "ح 3", "ح 4"]

DAY_NAME_TO_DOW = {
    "الاثنين": 1, "الإثنين": 1, "Lundi": 1, "Monday": 1,
    "الثلاثاء": 2, "Mardi": 2, "Tuesday": 2,
    "الاربعاء": 3, "الأربعاء": 3, "Mercredi": 3, "Wednesday": 3,
    "الخميس": 4, "Jeudi": 4, "Thursday": 4,
    "الجمعة": 5, "Vendredi": 5, "Friday": 5,
    "السبت": 6, "Samedi": 6, "Saturday": 6
}

def clean_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip(' \t\r\n\ufeff')

def generate_8char_code(used_set: set) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        if code not in used_set:
            used_set.add(code)
            return code

def parse_day_and_hour(day_raw: str, hour_raw: str) -> Tuple[str, str, int, int, str]:
    """
    Returns (day_12, hour_4, day_of_week_1_to_6, slot_index_1_to_8, period_ص_or_م)
    """
    d_clean = clean_str(day_raw)
    h_clean = clean_str(hour_raw)
    
    # Detect period
    period = "ص"
    if " م" in d_clean or "مساء" in d_clean or "soir" in d_clean.lower() or "pm" in d_clean.lower():
        period = "م"
    elif " ص" in d_clean or "صباح" in d_clean or "matin" in d_clean.lower() or "am" in d_clean.lower():
        period = "ص"

    # Base day name
    base_day = "الاثنين"
    for d_name in ["الاثنين", "الإثنين", "الثلاثاء", "الاربعاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]:
        if d_name in d_clean:
            base_day = "الاربعاء" if d_name in ["الاربعاء", "الأربعاء"] else ("الاثنين" if d_name in ["الاثنين", "الإثنين"] else d_name)
            break
            
    dow = DAY_NAME_TO_DOW.get(base_day, 1)

    # Detect hour number (1 to 4 or 1 to 8)
    hour_num = 1
    import re
    h_match = re.search(r'(\d+)', h_clean)
    if h_match:
        hour_num = int(h_match.group(1))

    if hour_num > 4 and hour_num <= 8:
        # 8-hour format
        period = "م"
        h_in_period = hour_num - 4
        slot_idx = hour_num
    else:
        h_in_period = max(1, min(4, hour_num))
        slot_idx = (h_in_period) if period == "ص" else (h_in_period + 4)

    day_12 = f"{base_day} {period}"
    hour_4 = f"ح {h_in_period}"
    return (day_12, hour_4, dow, slot_idx, period)

class MasterTimetableEngine:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.active_info_file = os.path.join(data_dir, "active_master_timetable_info.json")
        self.cache_file = os.path.join(data_dir, "timetable_result.json")

    def get_active_info(self) -> Dict[str, Any]:
        if os.path.exists(self.active_info_file):
            try:
                with open(self.active_info_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Fallback to cache file info
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "filename": "جدول الحصص المعتمد",
                        "adopted_at": data.get("generated_at", "معتمد"),
                        "teachers_count": len(data.get("teacher_timetables", {})),
                        "classes_count": len(data.get("student_timetables", {})),
                        "slots_count": data.get("total_activities", 0),
                        "status": "ACTIVE"
                    }
            except Exception:
                pass
        return {
            "filename": "لا يوجد جدول معتمد بعد",
            "adopted_at": "-",
            "teachers_count": 0,
            "classes_count": 0,
            "slots_count": 0,
            "status": "EMPTY"
        }

    def save_active_info(self, info: Dict[str, Any]):
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.active_info_file, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MasterTimetableEngine] Error saving active info: {e}")

    def parse_any_timetable(self, file_content: Any, filename: str = "", file_bytes: bytes = None) -> Dict[str, Any]:
        """
        Universal parser for all timetable formats:
        - FET Output XML (*_activities.xml, *_teachers.xml, *_data_and_timetable.fet / .xml)
        - FET Data XML (.fet)
        - Excel Master Timetable (.xlsx / .xls)
        - JSON / RZF backup (timetable_result.json)
        - ZIP containing FET output files
        """
        fn_lower = filename.lower()
        
        # 1. ZIP Archive (e.g. zipped FET output folder)
        if fn_lower.endswith(".zip") and file_bytes:
            return self._parse_zip_archive(file_bytes, filename)

        # 2. Excel Master Timetable (.xlsx, .xlsm, .xls)
        if fn_lower.endswith((".xlsx", ".xlsm", ".xls")) or (file_bytes and len(file_bytes) > 4 and file_bytes[:4] == b'PK\x03\x04' and not fn_lower.endswith(".zip")):
            parse_master_timetable_from_excel = _get_server_fn("parse_master_timetable_from_excel")
            parsed_excel = parse_master_timetable_from_excel(file_bytes)
            if parsed_excel.get("success") and parsed_excel.get("teacher_timetables"):
                return self._enrich_parsed_timetable(parsed_excel, filename)

        # 2b. CSV Master Timetable
        raw_text = ""
        if isinstance(file_content, str):
            raw_text = file_content
        elif file_bytes:
            raw_text = file_bytes.decode("utf-8", errors="ignore")

        raw_trimmed = raw_text.strip()
        if fn_lower.endswith(".csv") or ("," in raw_trimmed[:500] and any(k in raw_trimmed for k in ("الأستاذ", "الاستاذ", "المادة", "القاعة", "الاثنين", "TCSEF", "1BAC", "2BAC", "TC-SC", "2BACSVT"))):
            csv_res = self._parse_csv_master_timetable(raw_trimmed, filename)
            if csv_res.get("success"):
                return csv_res

        # 3. JSON Timetable (.json or .rzf)
        raw_text = ""
        if isinstance(file_content, str):
            raw_text = file_content
        elif file_bytes:
            raw_text = file_bytes.decode("utf-8", errors="ignore")

        raw_trimmed = raw_text.strip()
        if fn_lower.endswith((".json", ".rzf")) or raw_trimmed.startswith("{"):
            try:
                j_obj = json.loads(raw_trimmed)
                tt_data = j_obj.get("timetable") or j_obj
                if isinstance(tt_data, dict) and ("teacher_timetables" in tt_data or "master_teachers_data" in tt_data):
                    return self._enrich_parsed_timetable(tt_data, filename)
            except Exception as e:
                print(f"[MasterTimetableEngine] JSON parse attempt failed: {e}")

        # 4. XML / FET File
        if "<fet" in raw_trimmed.lower() or "<activities_timetable" in raw_trimmed.lower() or "<teachers_timetable" in raw_trimmed.lower() or "<timetable" in raw_trimmed.lower():
            return self._parse_xml_timetable(raw_trimmed, filename)

        return {"success": False, "error": f"تعذر التعرف على صيغة ملف الجدول ({filename}). يرجى التأكد من اختيار ملف FET أو XML أو Excel أو JSON معتمد."}


    def _parse_csv_master_timetable(self, csv_str: str, filename: str) -> Dict[str, Any]:
        """
        Parses Moroccan official CSV Master Timetable (الجدول العام لاستعمالات الزمن للمدرسين)
        Columns: [Teacher, Subject, Room, P1..P48]
        P1..P48 corresponds to 12 half-days x 4 hours:
          الاثنين ص (1..4), الاثنين م (1..4), الثلاثاء ص (1..4), الثلاثاء م (1..4)...
        """
        import csv, io

        lines = list(csv.reader(io.StringIO(csv_str)))
        if not lines:
            return {"success": False, "error": "ملف CSV فارغ"}

        # Find header row
        header_idx = -1
        for i, row in enumerate(lines[:15]):
            row_str = " ".join(row).lower()
            if any(k in row_str for k in ("أستاذ", "استاذ", "مدرس", "prof", "teacher")):
                header_idx = i
                break

        if header_idx == -1:
            header_idx = 0

        PERIODS_48 = [
            ("الاثنين ص", "ح 1", 1, 1, "ص"), ("الاثنين ص", "ح 2", 1, 2, "ص"), ("الاثنين ص", "ح 3", 1, 3, "ص"), ("الاثنين ص", "ح 4", 1, 4, "ص"),
            ("الاثنين م", "ح 1", 1, 5, "م"), ("الاثنين م", "ح 2", 1, 6, "م"), ("الاثنين م", "ح 3", 1, 7, "م"), ("الاثنين م", "ح 4", 1, 8, "م"),
            ("الثلاثاء ص", "ح 1", 2, 1, "ص"), ("الثلاثاء ص", "ح 2", 2, 2, "ص"), ("الثلاثاء ص", "ح 3", 2, 3, "ص"), ("الثلاثاء ص", "ح 4", 2, 4, "ص"),
            ("الثلاثاء م", "ح 1", 2, 5, "م"), ("الثلاثاء م", "ح 2", 2, 6, "م"), ("الثلاثاء م", "ح 3", 2, 7, "م"), ("الثلاثاء م", "ح 4", 2, 8, "م"),
            ("الاربعاء ص", "ح 1", 3, 1, "ص"), ("الاربعاء ص", "ح 2", 3, 2, "ص"), ("الاربعاء ص", "ح 3", 3, 3, "ص"), ("الاربعاء ص", "ح 4", 3, 4, "ص"),
            ("الاربعاء م", "ح 1", 3, 5, "م"), ("الاربعاء م", "ح 2", 3, 6, "م"), ("الاربعاء م", "ح 3", 3, 7, "م"), ("الاربعاء م", "ح 4", 3, 8, "م"),
            ("الخميس ص", "ح 1", 4, 1, "ص"), ("الخميس ص", "ح 2", 4, 2, "ص"), ("الخميس ص", "ح 3", 4, 3, "ص"), ("الخميس ص", "ح 4", 4, 4, "ص"),
            ("الخميس م", "ح 1", 4, 5, "م"), ("الخميس م", "ح 2", 4, 6, "م"), ("الخميس م", "ح 3", 4, 7, "م"), ("الخميس م", "ح 4", 4, 8, "م"),
            ("الجمعة ص", "ح 1", 5, 1, "ص"), ("الجمعة ص", "ح 2", 5, 2, "ص"), ("الجمعة ص", "ح 3", 5, 3, "ص"), ("الجمعة ص", "ح 4", 5, 4, "ص"),
            ("الجمعة م", "ح 1", 5, 5, "م"), ("الجمعة م", "ح 2", 5, 6, "م"), ("الجمعة م", "ح 3", 5, 7, "م"), ("الجمعة م", "ح 4", 5, 8, "م"),
            ("السبت ص", "ح 1", 6, 1, "ص"), ("السبت ص", "ح 2", 6, 2, "ص"), ("السبت ص", "ح 3", 6, 3, "ص"), ("السبت ص", "ح 4", 6, 4, "ص"),
            ("السبت م", "ح 1", 6, 5, "م"), ("السبت م", "ح 2", 6, 6, "م"), ("السبت م", "ح 3", 6, 7, "م"), ("السبت م", "ح 4", 6, 8, "م"),
        ]

        teacher_timetables = {}
        teacher_subjects = {}
        teacher_rooms = {}
        classes_set = set()
        rooms_set = set()
        slots_count = 0

        data_rows = lines[header_idx + 1:]
        if data_rows and any(c.strip() in ("1", "2", "3", "4", "ح 1") for c in data_rows[0][:10]):
            data_rows = data_rows[1:]

        for row in data_rows:
            if not row or len(row) < 4:
                continue
            t_name = clean_str(row[0])
            if not t_name or any(skip_word in t_name for skip_word in ("المملكة", "وزارة", "مديرية", "الأستاذ", "مجموع", "الموسم", "رمز المؤسسة")):
                continue

            subj = clean_str(row[1]) if len(row) > 1 else ""
            rm = clean_str(row[2]) if len(row) > 2 else ""
            if rm and rm != "غير محددة":
                rooms_set.add(rm)

            if t_name not in teacher_timetables:
                teacher_timetables[t_name] = {d[0]: {} for d in PERIODS_48}
                teacher_subjects[t_name] = subj
                teacher_rooms[t_name] = rm

            period_cells = row[3:]
            for p_idx, cell_raw in enumerate(period_cells):
                if p_idx >= len(PERIODS_48):
                    break
                class_code = clean_str(cell_raw)
                if not class_code:
                    continue

                day_12, hour_4, dow, slot_idx, period_sym = PERIODS_48[p_idx]
                classes_set.add(class_code)
                slots_count += 1

                teacher_timetables[t_name][day_12][hour_4] = {
                    "class": class_code,
                    "students": class_code,
                    "subject": subj,
                    "room": rm or "ق 1",
                    "dayOfWeek": dow,
                    "slotIndex": slot_idx,
                    "period": period_sym
                }

        if not teacher_timetables:
            return {"success": False, "error": "لم يتم العثور على أي أساتذة أو حصص داخل ملف CSV."}

        raw_res = {
            "success": True,
            "source_type": "MOROCCAN_CSV_MASTER",
            "teacher_timetables": teacher_timetables,
            "teacher_dominant_subjects": teacher_subjects,
            "teacher_default_rooms": teacher_rooms,
            "classes_list": sorted(list(classes_set)),
            "rooms_list": sorted(list(rooms_set)),
            "slots_count": slots_count
        }
        return self._enrich_parsed_timetable(raw_res, filename)

    def _parse_zip_archive(self, zip_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses a zip archive containing FET output files"""
        import io
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                namelist = zf.namelist()
                
                # Check for activities.xml and .fet
                act_xml_name = next((n for n in namelist if n.endswith("_activities.xml")), None)
                fet_name = next((n for n in namelist if n.endswith("_data_and_timetable.fet") or n.endswith(".fet")), None)
                teachers_xml_name = next((n for n in namelist if n.endswith("_teachers.xml")), None)
                
                if act_xml_name and fet_name:
                    act_xml_content = zf.read(act_xml_name).decode("utf-8", errors="ignore")
                    fet_content = zf.read(fet_name).decode("utf-8", errors="ignore")
                    return self._parse_fet_and_activities(fet_content, act_xml_content, filename)
                
                # Check for standalone timetable xml or excel inside zip
                excel_name = next((n for n in namelist if n.endswith((".xlsx", ".xls"))), None)
                if excel_name:
                    parse_master_timetable_from_excel = _get_server_fn("parse_master_timetable_from_excel")
                    res = parse_master_timetable_from_excel(zf.read(excel_name))
                    if res.get("success"):
                        return self._enrich_parsed_timetable(res, filename)

                if teachers_xml_name and fet_name:
                    t_xml = zf.read(teachers_xml_name).decode("utf-8", errors="ignore")
                    fet_content = zf.read(fet_name).decode("utf-8", errors="ignore")
                    return self._parse_teachers_xml_and_fet(t_xml, fet_content, filename)

        except Exception as e:
            return {"success": False, "error": f"خطأ أثناء قراءة ملف الأرشيف المضغوط: {str(e)}"}

        return {"success": False, "error": "لم يتم العثور على ملفات جدول FET (_activities.xml و _data_and_timetable.fet) داخل الأرشيف المضغوط."}

    def _parse_xml_timetable(self, xml_str: str, filename: str) -> Dict[str, Any]:
        """Parses XML or FET content into full timetable structure"""
        try:
            root = ET.fromstring(xml_str)
        except Exception as e:
            return {"success": False, "error": f"خطأ في معالجة بنية XML: {str(e)}"}

        tag_lower = root.tag.lower()

        # Case A: <Activities_Timetable>
        if "activities_timetable" in tag_lower:
            # Need companion activities info (teacher, subject, students)
            companion_fet = self._find_companion_fet_in_data()
            if companion_fet:
                return self._parse_fet_and_activities(companion_fet, xml_str, filename)
            else:
                return {"success": False, "error": "ملف _activities.xml يتطلب ملف البيانات المقترن _data_and_timetable.fet لاستخراج أسماء الأساتذة والمواد."}

        # Case B: <Teachers_Timetable>
        if "teachers_timetable" in tag_lower:
            companion_fet = self._find_companion_fet_in_data()
            return self._parse_teachers_xml_and_fet(xml_str, companion_fet, filename)

        # Case C: <fet version="..."> (Full FET file or data_and_timetable.fet)
        if "fet" in tag_lower:
            # Check if this .fet already has scheduled times in Time_Constraints_List
            scheduled_acts = self._extract_scheduled_activities_from_fet(root)
            if scheduled_acts:
                return self._build_timetable_from_scheduled_acts(scheduled_acts, root, filename)

            # Check if companion activities.xml exists in data/
            companion_act_xml = self._find_companion_activities_xml_in_data()
            if companion_act_xml:
                return self._parse_fet_and_activities(xml_str, companion_act_xml, filename)

            return {"success": False, "error": "ملف FET هذا يحتوي على مدخلات ولم يتم توليد جدوله بعد أو لا يحتوي على قيود مواعيد مثبتة. يرجى اختيار ملف النتائج الصادر من FET (_activities.xml أو _data_and_timetable.xml)."}

        # Case D: Custom timetable XML with <session> or <activity> containing full attributes
        sessions = []
        for el in root.iter():
            if el.tag.lower() in ("session", "activity", "seance", "slot"):
                t = clean_str(el.findtext("teacher") or el.findtext("Teacher") or el.get("teacher"))
                s = clean_str(el.findtext("subject") or el.findtext("Subject") or el.get("subject"))
                c = clean_str(el.findtext("class") or el.findtext("classCode") or el.findtext("Students") or el.get("class"))
                d = clean_str(el.findtext("day") or el.findtext("Day") or el.get("day"))
                h = clean_str(el.findtext("hour") or el.findtext("Hour") or el.get("hour"))
                r = clean_str(el.findtext("room") or el.findtext("Room") or el.get("room") or "عامة")
                if t and c and d and h:
                    sessions.append({
                        "teacher": t, "subject": s, "class": c,
                        "day": d, "hour": h, "room": r, "duration": 1
                    })

        if sessions:
            return self._build_timetable_from_session_list(sessions, filename)

        return {"success": False, "error": "تعذر استخراج حصص الجدول من ملف XML. يرجى التأكد من استخدام ملفات نتائج FET الرسمية."}

    def _find_companion_fet_in_data(self) -> Optional[str]:
        """Finds any companion .fet file in data/ or generated_output/"""
        search_dirs = [
            os.path.join(self.data_dir, "generated_output", "timetables", "*"),
            os.path.join(self.data_dir, "timetables", "*"),
            self.data_dir
        ]
        for pattern in search_dirs:
            matches = glob.glob(os.path.join(pattern, "*_data_and_timetable.fet")) or glob.glob(os.path.join(pattern, "*.fet"))
            if matches:
                try:
                    with open(matches[0], "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    pass
        return None

    def _find_companion_activities_xml_in_data(self) -> Optional[str]:
        search_dirs = [
            os.path.join(self.data_dir, "generated_output", "timetables", "*"),
            os.path.join(self.data_dir, "timetables", "*")
        ]
        for pattern in search_dirs:
            matches = glob.glob(os.path.join(pattern, "*_activities.xml"))
            if matches:
                latest = max(matches, key=os.path.getmtime)
                try:
                    with open(latest, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    pass
        return None

    def _parse_fet_and_activities(self, fet_str: str, act_xml_str: str, filename: str) -> Dict[str, Any]:
        """Merges FET activities metadata with Activities_Timetable schedule"""
        root_fet = ET.fromstring(fet_str)
        activities_dict = {}
        act_list_el = root_fet.find("Activities_List")
        if act_list_el is not None:
            for act in act_list_el.findall("Activity"):
                aid = clean_str(act.findtext("Id"))
                t = clean_str(act.findtext("Teacher"))
                s = clean_str(act.findtext("Subject"))
                c = clean_str(act.findtext("Students"))
                dur = int(act.findtext("Duration") or "1")
                activities_dict[aid] = {
                    "id": aid, "teacher": t, "subject": s,
                    "students": c, "duration": dur
                }

        root_act = ET.fromstring(act_xml_str)
        sessions = []
        for act in root_act.findall("Activity"):
            aid = clean_str(act.findtext("Id"))
            day = clean_str(act.findtext("Day"))
            hour = clean_str(act.findtext("Hour"))
            room = clean_str(act.findtext("Room") or "عامة")

            info = activities_dict.get(aid, {})
            t = info.get("teacher", "")
            s = info.get("subject", "")
            c = info.get("students", "")
            dur = info.get("duration", 1)

            if t and c and day and hour:
                sessions.append({
                    "activity_id": aid, "teacher": t, "subject": s,
                    "class": c, "day": day, "hour": hour, "room": room, "duration": dur
                })

        return self._build_timetable_from_session_list(sessions, filename)

    def _parse_teachers_xml_and_fet(self, t_xml_str: str, fet_str: Optional[str], filename: str) -> Dict[str, Any]:
        """Parses Teachers_Timetable XML and resolves activity classes/subjects"""
        activities_dict = {}
        if fet_str:
            try:
                root_fet = ET.fromstring(fet_str)
                act_list_el = root_fet.find("Activities_List")
                if act_list_el is not None:
                    for act in act_list_el.findall("Activity"):
                        aid = clean_str(act.findtext("Id"))
                        activities_dict[aid] = {
                            "teacher": clean_str(act.findtext("Teacher")),
                            "subject": clean_str(act.findtext("Subject")),
                            "students": clean_str(act.findtext("Students")),
                            "duration": int(act.findtext("Duration") or "1")
                        }
            except Exception:
                pass

        root_t = ET.fromstring(t_xml_str)
        sessions = []
        for teacher in root_t.findall("Teacher"):
            t_name = clean_str(teacher.get("name") or teacher.findtext("Name"))
            for day in teacher.findall("Day"):
                d_name = clean_str(day.get("name") or day.findtext("Name"))
                for hour in day.findall("Hour"):
                    h_name = clean_str(hour.get("name") or hour.findtext("Name"))
                    act = hour.find("Activity")
                    if act is not None:
                        aid = clean_str(act.get("id") or act.findtext("Id"))
                        room = clean_str(act.get("room") or act.findtext("Room") or "عامة")
                        info = activities_dict.get(aid, {})
                        s = info.get("subject", "")
                        c = info.get("students", "")
                        dur = info.get("duration", 1)
                        if t_name and d_name and h_name:
                            sessions.append({
                                "activity_id": aid, "teacher": t_name, "subject": s,
                                "class": c, "day": d_name, "hour": h_name, "room": room, "duration": dur
                            })

        return self._build_timetable_from_session_list(sessions, filename)

    def _extract_scheduled_activities_from_fet(self, root_fet: ET.Element) -> List[Dict[str, Any]]:
        """Extracts pre-locked or scheduled starting times from a .fet file"""
        activities_dict = {}
        act_list_el = root_fet.find("Activities_List")
        if act_list_el is not None:
            for act in act_list_el.findall("Activity"):
                aid = clean_str(act.findtext("Id"))
                activities_dict[aid] = {
                    "id": aid, "teacher": clean_str(act.findtext("Teacher")),
                    "subject": clean_str(act.findtext("Subject")),
                    "students": clean_str(act.findtext("Students")),
                    "duration": int(act.findtext("Duration") or "1")
                }

        scheduled = []
        tc_list = root_fet.find("Time_Constraints_List")
        if tc_list is not None:
            for c in tc_list.findall("ConstraintActivityPreferredStartingTime"):
                active = clean_str(c.findtext("Active") or "true").lower()
                if active == "true" or active == "1":
                    aid = clean_str(c.findtext("Activity_Id"))
                    day = clean_str(c.findtext("Preferred_Day"))
                    hour = clean_str(c.findtext("Preferred_Hour"))
                    permanently_locked = clean_str(c.findtext("Permanently_Locked") or "").lower() == "true"
                    if aid in activities_dict and day and hour:
                        info = activities_dict[aid]
                        scheduled.append({
                            "activity_id": aid, "teacher": info["teacher"], "subject": info["subject"],
                            "class": info["students"], "day": day, "hour": hour, "room": "عامة",
                            "duration": info["duration"]
                        })

        return scheduled if len(scheduled) > 10 else []

    def _build_timetable_from_session_list(self, sessions: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """
        Converts flat session list into standard Moroccan timetable structure:
        - teacher_timetables
        - student_timetables
        - room_timetables
        - master_teachers_data
        - derived assignments & workload
        """
        teacher_timetables: Dict[str, Dict[str, Dict[str, Any]]] = {}
        student_timetables: Dict[str, Dict[str, Dict[str, Any]]] = {}
        room_timetables: Dict[str, Dict[str, Dict[str, Any]]] = {}
        teacher_assignments: Dict[str, Dict[str, Any]] = {}
        all_activities_list: List[Dict[str, Any]] = []

        teachers_set = set()
        classes_set = set()
        rooms_set = set()

        for s in sessions:
            t = clean_str(s.get("teacher"))
            subj = clean_str(s.get("subject"))
            c = clean_str(s.get("class"))
            d_raw = clean_str(s.get("day"))
            h_raw = clean_str(s.get("hour"))
            r = clean_str(s.get("room") or "عامة")
            dur = int(s.get("duration", 1))

            if not t or not c or not d_raw or not h_raw:
                continue

            day_12, hour_4, dow, slot_idx, period = parse_day_and_hour(d_raw, h_raw)

            teachers_set.add(t)
            classes_set.add(c)
            rooms_set.add(r)

            # Cell object
            cell_data = {
                "teacher": t,
                "subject": subj,
                "class": c,
                "room": r,
                "period": period,
                "day": day_12,
                "hour": hour_4,
                "dayOfWeek": dow,
                "slotIndex": slot_idx,
                "duration": dur,
                "activity_id": s.get("activity_id", "")
            }

            # 1. Teacher timetable
            if t not in teacher_timetables:
                teacher_timetables[t] = {}
            if day_12 not in teacher_timetables[t]:
                teacher_timetables[t][day_12] = {}
            teacher_timetables[t][day_12][hour_4] = cell_data

            # 2. Student timetable
            if c not in student_timetables:
                student_timetables[c] = {}
            if day_12 not in student_timetables[c]:
                student_timetables[c][day_12] = {}
            student_timetables[c][day_12][hour_4] = cell_data

            # 3. Room timetable
            if r not in room_timetables:
                room_timetables[r] = {}
            if day_12 not in room_timetables[r]:
                room_timetables[r][day_12] = {}
            room_timetables[r][day_12][hour_4] = cell_data

            # 4. Teacher assignment aggregation
            if t not in teacher_assignments:
                teacher_assignments[t] = {
                    "teacher_name": t,
                    "subjects": {},
                    "classes": {},
                    "rooms": {},
                    "total_hours": 0
                }
            if subj:
                teacher_assignments[t]["subjects"][subj] = teacher_assignments[t]["subjects"].get(subj, 0) + dur
            teacher_assignments[t]["classes"][c] = teacher_assignments[t]["classes"].get(c, 0) + dur
            teacher_assignments[t]["rooms"][r] = teacher_assignments[t]["rooms"].get(r, 0) + dur
            teacher_assignments[t]["total_hours"] += dur

            all_activities_list.append(cell_data)

        # Build master teachers list & assignments
        master_teachers_data = []
        master_assignments = []
        for t_name, info in sorted(teacher_assignments.items(), key=lambda x: x[0]):
            dominant_subj = max(info["subjects"].items(), key=lambda x: x[1])[0] if info["subjects"] else "عامة"
            dominant_room = max(info["rooms"].items(), key=lambda x: x[1])[0] if info["rooms"] else "ق 1"
            class_list = sorted(list(info["classes"].keys()))
            
            assigned_str = ", ".join(f"{cls} ({hrs}س)" for cls, hrs in sorted(info["classes"].items()))
            
            t_obj = {
                "name": t_name,
                "fullName": t_name,
                "subject": dominant_subj,
                "classes": class_list,
                "defaultRoom": dominant_room,
                "rooms": list(info["rooms"].keys()),
                "weekly_hours": info["total_hours"],
                "weeklyHours": info["total_hours"],
                "assigned_classes_str": assigned_str
            }
            master_teachers_data.append(t_obj)

            master_assignments.append({
                "teacher_name": t_name,
                "subject": dominant_subj,
                "classes": class_list,
                "weekly_hours": info["total_hours"],
                "assigned_classes_str": assigned_str,
                "classes_hours": info["classes"]
            })

        result = {
            "success": True,
            "source_filename": filename,
            "total_activities": len(all_activities_list),
            "teachers_count": len(teachers_set),
            "classes_count": len(classes_set),
            "rooms_count": len(rooms_set),
            "days": DAYS_12,
            "hours": HOURS_4,
            "teachers_list": sorted(list(teachers_set)),
            "classes_list": sorted(list(classes_set)),
            "rooms_list": sorted(list(rooms_set)),
            "teacher_timetables": teacher_timetables,
            "student_timetables": student_timetables,
            "room_timetables": room_timetables,
            "master_teachers_data": master_teachers_data,
            "master_assignments": master_assignments,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return result

    def _enrich_parsed_timetable(self, tt_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Enriches an already parsed timetable structure with assignments & teachers metadata"""
        tt_data["success"] = True
        tt_data["source_filename"] = filename
        if "generated_at" not in tt_data:
            tt_data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        teacher_timetables = tt_data.get("teacher_timetables", {})
        teachers_set = set(teacher_timetables.keys())
        student_timetables = tt_data.get("student_timetables", {})
        classes_set = set(student_timetables.keys())
        room_timetables = tt_data.get("room_timetables", {})
        rooms_set = set(room_timetables.keys())
        total_slots_count = 0

        master_assignments = []
        master_teachers_data = []

        for t_name, days in sorted(teacher_timetables.items()):
            subjs: Dict[str, int] = {}
            classes_hrs: Dict[str, int] = {}
            rooms_used: Dict[str, int] = {}
            total_hrs = 0
            for d, hours in days.items():
                if isinstance(hours, dict):
                    for h, cell in hours.items():
                        if isinstance(cell, dict):
                            s = cell.get("subject", "")
                            c = cell.get("class") or cell.get("students") or cell.get("classCode") or ""
                            r = cell.get("room", "")
                            if c:
                                cell["class"] = c
                                cell["students"] = c
                                classes_set.add(c)
                                classes_hrs[c] = classes_hrs.get(c, 0) + 1
                                total_slots_count += 1
                            if s:
                                subjs[s] = subjs.get(s, 0) + 1
                            if r and r != "غير محددة":
                                rooms_set.add(r)
                                rooms_used[r] = rooms_used.get(r, 0) + 1
                            if c or s:
                                total_hrs += 1

            dom_subj = max(subjs.items(), key=lambda x: x[1])[0] if subjs else "عامة"
            dom_room = max(rooms_used.items(), key=lambda x: x[1])[0] if rooms_used else "ق 1"
            cl_list = sorted(list(classes_hrs.keys()))
            assigned_str = ", ".join(f"{cls} ({hrs}س)" for cls, hrs in sorted(classes_hrs.items()))

            master_teachers_data.append({
                "name": t_name, "fullName": t_name, "subject": dom_subj,
                "classes": cl_list, "defaultRoom": dom_room, "rooms": list(rooms_used.keys()),
                "weekly_hours": total_hrs, "weeklyHours": total_hrs, "assigned_classes_str": assigned_str
            })
            master_assignments.append({
                "teacher_name": t_name, "subject": dom_subj, "classes": cl_list,
                "weekly_hours": total_hrs, "assigned_classes_str": assigned_str, "classes_hours": classes_hrs
            })

        tt_data["master_teachers_data"] = master_teachers_data
        tt_data["master_assignments"] = master_assignments
        tt_data["classes_list"] = sorted(list(classes_set))
        tt_data["rooms_list"] = sorted(list(rooms_set))
        tt_data["teachers_count"] = len(teachers_set)
        tt_data["classes_count"] = len(classes_set)
        tt_data["rooms_count"] = len(rooms_set)
        tt_data["slots_count"] = total_slots_count
        return tt_data

    def adopt_master_timetable_into_app(self, parsed_result: Dict[str, Any], app_state: Any, source_filename: str = "") -> Dict[str, Any]:
        """
        Adopts the parsed timetable as the ABSOLUTE SINGLE SOURCE OF TRUTH across the app:
        - Saves to data/timetable_result.json
        - Updates app_state assignments & teachers
        - Updates attendance_mobile_db.json (with preserved 8-char codes)
        - Updates attendance_school_data.js & hosting_public
        - Refreshes exams planning engine
        - Triggers Cloud Firestore push
        """
        if not parsed_result.get("success"):
            return parsed_result

        fn = source_filename or parsed_result.get("source_filename") or "جدول الحصص المعتمد"
        
        # 1. Save to timetable_result.json
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(parsed_result, f, ensure_ascii=False, indent=2)

        # Also copy to LocalAppData
        user_appdata_tt = os.path.expandvars(r'%LOCALAPPDATA%\RzzakFet\data\timetable_result.json')
        if os.path.exists(os.path.dirname(user_appdata_tt)):
            try:
                import shutil
                shutil.copy2(self.cache_file, user_appdata_tt)
            except Exception:
                pass

        # 2. Update app_state assignments directly from Master Timetable
        class SimpleAssignment:
            def __init__(self, idx, data):
                self.row_id = idx + 1
                self.id = idx + 1
                self.teacher_name = data.get("teacher_name", "")
                self.def_teacher_name = self.teacher_name
                self.subject = data.get("subject", "")
                self.classes = data.get("classes", [])
                self.weekly_hours = data.get("weekly_hours", 0)
                self.total_hours = self.weekly_hours
                self.assigned_classes_str = data.get("assigned_classes_str", "")
                self.classes_hours = data.get("classes_hours", {})
                self.total_classes = len(self.classes)
                c1_list = [c for c in self.classes if any(k in c.upper() for k in ("TC", "1APIC"))]
                c2_list = [c for c in self.classes if any(k in c.upper() for k in ("1BAC", "2APIC"))]
                c3_list = [c for c in self.classes if any(k in c.upper() for k in ("2BAC", "3APIC"))]
                self.classes_1 = ", ".join(c1_list) if c1_list else "-"
                self.classes_2 = ", ".join(c2_list) if c2_list else "-"
                self.classes_3 = ", ".join(c3_list) if c3_list else "-"
                levels = set()
                if c1_list: levels.add(1)
                if c2_list: levels.add(2)
                if c3_list: levels.add(3)
                self.levels_count = len(levels) or 1
                self.two_levels_satisfied = (self.levels_count <= 2)
                self.status_note = "معتمد من الجدول العام"

        m_assignments = [SimpleAssignment(i, a) for i, a in enumerate(parsed_result.get("master_assignments", []))]
        app_state.master_timetable_assignments = m_assignments

        # Also register teachers and rooms in app_state
        if hasattr(app_state, "institution"):
            t_counts = {}
            for a in m_assignments:
                t_counts[a.subject] = t_counts.get(a.subject, 0) + 1
            if t_counts:
                app_state.institution.teacher_counts_by_subject.update(t_counts)

            for idx, a in enumerate(m_assignments):
                key = f"t_{idx+1}"
                app_state.institution.teacher_custom_names[key] = a.teacher_name
                app_state.institution.teacher_custom_names[a.teacher_name] = a.teacher_name

            r_list = parsed_result.get("rooms_list", [])
            if r_list:
                gen_rooms = [r for r in r_list if "م" not in r and "ملعب" not in r and "ورير" not in r]
                if gen_rooms:
                    app_state.institution.general_rooms_count = max(app_state.institution.general_rooms_count, len(gen_rooms))

        app_state.master_timetable_info = {
            "filename": fn,
            "adopted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "teachers_count": parsed_result.get("teachers_count", len(m_assignments)),
            "classes_count": parsed_result.get("classes_count", len(parsed_result.get("classes_list", []))),
            "rooms_count": parsed_result.get("rooms_count", len(parsed_result.get("rooms_list", []))),
            "slots_count": parsed_result.get("slots_count", parsed_result.get("total_activities", 0)),
            "status": "ADOPTED_AND_ACTIVE"
        }
        self.save_active_info(app_state.master_timetable_info)

        # 3. Synchronize Mobile Attendance DB with preserved 8-char codes
        self._sync_mobile_db(parsed_result, app_state)

        # 4. Trigger Cloud Firestore sync in background thread
        try:
            import threading
            sync_fn = _get_server_fn("sync_attendance_with_cloud")
            if sync_fn:
                threading.Thread(target=lambda: sync_fn(upload_metadata=True), daemon=True).start()
        except Exception as e:
            print(f"[MasterTimetableEngine] Cloud sync start note: {e}")

        return {
            "success": True,
            "message": f"✅ تم بنجاح اعتماد وتثبيت جدول الحصص الرسمي ({fn}) كقاعدة بيانات موحدة لكافة وظائف المنظومة!",
            "info": app_state.master_timetable_info,
            "teachers_count": app_state.master_timetable_info["teachers_count"],
            "classes_count": app_state.master_timetable_info["classes_count"],
            "slots_count": app_state.master_timetable_info["slots_count"],
            "rooms_count": app_state.master_timetable_info["rooms_count"]
        }

    def _load_mobile_db(self) -> dict:
        candidates = [
            os.path.join(self.data_dir, "attendance_mobile_db.json"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "RzzakFet", "data", "attendance_mobile_db.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "attendance_mobile_db.json"),
        ]
        for p in candidates:
            if p and os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            return data
                except Exception:
                    pass
        return {"teachers": [], "classes": [], "timetable": [], "examsPlanning": [], "settings": {}}

    def _save_mobile_db(self, db: dict, app_state: Any = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Save JSON to candidates
        json_targets = {
            os.path.join(self.data_dir, "attendance_mobile_db.json"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "RzzakFet", "data", "attendance_mobile_db.json"),
            os.path.join(base_dir, "data", "attendance_mobile_db.json"),
        }
        for jp in json_targets:
            if jp:
                try:
                    os.makedirs(os.path.dirname(jp), exist_ok=True)
                    with open(jp, "w", encoding="utf-8") as f:
                        json.dump(db, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

        # Write attendance_school_data.js to all UI locations
        js_code = f"window.INITIAL_SCHOOL_DATA = {json.dumps(db, ensure_ascii=False, indent=2)};\nwindow.ANFG_SCHOOL_DATA = window.INITIAL_SCHOOL_DATA;\n"
        js_targets = {
            os.path.join(base_dir, "hosting_public", "attendance_school_data.js"),
            os.path.join(base_dir, "ui", "attendance_school_data.js"),
            os.path.join(base_dir, "data", "ui", "attendance_school_data.js"),
            os.path.join(self.data_dir, "ui", "attendance_school_data.js"),
            os.path.expanduser(r"~\AppData\Local\Programs\RzzakFet\ui\attendance_school_data.js"),
            os.path.expanduser(r"~\AppData\Local\Programs\RzzakFet\_internal\ui\attendance_school_data.js"),
            os.path.expanduser(r"~\AppData\Local\RzzakFet\data\ui\attendance_school_data.js"),
        }
        for jp in js_targets:
            if jp and os.path.exists(os.path.dirname(jp)):
                try:
                    with open(jp, "w", encoding="utf-8") as _jsf:
                        _jsf.write(js_code)
                except Exception:
                    pass

        _gen_fn = _get_server_fn("generate_attendance_school_data_js")
        if _gen_fn:
            try:
                _gen_fn(db)
            except Exception:
                pass

    def _sync_mobile_db(self, parsed_result: Dict[str, Any], app_state: Any):
        """Updates attendance_mobile_db.json and rebuilds attendance_school_data.js"""
        db = self._load_mobile_db()

        # Preserve existing teacher login codes
        existing_codes_map = {}
        used_codes = {"ADMIN888"}
        for t in db.get("teachers", []):
            fn = clean_str(t.get("fullName") or t.get("name"))
            code = clean_str(t.get("loginCode"))
            if fn and code and len(code) == 8:
                existing_codes_map[fn] = code
                used_codes.add(code)

        # Build fresh teachers list from master timetable
        teachers_list = []
        raw_teachers = parsed_result.get("master_teachers_data", [])
        for idx, t_raw in enumerate(raw_teachers):
            fn = clean_str(t_raw.get("fullName") or t_raw.get("name"))
            t_id = f"T{idx+1:02d}"
            code = existing_codes_map.get(fn) or generate_8char_code(used_codes)
            used_codes.add(code)

            teachers_list.append({
                "teacherId": t_id,
                "name": fn,
                "fullName": fn,
                "subject": t_raw.get("subject", ""),
                "loginCode": code,
                "defaultRoom": t_raw.get("defaultRoom", "ق 1"),
                "rooms": t_raw.get("rooms", []),
                "classes": t_raw.get("classes", []),
                "weeklyHours": t_raw.get("weeklyHours", 0)
            })

        db["teachers"] = teachers_list

        # Build classes list
        c_list = parsed_result.get("classes_list", [])
        db["classes"] = [{"classCode": c, "className": c} for c in c_list]

        # Build flat timetable slots list for mobile
        t_id_by_name = {t["fullName"]: t["teacherId"] for t in teachers_list}
        mobile_slots = []
        teacher_timetables = parsed_result.get("teacher_timetables", {})

        for t_name, days in teacher_timetables.items():
            t_id = t_id_by_name.get(t_name, "T01")
            for day_12, hours in days.items():
                for hour_4, cell in hours.items():
                    if isinstance(cell, dict):
                        dow = cell.get("dayOfWeek")
                        slot_idx = cell.get("slotIndex")
                        if dow is None or slot_idx is None:
                            _, _, dow, slot_idx, _ = parse_day_and_hour(day_12, hour_4)

                        c_code = cell.get("class") or cell.get("students") or cell.get("classCode") or ""
                        if not c_code:
                            continue
                        mobile_slots.append({
                            "teacherId": t_id,
                            "teacherName": t_name,
                            "classCode": c_code,
                            "subject": cell.get("subject", ""),
                            "dayOfWeek": dow,
                            "slotIndex": slot_idx,
                            "room": cell.get("room", "ق 1"),
                            "period": cell.get("period", "ص")
                        })

        db["timetable"] = mobile_slots

        # Update school metadata
        if "settings" not in db:
            db["settings"] = {}
        inst = getattr(app_state, "institution", None)
        if inst:
            db["settings"]["schoolName"] = getattr(inst, "institution_name", "الثانوية التأهيلية أنفك")
            db["settings"]["gresa"] = getattr(inst, "gresa_code", "H12657")
            db["settings"]["schoolId"] = getattr(inst, "gresa_code", "H12657")
            db["settings"]["institution_cycle"] = getattr(inst, "institution_cycle", "qualifying")
            db["settings"]["cycle"] = getattr(inst, "institution_cycle", "qualifying")
            db["settings"]["principalName"] = getattr(inst, "principal_name", "عبدالله الرزاق")

        self._save_mobile_db(db, app_state)
