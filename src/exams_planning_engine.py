# -*- coding: utf-8 -*-

"""

محرك برمجة وتتبع فروض المراقبة المستمرة

Continuous Assessment & Exams Scheduling Engine

متوافق مع التوجيهات التربوية والمذكرات الوزارية المنظمة للتقويم بالثانوي الإعدادي والتأهيلي.

"""



import os

import sys

import json

import shutil

from datetime import datetime, timedelta

from typing import Dict, List, Any, Optional



def get_exams_planning_db_path(filename: str = 'exams_planning_db.json') -> str:

    appdata_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "RzzakFet", "data")

    appdata_path = os.path.join(appdata_dir, filename)

    candidates = [

        appdata_path,

        os.path.join(os.getcwd(), 'data', filename),

        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', filename),

    ]

    if getattr(sys, '_MEIPASS', None):

        candidates.append(os.path.join(sys._MEIPASS, 'data', filename))

    if getattr(sys, 'frozen', False):

        exe_dir = os.path.dirname(sys.executable)

        candidates.append(os.path.join(exe_dir, 'data', filename))

        candidates.append(os.path.join(exe_dir, '_internal', 'data', filename))



    for cand in candidates:

        if cand != appdata_path and os.path.exists(cand) and os.path.getsize(cand) > 10:

            try:

                os.makedirs(appdata_dir, exist_ok=True)

                if not os.path.exists(appdata_path) or os.path.getsize(appdata_path) < 10:

                    shutil.copy2(cand, appdata_path)

            except Exception:

                pass

            return appdata_path



    os.makedirs(appdata_dir, exist_ok=True)

    return appdata_path



ARABIC_DAYS = ["الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة", "السبت"]

WEEKDAY_TO_ARABIC = {

    0: "الاثنين",

    1: "الثلاثاء",

    2: "الاربعاء",

    3: "الخميس",

    4: "الجمعة",

    5: "السبت",

    6: "الأحد"

}



HOURS_TIMES_MAP = {

    "ح 1": "08:00 - 09:00",

    "ح 2": "09:00 - 10:00",

    "ح 3": "10:00 - 11:00",

    "ح 4": "11:00 - 12:00",

    "ح 5": "14:00 - 15:00",

    "ح 6": "15:00 - 16:00",

    "ح 7": "16:00 - 17:00",

    "ح 8": "17:00 - 18:00"

}



PERIOD_TIMES = {

    "ص": {

        "ح 1": "08:00 - 09:00",

        "ح 2": "09:00 - 10:00",

        "ح 3": "10:00 - 11:00",

        "ح 4": "11:00 - 12:00"

    },

    "م": {

        "ح 1": "14:00 - 15:00",

        "ح 2": "15:00 - 16:00",

        "ح 3": "16:00 - 17:00",

        "ح 4": "17:00 - 18:00"

    }

}



class ExamsPlanningEngine:

    def __init__(self, db_path: Optional[str] = None):

        self.db_path = db_path or get_exams_planning_db_path()

        self.exams: List[Dict[str, Any]] = []

        self.settings: Dict[str, Any] = {

            "max_submission_delay_days": 15,

            "current_semester": 1,

            "academic_year": "2026/2027",

            "ministerial_calendar": {

                "1": {

                    "exam_1": {

                        "name": "الفرض الأول",

                        "start_date": "2026-11-02",

                        "end_date": "2026-11-14",

                        "exam_deadline": "2026-11-14",

                        "submission_deadline": "2026-11-28"

                    },

                    "exam_2": {

                        "name": "الفرض الثاني",

                        "start_date": "2026-12-07",

                        "end_date": "2026-12-19",

                        "exam_deadline": "2026-12-19",

                        "submission_deadline": "2027-01-02"

                    },

                    "exam_3": {

                        "name": "الفرض الثالث (للمواد المعنية)",

                        "start_date": "2027-01-04",

                        "end_date": "2027-01-16",

                        "exam_deadline": "2027-01-16",

                        "submission_deadline": "2027-01-23"

                    },

                    "exam_4": {

                        "name": "الفرض الرابع (للمواد المعنية)",

                        "start_date": "2027-01-11",

                        "end_date": "2027-01-16",

                        "exam_deadline": "2027-01-16",

                        "submission_deadline": "2027-01-23"

                    },

                    "final_exam_deadline": "2027-01-16",

                    "final_submission_deadline": "2027-01-23"

                },

                "2": {

                    "exam_1": {

                        "name": "الفرض الأول",

                        "start_date": "2027-03-08",

                        "end_date": "2027-03-20",

                        "exam_deadline": "2027-03-20",

                        "submission_deadline": "2027-04-03"

                    },

                    "exam_2": {

                        "name": "الفرض الثاني",

                        "start_date": "2027-04-26",

                        "end_date": "2027-05-08",

                        "exam_deadline": "2027-05-08",

                        "submission_deadline": "2027-05-22"

                    },

                    "exam_3": {

                        "name": "الفرض الثالث (للمواد المعنية)",

                        "start_date": "2027-05-24",

                        "end_date": "2027-06-05",

                        "exam_deadline": "2027-06-05",

                        "submission_deadline": "2027-06-12"

                    },

                    "exam_4": {

                        "name": "الفرض الرابع (للمواد المعنية)",

                        "start_date": "2027-05-31",

                        "end_date": "2027-06-05",

                        "exam_deadline": "2027-06-05",

                        "submission_deadline": "2027-06-12"

                    },

                    "final_exam_deadline": "2027-06-05",

                    "final_submission_deadline": "2027-06-12"

                }

            },

            "default_exam_counts_by_subject": {

                "الرياضيات": 3,

                "الفيزياء والكيمياء": 3,

                "علوم الحياة والأرض": 3,

                "علوم الحياة  والأرض": 3,

                "اللغة العربية": 3,

                "اللغة  العربية": 3,

                "اللغة الفرنسية": 3,

                "اللغة  الفرنسية": 3,

                "اللغة الإنجليزية": 3,

                "الاجتماعيات": 3,

                "التاريخ والجغرافيا": 3,

                "الفلسفة": 2,

                "التربية الإسلامية": 2,

                "التربية البدنية والرياضة": 2,

                "المعلوميات": 2

            }

        }

        self.load_state()



    @staticmethod
    def _exam_sort_key(x):
        try:
            num = int(x.get('exam_number', 1) or 1)
        except Exception:
            num = 1
        return (
            str(x.get('exam_date', '9999-99-99') or '9999-99-99'),
            str(x.get('exam_time_str', '') or ''),
            str(x.get('class_name', '') or ''),
            num
        )

    def load_state(self):

        if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 10:

            try:

                with open(self.db_path, "r", encoding="utf-8") as f:

                    data = json.load(f)

                    self.exams = data.get("exams", [])

                    saved_settings = data.get("settings", {})

                    for k, v in self.settings.items():

                        if k not in saved_settings:

                            saved_settings[k] = v

                        elif k == "ministerial_calendar" and isinstance(saved_settings.get(k), dict):

                            for sem_k, sem_v in v.items():

                                if sem_k not in saved_settings[k]:

                                    saved_settings[k][sem_k] = sem_v

                    self.settings = saved_settings

                    # Normalize fields for all loaded exams (rooms, deadlines, Arabic day names, days calculation)
                    day_names_ar = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
                    for ex in self.exams:
                        rm = ex.get("room_name") or ex.get("exam_room") or ex.get("room") or ""
                        ex["room_name"] = rm
                        ex["exam_room"] = rm

                        s_date = ex.get("submission_deadline") or ex.get("grades_submission_date") or ex.get("submission_date") or ""
                        ex["submission_deadline"] = s_date
                        ex["grades_submission_date"] = s_date

                        e_date = ex.get("exam_date", "")
                        if not ex.get("exam_day_name") and e_date:
                            try:
                                dt = datetime.strptime(e_date, "%Y-%m-%d")
                                ex["exam_day_name"] = day_names_ar[dt.weekday()]
                            except Exception:
                                pass

                        cur_diff = ex.get("days_to_submission")
                        if (not cur_diff or cur_diff == 0) and e_date and s_date:
                            try:
                                d_diff = (datetime.strptime(s_date, "%Y-%m-%d") - datetime.strptime(e_date, "%Y-%m-%d")).days
                                ex["days_to_submission"] = max(0, d_diff)
                                ex["is_compliant_15_days"] = (d_diff <= 15)
                            except Exception:
                                pass

            except Exception as e:

                print(f"Error loading exams planning database: {e}")

                self.exams = []

        else:

            self.exams = []

            self.save_state()



    def save_state(self):

        try:

            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            with open(self.db_path, "w", encoding="utf-8") as f:

                json.dump({

                    "exams": self.exams,

                    "settings": self.settings,

                    "last_updated": datetime.now().isoformat()

                }, f, ensure_ascii=False, indent=2)



            # Also mirror to data/exams_planning_db.json in project root if different

            proj_data = os.path.join(os.getcwd(), "data", "exams_planning_db.json")

            if os.path.abspath(proj_data) != os.path.abspath(self.db_path):

                os.makedirs(os.path.dirname(proj_data), exist_ok=True)

                with open(proj_data, "w", encoding="utf-8") as f:

                    json.dump({

                        "exams": self.exams,

                        "settings": self.settings,

                        "last_updated": datetime.now().isoformat()

                    }, f, ensure_ascii=False, indent=2)

        except Exception as e:

            print(f"Error saving exams planning database: {e}")



    def get_teacher_class_sessions(self, teacher_name: str, class_name: str, timetable_data: Dict[str, Any]) -> List[Dict[str, Any]]:

        """

        استخراج جميع الحصص الأسبوعية التي يدرس فيها الأستاذ هذا القسم حسب استعمال الزمن المعتمد

        """

        if not timetable_data:

            return []



        teacher_name = (teacher_name or "").strip()

        class_name = (class_name or "").strip(' ,;،\t\r\n')

        sessions = []



        # 1. Search in student_timetables

        student_timetables = timetable_data.get("student_timetables", {})

        cls_tt = student_timetables.get(class_name, {})

        if not cls_tt:

            for k, v in student_timetables.items():

                if k.strip(' ,;،\t\r\n') == class_name:

                    cls_tt = v

                    break



        if cls_tt:

            for sub_day, hours in cls_tt.items():

                parts = sub_day.split()

                day_name = parts[0] if parts else sub_day

                period = parts[1] if len(parts) > 1 else ("ص" if "ص" in sub_day else "م")



                if isinstance(hours, dict):

                    for hour_key, cell in hours.items():

                        if isinstance(cell, dict) and cell.get("teacher") == teacher_name:

                            time_str = PERIOD_TIMES.get(period, {}).get(hour_key, HOURS_TIMES_MAP.get(hour_key, hour_key))

                            room = cell.get("room", "")

                            sessions.append({

                                "sub_day": sub_day,

                                "day_name": day_name,

                                "period": period,

                                "period_label": "صباحية" if period == "ص" else "مسائية",

                                "hour": hour_key,

                                "time_str": time_str,

                                "room": room,

                                "subject": cell.get("subject", ""),

                                "duration": cell.get("duration", 1),

                                "is_first": cell.get("is_first", True)

                            })



        # 2. Fallback to master_teachers_data if student_timetables didn't find any

        if not sessions:

            master_teachers = timetable_data.get("master_teachers_data", [])

            for item in master_teachers:

                if isinstance(item, dict) and item.get("teacher") == teacher_name:

                    sch = item.get("schedule", {})

                    for sub_day, hours in sch.items():

                        parts = sub_day.split()

                        day_name = parts[0] if parts else sub_day

                        period = parts[1] if len(parts) > 1 else ("ص" if "ص" in sub_day else "م")

                        if isinstance(hours, dict):

                            for hour_key, cell in hours.items():

                                if isinstance(cell, dict) and cell.get("students", "").strip(' ,;،\t\r\n') == class_name:

                                    time_str = PERIOD_TIMES.get(period, {}).get(hour_key, HOURS_TIMES_MAP.get(hour_key, hour_key))

                                    room = cell.get("room", "")

                                    sessions.append({

                                        "sub_day": sub_day,

                                        "day_name": day_name,

                                        "period": period,

                                        "period_label": "صباحية" if period == "ص" else "مسائية",

                                        "hour": hour_key,

                                        "time_str": time_str,

                                        "room": room,

                                        "subject": cell.get("subject", ""),

                                        "duration": cell.get("duration", 1),

                                        "is_first": cell.get("is_first", True)

                                    })



        # Order by day and hour

        day_order = {d: i for i, d in enumerate(ARABIC_DAYS)}

        hour_order = {"ح 1": 1, "ح 2": 2, "ح 3": 3, "ح 4": 4}

        sessions.sort(key=lambda s: (day_order.get(s["day_name"], 99), 0 if s["period"] == "ص" else 1, hour_order.get(s["hour"], 99)))

        return sessions



    

    def check_compensatory_slot_availability(

        self,

        class_name: str,

        room_name: str,

        exam_date_str: str,

        slot_index: int,

        day_of_week: int,

        timetable_data: Dict[str, Any],

        exclude_exam_id: Optional[str] = None,

        teacher_name: Optional[str] = None

    ) -> Dict[str, Any]:

        """

        التحقق من شغور القسم وشغور القاعة/الملعب لحصة تعويضية:

        الشرط 1: القسم شاغر وليس لديه حصة مع أي أستاذ في جدول الحصص الرسمي أو فرض مبرمج.

        الشرط 2: القاعة أو الملعب شاغر وغير محجوز لحصة أخرى أو لفرض مبرمج لأستاذ آخر.

        """

        day_names = {

            1: "الاثنين",

            2: "الثلاثاء",

            3: "الاربعاء",

            4: "الخميس",

            5: "الجمعة",

            6: "السبت"

        }

        day_name = day_names.get(day_of_week, "الاثنين")

        period_suffix = " ص" if slot_index <= 4 else " م"

        st_day = f"{day_name}{period_suffix}"

        hour_num = slot_index if slot_index <= 4 else (slot_index - 4)

        st_hour = f"ح {hour_num}"



        st_data = timetable_data.get("student_timetables", {})

        rt_data = timetable_data.get("room_timetables", {})

        tt_data = timetable_data.get("teacher_timetables", {})



        conflicts = []

        class_conflict = None

        room_conflict = None

        teacher_conflict = None



        # 1. فحص شغور القسم في جدول الحصص

        cls_day_schedule = st_data.get(class_name, {}).get(st_day, {})

        cls_act = cls_day_schedule.get(st_hour)

        if cls_act and isinstance(cls_act, dict) and cls_act.get("subject"):

            subj = cls_act.get("subject", "")

            t_act = cls_act.get("teacher", "")

            r_act = cls_act.get("room", "")

            class_conflict = f"القسم لديه حصة رسمية مقررة ({subj}) مع الأستاذ(ة) {t_act} بقاعة {r_act}"

            conflicts.append(class_conflict)



        # فحص شغور القسم في الفروض المحروسة المبرمجة سابقاً

        for ex in self.exams:

            if ex.get("id") == exclude_exam_id:

                continue

            if ex.get("exam_date") == exam_date_str and int(ex.get("slot_index", 0)) == int(slot_index):

                if ex.get("class_name") == class_name:

                    ex_subj = ex.get("subject_name", "")

                    ex_t = ex.get("teacher_name", "")

                    class_conflict = f"القسم مبرمج له فرض آخر ({ex_subj}) مع الأستاذ(ة) {ex_t}"

                    conflicts.append(class_conflict)

                    break



        # 2. فحص شغور القاعة / الملعب في جدول الحصص

        clean_room = room_name.strip()

        room_day_schedule = None

        # البحث بمرونة عن اسم القاعة في جدول القاعات

        for r_key, r_days in rt_data.items():

            if r_key.strip() == clean_room:

                room_day_schedule = r_days.get(st_day, {})

                break



        if room_day_schedule:

            rm_act = room_day_schedule.get(st_hour)

            if rm_act and isinstance(rm_act, dict) and rm_act.get("subject"):

                subj = rm_act.get("subject", "")

                st_cls = rm_act.get("students", "")

                t_act = rm_act.get("teacher", "")

                room_conflict = f"القاعة/الملعب محجوز لحصة ({subj}) لقسم {st_cls} مع الأستاذ(ة) {t_act}"

                conflicts.append(room_conflict)



        # فحص شغور القاعة / الملعب في الفروض المحروسة المبرمجة

        for ex in self.exams:

            if ex.get("id") == exclude_exam_id:

                continue

            if ex.get("exam_date") == exam_date_str and int(ex.get("slot_index", 0)) == int(slot_index):

                ex_rm = (ex.get("room_name") or "").strip()

                if ex_rm == clean_room:

                    ex_t = ex.get("teacher_name", "")

                    ex_cls = ex.get("class_name", "")

                    room_conflict = f"القاعة/الملعب محجوز لفرض محروس لقسم {ex_cls} مع الأستاذ(ة) {ex_t}"

                    conflicts.append(room_conflict)

                    break



        # 3. فحص الأستاذ إن كان يدرس قسماً آخر في نفس الساعة

        if teacher_name:

            t_day_schedule = tt_data.get(teacher_name, {}).get(st_day, {})

            t_act = t_day_schedule.get(st_hour)

            if t_act and isinstance(t_act, dict) and t_act.get("subject"):

                other_cls = t_act.get("students", "")

                teacher_conflict = f"الأستاذ(ة) لديه حصة رسمية مع قسم آخر ({other_cls})"

                conflicts.append(teacher_conflict)



        is_available = len(conflicts) == 0

        message = "✓ الموعد متاح بالكامل (القسم شاغر والقاعة/الملعب شاغر)" if is_available else "؛ ".join(conflicts)



        return {

            "available": is_available,

            "class_free": class_conflict is None,

            "room_free": room_conflict is None,

            "teacher_free": teacher_conflict is None,

            "class_conflict": class_conflict,

            "room_conflict": room_conflict,

            "teacher_conflict": teacher_conflict,

            "conflicts": conflicts,

            "message": message,

            "st_day": st_day,

            "st_hour": st_hour

        }



    def check_15_days_compliance(self, exam_date_str: str, submission_date_str: str) -> Dict[str, Any]:

        """

        فحص التقيد بالأجل القانوني (ألا تتجاوز المدة الفاصلة بين تمرير الفرض وتسليم النقط 15 يوماً)

        """

        try:

            e_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()

            s_date = datetime.strptime(submission_date_str, "%Y-%m-%d").date()

            diff_days = (s_date - e_date).days

            max_allowed = self.settings.get("max_submission_delay_days", 15)



            if diff_days < 0:

                return {

                    "is_compliant": False,

                    "days": diff_days,

                    "max_allowed": max_allowed,

                    "status_label": "خطأ في التواريخ",

                    "badge_color": "red",

                    "warning_message": "تاريخ تسليم النقط لا يمكن أن يكون قبل تاريخ إجراء الفرض!"

                }

            elif diff_days > max_allowed:

                return {

                    "is_compliant": False,

                    "days": diff_days,

                    "max_allowed": max_allowed,

                    "status_label": f"تجاوز الأجل المحدد ({diff_days} يوماً)",

                    "badge_color": "red",

                    "warning_message": f"تنبيه نظامي: المدة الفاصلة ({diff_days} يوماً) تتجاوز الحد الأقصى المسموح به ({max_allowed} يوماً طبقاً للمذكرات الوزارية المنظمة للتقويم والمراقبة المستمرة)!"

                }

            else:

                return {

                    "is_compliant": True,

                    "days": diff_days,

                    "max_allowed": max_allowed,

                    "status_label": f"متقيد بالنظام ({diff_days} يوماً) ✓",

                    "badge_color": "green",

                    "warning_message": ""

                }

        except Exception as e:

            return {

                "is_compliant": True,

                "days": 0,

                "max_allowed": 15,

                "status_label": "تاريخ غير محدد",

                "badge_color": "gray",

                "warning_message": str(e)

            }



    def get_class_daily_exam_load(self, class_name: str, target_date_str: str, exclude_exam_id: Optional[str] = None) -> List[Dict[str, Any]]:

        """

        حساب عدد الفروض المبرمجة لنفس القسم في تاريخ محدد من قبل سائر الأساتذة

        """

        matches = []

        for ex in self.exams:

            if ex.get("id") == exclude_exam_id:

                continue

            if ex.get("class_name") == class_name and ex.get("exam_date") == target_date_str:

                matches.append(ex)

        return matches



    def calculate_recommended_deadlines(

        self,

        teacher_name: str,

        exam_date: datetime.date,

        semester: int,

        timetable_data: Optional[Dict[str, Any]] = None

    ) -> Dict[str, Any]:

        """

        احتساب المدة الفاصلة وتاريخ التصحيح وتاريخ تسليم النقط بمرونة وبناء على عدد الأقسام المسندة للأستاذ

        مع مراعاة ألا تتجاوز 15 يوماً وعدم تجاوز آخر أجل محدد من طرف الإدارة.

        """

        # Count classes for teacher

        classes_count = 1

        if timetable_data:

            teacher_classes = set()

            st_data = timetable_data.get("student_timetables", {})

            for c_name, days in st_data.items():

                for d, hours in days.items():

                    if isinstance(hours, dict):

                        for h, cell in hours.items():

                            if isinstance(cell, dict) and cell.get("teacher") == teacher_name:

                                teacher_classes.add(c_name.strip(' ,;،\t\r\n'))

            if teacher_classes:

                classes_count = len(teacher_classes)



        # Workload-based dynamic delay:

        # 1-2 classes -> 9 days submission delay, 4 days correction

        # 3-4 classes -> 12 days submission delay, 6 days correction

        # 5+ classes  -> 15 days submission delay (المهلة القصوى), 8 days correction

        if classes_count <= 2:

            sub_delay = 9

            corr_delay = 4

            load_label = f"عبء خفيف ({classes_count} أقسام)"

        elif classes_count <= 4:

            sub_delay = 12

            corr_delay = 6

            load_label = f"عبء متوسط ({classes_count} أقسام)"

        else:

            sub_delay = 15

            corr_delay = 8

            load_label = f"عبء مرتفع ({classes_count} أقسام - مهلة قصوى)"



        max_allowed = self.settings.get("max_submission_delay_days", 15)

        sub_delay = min(sub_delay, max_allowed)



        # Check against principal's ministerial final deadline

        cal_sem = self.settings.get("ministerial_calendar", {}).get(str(semester), {})

        final_sub_deadline_str = cal_sem.get("final_submission_deadline")



        target_sub_date = exam_date + timedelta(days=sub_delay)

        if final_sub_deadline_str:

            try:

                final_sub_dt = datetime.strptime(final_sub_deadline_str, "%Y-%m-%d").date()

                if target_sub_date > final_sub_dt:

                    target_sub_date = final_sub_dt

                    sub_delay = max(1, (target_sub_date - exam_date).days)

            except Exception:

                pass



        target_corr_date = exam_date + timedelta(days=min(corr_delay, max(2, sub_delay - 2)))



        return {

            "classes_count": classes_count,

            "load_label": load_label,

            "days_to_submission": sub_delay,

            "correction_date": target_corr_date.strftime("%Y-%m-%d"),

            "grades_submission_date": target_sub_date.strftime("%Y-%m-%d")

        }



    def get_recommendations_for_exam(

        self,

        teacher_name: str,

        class_name: str,

        semester: int,

        exam_number: int,

        target_week_start: Optional[str] = None,

        timetable_data: Optional[Dict[str, Any]] = None

    ) -> List[Dict[str, Any]]:

        """

        محرك التوصية الذكي:

        يقترح على الأستاذ أفضل الأيام والحصص المتاحة في جدول القسم مع مراعاة تفادي تزامن الفروض في نفس اليوم

        """

        if not timetable_data:

            return []



        weekly_sessions = self.get_teacher_class_sessions(teacher_name, class_name, timetable_data)

        if not weekly_sessions:

            return []



        # Reference start date (e.g. today or next Monday)

        now = datetime.now().date()

        if target_week_start:

            try:

                base_date = datetime.strptime(target_week_start, "%Y-%m-%d").date()

            except Exception:

                base_date = now

        else:

            base_date = now



        # Align base_date to Monday of that week

        monday = base_date - timedelta(days=base_date.weekday())



        recommendations = []

        # Check next 2 weeks

        for week_offset in [0, 1]:

            cur_monday = monday + timedelta(weeks=week_offset)

            for sess in weekly_sessions:

                day_name = sess["day_name"]

                day_idx = ARABIC_DAYS.index(day_name) if day_name in ARABIC_DAYS else 0

                actual_date = cur_monday + timedelta(days=day_idx)

                date_str = actual_date.strftime("%Y-%m-%d")



                # Look up existing exams for this class on this date

                existing_for_class = self.get_class_daily_exam_load(class_name, date_str)

                count = len(existing_for_class)



                if count == 0:

                    score = 100

                    status = "optimal"

                    badge_label = "🟢 موصى به جداً (0 فروض للقسم في هذا اليوم)"

                    note = "اليوم خالٍ تماماً من أي فرض آخر لهذا القسم. راحة تامة للمتعلمين."

                elif count == 1:

                    other_subj = existing_for_class[0].get("subject", "مادة أخرى")

                    score = 60

                    status = "acceptable"

                    badge_label = f"🟡 مقبول مع تنبيه (يوجد فرض مبرمج: {other_subj})"

                    note = f"ملاحظة: لدى القسم فرض في مادة {other_subj} في هذا اليوم. يفضل اختيار يوم آخر إن أمكن."

                else:

                    other_subjs = "، ".join([e.get("subject", "") for e in existing_for_class])

                    score = 20

                    status = "crowded"

                    badge_label = f"🔴 غير مناسب (لدى القسم {count} فروض: {other_subjs})"

                    note = "تحذير: تراكم مفرط للفروض على القسم في نفس اليوم! لا ينصح ببرمجة الفرض هنا إطلاقاً."



                recommendations.append({

                    "date": date_str,

                    "date_display": actual_date.strftime("%d/%m/%Y"),

                    "day_name": day_name,

                    "period": sess["period"],

                    "period_label": sess["period_label"],

                    "hour": sess["hour"],

                    "time_str": sess["time_str"],

                    "room": sess["room"],

                    "existing_exams_count": count,

                    "existing_exams": existing_for_class,

                    "score": score,

                    "status": status,

                    "badge_label": badge_label,

                    "note": note

                })



        # Sort recommendations by score descending, then date

        recommendations.sort(key=lambda r: (-r["score"], r["date"]))

        return recommendations



    def save_or_update_exam(self, exam_data: Dict[str, Any]) -> Dict[str, Any]:

        """

        حفظ أو تحديث برمجة فرض محروس

        """

        exam_id = exam_data.get("id")

        if not exam_id:

            teacher = exam_data.get("teacher_name", "teacher")

            cls = exam_data.get("class_name", "class")

            sem = exam_data.get("semester", 1)

            num = exam_data.get("exam_number", 1)

            exam_id = f"exam_{teacher}_{cls}_s{sem}_n{num}".replace(" ", "_").replace("/", "_")

            exam_data["id"] = exam_id



        # Normalize room names & deadline keys
        rm = exam_data.get("room_name") or exam_data.get("exam_room") or exam_data.get("room") or ""
        exam_data["room_name"] = rm
        exam_data["exam_room"] = rm

        s_date = exam_data.get("submission_deadline") or exam_data.get("grades_submission_date") or exam_data.get("submission_date") or ""
        exam_data["submission_deadline"] = s_date
        exam_data["grades_submission_date"] = s_date

        e_date = exam_data.get("exam_date", "")
        if not exam_data.get("exam_day_name") and e_date:
            try:
                dt = datetime.strptime(e_date, "%Y-%m-%d")
                day_names_ar = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
                exam_data["exam_day_name"] = day_names_ar[dt.weekday()]
            except Exception:
                pass

        # Calculate 15-day compliance
        comp = self.check_15_days_compliance(e_date, s_date)
        exam_data["days_to_submission"] = comp["days"]
        exam_data["is_compliant_15_days"] = comp["is_compliant"]
        exam_data["compliance_info"] = comp
        exam_data["updated_at"] = datetime.now().isoformat()



        # Update or add

        found = False

        for i, ex in enumerate(self.exams):

            if ex.get("id") == exam_id:

                self.exams[i] = exam_data

                found = True

                break

        if not found:

            exam_data["created_at"] = datetime.now().isoformat()

            self.exams.append(exam_data)



        self.save_state()

        return {"success": True, "exam": exam_data}



    def delete_exam(self, exam_id: str) -> bool:

        """حذف فرض مبرمج"""

        initial_len = len(self.exams)

        self.exams = [e for e in self.exams if e.get("id") != exam_id]

        if len(self.exams) < initial_len:

            self.save_state()

            return True

        return False

    def delete_exams_bulk(self, filters: Dict[str, Any]) -> int:
        """
        حذف وإلغاء الفروض بشكل مجمع:
        - type: 'all' (جميع الفروض في الدورة أو المؤسسة)
        - type: 'teacher' (جميع فروض أستاذ معين)
        - type: 'exam_numbers' (حذف الفروض برقم معين مثلاً [4] أو [1, 3])
        - type: 'ids' (قائمة معرفات محددة)
        """
        initial_len = len(self.exams)
        del_type = filters.get("type", "all")
        sem = filters.get("semester")
        if sem is not None:
            try:
                sem = int(sem)
            except Exception:
                sem = None

        to_keep = []
        for ex in self.exams:
            ex_sem = ex.get("semester")
            try:
                ex_sem = int(ex_sem)
            except Exception:
                ex_sem = None

            if sem is not None and ex_sem is not None and ex_sem != sem:
                to_keep.append(ex)
                continue

            match_delete = False
            if del_type == "all":
                match_delete = True
            elif del_type == "teacher":
                target_teacher = (filters.get("teacher_name") or filters.get("teacherId") or "").strip()
                t_name = (ex.get("teacher_name") or "").strip()
                t_id = (ex.get("teacher_id") or "").strip()
                if target_teacher and (target_teacher == t_name or target_teacher == t_id):
                    match_delete = True
            elif del_type == "exam_numbers":
                raw_nums = filters.get("exam_numbers", [])
                nums = [int(n) for n in raw_nums if str(n).isdigit()]
                target_teacher = (filters.get("teacher_name") or filters.get("teacherId") or "").strip()
                t_name = (ex.get("teacher_name") or "").strip()
                t_id = (ex.get("teacher_id") or "").strip()
                teacher_matches = True
                if target_teacher and (target_teacher != t_name and target_teacher != t_id):
                    teacher_matches = False
                ex_num = int(ex.get("exam_number") or 1)
                if teacher_matches and ex_num in nums:
                    match_delete = True
            elif del_type == "ids":
                ids_set = set(filters.get("ids", []))
                if ex.get("id") in ids_set:
                    match_delete = True

            if not match_delete:
                to_keep.append(ex)

        deleted_count = initial_len - len(to_keep)
        if deleted_count > 0:
            self.exams = to_keep
            self.save_state()

        return deleted_count



    def get_dashboard_summary(self, semester: Optional[int] = None) -> Dict[str, Any]:

        """

        إحصائيات شاملة للوحة قيادة الإدارة والأساتذة

        """

        exams = self.exams

        if semester:

            exams = [e for e in exams if e.get("semester") == semester]



        total_exams = len(exams)

        compliant_count = sum(1 for e in exams if e.get("is_compliant_15_days", True))

        non_compliant_count = total_exams - compliant_count



        classes_covered = set(e.get("class_name") for e in exams if e.get("class_name"))

        teachers_covered = set(e.get("teacher_name") for e in exams if e.get("teacher_name"))



        # Find any multi-exam collisions on the same day for any class

        class_day_counts: Dict[str, List[Dict[str, Any]]] = {}

        for e in exams:

            c = e.get("class_name")

            d = e.get("exam_date")

            if c and d:

                key = f"{c}##{d}"

                class_day_counts.setdefault(key, []).append(e)



        crowded_days = []

        for key, ex_list in class_day_counts.items():

            if len(ex_list) >= 2:

                cls, dt = key.split("##")

                crowded_days.append({

                    "class_name": cls,

                    "date": dt,

                    "day_name": ex_list[0].get("exam_day_name", ""),

                    "exams_count": len(ex_list),

                    "subjects": [x.get("subject") for x in ex_list],

                    "teachers": [x.get("teacher_name") for x in ex_list]

                })



        return {

            "total_exams": total_exams,

            "compliant_count": compliant_count,

            "non_compliant_count": non_compliant_count,

            "compliance_rate": round((compliant_count / total_exams * 100), 1) if total_exams > 0 else 100.0,

            "classes_count": len(classes_covered),

            "teachers_count": len(teachers_covered),

            "crowded_days_count": len(crowded_days),

            "crowded_days": crowded_days

        }



    def render_teacher_schedule_sheet_html(self, teacher_name: str, semester: int, institution_info: Dict[str, Any]) -> str:

        """

        توليد وثيقة A4 الرسمية لبطاقة برمجة وتتبع فروض المراقبة المستمرة للأستاذ

        """

        t_exams = [e for e in self.exams if e.get("teacher_name") == teacher_name and e.get("semester") == semester]

        t_exams.sort(key=lambda x: (

            x.get("exam_date", "9999-99-99"),

            x.get("exam_time_str", ""),

            x.get("class_name", ""),

            x.get("exam_number", 1)

        ))



        inst_name = institution_info.get("name", "الثانوية التأهيلية")

        academy = institution_info.get("academy", "الأكاديمية الجهوية للتربية والتكوين")

        province = institution_info.get("province", "المديرية الإقليمية")

        year = institution_info.get("academic_year", "2026/2027")

        principal = institution_info.get("principal", "رئيس المؤسسة")

        subject = t_exams[0].get("subject", "") if t_exams else ""



        sem_label = "الدورة الأولى" if semester == 1 else "الدورة الثانية"



        rows_html = ""

        if not t_exams:

            rows_html = """<tr><td colspan="9" style="text-align:center; padding: 25px; color:#888;">لم يتم تسجيل أي برمجة للفروض لهذا الأستاذ في هذه الدورة بعد.</td></tr>"""

        else:

            for idx, ex in enumerate(t_exams, 1):

                cls = ex.get("class_name", "")

                num = ex.get("exam_number", 1)

                num_lbl = f"الفرض رقم {num}"

                e_date = ex.get("exam_date", "-")

                e_day = ex.get("exam_day_name", "")

                e_time = ex.get("exam_time_str", "")

                e_room = ex.get("room_name") or ex.get("exam_room") or ex.get("room") or "-"
                c_date = ex.get("correction_date", "-")
                s_date = ex.get("submission_deadline") or ex.get("grades_submission_date") or ex.get("submission_date") or "-"
                diff = ex.get("days_to_submission", 0)
                if (not diff or diff == 0) and e_date != "-" and s_date != "-":
                    try:
                        diff = (datetime.strptime(s_date, "%Y-%m-%d") - datetime.strptime(e_date, "%Y-%m-%d")).days
                    except Exception:
                        diff = 0
                is_comp = ex.get("is_compliant_15_days", (diff <= 15))
                status_badge = f'<span style="font-weight:bold; color:{"#047857" if is_comp else "#b91c1c"};">{diff} يوماً</span>' if diff > 0 else '<span style="color:#64748b;">-</span>'

                notes = ex.get("notes", "-") or "-"



                rows_html += f"""

                <tr style="border-bottom: 1px solid #cbd5e1; text-align: center; height: 36px; font-size: 11px;">

                    <td style="font-weight:bold; border-left: 1px solid #cbd5e1;">{idx}</td>

                    <td style="font-weight:bold; color:#0f172a; border-left: 1px solid #cbd5e1;">{cls}</td>

                    <td style="font-weight:bold; color:#1e3a8a; border-left: 1px solid #cbd5e1;">{num_lbl}</td>

                    <td style="border-left: 1px solid #cbd5e1; white-space:nowrap; padding:3px 6px;">
                        <span style="font-weight:900; font-size:12px; color:#0f172a; direction:ltr; display:inline-block;">{e_date}</span><br>
                        <span style="color:#334155; font-weight:700; font-size:10px;">{e_day} • {e_time}</span>
                    </td>

                    <td style="border-left: 1px solid #cbd5e1;">{e_room}</td>

                    <td style="border-left: 1px solid #cbd5e1;">{c_date}</td>

                    <td style="border-left: 1px solid #cbd5e1;">{s_date}</td>

                    <td style="border-left: 1px solid #cbd5e1;">{status_badge}</td>

                    <td style="color:#475569;">{notes}</td>

                </tr>

                """



        html = f"""<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

    <meta charset="UTF-8">

    <title>ورقة برمجة الفروض المحروسة - {teacher_name}</title>

    <style>

        @page {{

            size: A4 portrait;

            margin: 12mm 15mm 15mm 15mm;

        }}

        body {{

            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;

            background: #fff;

            color: #0f172a;

            margin: 0;

            padding: 0;

            direction: rtl;

        }}

        .header-box {{

            display: flex;

            justify-content: space-between;

            align-items: center;

            border-bottom: 2px solid #0f172a;

            padding-bottom: 8px;

            margin-bottom: 12px;

        }}

        .title-box {{

            text-align: center;

            background: #f1f5f9;

            border: 1.5px solid #0f172a;

            border-radius: 8px;

            padding: 8px;

            margin-bottom: 15px;

        }}

        .info-grid {{

            display: grid;

            grid-template-columns: repeat(4, 1fr);

            gap: 8px;

            background: #f8fafc;

            border: 1px solid #cbd5e1;

            border-radius: 6px;

            padding: 8px 12px;

            margin-bottom: 15px;

            font-size: 12px;

        }}

        table {{

            width: 100%;

            border-collapse: collapse;

            border: 1.5px solid #0f172a;

            margin-bottom: 20px;

        }}

        th {{

            background: #1e293b;

            color: white;

            font-size: 11.5px;

            font-weight: bold;

            padding: 7px 4px;

            border: 1px solid #0f172a;

            text-align: center;

        }}

        .signatures-box {{

            margin-top: 30px;

            display: grid;

            grid-template-columns: 1fr 1fr 1fr;

            text-align: center;

            font-size: 12px;

            page-break-inside: avoid;

        }}

        .sig-col {{

            height: 90px;

            display: flex;

            flex-direction: column;

            justify-content: space-between;

        }}

        .legal-notice {{

            font-size: 10px;

            color: #475569;

            background: #f8fafc;

            border-right: 3px solid #3b82f6;

            padding: 5px 10px;

            margin-bottom: 15px;

        }}

        @media print {{

            .no-print {{ display: none; }}

            body {{ -webkit-print-color-adjust: exact; }}

        }}

    </style>

</head>

<body>

    <div class="no-print" style="background:#1e293b; color:#fff; padding:10px; text-align:center; margin-bottom:15px; border-radius:6px;">

        <button onclick="window.print()" style="background:#10b981; color:#fff; border:none; padding:8px 24px; font-weight:bold; border-radius:6px; cursor:pointer; font-size:14px;">🖨️ طباعة الوثيقة (A4)</button>

        <button onclick="window.close()" style="background:#64748b; color:#fff; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; margin-right:10px;">إغلاق</button>

    </div>



    <div class="header-box">

        <div style="text-align: right; font-size: 11px; line-height: 1.4;">

            <strong>المملكة المغربية</strong><br>

            وزارة التربية الوطنية والتعليم الأولي والرياضة<br>

            {academy}<br>

            {province}

        </div>

        <div style="text-align: center;">

            <div style="font-size: 18px; font-weight: 900; color: #1e3a8a;">{inst_name}</div>

            <div style="font-size: 11px; color: #64748b;">الموسم الدراسي: {year}</div>

        </div>

        <div style="text-align: left; font-size: 11px; line-height: 1.4;">

            <strong>إدارة المؤسسة</strong><br>

            مصلحة الشؤون التربوية<br>

            تنظيم المراقبة المستمرة

        </div>

    </div>



    <div class="title-box">

        <h2 style="margin: 0; font-size: 16px; color: #0f172a;">بطاقة برمجة وتتبع فروض المراقبة المستمرة</h2>

        <div style="font-size: 12px; color: #475569; margin-top: 3px;">{sem_label} — وفق المذكرات الوزارية المنظمة للتقويم التربوي</div>

    </div>



    <div class="info-grid">

        <div><strong>الأستاذ(ة):</strong> {teacher_name}</div>

        <div><strong>المادة:</strong> {subject or 'التعليم العام'}</div>

        <div><strong>الدورة:</strong> {sem_label}</div>

        <div><strong>تاريخ اعتماد البرمجة:</strong> {datetime.now().strftime('%d/%m/%Y')}</div>

    </div>



    



    <table>

        <thead>
            <tr>
                <th style="width: 4%;">ر.ت</th>
                <th style="width: 11%;">القسم</th>
                <th style="width: 11%;">الفرض</th>
                <th style="width: 32%;">تاريخ وتوقيت الإجراء</th>
                <th style="width: 7%;">القاعة</th>
                <th style="width: 12%;">تاريخ التصحيح</th>
                <th style="width: 12%;">تاريخ تسليم النقط</th>
                <th style="width: 6%;">المدة</th>
                <th style="width: 5%;">ملاحظات</th>
            </tr>
        </thead>

        <tbody>

            {rows_html}

        </tbody>

    </table>



    <div class="signatures-box">

        <div class="sig-col">

            <strong>توقيع السيد(ة) الأستاذ(ة):</strong>

            <span style="color:#94a3b8; font-size:10px;">التاريخ: ........................</span>

        </div>

        <div class="sig-col">

            <strong>تأشيرة الحراسة العامة للخارجية:</strong>

            <span style="color:#94a3b8; font-size:10px;">التاريخ: ........................</span>

        </div>

        <div class="sig-col">

            <strong>تأشيرة وخاتم السيد مدير المؤسسة:</strong>

            <span style="color:#94a3b8; font-size:10px;">{principal}</span>

        </div>

    </div>

</body>

</html>"""

        return html



    def render_school_calendar_html(self, semester: int, institution_info: Dict[str, Any]) -> str:

        """

        توليد الجدولة العامة الشاملة لفروض المؤسسة للطباعة والعرض في قاعة الأساتذة

        """

        inst_name = institution_info.get("name", "المؤسسة التعليمية")

        year = institution_info.get("academic_year", "2026/2027")

        sem_label = "الدورة الأولى" if semester == 1 else "الدورة الثانية"



        exams = [e for e in self.exams if e.get("semester") == semester]

        exams.sort(key=self._exam_sort_key)



        # Group by date

        by_date = {}

        for e in exams:

            d = e.get("exam_date", "غير محدد")

            by_date.setdefault(d, []).append(e)



        rows = ""

        for d, ex_list in sorted(by_date.items()):

            d_name = ex_list[0].get("exam_day_name", "")
            if not d_name and d and d != "غير محدد":
                try:
                    dt = datetime.strptime(d, "%Y-%m-%d")
                    day_names_ar = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
                    d_name = day_names_ar[dt.weekday()]
                except Exception:
                    d_name = ""

            for i, ex in enumerate(ex_list):

                date_cell = f'<td rowspan="{len(ex_list)}" style="font-weight:bold; background:#f8fafc; border:1px solid #cbd5e1; text-align:center;">{d_name}<br>{d}</td>' if i == 0 else ""

                cls = ex.get("class_name", "")

                t = ex.get("teacher_name", "")

                s = ex.get("subject", "")

                num = ex.get("exam_number", 1)

                tm = ex.get("exam_time_str", "")

                rm = ex.get("room_name") or ex.get("exam_room") or ex.get("room") or ""

                rows += f"""

                <tr style="border-bottom: 1px solid #cbd5e1; text-align: center; height: 32px; font-size: 11px;">

                    {date_cell}

                    <td style="font-weight:bold; color:#0f172a; border-left: 1px solid #cbd5e1;">{cls}</td>

                    <td style="font-weight:bold; color:#1e3a8a; border-left: 1px solid #cbd5e1;">الفرض {num}</td>

                    <td style="border-left: 1px solid #cbd5e1;">{s}</td>

                    <td style="border-left: 1px solid #cbd5e1;">{t}</td>

                    <td style="border-left: 1px solid #cbd5e1;">{tm}</td>

                    <td>{rm}</td>

                </tr>

                """



        if not rows:

            rows = """<tr><td colspan="7" style="text-align:center; padding: 25px; color:#888;">لا توجد فروض مبرمجة حالياً في هذه الدورة.</td></tr>"""



        return f"""<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

    <meta charset="UTF-8">

    <title>البرنامج العام لفروض المراقبة المستمرة - {sem_label}</title>

    <style>

        @page {{ size: A4 landscape; margin: 10mm 12mm; }}

        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #fff; margin:0; padding:10px; direction:rtl; }}

        table {{ width: 100%; border-collapse: collapse; border: 2px solid #0f172a; }}

        th {{ background: #1e293b; color: #fff; padding: 6px; font-size: 11.5px; border: 1px solid #0f172a; }}

        @media print {{ .no-print {{ display: none; }} }}

    </style>

</head>

<body>

    <div class="no-print" style="text-align:center; margin-bottom:10px;">

        <button onclick="window.print()" style="background:#10b981; color:#fff; border:none; padding:8px 20px; font-weight:bold; border-radius:6px; cursor:pointer;">🖨️ طباعة الجدول العام (A4 أفقي)</button>

    </div>

    <div style="text-align:center; border-bottom: 2px solid #0f172a; padding-bottom:8px; margin-bottom:12px;">

        <h2 style="margin:0; font-size: 18px; color: #0f172a;">{inst_name} — البرنامج العام لفروض المراقبة المستمرة ({sem_label})</h2>

        <div style="font-size: 12px; color: #475569; margin-top: 3px;">الموسم الدراسي: {year} | للإخبار وتنسيق وتفادي تراكم الفروض على الأقسام</div>

    </div>

    <table>

        <thead>

            <tr>

                <th style="width: 15%;">تاريخ الإجراء</th>

                <th style="width: 14%;">القسم</th>

                <th style="width: 12%;">الفرض</th>

                <th style="width: 18%;">المادة</th>

                <th style="width: 20%;">الأستاذ(ة)</th>

                <th style="width: 13%;">التوقيت</th>

                <th style="width: 8%;">القاعة</th>

            </tr>

        </thead>

        <tbody>

            {rows}

        </tbody>

    </table>

</body>

</html>"""

