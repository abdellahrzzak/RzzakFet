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

    def clean_invalid_overrides(self, assignments: List[TeacherAssignment]):
        valid_teachers = {a.teacher_name for a in assignments if a.teacher_name}
        keys_to_clean = []
        for rk, sess_dict in list(self.manual_overrides.items()):
            for sess in ["morning", "afternoon"]:
                tname = sess_dict.get(sess)
                if tname and "شاغر" not in tname and tname != "-":
                    if tname not in valid_teachers:
                        del sess_dict[sess]
            if not sess_dict:
                keys_to_clean.append(rk)
        for k in keys_to_clean:
            if k in self.manual_overrides:
                del self.manual_overrides[k]

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
        self.clean_invalid_overrides(assignments)
        n_gen = self.institution.general_rooms_count
        gen_subjects_allowed = [
            "اللغة العربية", "اللغة  العربية",
            "اللغة الفرنسية", "اللغة  الفرنسية",
            "التربية الإسلامية",
            "الاجتماعيات", "التاريخ والجغرافيا",
            "الرياضيات",
            "اللغة الأجنبية الثانية (الإنجليزية)", "اللغة الإنجليزية",
            "الفلسفة", "الترجمة",
            "الاقتصاد العام والاحصاء", "المحاسبة", "الاقتصاد والتنظيم الإداري للمقاولات", "القانون",
            "الفقه والأصول", "التفسير والحديث", "الفرائض والتوقيت", "التوثيق",
            "الرسم والتعبير التشكيلي", "علوم المهندس", "معلوميات التدبير"
        ]
        
        # Collect teachers assigned to dedicated custom rooms so they are prioritized there and excluded from general rooms
        dedicated_custom_teachers = set()
        for crt in self.institution.custom_room_types:
            c_subj = crt.get("subject")
            c_count = int(crt.get("count", 1))
            if c_subj and c_subj != "عامة":
                c_teachers = [a.teacher_name for a in assignments if a.subject == c_subj and a.total_hours > 0]
                dedicated_custom_teachers.update(c_teachers[:c_count * 2])

        gen_teachers = [
            a for a in assignments 
            if a.subject in gen_subjects_allowed 
            and a.total_hours > 0 
            and a.teacher_name not in dedicated_custom_teachers
        ]
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
        svt_teachers = [a for a in assignments if any(k in (a.subject or "") for k in ["علوم الحياة", "SVT", "svt"])]
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

            svt_subj = svt_teachers[0].subject if svt_teachers else "علوم الحياة والأرض"
            rooms.append(CustomRoom(
                room_id=curr_id, room_name=r_name, room_type="مختبر متخصص",
                assigned_subject=svt_subj, morning_teacher=t1, afternoon_teacher=t2,
                total_hours=tot_h, max_capacity_hours=max_cap,
                utilization_pct=min(100.0, util), status=f"مختبر مخصص ({tot_h}/{max_cap}س) ✓", is_custom=False
            ))
            curr_id += 1

        # 3. PC Labs
        pc_teachers = [a for a in assignments if any(k in (a.subject or "") for k in ["الفيزياء", "الكيمياء", "PC", "pc"])]
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

            pc_subj = pc_teachers[0].subject if pc_teachers else "الفيزياء والكيمياء"
            rooms.append(CustomRoom(
                room_id=curr_id, room_name=r_name, room_type="مختبر متخصص",
                assigned_subject=pc_subj, morning_teacher=t1, afternoon_teacher=t2,
                total_hours=tot_h, max_capacity_hours=max_cap,
                utilization_pct=min(100.0, util), status=f"مختبر مخصص ({tot_h}/{max_cap}س) ✓", is_custom=False
            ))
            curr_id += 1

        # 4. Multimedia Labs
        it_teachers = [a for a in assignments if any(k in (a.subject or "") for k in ["المعلوميات", "معلوميات", "INF", "inf"])]
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
        pe_teachers = [a for a in assignments if any(k in (a.subject or "") for k in ["التربية البدنية", "EPS", "eps"])]
        num_pe = len(pe_teachers)
        num_fields = self.institution.sports_fields_count

        for j in range(num_fields):
            def_name = f"ملعب التربية البدنية {j+1}"
            r_name = self.get_room_display_name(def_name)

            if num_pe <= num_fields:
                t1 = pe_teachers[j].teacher_name if j < num_pe else "شاغر (صباحي)"
                t2 = "شاغر (مسائي)"
            else:
                t1 = pe_teachers[j*2].teacher_name if (j*2) < num_pe else "شاغر (صباحي)"
                t2 = pe_teachers[j*2+1].teacher_name if (j*2+1) < num_pe else "شاغر (مسائي)"
            
            override_key = r_name if r_name in self.manual_overrides else (def_name if def_name in self.manual_overrides else None)
            if override_key:
                t1 = self.manual_overrides[override_key].get("morning", t1)
                t2 = self.manual_overrides[override_key].get("afternoon", t2)
            else:
                if t1 in occupied_teachers: t1 = "شاغر (صباحي)"
                if t2 in occupied_teachers: t2 = "شاغر (مسائي)"

            t1_h = next((a.total_hours for a in assignments if a.teacher_name == t1), 21) if "شاغر" not in t1 and t1 != "-" else 0
            t2_h = next((a.total_hours for a in assignments if a.teacher_name == t2), 21) if "شاغر" not in t2 and t2 != "-" else 0
            tot_h = t1_h + t2_h

            pe_subj_name = pe_teachers[0].subject if pe_teachers else "التربية البدنية"
            rooms.append(CustomRoom(
                room_id=curr_id, room_name=r_name, room_type="فضاء رياضي",
                assigned_subject=pe_subj_name, morning_teacher=t1, afternoon_teacher=t2,
                total_hours=min(tot_h, max_cap) if tot_h > 0 else min(40, max_cap),
                max_capacity_hours=max_cap,
                utilization_pct=100.0, status=f"ملعب رياضي ({max_cap}/{max_cap}س) ✓", is_custom=False
            ))
            curr_id += 1

        # 6. User-added Custom Room Types (e.g. قاعة الاجتماعيات 1, 2...)
        teacher_subject_map = {a.teacher_name: a.subject for a in assignments}

        def _is_subj_match(a_subj, target_subj):
            if not a_subj or not target_subj: return False
            s1 = " ".join(a_subj.split())
            s2 = " ".join(target_subj.split())
            if s1 == s2: return True
            if ("اجتماعيات" in s1 or "تاريخ" in s1) and ("اجتماعيات" in s2 or "تاريخ" in s2): return True
            if ("فيزياء" in s1 or "PC" in s1) and ("فيزياء" in s2 or "PC" in s2): return True
            if ("حياة" in s1 or "SVT" in s1) and ("حياة" in s2 or "SVT" in s2): return True
            if ("إعلاميات" in s1 or "معلوميات" in s1) and ("إعلاميات" in s2 or "معلوميات" in s2): return True
            if "إسلامية" in s1 and "إسلامية" in s2: return True
            if "فلسفة" in s1 and "فلسفة" in s2: return True
            if ("إنجليزية" in s1 or "انجليزية" in s1) and ("إنجليزية" in s2 or "انجليزية" in s2): return True
            return False

        for crt in self.institution.custom_room_types:
            c_name = crt.get("name", "قاعة مخصصة")
            c_subj = crt.get("subject", "عامة")
            c_type = crt.get("room_type", "قاعة مخصصة")
            c_count = int(crt.get("count", 1))

            subj_teachers = [a.teacher_name for a in assignments if _is_subj_match(a.subject, c_subj) and a.total_hours > 0]
            num_subj = len(subj_teachers)

            for k in range(1, c_count + 1):
                def_name = f"{c_name} {k}" if c_count > 1 else c_name
                r_name = self.get_room_display_name(def_name)
                
                # Balanced distribution across all custom rooms:
                # 1..c_count in morning; (c_count + 1).. in afternoon
                m_idx = k - 1
                e_idx = c_count + (k - 1)
                m_teach = subj_teachers[m_idx] if m_idx < num_subj else "شاغر (صباحي)"
                e_teach = subj_teachers[e_idx] if e_idx < num_subj else "شاغر (مسائي)"

                override_key = r_name if r_name in self.manual_overrides else (def_name if def_name in self.manual_overrides else None)
                if override_key:
                    cand_m = self.manual_overrides[override_key].get("morning")
                    cand_e = self.manual_overrides[override_key].get("afternoon")
                    if cand_m is not None:
                        m_teach = cand_m
                    if cand_e is not None:
                        e_teach = cand_e
                else:
                    if m_teach in occupied_teachers: m_teach = "شاغر (صباحي)"
                    if e_teach in occupied_teachers: e_teach = "شاغر (مسائي)"

                m_h = next((a.total_hours for a in assignments if a.teacher_name == m_teach), 20) if "شاغر" not in m_teach and m_teach != "-" else 0
                e_h = next((a.total_hours for a in assignments if a.teacher_name == e_teach), 20) if "شاغر" not in e_teach and e_teach != "-" else 0
                tot_h = m_h + e_h
                util = round((tot_h / float(max_cap)) * 100, 1) if max_cap > 0 else 0

                assigned_subj = c_subj
                if "شاغر" not in m_teach and m_teach != "-":
                    m_subj = next((a.subject for a in assignments if a.teacher_name == m_teach), None)
                    if m_subj and (c_subj == "عامة" or not c_subj):
                        assigned_subj = m_subj

                rooms.append(CustomRoom(
                    room_id=curr_id, room_name=r_name, room_type=c_type,
                    assigned_subject=assigned_subj, morning_teacher=m_teach, afternoon_teacher=e_teach,
                    total_hours=tot_h, max_capacity_hours=max_cap,
                    utilization_pct=min(100.0, util), status=f"مخصصة لـ ({assigned_subj}) ✓", is_custom=True
                ))
                curr_id += 1

        return rooms
