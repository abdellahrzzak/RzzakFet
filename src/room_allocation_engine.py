# -*- coding: utf-8 -*-
from typing import List, Dict
from .models import InstitutionData, CustomRoom, TeacherAssignment

class RoomAllocationEngine:
    def __init__(self, institution: InstitutionData = None):
        self.institution = institution or InstitutionData()
        self.manual_overrides: Dict[str, Dict[str, str]] = {}

    def get_room_display_name(self, default_name: str) -> str:
        return self.institution.room_custom_names.get(default_name, default_name)

    def clear_all_overrides(self):
        self.manual_overrides.clear()

    def set_teacher(self, room_key: str, session: str, teacher_name: str):
        if teacher_name and "شاغر" not in teacher_name and teacher_name != "-":
            for rk, sess_dict in self.manual_overrides.items():
                if rk != room_key:
                    if sess_dict.get("morning") == teacher_name:
                        sess_dict["morning"] = "شاغر (صباحي)"
                    if sess_dict.get("afternoon") == teacher_name:
                        sess_dict["afternoon"] = "شاغر (مسائي)"

        if room_key not in self.manual_overrides:
            self.manual_overrides[room_key] = {}
        self.manual_overrides[room_key][session] = teacher_name

    def allocate_rooms(self, assignments: List[TeacherAssignment]) -> List[CustomRoom]:
        n_gen = self.institution.general_rooms_count
        gen_subjects_allowed = ["اللغة العربية", "اللغة الفرنسية", "التربية الإسلامية", "الاجتماعيات", "الرياضيات", "اللغة الأجنبية الثانية (الإنجليزية)"]
        
        gen_teachers = [a for a in assignments if a.subject in gen_subjects_allowed and a.total_hours > 0]
        num_gen = len(gen_teachers)
        max_cap = self.institution.max_room_capacity_hours
        is_float_all = self.institution.float_all_general_teachers

        # Collect occupied teachers in overrides
        occupied_teachers = set()
        for rk, sess in self.manual_overrides.items():
            m_val = sess.get("morning")
            e_val = sess.get("afternoon")
            if m_val and "شاغر" not in m_val and m_val != "-":
                occupied_teachers.add(m_val)
            if e_val and "شاغر" not in e_val and e_val != "-":
                occupied_teachers.add(e_val)

        rooms: List[CustomRoom] = []
        curr_id = 1

        # 1. Base General Classrooms
        for i in range(1, n_gen + 1):
            def_name = f"القاعة العامة رقم {i}"
            r_name = self.get_room_display_name(def_name)
            m_idx = i - 1
            e_idx = (i - 1) + n_gen

            m_teach = gen_teachers[m_idx].teacher_name if m_idx < num_gen else "شاغر (صباحي)"
            e_teach = gen_teachers[e_idx].teacher_name if e_idx < num_gen else "شاغر (مسائي)"

            # Check manual overrides (search by r_name or def_name)
            override_key = r_name if r_name in self.manual_overrides else (def_name if def_name in self.manual_overrides else None)
            if override_key:
                m_teach = self.manual_overrides[override_key].get("morning", m_teach)
                e_teach = self.manual_overrides[override_key].get("afternoon", e_teach)
            else:
                if m_teach in occupied_teachers:
                    m_teach = "شاغر (صباحي)"
                if e_teach in occupied_teachers:
                    e_teach = "شاغر (مسائي)"

            m_h = next((a.total_hours for a in assignments if a.teacher_name == m_teach), 20) if "شاغر" not in m_teach and m_teach != "-" else 0
            e_h = next((a.total_hours for a in assignments if a.teacher_name == e_teach), 20) if "شاغر" not in e_teach and e_teach != "-" else 0
            
            tot_h = m_h + e_h
            util = round((tot_h / float(max_cap)) * 100, 1) if max_cap > 0 else 0
            
            if is_float_all:
                status = f"تعويم شامل ({tot_h}/{max_cap}س)"
            elif tot_h > max_cap and e_h > 0:
                status = f"تدريس مرن ({m_h}س مثبت + {e_h}س عائم / {max_cap}س)"
            elif util >= 90:
                status = f"استثمار تام ({tot_h}/{max_cap}س) ✓"
            else:
                status = f"استثمار ({tot_h}/{max_cap}س)"

            rooms.append(CustomRoom(
                room_id=curr_id, room_name=r_name, room_type="عامة",
                assigned_subject="عامة", morning_teacher=m_teach, afternoon_teacher=e_teach,
                total_hours=tot_h, max_capacity_hours=max_cap,
                utilization_pct=min(100.0, util), status=status, is_custom=False
            ))
            curr_id += 1

        # 2. SVT Labs
        svt_teachers = [a for a in assignments if a.subject in ["علوم الحياة و الأرض", "علوم الحياة والأرض"]]
        for j in range(self.institution.svt_labs_count):
            def_name = f"مختبر علوم الحياة والأرض {j+1}"
            r_name = self.get_room_display_name(def_name)
            t1 = svt_teachers[j*2].teacher_name if (j*2) < len(svt_teachers) else "شاغر (صباحي)"
            t2 = svt_teachers[j*2+1].teacher_name if (j*2+1) < len(svt_teachers) else "شاغر (مسائي)"
            
            override_key = r_name if r_name in self.manual_overrides else (def_name if def_name in self.manual_overrides else None)
            if override_key:
                t1 = self.manual_overrides[override_key].get("morning", t1)
                t2 = self.manual_overrides[override_key].get("afternoon", t2)
            else:
                if t1 in occupied_teachers: t1 = "شاغر (صباحي)"
                if t2 in occupied_teachers: t2 = "شاغر (مسائي)"

            t1_h = next((a.total_hours for a in assignments if a.teacher_name == t1), 18) if "شاغر" not in t1 and t1 != "-" else 0
            t2_h = next((a.total_hours for a in assignments if a.teacher_name == t2), 18) if "شاغر" not in t2 and t2 != "-" else 0
            tot_h = t1_h + t2_h
            util = round((tot_h / float(max_cap)) * 100, 1) if max_cap > 0 else 0

            rooms.append(CustomRoom(
                room_id=curr_id, room_name=r_name, room_type="مختبر متخصص",
                assigned_subject="علوم الحياة و الأرض", morning_teacher=t1, afternoon_teacher=t2,
                total_hours=tot_h, max_capacity_hours=max_cap,
                utilization_pct=min(100.0, util), status=f"مختبر مخصص ({tot_h}/{max_cap}س) ✓", is_custom=False
            ))
            curr_id += 1

        # 3. PC Labs
        pc_teachers = [a for a in assignments if a.subject in ["الكيمياء و الفيزياء", "الفيزياء والكيمياء"]]
        for j in range(self.institution.pc_labs_count):
            def_name = f"مختبر الفيزياء والكيمياء {j+1}"
            r_name = self.get_room_display_name(def_name)
            t1 = pc_teachers[j*2].teacher_name if (j*2) < len(pc_teachers) else "شاغر (صباحي)"
            t2 = pc_teachers[j*2+1].teacher_name if (j*2+1) < len(pc_teachers) else "شاغر (مسائي)"
            
            override_key = r_name if r_name in self.manual_overrides else (def_name if def_name in self.manual_overrides else None)
            if override_key:
                t1 = self.manual_overrides[override_key].get("morning", t1)
                t2 = self.manual_overrides[override_key].get("afternoon", t2)
            else:
                if t1 in occupied_teachers: t1 = "شاغر (صباحي)"
                if t2 in occupied_teachers: t2 = "شاغر (مسائي)"

            t1_h = next((a.total_hours for a in assignments if a.teacher_name == t1), 18) if "شاغر" not in t1 and t1 != "-" else 0
            t2_h = next((a.total_hours for a in assignments if a.teacher_name == t2), 18) if "شاغر" not in t2 and t2 != "-" else 0
            tot_h = t1_h + t2_h
            util = round((tot_h / float(max_cap)) * 100, 1) if max_cap > 0 else 0

            rooms.append(CustomRoom(
                room_id=curr_id, room_name=r_name, room_type="مختبر متخصص",
                assigned_subject="الكيمياء و الفيزياء", morning_teacher=t1, afternoon_teacher=t2,
                total_hours=tot_h, max_capacity_hours=max_cap,
                utilization_pct=min(100.0, util), status=f"مختبر مخصص ({tot_h}/{max_cap}س) ✓", is_custom=False
            ))
            curr_id += 1

        # 4. Multimedia Labs
        it_teachers = [a for a in assignments if a.subject == "المعلوميات"]
        for j in range(self.institution.multimedia_rooms_count):
            def_name = "قاعة الإعلاميات المتعددة الوسائط" if self.institution.multimedia_rooms_count == 1 else f"قاعة الإعلاميات {j+1}"
            r_name = self.get_room_display_name(def_name)
            t1 = it_teachers[0].teacher_name if it_teachers else "شاغر (صباحي)"
            t2 = it_teachers[1].teacher_name if len(it_teachers) > 1 else (it_teachers[0].teacher_name if it_teachers else "شاغر (مسائي)")
            
            override_key = r_name if r_name in self.manual_overrides else (def_name if def_name in self.manual_overrides else None)
            if override_key:
                t1 = self.manual_overrides[override_key].get("morning", t1)
                t2 = self.manual_overrides[override_key].get("afternoon", t2)
            else:
                if t1 in occupied_teachers: t1 = "شاغر (صباحي)"
                if t2 in occupied_teachers: t2 = "شاغر (مسائي)"

            t1_h = next((a.total_hours for a in assignments if a.teacher_name == t1), 20) if "شاغر" not in t1 and t1 != "-" else 0
            t2_h = next((a.total_hours for a in assignments if a.teacher_name == t2), 20) if "شاغر" not in t2 and t2 != "-" else 0
            tot_h = t1_h + t2_h
            util = round((tot_h / float(max_cap)) * 100, 1) if max_cap > 0 else 0

            rooms.append(CustomRoom(
                room_id=curr_id, room_name=r_name, room_type="قاعة وسائط متعددة",
                assigned_subject="المعلوميات", morning_teacher=t1, afternoon_teacher=t2,
                total_hours=tot_h, max_capacity_hours=max_cap,
                utilization_pct=min(100.0, util), status=f"قاعة وسائط ({tot_h}/{max_cap}س) ✓", is_custom=False
            ))
            curr_id += 1

        # 5. Sports Fields
        pe_teachers = [a for a in assignments if a.subject == "التربية البدنية"]
        for j in range(self.institution.sports_fields_count):
            def_name = f"ملعب التربية البدنية {j+1}"
            r_name = self.get_room_display_name(def_name)
            t1 = pe_teachers[j].teacher_name if j < len(pe_teachers) else "شاغر (صباحي)"
            t2 = pe_teachers[j+1].teacher_name if (j+1) < len(pe_teachers) else "شاغر (مسائي)"
            
            override_key = r_name if r_name in self.manual_overrides else (def_name if def_name in self.manual_overrides else None)
            if override_key:
                t1 = self.manual_overrides[override_key].get("morning", t1)
                t2 = self.manual_overrides[override_key].get("afternoon", t2)
            else:
                if t1 in occupied_teachers: t1 = "شاغر (صباحي)"
                if t2 in occupied_teachers: t2 = "شاغر (مسائي)"

            rooms.append(CustomRoom(
                room_id=curr_id, room_name=r_name, room_type="فضاء رياضي",
                assigned_subject="التربية البدنية", morning_teacher=t1, afternoon_teacher=t2,
                total_hours=min(40, max_cap), max_capacity_hours=max_cap,
                utilization_pct=100.0, status=f"ملعب رياضي ({max_cap}/{max_cap}س) ✓", is_custom=False
            ))
            curr_id += 1

        # 6. User-added Custom Room Types (e.g. قاعة الاجتماعيات 1, 2...)
        for crt in self.institution.custom_room_types:
            c_name = crt.get("name", "قاعة مخصصة")
            c_subj = crt.get("subject", "عامة")
            c_type = crt.get("room_type", "قاعة مخصصة")
            c_count = int(crt.get("count", 1))

            subj_teachers = [a.teacher_name for a in assignments if a.subject == c_subj and a.total_hours > 0]

            for k in range(1, c_count + 1):
                def_name = f"{c_name} {k}" if c_count > 1 else c_name
                r_name = self.get_room_display_name(def_name)
                
                m_teach = subj_teachers[(k-1)*2] if (k-1)*2 < len(subj_teachers) else "شاغر (صباحي)"
                e_teach = subj_teachers[(k-1)*2+1] if (k-1)*2+1 < len(subj_teachers) else "شاغر (مسائي)"

                override_key = r_name if r_name in self.manual_overrides else (def_name if def_name in self.manual_overrides else None)
                if override_key:
                    m_teach = self.manual_overrides[override_key].get("morning", m_teach)
                    e_teach = self.manual_overrides[override_key].get("afternoon", e_teach)
                else:
                    if m_teach in occupied_teachers: m_teach = "شاغر (صباحي)"
                    if e_teach in occupied_teachers: e_teach = "شاغر (مسائي)"

                m_h = next((a.total_hours for a in assignments if a.teacher_name == m_teach), 20) if "شاغر" not in m_teach and m_teach != "-" else 0
                e_h = next((a.total_hours for a in assignments if a.teacher_name == e_teach), 20) if "شاغر" not in e_teach and e_teach != "-" else 0
                tot_h = m_h + e_h
                util = round((tot_h / float(max_cap)) * 100, 1) if max_cap > 0 else 0

                rooms.append(CustomRoom(
                    room_id=curr_id, room_name=r_name, room_type=c_type,
                    assigned_subject=c_subj, morning_teacher=m_teach, afternoon_teacher=e_teach,
                    total_hours=tot_h, max_capacity_hours=max_cap,
                    utilization_pct=min(100.0, util), status=f"مخصصة لـ ({c_subj}) ✓", is_custom=True
                ))
                curr_id += 1

        return rooms
