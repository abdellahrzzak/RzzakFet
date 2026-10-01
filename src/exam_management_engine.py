# -*- coding: utf-8 -*-
"""
محرك تنظيم الامتحانات الإشهادية والمراقبة الموحدة — Exam & Invigilation Engine
مطور خصيصاً للإدارة التربوية المغربية (الناظر / المدير / الحراسة العامة)
وفق مقتضيات المذكرات الوزارية لتنظيم الامتحانات والمراقبة المستمرة.
يعتمد حصرياً على الأساتذة المتوفرين حقيقياً بالمؤسسة والقاعات المتاحة فعلياً.
"""

import math
import random
import re
from typing import List, Dict, Any, Optional

def clean_teacher_name(name: str) -> str:
    """
    تنقية اسم الأستاذ وإزالة أي زوائد مثل:
    (أستاذ منتدب)، (أستاذة منتدبة)، (ملحق تربوي)، (ملحقة تربوية)
    لضمان مظهر رسمي ومهني في جداول الحراسة ولوائح التكليفات.
    """
    if not name:
        return ""
    cleaned = re.sub(r'\s*\((?:أستاذ|أستاذة)\s+منتدب[ة]?\)', '', str(name))
    cleaned = re.sub(r'\s*\((?:ملحق|ملحقة)\s+تربوي[ة]?\)', '', cleaned)
    cleaned = re.sub(r'\s*أستاذ(?:ة)?\s+منتدب(?:ة)?', '', cleaned)
    cleaned = re.sub(r'\s*ملحق(?:ة)?\s+تربوي(?:ة)?', '', cleaned)
    cleaned = re.sub(r'\s*\(منتدب[ة]?\)', '', cleaned)
    return cleaned.strip()

DEFAULT_EXAM_PRESETS = {
    "local_3apic": {
        "id": "local_3apic",
        "name": "الامتحان الموحد المحلي لنيل شهادة السلك الإعدادي",
        "session": "دورة يناير",
        "exam_dates": "15 و 16 يناير 2027",
        "day1_date": "15 يناير 2027",
        "day2_date": "16 يناير 2027",
        "target_level": "الثالثة إعدادي (3APIC)",
        "available_rooms_count": 11,
        "capacity_per_room": 20,
        "invigilators_per_room": 2,
        "reserve_count": 2,
        "slots": [
            {"id": "slot_1", "day": "اليوم الأول (صباحاً)", "date": "15 يناير 2027", "start_time": "08:30", "end_time": "10:30", "time": "08:30 - 10:30", "subject": "اللغة العربية", "duration": 2.0},
            {"id": "slot_2", "day": "اليوم الأول (صباحاً)", "date": "15 يناير 2027", "start_time": "10:45", "end_time": "11:45", "time": "10:45 - 11:45", "subject": "التربية الإسلامية", "duration": 1.0},
            {"id": "slot_3", "day": "اليوم الأول (مساءً)", "date": "15 يناير 2027", "start_time": "15:00", "end_time": "17:00", "time": "15:00 - 17:00", "subject": "الرياضيات", "duration": 2.0},
            {"id": "slot_4", "day": "اليوم الثاني (صباحاً)", "date": "16 يناير 2027", "start_time": "08:30", "end_time": "10:30", "time": "08:30 - 10:30", "subject": "اللغة الفرنسية", "duration": 2.0},
            {"id": "slot_5", "day": "اليوم الثاني (صباحاً)", "date": "16 يناير 2027", "start_time": "10:45", "end_time": "11:45", "time": "10:45 - 11:45", "subject": "علوم الحياة و الأرض", "duration": 1.0},
            {"id": "slot_6", "day": "اليوم الثاني (مساءً)", "date": "16 يناير 2027", "start_time": "15:00", "end_time": "16:00", "time": "15:00 - 16:00", "subject": "الكيمياء و الفيزياء", "duration": 1.0},
            {"id": "slot_7", "day": "اليوم الثاني (مساءً)", "date": "16 يناير 2027", "start_time": "16:15", "end_time": "17:15", "time": "16:15 - 17:15", "subject": "الاجتماعيات", "duration": 1.0}
        ]
    },
    "regional_3apic": {
        "id": "regional_3apic",
        "name": "الامتحان الجهوي الموحد لنيل شهادة السلك الإعدادي",
        "session": "دورة يونيو",
        "exam_dates": "18 و 19 يونيو 2027",
        "day1_date": "18 يونيو 2027",
        "day2_date": "19 يونيو 2027",
        "target_level": "الثالثة إعدادي (3APIC)",
        "available_rooms_count": 11,
        "capacity_per_room": 20,
        "invigilators_per_room": 2,
        "reserve_count": 2,
        "slots": [
            {"id": "slot_1", "day": "اليوم الأول (صباحاً)", "date": "18 يونيو 2027", "start_time": "08:30", "end_time": "10:30", "time": "08:30 - 10:30", "subject": "اللغة العربية", "duration": 2.0},
            {"id": "slot_2", "day": "اليوم الأول (صباحاً)", "date": "18 يونيو 2027", "start_time": "10:45", "end_time": "11:45", "time": "10:45 - 11:45", "subject": "التربية الإسلامية", "duration": 1.0},
            {"id": "slot_3", "day": "اليوم الأول (مساءً)", "date": "18 يونيو 2027", "start_time": "15:00", "end_time": "17:00", "time": "15:00 - 17:00", "subject": "الرياضيات", "duration": 2.0},
            {"id": "slot_4", "day": "اليوم الثاني (صباحاً)", "date": "19 يونيو 2027", "start_time": "08:30", "end_time": "10:30", "time": "08:30 - 10:30", "subject": "اللغة الفرنسية", "duration": 2.0},
            {"id": "slot_5", "day": "اليوم الثاني (صباحاً)", "date": "19 يونيو 2027", "start_time": "10:45", "end_time": "11:45", "time": "10:45 - 11:45", "subject": "علوم الحياة و الأرض", "duration": 1.0},
            {"id": "slot_6", "day": "اليوم الثاني (مساءً)", "date": "19 يونيو 2027", "start_time": "15:00", "end_time": "16:15", "time": "15:00 - 16:15", "subject": "الاجتماعيات", "duration": 1.25},
            {"id": "slot_7", "day": "اليوم الثاني (مساءً)", "date": "19 يونيو 2027", "start_time": "16:30", "end_time": "17:30", "time": "16:30 - 17:30", "subject": "الكيمياء و الفيزياء", "duration": 1.0}
        ]
    },
    "continuous_unified": {
        "id": "continuous_unified",
        "name": "المراقبة المستمرة الموحدة على صعيد المؤسسة",
        "session": "الأسدس الأول / الثاني",
        "exam_dates": "10 و 11 يناير 2027",
        "day1_date": "10 يناير 2027",
        "day2_date": "11 يناير 2027",
        "target_level": "جميع المستويات",
        "available_rooms_count": 11,
        "capacity_per_room": 20,
        "invigilators_per_room": 2,
        "reserve_count": 2,
        "slots": [
            {"id": "slot_1", "day": "الفترة 1", "date": "10 يناير 2027", "start_time": "08:30", "end_time": "10:30", "time": "08:30 - 10:30", "subject": "الرياضيات", "duration": 2.0},
            {"id": "slot_2", "day": "الفترة 2", "date": "10 يناير 2027", "start_time": "10:45", "end_time": "12:45", "time": "10:45 - 12:45", "subject": "اللغة الفرنسية", "duration": 2.0},
            {"id": "slot_3", "day": "الفترة 3", "date": "11 يناير 2027", "start_time": "14:30", "end_time": "16:30", "time": "14:30 - 16:30", "subject": "اللغة العربية", "duration": 2.0}
        ]
    }
}


class ExamManagementEngine:
    def __init__(self, institution_data: Any = None, structure_data: Any = None):
        self.institution = institution_data
        self.structure = structure_data

    def estimate_candidates_count(self) -> int:
        """تقدير عدد المترشحين بناءً على بنية المؤسسة المعتمدة"""
        if self.structure:
            s3 = getattr(self.structure, "students_3_apic", 0)
            if s3 > 0:
                return s3
            c3 = getattr(self.structure, "classes_3_apic", 4)
            return c3 * 38
        return 380

    def get_default_available_rooms_count(self) -> int:
        """تحديد عدد القاعات المتاحة فعلياً بالمؤسسة"""
        if self.structure:
            tot_c = getattr(self.structure, "total_classes", 0)
            if tot_c > 0:
                return tot_c
            c1 = getattr(self.structure, "classes_1_apic", 4)
            c2 = getattr(self.structure, "classes_2_apic", 3)
            c3 = getattr(self.structure, "classes_3_apic", 4)
            if (c1 + c2 + c3) > 0:
                return c1 + c2 + c3
        if self.institution:
            gen_rooms = getattr(self.institution, "general_rooms_count", 11)
            if gen_rooms > 0:
                return gen_rooms
        return 11

    def generate_rooms_setup(
        self,
        total_candidates: int,
        capacity_per_room: int = 20,
        forced_rooms_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        حساب وتوزيع القاعات المتاحة فعلياً وأرقام المقاعد تسلسلياً.
        احترام سعة القاعة المحددة (مثلاً 20 تلميذاً في القاعة) بدقة كاملة وتوزيع المترشحين.
        """
        capacity = max(1, int(capacity_per_room)) if capacity_per_room else 20
        needed_rooms = math.ceil(total_candidates / max(1, capacity))
        
        # إذا تم تمرير عدد قاعات مخصص:
        # إذا كان عدد القاعات المتاح أقل من الحاجة، نرفع السعة لتستوعب الجميع في تلك القاعات
        # إذا كان عدد القاعات المتوفر أكبر من المطلوب (مثلاً 11 قاعة متوفرة بينما 143 مترشحاً يحتاجون 8 قاعات فقط بسعة 20)
        # نلتزم فقط بعدد القاعات المطلوب (8 قاعات) لضمان 20 تلميذاً بكل قاعة وعدم تخفيف السعة إلى 13 تلميذاً
        if forced_rooms_count and forced_rooms_count > 0:
            if forced_rooms_count < needed_rooms:
                total_rooms = forced_rooms_count
                capacity = math.ceil(total_candidates / total_rooms)
            else:
                total_rooms = needed_rooms
        else:
            total_rooms = max(1, needed_rooms)
        
        rooms = []
        current_candidate_start = 1
        for i in range(1, total_rooms + 1):
            c_count = min(capacity, total_candidates - current_candidate_start + 1)
            c_count = max(0, c_count)
            c_end = current_candidate_start + c_count - 1 if c_count > 0 else current_candidate_start
            seats_str = f"من {current_candidate_start} إلى {c_end}" if c_count > 0 else "-"
            rooms.append({
                "room_index": i,
                "room_name": f"القاعة {i}",
                "capacity": capacity,
                "assigned_candidates_count": c_count,
                "candidate_start": current_candidate_start,
                "candidate_end": c_end,
                "seats_range": seats_str
            })
            current_candidate_start = c_end + 1
        return rooms

    def build_invigilation_matrix(
        self,
        exam_config: Dict[str, Any],
        teachers_list: List[Dict[str, str]],
        total_candidates: int = None
    ) -> Dict[str, Any]:
        """
        خوارزمية الإسناد الذكي والعادل للحراسة:
        1. استغلال حصري للأساتذة المتوفرين حقيقياً بالمؤسسة (بدون أي أساتذة افتراضيين أو منتدبين).
        2. استغلال فقط القاعات المتاحة فعلياً بالمؤسسة وتوزيع المترشحين والأساتذة عليها.
        3. إعفاء أساتذة المادة المعنية بالامتحان وفق الضوابط، وتوزيع باقي الأساتذة بتكافؤ وإنصاف تام.
        4. تعيين أساتذة الاحتياط من الأساتذة المتوفرين بالمؤسسة.
        """
        if total_candidates is None:
            total_candidates = self.estimate_candidates_count()

        capacity_per_room = int(exam_config.get("capacity_per_room", 20))
        forced_rooms = exam_config.get("available_rooms_count") or exam_config.get("rooms_count")
        if forced_rooms is not None:
            try:
                forced_rooms = int(forced_rooms)
            except Exception:
                forced_rooms = None

        if not forced_rooms or forced_rooms <= 0:
            forced_rooms = math.ceil(total_candidates / max(1, capacity_per_room))

        invigilators_per_room = max(1, int(exam_config.get("invigilators_per_room", 2)))
        
        rooms = self.generate_rooms_setup(total_candidates, capacity_per_room, forced_rooms_count=forced_rooms)
        num_rooms = len(rooms)
        reserve_count = max(0, int(exam_config.get("reserve_count", 2)))
        raw_slots = exam_config.get("slots", [])

        # معالجة فترات الامتحان وتوقيت البداية والنهاية والمدة المحسوبة بدقة
        slots = []
        for s_idx, s in enumerate(raw_slots):
            slot_copy = dict(s)
            start_t = str(slot_copy.get("start_time", "")).strip()
            end_t = str(slot_copy.get("end_time", "")).strip()

            dur_calc = None
            if start_t and end_t and ":" in start_t and ":" in end_t:
                try:
                    s_h, s_m = map(int, start_t.split(":"))
                    e_h, e_m = map(int, end_t.split(":"))
                    mins = (e_h * 60 + e_m) - (s_h * 60 + s_m)
                    if mins > 0:
                        dur_calc = round(mins / 60.0, 2)
                except Exception:
                    pass

            duration = dur_calc if dur_calc is not None else float(slot_copy.get("duration", 2.0))
            slot_copy["duration"] = duration

            if start_t and end_t:
                slot_copy["time"] = f"{start_t} - {end_t}"
            elif not slot_copy.get("time"):
                slot_copy["time"] = "08:30 - 10:30"

            if not slot_copy.get("id"):
                slot_copy["id"] = f"slot_{s_idx + 1}"

            slots.append(slot_copy)

        # استغلال فقط الأساتذة المتوفرين حقيقياً بالمؤسسة بدون أي أساتذة خارجيين أو افتراضيين
        teachers = []
        seen_names = set()
        for t in teachers_list:
            raw_name = t.get("name", "").strip()
            c_name = clean_teacher_name(raw_name)
            if c_name and c_name not in seen_names:
                seen_names.add(c_name)
                teachers.append({
                    "name": c_name,
                    "subject": t.get("subject", "").strip(),
                    "assigned_count": 0,
                    "assigned_duration": 0.0,
                    "assignments": []
                })

        slots_result = []

        # حلقة على فترات الامتحان
        for slot in slots:
            slot_id = slot.get("id")
            subject_exam = slot.get("subject", "").strip()
            slot_duration = float(slot.get("duration", 2.0))

            # 1. تحديد الأساتذة المؤهلين (استبعاد أساتذة مادة الامتحان من الحراسة)
            eligible_teachers = [
                t for t in teachers
                if t["subject"].strip() != subject_exam
            ]
            # إذا كان عدد الأساتذة المؤهلين أقل من عدد القاعات المتاحة، يُسمح لباقي أساتذة المؤسسة بالمشاركة
            if len(eligible_teachers) < num_rooms and len(teachers) > len(eligible_teachers):
                subj_teachers = [t for t in teachers if t["subject"].strip() == subject_exam]
                eligible_teachers.extend(subj_teachers)

            # فرز المؤهلين حسب الأقل تكليفاً لضمان التكافؤ التام
            eligible_teachers.sort(key=lambda t: (t["assigned_count"], t["assigned_duration"], random.random()))

            # إسناد القاعات المتوفرة حصرياً بين الأساتذة الحقيقيين
            room_assignments = []
            assigned_idx = 0

            # الخطوة 1: إسناد الحارس الأول لكل قاعة
            for r_idx, r in enumerate(rooms):
                room_invigilators = []
                if assigned_idx < len(eligible_teachers):
                    t_obj = eligible_teachers[assigned_idx]
                    assigned_idx += 1
                    room_invigilators.append(t_obj["name"])
                    t_obj["assigned_count"] += 1
                    t_obj["assigned_duration"] += slot_duration
                    t_obj["assignments"].append({
                        "slot_id": slot_id,
                        "day": slot.get("day"),
                        "date": slot.get("date", ""),
                        "time": slot.get("time"),
                        "subject": subject_exam,
                        "room_name": r["room_name"],
                        "role": "حارس رئيسي"
                    })
                else:
                    room_invigilators.append("حراسة مشتركة")

                room_assignments.append({
                    "room_name": r["room_name"],
                    "seats_range": r["seats_range"],
                    "candidates_count": r["assigned_candidates_count"],
                    "invigilators": room_invigilators,
                    "invigilator": " / ".join(room_invigilators),
                    "invigilator_1": room_invigilators[0] if len(room_invigilators) > 0 else "-",
                    "invigilator_2": "-"
                })

            # الخطوة 2: إذا كان المطلوب أستاذين لكل قاعة وتبقى أساتذة متوفرون قبل رصيد الاحتياط
            avail_for_double = len(eligible_teachers) - assigned_idx - reserve_count
            if invigilators_per_room > 1 and avail_for_double > 0:
                for r_idx in range(min(num_rooms, avail_for_double)):
                    t_obj = eligible_teachers[assigned_idx]
                    assigned_idx += 1
                    room_assignments[r_idx]["invigilators"].append(t_obj["name"])
                    room_assignments[r_idx]["invigilator"] = " / ".join(room_assignments[r_idx]["invigilators"])
                    room_assignments[r_idx]["invigilator_2"] = t_obj["name"]
                    t_obj["assigned_count"] += 1
                    t_obj["assigned_duration"] += slot_duration
                    t_obj["assignments"].append({
                        "slot_id": slot_id,
                        "day": slot.get("day"),
                        "date": slot.get("date", ""),
                        "time": slot.get("time"),
                        "subject": subject_exam,
                        "room_name": rooms[r_idx]["room_name"],
                        "role": "حارس مساعد"
                    })

            # الخطوة 3: الأساتذة المتبقون يسندون لحراسة الاحتياط
            reserve_names = []
            while assigned_idx < len(eligible_teachers):
                r_teacher = eligible_teachers[assigned_idx]
                assigned_idx += 1
                reserve_names.append(r_teacher["name"])
                r_teacher["assigned_count"] += 1
                r_teacher["assigned_duration"] += slot_duration
                r_teacher["assignments"].append({
                    "slot_id": slot_id,
                    "day": slot.get("day"),
                    "date": slot.get("date", ""),
                    "time": slot.get("time"),
                    "subject": subject_exam,
                    "room_name": "قاعة الاحتياط / الإدارة",
                    "role": "احتياط"
                })

            # أساتذة المادة المعفون من الحراسة (مكلفون بالتصحيح / الإشراف البيداغوجي)
            subject_teachers_exempt = [
                clean_teacher_name(t["name"]) for t in teachers
                if t["subject"].strip() == subject_exam
            ]

            slots_result.append({
                "slot_info": slot,
                "room_assignments": room_assignments,
                "reserve_teachers": reserve_names,
                "exempt_subject_teachers": subject_teachers_exempt
            })

        # إحصائيات التكافؤ والعدالة
        counts = [t["assigned_count"] for t in teachers if t["name"]]
        min_c = min(counts) if counts else 0
        max_c = max(counts) if counts else 0
        avg_c = round(sum(counts) / len(counts), 1) if counts else 0

        # الاستدعاءات الفردية لكل أستاذ من الأساتذة الحقيقيين
        convocations = []
        for t in teachers:
            if not t["name"]:
                continue
            convocations.append({
                "teacher_name": clean_teacher_name(t["name"]),
                "subject": t["subject"],
                "total_sessions": t["assigned_count"],
                "total_hours": round(t["assigned_duration"], 1),
                "schedule": t["assignments"]
            })
        convocations.sort(key=lambda c: c["teacher_name"])

        # تحديد تواريخ الامتحان الرسمية المعتمدة
        day1_date = exam_config.get("day1_date", "").strip()
        day2_date = exam_config.get("day2_date", "").strip()
        exam_dates = exam_config.get("exam_dates", "").strip()
        if not exam_dates:
            if day1_date and day2_date:
                exam_dates = f"{day1_date} و {day2_date}"
            elif day1_date:
                exam_dates = day1_date
            elif day2_date:
                exam_dates = day2_date
            else:
                exam_dates = "15 و 16 يناير 2027"

        return {
            "success": True,
            "exam_name": exam_config.get("name", "الامتحان الموحد"),
            "session": exam_config.get("session", ""),
            "exam_dates": exam_dates,
            "day1_date": day1_date or "15 يناير 2027",
            "day2_date": day2_date or "16 يناير 2027",
            "total_candidates": total_candidates,
            "total_rooms": num_rooms,
            "capacity_per_room": capacity_per_room,
            "invigilators_per_room": invigilators_per_room,
            "rooms": rooms,
            "slots_result": slots_result,
            "convocations": convocations,
            "fairness_stats": {
                "min_sessions": min_c,
                "max_sessions": max_c,
                "avg_sessions": avg_c,
                "delta": max_c - min_c,
                "is_strictly_fair": (max_c - min_c) <= 1
            }
        }
