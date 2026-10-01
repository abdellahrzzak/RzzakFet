# -*- coding: utf-8 -*-
"""
محرك النافذة الذهبية للمجالس التعليمية — The Golden Window Engine
يحلل جدول الحصص النهائي بذكاء لتحديد الأوقات المشتركة لأساتذة المادة الواحدة
دون فرض قيود مسبقة في FET قد تشوه جودة جدول التلاميذ أو تعقد حله.
"""

from typing import Dict, List, Any, Optional

DAYS_12_ORDER = [
    "الاثنين ص", "الاثنين م",
    "الثلاثاء ص", "الثلاثاء م",
    "الاربعاء ص", "الاربعاء م",
    "الخميس ص", "الخميس م",
    "الجمعة ص", "الجمعة م",
    "السبت ص", "السبت م"
]

HOURS_4_ORDER = ["ح 1", "ح 2", "ح 3", "ح 4"]


class GoldenWindowEngine:
    def __init__(self, timetable_result: Dict[str, Any] = None):
        self.timetable = timetable_result or {}

    def set_timetable(self, timetable_result: Dict[str, Any]):
        self.timetable = timetable_result or {}

    def analyze_all_subjects(self, fallback_assignments: List[Any] = None) -> Dict[str, Any]:
        """
        تحليل شامل لجميع المواد لإيجاد النوافذ الذهبية للمجالس التعليمية.
        """
        teacher_timetables = self.timetable.get("teacher_timetables", {})
        master_teachers_data = self.timetable.get("master_teachers_data", [])
        
        # 1. تحديد أساتذة كل مادة
        subject_to_teachers: Dict[str, List[str]] = {}

        if isinstance(master_teachers_data, list):
            for item in master_teachers_data:
                t_name = item.get("teacher", "").strip()
                subj = item.get("subject", "").strip()
                if t_name and subj and subj not in ["-", "شاغر"]:
                    if t_name not in subject_to_teachers.setdefault(subj, []):
                        subject_to_teachers[subj].append(t_name)
        elif isinstance(master_teachers_data, dict):
            for t_name, t_info in master_teachers_data.items():
                subj = t_info.get("subject", "").strip()
                if subj and subj not in ["-", "شاغر"]:
                    if t_name not in subject_to_teachers.setdefault(subj, []):
                        subject_to_teachers[subj].append(t_name)

        # استكمال من fallback_assignments إذا تم تمريرها
        if fallback_assignments:
            for a in fallback_assignments:
                t_name = getattr(a, "teacher_name", "")
                subj = getattr(a, "subject", "")
                if t_name and subj:
                    if t_name not in subject_to_teachers.setdefault(subj, []):
                        subject_to_teachers[subj].append(t_name)

        # استكمال من teacher_timetables إن وجد تفاوت
        if not subject_to_teachers:
            for t_name, days_data in teacher_timetables.items():
                found_subj = ""
                for day, hours in days_data.items():
                    for h, cell in hours.items():
                        if cell and cell.get("subject"):
                            found_subj = cell["subject"]
                            break
                    if found_subj:
                        break
                if found_subj:
                    if t_name not in subject_to_teachers.setdefault(found_subj, []):
                        subject_to_teachers[found_subj].append(t_name)

        subjects_analysis = {}
        calendar_recommendations = []

        # 2. تحليل كل مادة على حدة
        for subject, teachers in sorted(subject_to_teachers.items()):
            if not teachers:
                continue

            total_t = len(teachers)
            slots_scores = []

            for day in DAYS_12_ORDER:
                for hour in HOURS_4_ORDER:
                    free_teachers = []
                    busy_teachers = []

                    for t_name in teachers:
                        t_sched = teacher_timetables.get(t_name, {})
                        day_sched = t_sched.get(day, {})
                        cell = day_sched.get(hour)

                        if cell is None:
                            free_teachers.append(t_name)
                        else:
                            busy_teachers.append({
                                "teacher": t_name,
                                "class": cell.get("students", ""),
                                "subject": cell.get("subject", ""),
                                "room": cell.get("room", "")
                            })

                    free_count = len(free_teachers)
                    free_percent = round((free_count / total_t) * 100, 1)

                    is_perfect = (free_count == total_t)
                    is_near_golden = (free_count == total_t - 1 and total_t >= 2)

                    swap_suggestions = []
                    if is_near_golden and busy_teachers:
                        # الأستاذ الوحيد المنشغل: نبحث له عن فترة بديلة يكون هو وقسمه فارغين فيها
                        b_teacher = busy_teachers[0]["teacher"]
                        b_class = busy_teachers[0]["class"]
                        alt_slots = self._find_alternate_slots(b_teacher, b_class, day, hour)
                        if alt_slots:
                            swap_suggestions = alt_slots[:2]

                    slots_scores.append({
                        "day": day,
                        "hour": hour,
                        "time_slot": f"{day} - {hour}",
                        "free_count": free_count,
                        "total_teachers": total_t,
                        "free_percent": free_percent,
                        "is_perfect": is_perfect,
                        "is_near_golden": is_near_golden,
                        "free_teachers": free_teachers,
                        "busy_teachers": busy_teachers,
                        "swap_suggestions": swap_suggestions
                    })

            # فرز الفترات: المثالية أولاً ثم الأعلى نسبة فراغ
            slots_scores.sort(key=lambda s: (-s["free_percent"], s["day"], s["hour"]))

            perfect_slots = [s for s in slots_scores if s["is_perfect"]]
            near_golden_slots = [s for s in slots_scores if s["is_near_golden"]]
            best_slot = slots_scores[0] if slots_scores else None

            subjects_analysis[subject] = {
                "subject": subject,
                "total_teachers": total_t,
                "teachers": teachers,
                "perfect_slots_count": len(perfect_slots),
                "perfect_slots": perfect_slots,
                "near_golden_slots": near_golden_slots[:4],
                "top_recommendations": slots_scores[:6],
                "status": "مثالية 100%" if perfect_slots else ("شبه ذهبية (تحتاج تبادل أستاذ 1)" if near_golden_slots else "تتطلب تنسيقاً خاصاً")
            }

            if best_slot:
                calendar_recommendations.append({
                    "subject": subject,
                    "recommended_slot": best_slot["time_slot"],
                    "day": best_slot["day"],
                    "hour": best_slot["hour"],
                    "free_percent": best_slot["free_percent"],
                    "is_perfect": best_slot["is_perfect"],
                    "total_teachers": total_t,
                    "busy_note": f"مشغول {len(best_slot['busy_teachers'])} أستاذ" if best_slot['busy_teachers'] else "تفرغ تام 100%"
                })

        return {
            "success": True,
            "subjects_count": len(subjects_analysis),
            "subjects_analysis": subjects_analysis,
            "calendar_recommendations": calendar_recommendations
        }

    def _find_alternate_slots(self, teacher_name: str, class_name: str, exclude_day: str, exclude_hour: str) -> List[str]:
        """البحث عن فترات بديلة مشتركة بين أستاذ وقسم لنقل حصة"""
        t_sched = self.timetable.get("teacher_timetables", {}).get(teacher_name, {})
        c_sched = self.timetable.get("student_timetables", {}).get(class_name, {})

        candidates = []
        for day in DAYS_12_ORDER:
            for hour in HOURS_4_ORDER:
                if day == exclude_day and hour == exclude_hour:
                    continue
                # الأستاذ فارغ؟
                t_free = (t_sched.get(day, {}).get(hour) is None)
                # القسم فارغ؟
                c_free = (c_sched.get(day, {}).get(hour) is None)
                if t_free and c_free:
                    candidates.append(f"{day} - {hour}")
        return candidates
