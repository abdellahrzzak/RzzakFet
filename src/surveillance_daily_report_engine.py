# -*- coding: utf-8 -*-
"""
محرك تقرير الحراسة العامة اليومي — General Supervisor Daily Operational Report
وثيقة إدارية رسمية معتمدة بالمؤسسات التعليمية المغربية لرصد سير الدراسة اليومي،
مواظبة الأطر التربوية، حالة الأقسام، وتوثيق الحوادث وتأشيرة الإدارة.
"""

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
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        توليد التقرير اليومي الكامل مع المؤشرات الرياضية والإدارية
        """
        sched = self.get_scheduled_day_summary(day_base)
        total_scheduled = sched["total_sessions_scheduled"]

        # حساب الساعات الضائعة بسبب غياب الأساتذة
        lost_sessions_count = 0
        affected_classes = set()

        cleaned_absences = []
        for ab in absent_teachers:
            t_name = ab.get("teacher_name", "").strip()
            hours_count = int(ab.get("hours_count", 0))
            reason = ab.get("reason", "غير مبرر")
            classes_affected = ab.get("classes", [])

            lost_sessions_count += hours_count
            for c in classes_affected:
                affected_classes.add(c)

            cleaned_absences.append({
                "teacher_name": t_name,
                "subject": ab.get("subject", ""),
                "period": ab.get("period", "كامل اليوم"),
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

        inst_name = getattr(self.institution, "institution_name", "المؤسسة التعليمية") if self.institution else "المؤسسة التعليمية"
        academy = getattr(self.institution, "academy", "الأكاديمية الجهوية للتربية والتكوين") if self.institution else ""
        province = getattr(self.institution, "province", "المديرية الإقليمية") if self.institution else ""
        year = getattr(self.institution, "academic_year", "2026-2027") if self.institution else "2026-2027"
        principal = getattr(self.institution, "principal_name", "رئيس المؤسسة") if self.institution else "رئيس المؤسسة"

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
                "report_date": date_str or datetime.now().strftime("%Y-%m-%d")
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
            "incidents": incidents or "سير عادي للدراسة بالمؤسسة ولم تسجل أي حوادث تذكر.",
            "notes": notes,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
