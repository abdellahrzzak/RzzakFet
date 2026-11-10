# -*- coding: utf-8 -*-
"""
محرك تقرير الحراسة العامة اليومي — General Supervisor Daily Operational Report
وثيقة إدارية رسمية معتمدة بالمؤسسات التعليمية المغربية لرصد سير الدراسة اليومي،
مواظبة الأطر التربوية، حالة الأقسام، وتوثيق الحوادث وتأشيرة الإدارة.
"""

import os, sys, base64
from typing import Dict, List, Any, Optional
from datetime import datetime

DAYS_AR_MAP = {
    "الاثنين": ["الاثنين ص", "الاثنين م"],
    "الإثنين": ["الاثنين ص", "الاثنين م"],
    "الثلاثاء": ["الثلاثاء ص", "الثلاثاء م"],
    "الاربعاء": ["الاربعاء ص", "الاربعاء م"],
    "الأربعاء": ["الاربعاء ص", "الاربعاء م"],
    "الخميس": ["الخميس ص", "الخميس م"],
    "الجمعة": ["الجمعة ص", "الجمعة م"],
    "السبت": ["السبت ص", "السبت م"]
}


class SurveillanceDailyReportEngine:
    def __init__(self, timetable_result: Dict[str, Any] = None, institution_data: Any = None):
        self.timetable = timetable_result or {}
        self.institution = institution_data

        # Automatically invert teacher_timetables to student_timetables if missing
        if not self.timetable.get("student_timetables") and self.timetable.get("teacher_timetables"):
            st = {}
            for t_name, days in self.timetable["teacher_timetables"].items():
                for d_name, hours in days.items():
                    for h, cell in hours.items():
                        if not cell or not isinstance(cell, dict):
                            continue
                        cls_name = cell.get("class") or cell.get("students")
                        if not cls_name:
                            continue
                        if cls_name not in st:
                            st[cls_name] = {}
                        if d_name not in st[cls_name]:
                            st[cls_name][d_name] = {}
                        st[cls_name][d_name][str(h)] = {
                            "subject": cell.get("subject", ""),
                            "teacher": t_name,
                            "room": cell.get("room", ""),
                            "class": cls_name
                        }
            # Alias TCSEF-1 and TCSF-1
            if "TCSEF-1" in st and "TCSF-1" not in st:
                st["TCSF-1"] = st["TCSEF-1"]
            elif "TCSF-1" in st and "TCSEF-1" not in st:
                st["TCSEF-1"] = st["TCSF-1"]
            self.timetable["student_timetables"] = st

    
    def get_slot_times(self):
        inst = self.institution
        m_times = []
        a_times = []
        if inst:
            if hasattr(inst, "morning_period_times") and inst.morning_period_times:
                m_times = list(inst.morning_period_times)
            elif isinstance(inst, dict) and inst.get("morning_period_times"):
                m_times = list(inst["morning_period_times"])
            if hasattr(inst, "afternoon_period_times") and inst.afternoon_period_times:
                a_times = list(inst.afternoon_period_times)
            elif isinstance(inst, dict) and inst.get("afternoon_period_times"):
                a_times = list(inst["afternoon_period_times"])

        if not m_times or not a_times:
            try:
                import json
                state_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app_state.json')
                if os.path.exists(state_path):
                    with open(state_path, 'r', encoding='utf-8') as f:
                        app_st = json.load(f)
                    inst_d = app_st.get("institution", {})
                    if not m_times and inst_d.get("morning_period_times"):
                        m_times = list(inst_d["morning_period_times"])
                    if not a_times and inst_d.get("afternoon_period_times"):
                        a_times = list(inst_d["afternoon_period_times"])
            except Exception:
                pass

        if not m_times or len(m_times) < 4:
            m_times = ["08:00 - 09:00", "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00"]
        if not a_times or len(a_times) < 4:
            a_times = ["14:00 - 15:00", "15:00 - 16:00", "16:00 - 17:00", "17:00 - 18:00"]

        def parse_range(s, default_st, default_en):
            parts = s.split("-") if "-" in s else [default_st, default_en]
            return parts[0].strip(), parts[1].strip()

        slot_times_m = {
            "1": parse_range(m_times[0], "08:00", "09:00"),
            "2": parse_range(m_times[1], "09:00", "10:00"),
            "3": parse_range(m_times[2], "10:00", "11:00"),
            "4": parse_range(m_times[3], "11:00", "12:00")
        }
        slot_times_a = {
            "1": parse_range(a_times[0], "14:00", "15:00"),
            "2": parse_range(a_times[1], "15:00", "16:00"),
            "3": parse_range(a_times[2], "16:00", "17:00"),
            "4": parse_range(a_times[3], "17:00", "18:00")
        }
        return slot_times_m, slot_times_a

    def get_scheduled_day_summary(self, day_base: str) -> Dict[str, Any]:
        """
        استخراج الإحصائيات المبرمجة لليوم المحدد من جدول الحصص الفعلي
        """
        student_timetables = self.timetable.get("student_timetables", {})
        teacher_timetables = self.timetable.get("teacher_timetables", {})

        # الأيام الفرعية (صباح ومساء)
        sub_days = DAYS_AR_MAP.get(day_base, [f"{day_base} ص", f"{day_base} م"])

        morning_day = sub_days[0]
        afternoon_day = sub_days[1] if len(sub_days) > 1 else sub_days[0]

        morning_sessions = []
        afternoon_sessions = []

        active_classes_m = set()
        active_classes_a = set()
        active_teachers_m = set()
        active_teachers_a = set()

        for c_name, days_data in student_timetables.items():
            # صباح
            m_hours = days_data.get(morning_day, {})
            for h, cell in m_hours.items():
                if cell and cell.get("subject"):
                    active_classes_m.add(c_name)
                    if cell.get("teacher"):
                        active_teachers_m.add(cell["teacher"])
                    morning_sessions.append({
                        "period": "صباحية",
                        "hour": h,
                        "class": c_name,
                        "subject": cell.get("subject", ""),
                        "teacher": cell.get("teacher", ""),
                        "room": cell.get("room", "")
                    })
            # مساء
            a_hours = days_data.get(afternoon_day, {})
            for h, cell in a_hours.items():
                if cell and cell.get("subject"):
                    active_classes_a.add(c_name)
                    if cell.get("teacher"):
                        active_teachers_a.add(cell["teacher"])
                    afternoon_sessions.append({
                        "period": "مسائية",
                        "hour": h,
                        "class": c_name,
                        "subject": cell.get("subject", ""),
                        "teacher": cell.get("teacher", ""),
                        "room": cell.get("room", "")
                    })

        all_teachers_today = sorted(list(active_teachers_m | active_teachers_a))
        all_classes_today = sorted(list(active_classes_m | active_classes_a))

        # Generate intelligent scheduled blocks per class (pairing 2-hour blocks where subject/teacher match)
        slot_times_m, slot_times_a = self.get_slot_times()

        m_1_2 = f"{slot_times_m['1'][0]} - {slot_times_m['2'][1]}"
        m_3_4 = f"{slot_times_m['3'][0]} - {slot_times_m['4'][1]}"
        m_half = f"{slot_times_m['1'][0]} - {slot_times_m['4'][1]}"

        a_1_2 = f"{slot_times_a['1'][0]} - {slot_times_a['2'][1]}"
        a_2_3 = f"{slot_times_a['2'][0]} - {slot_times_a['3'][1]}"
        a_3_4 = f"{slot_times_a['3'][0]} - {slot_times_a['4'][1]}"
        a_half = f"{slot_times_a['1'][0]} - {slot_times_a['4'][1]}"

        full_day = f"{slot_times_m['1'][0]} - {slot_times_a['4'][1]}"

        class_sessions_map = {}
        for c_name, days_data in student_timetables.items():
            blocks = []
            m_hours = days_data.get(morning_day, {})
            a_hours = days_data.get(afternoon_day, {})

            # Morning 2-hour blocks
            h1 = m_hours.get("1") or m_hours.get(1)
            h2 = m_hours.get("2") or m_hours.get(2)
            h3 = m_hours.get("3") or m_hours.get(3)
            h4 = m_hours.get("4") or m_hours.get(4)

            if h1 and h2 and h1.get("subject") and h1.get("subject") == h2.get("subject") and h1.get("teacher") == h2.get("teacher"):
                blocks.append({
                    "value": f"ح 1 و 2 ص ({m_1_2})",
                    "label": f"ح 1 و 2 ص ({m_1_2}) — ساعتان",
                    "hours": 2,
                    "period": "صباحية",
                    "time_range": m_1_2,
                    "subject": h1.get("subject", ""),
                    "teacher": h1.get("teacher", ""),
                    "room": h1.get("room", "")
                })

            if h3 and h4 and h3.get("subject") and h3.get("subject") == h4.get("subject") and h3.get("teacher") == h4.get("teacher"):
                blocks.append({
                    "value": f"ح 3 و 4 ص ({m_3_4})",
                    "label": f"ح 3 و 4 ص ({m_3_4}) — ساعتان",
                    "hours": 2,
                    "period": "صباحية",
                    "time_range": m_3_4,
                    "subject": h3.get("subject", ""),
                    "teacher": h3.get("teacher", ""),
                    "room": h3.get("room", "")
                })

            # Morning individual hours
            for hk in ["1", "2", "3", "4"]:
                cell = m_hours.get(hk) or m_hours.get(int(hk))
                if cell and cell.get("subject"):
                    t_st, t_en = slot_times_m[hk]
                    blocks.append({
                        "value": f"ح {hk} ص ({t_st} - {t_en})",
                        "label": f"ح {hk} ص ({t_st} - {t_en}) — ساعة واحدة",
                        "hours": 1,
                        "period": "صباحية",
                        "time_range": f"{t_st} - {t_en}",
                        "subject": cell.get("subject", ""),
                        "teacher": cell.get("teacher", ""),
                        "room": cell.get("room", "")
                    })

            # Afternoon 2-hour blocks
            ah1 = a_hours.get("1") or a_hours.get(1)
            ah2 = a_hours.get("2") or a_hours.get(2)
            ah3 = a_hours.get("3") or a_hours.get(3)
            ah4 = a_hours.get("4") or a_hours.get(4)

            if ah1 and ah2 and ah1.get("subject") and ah1.get("subject") == ah2.get("subject") and ah1.get("teacher") == ah2.get("teacher"):
                blocks.append({
                    "value": f"ح 1 و 2 م ({a_1_2})",
                    "label": f"ح 1 و 2 م ({a_1_2}) — ساعتان",
                    "hours": 2,
                    "period": "مسائية",
                    "time_range": a_1_2,
                    "subject": ah1.get("subject", ""),
                    "teacher": ah1.get("teacher", ""),
                    "room": ah1.get("room", "")
                })
            elif ah2 and ah3 and ah2.get("subject") and ah2.get("subject") == ah3.get("subject") and ah2.get("teacher") == ah3.get("teacher"):
                blocks.append({
                    "value": f"ح 2 و 3 م ({a_2_3})",
                    "label": f"ح 2 و 3 م ({a_2_3}) — ساعتان",
                    "hours": 2,
                    "period": "مسائية",
                    "time_range": a_2_3,
                    "subject": ah2.get("subject", ""),
                    "teacher": ah2.get("teacher", ""),
                    "room": ah2.get("room", "")
                })
            elif ah3 and ah4 and ah3.get("subject") and ah3.get("subject") == ah4.get("subject") and ah3.get("teacher") == ah4.get("teacher"):
                blocks.append({
                    "value": f"ح 3 و 4 م ({a_3_4})",
                    "label": f"ح 3 و 4 م ({a_3_4}) — ساعتان",
                    "hours": 2,
                    "period": "مسائية",
                    "time_range": a_3_4,
                    "subject": ah3.get("subject", ""),
                    "teacher": ah3.get("teacher", ""),
                    "room": ah3.get("room", "")
                })

            # Afternoon individual hours
            for hk in ["1", "2", "3", "4"]:
                cell = a_hours.get(hk) or a_hours.get(int(hk))
                if cell and cell.get("subject"):
                    t_st, t_en = slot_times_a[hk]
                    blocks.append({
                        "value": f"ح {hk} م ({t_st} - {t_en})",
                        "label": f"ح {hk} م ({t_st} - {t_en}) — ساعة واحدة",
                        "hours": 1,
                        "period": "مسائية",
                        "time_range": f"{t_st} - {t_en}",
                        "subject": cell.get("subject", ""),
                        "teacher": cell.get("teacher", ""),
                        "room": cell.get("room", "")
                    })

            # Standard multi-hour periods
            blocks.append({
                "value": "نصف يوم صباحي (4س)",
                "label": f"نصف يوم صباحي ({m_half}) — 4 ساعات",
                "hours": 4,
                "period": "صباحية",
                "time_range": m_half,
                "subject": "حصص الفترة الصباحية",
                "teacher": ""
            })
            blocks.append({
                "value": "نصف يوم مسائي (4س)",
                "label": f"نصف يوم مسائي ({a_half}) — 4 ساعات",
                "hours": 4,
                "period": "مسائية",
                "time_range": a_half,
                "subject": "حصص الفترة المسائية",
                "teacher": ""
            })
            blocks.append({
                "value": "يوم كامل (8س)",
                "label": f"يوم كامل ({full_day}) — 8 ساعات",
                "hours": 8,
                "period": "يوم كامل",
                "time_range": full_day,
                "subject": "حصص اليوم كاملة",
                "teacher": ""
            })

            class_sessions_map[c_name] = blocks
            # Also alias TCSF-1 and TCSEF-1
            if c_name == "TCSEF-1":
                class_sessions_map["TCSF-1"] = blocks
            elif c_name == "TCSF-1":
                class_sessions_map["TCSEF-1"] = blocks

        return {
            "day_base": day_base,
            "morning_day_key": morning_day,
            "afternoon_day_key": afternoon_day,
            "morning_sessions_count": len(morning_sessions),
            "afternoon_sessions_count": len(afternoon_sessions),
            "total_sessions_scheduled": len(morning_sessions) + len(afternoon_sessions),
            "active_classes_count": len(all_classes_today),
            "active_teachers_count": len(all_teachers_today),
            "all_teachers_today": all_teachers_today,
            "all_classes_today": all_classes_today,
            "morning_sessions": morning_sessions,
            "afternoon_sessions": afternoon_sessions,
            "class_sessions_map": class_sessions_map
        }

    def generate_full_report(
        self,
        day_base: str,
        date_str: str,
        absent_teachers: List[Dict[str, Any]] = None,
        student_stats: Dict[str, Any] = None,
        incidents: str = "",
        supervisor_name: str = "",
        notes: str = "",
        students_attendance: List[Dict[str, Any]] = None,
        week_number: str = "08",
        inspections: List[Dict[str, Any]] = None,
        guidelines: Dict[str, Any] = None,
        extra_compensatory_hours: List[Dict[str, Any]] = None,
        template_type: str = "detailed"
    ) -> Dict[str, Any]:
        """
        توليد التقرير اليومي الكامل مع المؤشرات الرياضية والإدارية وسجل غيابات وتأخرات التلاميذ
        """
        if student_stats is None:
            student_stats = {}
        if not student_stats.get("entry_tickets_count"):
            try:
                from .desktop_server import load_attendance_mobile_db
                mdb = load_attendance_mobile_db()
                passes = mdb.get("entryPasses", {})
                d_target = date_str or datetime.now().strftime("%Y-%m-%d")
                valid_passes = [
                    p for p in passes.values()
                    if p and p.get("status") != "REVOKED" and (
                        p.get("validForDate") == d_target or
                        p.get("issuedDate") == d_target or
                        p.get("absentDate") == d_target
                    )
                ]
                if valid_passes:
                    student_stats["entry_tickets_count"] = len(valid_passes)
            except Exception:
                pass
        if absent_teachers is None:
            absent_teachers = []
        sched = self.get_scheduled_day_summary(day_base)
        total_scheduled = sched["total_sessions_scheduled"]

        # حساب الساعات الضائعة بسبب غياب الأساتذة
        lost_sessions_count = 0
        affected_classes = set()

        cleaned_absences = []
        for ab in absent_teachers:
            entry_type = ab.get("entry_type", "teacher")
            class_name = ab.get("class_name", "")
            inferred_teacher = ab.get("inferred_teacher", "").strip()
            subject = ab.get("subject", "").strip()
            if entry_type == "class":
                t_name = f"قسم {class_name}" if class_name else "عدم استفادة قسم"
                inferred_teacher = ""
            else:
                t_name = ab.get("teacher_name", "").strip() or inferred_teacher
            if not t_name and class_name:
                t_name = f"أستاذ(ة) قسم {class_name}"
            session_hour = ab.get("session_hour", "")
            hours_count = int(ab.get("hours_count", 0))
            reason = ab.get("reason", "غير مبرر")
            classes_affected = list(ab.get("classes", []))
            if class_name and class_name not in classes_affected:
                classes_affected.append(class_name)

            lost_sessions_count += hours_count
            for c in classes_affected:
                affected_classes.add(c)

            cleaned_absences.append({
                "entry_type": entry_type,
                "teacher_name": t_name,
                "inferred_teacher": inferred_teacher,
                "class_name": class_name,
                "session_hour": session_hour,
                "subject": subject,
                "period": ab.get("period", session_hour or "كامل اليوم"),
                "hours_count": hours_count,
                "reason": reason,
                "action_taken": ab.get("action_taken", "توجيه التلاميذ لقاعة المداومة / إشعار الإدارة"),
                "classes": classes_affected
            })

        completed_sessions = max(0, total_scheduled - lost_sessions_count)
        coverage_rate = round((completed_sessions / total_scheduled) * 100, 1) if total_scheduled > 0 else 100.0

        if student_stats is None:
            student_stats = {
                "absent_students_count": 0,
                "entry_tickets_count": 0,
                "late_students_count": 0
            }

        students_att_list = students_attendance or []
        if students_att_list:
            calc_abs = sum(1 for s in students_att_list if s.get("absent_sessions_count", 0) > 0)
            calc_late = sum(1 for s in students_att_list if s.get("late_sessions_count", 0) > 0)
            if not student_stats.get("absent_students_count"):
                student_stats["absent_students_count"] = calc_abs
            if not student_stats.get("late_students_count"):
                student_stats["late_students_count"] = calc_late

        inst_name = getattr(self.institution, "institution_name", "") if self.institution else ""
        principal = getattr(self.institution, "principal_name", "") if self.institution else ""
        year = getattr(self.institution, "academic_year", "") if self.institution else ""
        academy = getattr(self.institution, "academy", "") if self.institution else ""
        province = getattr(self.institution, "province", "") if self.institution else ""

        try:
            from .desktop_server import load_attendance_mobile_db
            mdb = load_attendance_mobile_db()
            m_set = mdb.get("settings", {})
            if not inst_name or inst_name == "المؤسسة التعليمية":
                inst_name = m_set.get("schoolName", "") or "الثانوية التأهيلية أنفك"
            if not principal or principal == "رئيس المؤسسة":
                principal = m_set.get("principalName", "") or "رئيس المؤسسة"
        except Exception:
            pass

        if not inst_name or inst_name == "المؤسسة التعليمية":
            inst_name = "الثانوية التأهيلية أنفك"
        if not year:
            year = "2026/2027"
        if not principal:
            principal = "رئيس المؤسسة"

        # Build dynamic classes matrix for the horizontal matrix table (Word Template 2)
        classes_matrix = []
        try:
            from .student_attendance_engine import attendance_engine
            classes_data = attendance_engine.students_by_class
        except Exception:
            classes_data = {}

        def _get_short_name(cname):
            u = cname.upper().replace(' ', '').replace('-', '').replace('_', '')
            if 'TCSF' in u or 'TCSC' in u or 'TCS' in u or 'جذععلم' in u: return 'TCSF-1'
            if 'TCLSHF1' in u or 'TCLSH1' in u or (('TCLSH' in u or 'جذعآداب' in u) and '2' not in u): return 'TCLSHF-1'
            if 'TCLSHF2' in u or 'TCLSH2' in u or 'جذعآداب2' in u: return 'TCLSHF-2'
            if '1BACSEF1' in u or '1BACEXP1' in u or '1BACEXPF1' in u or '1BACSE1' in u or 'أولىعلوَمتجريبية1' in u: return '1BACSEF-1'
            if '1BACSEF2' in u or '1BACEXP2' in u or '1BACEXPF2' in u or '1BACSE2' in u or 'أولىعلوَمتجريبية2' in u: return '1BACSEF-2'
            if '1BACSHF1' in u or '1BACLSH1' in u or '1BACSH1' in u or 'أولىآداب1' in u: return '1BACSHF-1'
            if '1BACSHF2' in u or '1BACLSH2' in u or '1BACSH2' in u or 'أولىآداب2' in u: return '1BACSHF-2'
            if '2BACLF' in u or '2BACL' in u or 'ثانيةآداب' in u: return '2BACLF-1'
            if '2BACSH' in u or 'ثانيةعلومإنسانية' in u: return '2BACSHF-1'
            if '2BACSPF' in u or '2BACPC' in u or 'ثانيةفيزياء' in u: return '2BACSPF-1'
            if '2BACSVT' in u or 'ثانيةعلومالحياة' in u: return '2BACSVTF-1'
            if '1AC' in u or '1APIC' in u: return cname.replace('1AC', '1/').replace('1APIC', '1/')
            if '2AC' in u or '2APIC' in u: return cname.replace('2AC', '2/').replace('2APIC', '2/')
            if '3AC' in u or '3APIC' in u: return cname.replace('3AC', '3/').replace('3APIC', '3/')
            return cname

        def _get_level_key(cname):
            u = cname.upper()
            if 'TC' in u or 'جذع' in u: return 'TC'
            if '1BAC' in u or 'أولى' in u: return '1BAC'
            if '2BAC' in u or 'ثانية' in u: return '2BAC'
            if '1AC' in u or '1APIC' in u: return '1AC'
            if '2AC' in u or '2APIC' in u: return '2AC'
            if '3AC' in u or '3APIC' in u: return '3AC'
            return 'OTHER'

        # Map absent students by class for today
        abs_counts_by_class = {}
        for st in (students_att_list or []):
            if st.get("absent_sessions_count", 0) > 0:
                c = str(st.get("class_name", "")).strip()
                abs_counts_by_class[c] = abs_counts_by_class.get(c, 0) + 1

        for cname, slist in classes_data.items():
            lvl = _get_level_key(cname)
            s_name = _get_short_name(cname)
            cnt = len(slist)
            abs_cnt = abs_counts_by_class.get(cname, 0)
            classes_matrix.append({
                "class_code": cname,
                "short_name": s_name,
                "level": lvl,
                "total_students": cnt,
                "absent_count": abs_cnt
            })

        order_weights = {'TC': 1, '1BAC': 2, '2BAC': 3, '1AC': 4, '2AC': 5, '3AC': 6, 'OTHER': 7}
        short_name_weights = {
            'TCSF-1': 1, 'TCLSHF-1': 2, 'TCLSHF-2': 3,
            '1BACSEF-1': 4, '1BACSEF-2': 5, '1BACSHF-1': 6, '1BACSHF-2': 7,
            '2BACLF-1': 8, '2BACSHF-1': 9, '2BACSPF-1': 10, '2BACSVTF-1': 11
        }
        classes_matrix.sort(key=lambda x: (
            order_weights.get(x["level"], 99),
            short_name_weights.get(x["short_name"], 99),
            x["class_code"]
        ))

        # Official Ministry banner in base64
        banner_b64 = ""
        banner_candidates = [
            os.path.join(os.path.dirname(__file__), "..", "assets", "surv_word_image2.png"),
            os.path.join(os.getcwd(), "assets", "surv_word_image2.png"),
        ]
        if hasattr(sys, "_MEIPASS"):
            banner_candidates.append(os.path.join(sys._MEIPASS, "assets", "surv_word_image2.png"))
        for bp in banner_candidates:
            if os.path.exists(bp):
                try:
                    with open(bp, "rb") as bf:
                        banner_b64 = "data:image/png;base64," + base64.b64encode(bf.read()).decode("ascii")
                        break
                except Exception:
                    pass

        return {
            "success": True,
            "report_id": f"REP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "header": {
                "institution_name": inst_name,
                "academy": academy,
                "province": province,
                "academic_year": year,
                "principal_name": principal,
                "supervisor_name": supervisor_name or "الحارس العام للخارجية",
                "day_name": day_base,
                "report_date": date_str or datetime.now().strftime("%Y-%m-%d"),
                "week_number": week_number or "08"
            },
            "metrics": {
                "total_scheduled_sessions": total_scheduled,
                "completed_sessions": completed_sessions,
                "lost_sessions": lost_sessions_count,
                "coverage_rate": coverage_rate,
                "scheduled_classes_count": sched["active_classes_count"],
                "affected_classes_count": len(affected_classes),
                "scheduled_teachers_count": sched["active_teachers_count"],
                "absent_teachers_count": len(cleaned_absences)
            },
            "absent_teachers": cleaned_absences,
            "student_stats": student_stats,
            "students_attendance": students_att_list,
            "classes_matrix": classes_matrix,
            "incidents": incidents or "سير عادي ومستقر للدراسة بالمؤسسة ولم تسجل أي حوادث تذكر.",
            "notes": notes,
            "week_number": week_number or "08",
            "inspections": inspections or [],
            "guidelines": guidelines or {},
            "extra_compensatory_hours": extra_compensatory_hours or [],
            "template_type": template_type or "detailed",
            "banner_base64": banner_b64,
            "institution_logo_base64": getattr(self.institution, "logo_base64", "") if self.institution else "",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
