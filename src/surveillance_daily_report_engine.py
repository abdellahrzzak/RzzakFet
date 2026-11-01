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
    "الثلاثاء": ["الثلاثاء ص", "الثلاثاء م"],
    "الاربعاء": ["الاربعاء ص", "الاربعاء م"],
    "الخميس": ["الخميس ص", "الخميس م"],
    "الجمعة": ["الجمعة ص", "الجمعة م"],
    "السبت": ["السبت ص", "السبت م"]
}


class SurveillanceDailyReportEngine:
    def __init__(self, timetable_result: Dict[str, Any] = None, institution_data: Any = None):
        self.timetable = timetable_result or {}
        self.institution = institution_data

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
            "afternoon_sessions": afternoon_sessions
        }

    def generate_full_report(
        self,
        day_base: str,
        date_str: str,
        absent_teachers: List[Dict[str, Any]],
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

        inst_name = getattr(self.institution, "institution_name", "المؤسسة التعليمية") if self.institution else "المؤسسة التعليمية"
        academy = getattr(self.institution, "academy", "الأكاديمية الجهوية للتربية والتكوين") if self.institution else ""
        province = getattr(self.institution, "province", "المديرية الإقليمية") if self.institution else ""
        year = getattr(self.institution, "academic_year", "2026-2027") if self.institution else "2026-2027"
        principal = getattr(self.institution, "principal_name", "رئيس المؤسسة") if self.institution else "رئيس المؤسسة"

        # Build dynamic classes matrix for the horizontal matrix table (Word Template 2)
        classes_matrix = []
        try:
            from .student_attendance_engine import attendance_engine
            classes_data = attendance_engine.students_by_class
        except Exception:
            classes_data = {}

        def _get_short_name(cname):
            u = cname.upper().replace(' ', '').replace('-', '').replace('_', '')
            if 'TCSF' in u or 'TCSC' in u: return 'علمي'
            if 'TCLSHF1' in u or 'TCLSH1' in u: return 'أدبي 1'
            if 'TCLSHF2' in u or 'TCLSH2' in u: return 'أدبي 2'
            if 'TCLSH' in u: return 'أدبي'
            if '1BACSEF1' in u or '1BACEXP1' in u: return 'ع تج 1'
            if '1BACSEF2' in u or '1BACEXP2' in u: return 'ع تج 2'
            if '1BACSHF1' in u or '1BACLSH1' in u: return 'آ ع إ 1'
            if '1BACSHF2' in u or '1BACLSH2' in u: return 'آ ع إ 2'
            if '2BACSPF' in u or '2BACPC' in u: return 'ع فزيائية'
            if '2BACSVT' in u: return 'ع ح أ'
            if '2BACSH' in u: return 'ع إنسانية'
            if '2BACLF' in u or '2BACL' in u: return 'آداب'
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
            'علمي': 1, 'أدبي 1': 2, 'أدبي 2': 3, 'أدبي': 3,
            'ع تج 1': 4, 'ع تج 2': 5, 'ع تجريبية': 5,
            'آ ع إ 1': 6, 'آ ع إ 2': 7, 'آداب و ع إ': 7,
            'ع فزيائية': 8, 'ع ح أ': 9, 'ع إنسانية': 10, 'آداب': 11
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
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
