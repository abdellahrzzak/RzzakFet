# -*- coding: utf-8 -*-
import math
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any
from .models import InstitutionData, EducationalStructure, TeacherAssignment, CustomRoom
from .fet_constraints_catalog import get_68_constraints

DEFAULT_SUBJECT_ACTIVITY_CONSTRAINTS = [
    {
        "subject": "التربية البدنية",
        "name": "التربية البدنية والرياضية",
        "min_days": 1,
        "max_days": None,
        "weight": 95.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "forbid_first_pm_slot": True,
        "desc": "التباعد بين حصص التربية البدنية ومنع الحصة الأولى مساءً"
    },
    {
        "subject": "المعلوميات",
        "name": "المعلوميات",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص المعلوميات وتفادي تكرارها في نفس اليوم"
    },
    {
        "subject": "الرياضيات",
        "name": "الرياضيات",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص الرياضيات الـ 5 يومياً كحد أقصى حصة في اليوم (1 1 1 1 1)"
    },
    {
        "subject": "اللغة العربية",
        "name": "اللغة العربية",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص العربية الـ 4 على 4 أيام مختلفة (1 1 1 1)"
    },
    {
        "subject": "اللغة الفرنسية",
        "name": "اللغة الفرنسية",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص الفرنسية الـ 4 على 4 أيام مختلفة (1 1 1 1)"
    },
    {
        "subject": "الاجتماعيات",
        "name": "الاجتماعيات",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص الاجتماعيات الـ 3 على 3 أيام مختلفة (1 1 1)"
    },
    {
        "subject": "التربية الإسلامية",
        "name": "التربية الإسلامية",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص التربية الإسلامية على يومين متباعدين (1 1)"
    },
    {
        "subject": "اللغة الإنجليزية",
        "name": "اللغة الإنجليزية",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص اللغة الإنجليزية على يومين متباعدين (1 1)"
    },
    {
        "subject": "علوم الحياة والأرض",
        "name": "علوم الحياة والأرض",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توطين حصص المختبرات وتفادي تكرار المادة في اليوم"
    },
    {
        "subject": "الفيزياء والكيمياء",
        "name": "الفيزياء والكيمياء",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توطين حصص الفيزياء وتفادي تكرار المادة في اليوم"
    },
    {
        "subject": "التكنولوجيا الصناعية",
        "name": "التكنولوجيا الصناعية",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص التكنولوجيا في القاعة المخصصة"
    },
    {
        "subject": "التربية الأسرية",
        "name": "التربية الأسرية",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص التربية الأسرية"
    },
    {
        "subject": "التربية التشكيلية",
        "name": "التربية التشكيلية",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص الفنون التشكيلية"
    },
    {
        "subject": "التربية الموسيقية",
        "name": "التربية الموسيقية",
        "min_days": 1,
        "max_days": None,
        "weight": 100.0,
        "is_active": True,
        "consecutive_if_same_day": False,
        "desc": "توزيع حصص التربية الموسيقية"
    }
]

PRIMARY_CONSTRAINTS_ORDER = [
    "tc_a_8",     # 1. ConstraintMinDaysBetweenActivities
    "tc_s_7",     # 2. ConstraintStudentsMaxHoursDaily
    "tc_s_9",     # 3. ConstraintStudentsMinHoursDaily
    "tc_t_10",    # 4. ConstraintTeachersMinHoursDaily
    "tc_t_8",     # 5. ConstraintTeachersMaxHoursDaily
    "tc_t_6",     # 6. ConstraintTeachersMaxGapsPerDay
    "tc_t_12",    # 7. ConstraintTeachersMaxHoursContinuously
    "tc_s_2",     # 8. ConstraintStudentsMaxGapsPerDay
    "tc_base_2",  # 9. ConstraintBreakTimes
    "sc_t_1",     # 10. ConstraintTeacherHomeRoom
    "sc_sub_2",   # 11. ConstraintSubjectPreferredRooms
    "tc_base_1",  # 12. ConstraintBasicCompulsoryTime
    "tc_t_14",    # 13. ConstraintTeachersIntervalMaxDaysPerWeek
    "sc_base_1",  # 14. ConstraintBasicCompulsorySpace
    "tc_s_3",     # 15. ConstraintStudentsMaxGapsPerWeek
]

class FetXmlGenerator:
    def __init__(self, institution: InstitutionData = None, structure: EducationalStructure = None):
        self.institution = institution or InstitutionData()
        self.structure = structure or EducationalStructure()
        
        # Default 15 Primary Constraints Matching Official Specification
        self.all_available_constraints = self._build_default_constraints()

    @staticmethod
    def _build_default_constraints() -> List[Dict]:
        all_c = get_68_constraints()
        c_dict = {c["id"]: dict(c) for c in all_c}
        primary_list = []
        for cid in PRIMARY_CONSTRAINTS_ORDER:
            if cid in c_dict:
                c = c_dict.pop(cid)
                c["is_primary"] = True
                primary_list.append(c)
        remaining_list = []
        for c in c_dict.values():
            c["is_primary"] = False
            remaining_list.append(c)
        return primary_list + remaining_list

    def get_primary_constraints(self) -> List[Dict]:
        """Returns the primary constraints ordered as set by the principal."""
        return [c for c in self.all_available_constraints if c.get("is_primary", False)]

    def get_library_constraints(self) -> List[Dict]:
        """Returns available secondary / unselected constraints in the bank."""
        return [c for c in self.all_available_constraints if not c.get("is_primary", False)]

    def get_active_constraints(self) -> List[Dict]:
        """Returns constraints that are currently active in generation."""
        return [c for c in self.all_available_constraints if c.get("is_active", True)]

    def reset_to_default_constraints(self):
        """Restores constraints to the 15 default primary constraints in original order."""
        self.all_available_constraints = self._build_default_constraints()

    def get_subject_activity_constraints(self) -> List[Dict]:
        cur_map = self.institution.subject_activity_constraints or {}
        res = []
        for def_item in DEFAULT_SUBJECT_ACTIVITY_CONSTRAINTS:
            s_key = def_item["subject"]
            if s_key in cur_map:
                merged = {**def_item, **cur_map[s_key]}
                res.append(merged)
            else:
                res.append(dict(def_item))
        return res

    def _is_qualifying_cycle(self, is_qualifying_param: bool = False) -> bool:
        if is_qualifying_param:
            return True
        inst_cycle = getattr(self.institution, 'institution_cycle', '') or getattr(self.institution, 'cycle', '')
        struct_cycle = getattr(self.structure, 'cycle', '')
        if inst_cycle == 'qualifying' or struct_cycle == 'qualifying' or getattr(self.structure, 'is_qualifying', False):
            return True
        if inst_cycle == 'middle' or struct_cycle == 'middle':
            return False
        hs = getattr(self.structure, 'high_school_streams', {})
        return bool(hs) and any(int(v) > 0 for v in hs.values())

    def get_subject_durations(self, subject: str, level: int, weekly_hours: int, is_qualifying: bool = False) -> List[int]:
        subj_clean = (subject or "").strip()
        is_qualifying = self._is_qualifying_cycle(is_qualifying)

        is_science_lab = any(k in subj_clean for k in ["علوم الحياة", "SVT", "svt", "الفيزياء", "الكيمياء", "PC", "pc"])
        is_pe = any(k in subj_clean for k in ["التربية البدنية", "EPS", "eps"])
        is_math = any(k in subj_clean for k in ["الرياضيات", "Math", "math"])
        is_arabic = any(k in subj_clean for k in ["اللغة العربية", "عربية", "العربية"])
        is_french = any(k in subj_clean for k in ["الفرنسية", "Français", "Francais", "français"])

        if is_qualifying:
            # Moroccan High School (الثانوي التأهيلي) Pedagogical Distribution Norms
            if is_science_lab:
                if weekly_hours == 1:
                    return [1]
                elif weekly_hours == 2:
                    return [2]
                elif weekly_hours == 3:
                    return [2, 1]
                elif weekly_hours == 4:
                    return [2, 2]
                elif weekly_hours == 5:
                    return [2, 2, 1]
                elif weekly_hours == 6:
                    return [2, 2, 2]
                elif weekly_hours >= 7:
                    return [2, 2, 2, 1]
                return [1] * weekly_hours
            elif is_pe:
                # Official Moroccan standard for Physical Education: 2 continuous hours in sports fields
                return [2] if weekly_hours == 2 else ([2, 1] if weekly_hours == 3 else [1] * weekly_hours)
            elif is_math:
                if weekly_hours <= 5:
                    return [1] * weekly_hours
                elif weekly_hours == 6:
                    return [2, 2, 1, 1]
                elif weekly_hours == 7:
                    return [2, 2, 1, 1, 1]
                elif weekly_hours >= 8:
                    return [2, 2, 2, 1, 1]
                return [1] * weekly_hours
            elif is_french:
                if weekly_hours <= 5:
                    return [1] * weekly_hours
                elif weekly_hours == 6:
                    return [2, 2, 1, 1]
                else:
                    return [2, 2, 2, 1]
            elif is_arabic:
                if weekly_hours <= 5:
                    return [1] * weekly_hours
                else:
                    return [2, 2, 1, 1]
            elif any(k in subj_clean for k in ["المعلوميات", "INF", "inf"]):
                return [weekly_hours] if weekly_hours <= 2 else [2, 1]
            elif any(k in subj_clean for k in ["الترجمة", "TR", "tr"]):
                return [weekly_hours] if weekly_hours <= 2 else [2, 1]
            else:
                return [1] * weekly_hours

        # Middle School (الإعدادي) split modes
        splits_cfg = getattr(self.institution, "subject_split_modes", {}) or {}
        
        matched_key = None
        for k in splits_cfg.keys():
            if k == subj_clean or (k in subj_clean) or (subj_clean in k):
                matched_key = k
                break
        
        cfg = splits_cfg.get(matched_key) if matched_key else None
        if cfg:
            mode = None
            if level == 3 and "mode_l3" in cfg:
                mode = cfg.get("mode_l3")
            elif level == 2 and "mode_l2" in cfg:
                mode = cfg.get("mode_l2")
            elif level == 1 and "mode_l1" in cfg:
                mode = cfg.get("mode_l1")
            
            if not mode:
                mode = cfg.get("mode")
            
            if mode:
                mode_str = str(mode).strip()
                if "+" in mode_str:
                    parts = [int(p.strip()) for p in mode_str.split("+") if p.strip().isdigit()]
                    if parts:
                        return parts
                elif mode_str.isdigit():
                    val = int(mode_str)
                    if val > 0:
                        return [val]

        # Fallback defaults based on official Moroccan Middle School Pedagogical Norms
        if is_science_lab:
            if weekly_hours == 2:
                return [2]
            elif weekly_hours == 3:
                return [2, 1]
            elif weekly_hours == 4:
                return [2, 2]
            elif weekly_hours == 5:
                return [2, 2, 1]
            elif weekly_hours == 6:
                return [2, 2, 2]
            elif weekly_hours >= 7:
                return [2, 2, 2, 1]
            else:
                return [1] * weekly_hours
        elif is_pe:
            # PE can be 2 continuous hours or 1+1
            return [2] if weekly_hours == 2 else [1] * weekly_hours
        elif is_math or is_arabic or is_french:
            # Moroccan requirement: individual 1-hour sessions distributed across days
            return [1] * weekly_hours
        else:
            return [1] * weekly_hours

    @staticmethod
    def can_teacher_satisfy_min_daily_hours(groups_durations: List[List[int]], min_h: int) -> bool:
        """
        Determines whether a teacher can mathematically satisfy Minimum_Hours_Daily >= min_h
        on all working days without creating an unsolvable contradiction (Pigeonhole conflict).
        
        Each item in groups_durations is a list of durations for one class/subject group
        that must be scheduled on distinct days due to MinDaysBetweenActivities >= 1.
        """
        if not groups_durations or min_h <= 1:
            return True

        total_hours = sum(sum(g) for g in groups_durations)
        if total_hours < min_h:
            return False

        # Teacher needs at least max(len(g)) days to spread activities for their largest class.
        # If total_hours < min_h * max_days, the average daily hours is < min_h, mathematically impossible!
        max_days_needed = max(len(g) for g in groups_durations)
        if total_hours < min_h * max_days_needed:
            return False

        total_groups = len(groups_durations)
        if total_groups == 1:
            # If the teacher only teaches one group/class, every activity is scheduled alone.
            # If any activity duration < min_h, that day will strictly have < min_h!
            return all(dur >= min_h for dur in groups_durations[0])

        # Pigeonhole check:
        # For any group G, its activities must appear on len(G) distinct days.
        # All other groups combined can cover at most sum(len(H) for H != G) days.
        # If len(G) > sum(len(H) for H != G), group G must appear ALONE on at least
        # alone_days = len(G) - sum(len(H) for H != G) days.
        # If the number of activities in G of duration >= min_h is less than alone_days,
        # then at least one alone day is forced to have an activity of duration < min_h.
        # That alone day cannot reach min_h, making ConstraintTeacherMinHoursDaily mathematically impossible!
        for i, g in enumerate(groups_durations):
            n_g = len(g)
            other_acts_count = sum(len(groups_durations[j]) for j in range(total_groups) if j != i)
            if n_g > other_acts_count:
                alone_days = n_g - other_acts_count
                ge_min_in_g = sum(1 for dur in g if dur >= min_h)
                if alone_days > ge_min_in_g:
                    return False

        return True

    def generate_xml(self, assignments: List[TeacherAssignment], rooms: List[CustomRoom], active_constraints_override: Optional[List[Dict]] = None, enable_3apic_grouping: bool = False) -> str:
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('')
        lines.append('<fet version="7.10.5">')
        lines.append('')
        lines.append(f'<Institution_Name>{self.institution.institution_name}</Institution_Name>')
        lines.append('')
        lines.append(f'<Comments>Exported natively from Moroccan Academic Engine</Comments>')
        lines.append('')

        # Moroccan 12 Half-Days
        days_names = [
            "الاثنين ص", "الاثنين م",
            "الثلاثاء ص", "الثلاثاء م",
            "الاربعاء ص", "الاربعاء م",
            "الخميس ص", "الخميس م",
            "الجمعة ص", "الجمعة م",
            "السبت ص", "السبت م"
        ]
        lines.append('<Days_List>')
        lines.append(f'<Number_of_Days>{len(days_names)}</Number_of_Days>')
        for d in days_names:
            lines.append('<Day>')
            lines.append(f'	<Name>{d}</Name>')
            lines.append('</Day>')
        lines.append('</Days_List>')
        lines.append('')

        # 4 Hours per Half-Day
        hours_names = ["ح 1", "ح 2", "ح 3", "ح 4"]
        lines.append('<Hours_List>')
        lines.append(f'<Number_of_Hours>{len(hours_names)}</Number_of_Hours>')
        for h in hours_names:
            lines.append('<Hour>')
            lines.append(f'	<Name>{h}</Name>')
            lines.append('</Hour>')
        lines.append('</Hours_List>')
        lines.append('')

        # Students Year & Classes
        lines.append('<Students_List>')
        
        is_qualifying = self._is_qualifying_cycle()

        if is_qualifying:
            hs_streams = getattr(self.structure, 'high_school_streams', {})
            try:
                from .high_school_curriculum import high_school_engine
            except (ImportError, ValueError):
                from high_school_curriculum import high_school_engine
            all_hs_classes = high_school_engine.generate_classes_list(hs_streams)
            tc_classes = [c for c in all_hs_classes if c["level"] == 1]
            bac1_classes = [c for c in all_hs_classes if c["level"] == 2]
            bac2_classes = [c for c in all_hs_classes if c["level"] == 3]

            levels_meta = [
                ("الجذوع المشتركة", tc_classes),
                ("الأولى باكالوريا", bac1_classes),
                ("الثانية باكالوريا", bac2_classes),
            ]
            for lvl_name, lvl_cls in levels_meta:
                if not lvl_cls:
                    continue
                tot_stu = len(lvl_cls) * 35
                lines.append('<Year>')
                lines.append(f'	<Name>{lvl_name}</Name>')
                lines.append(f'	<Number_of_Students>{tot_stu}</Number_of_Students>')
                for c in lvl_cls:
                    lines.append('	<Group>')
                    lines.append(f'		<Name>{c["code"]}</Name>')
                    lines.append('		<Number_of_Students>35</Number_of_Students>')
                    lines.append('	</Group>')
                lines.append('</Year>')
            valid_classes_set = set(c["code"] for c in all_hs_classes)
            all_students_set = valid_classes_set | {"الجذوع المشتركة", "الأولى باكالوريا", "الثانية باكالوريا", "TC", "1BAC", "2BAC"}
        else:
            # Year 1
            lines.append('<Year>')
            lines.append('	<Name>الأولى إعدادي</Name>')
            lines.append(f'	<Number_of_Students>{self.structure.classes_1_apic * 38}</Number_of_Students>')
            for i in range(1, self.structure.classes_1_apic + 1):
                lines.append('	<Group>')
                lines.append(f'		<Name>1APIC{i}</Name>')
                lines.append('		<Number_of_Students>38</Number_of_Students>')
                lines.append('	</Group>')
            lines.append('</Year>')

            # Year 2
            lines.append('<Year>')
            lines.append('	<Name>الثانية إعدادي</Name>')
            lines.append(f'	<Number_of_Students>{self.structure.classes_2_apic * 38}</Number_of_Students>')
            for i in range(1, self.structure.classes_2_apic + 1):
                lines.append('	<Group>')
                lines.append(f'		<Name>2APIC{i}</Name>')
                lines.append('		<Number_of_Students>38</Number_of_Students>')
                lines.append('	</Group>')
            lines.append('</Year>')

            # Year 3
            lines.append('<Year>')
            lines.append('	<Name>الثالثة إعدادي</Name>')
            lines.append(f'	<Number_of_Students>{self.structure.classes_3_apic * 38}</Number_of_Students>')
            for i in range(1, self.structure.classes_3_apic + 1):
                lines.append('	<Group>')
                lines.append(f'		<Name>3APIC{i}</Name>')
                lines.append('		<Number_of_Students>38</Number_of_Students>')
                if enable_3apic_grouping:
                    lines.append('		<Subgroup>')
                    lines.append(f'			<Name>3APIC{i}-G1</Name>')
                    lines.append('			<Number_of_Students>19</Number_of_Students>')
                    lines.append('		</Subgroup>')
                    lines.append('		<Subgroup>')
                    lines.append(f'			<Name>3APIC{i}-G2</Name>')
                    lines.append('			<Number_of_Students>19</Number_of_Students>')
                    lines.append('		</Subgroup>')
                lines.append('	</Group>')
            lines.append('</Year>')

            valid_classes_set = set()
            for i in range(1, self.structure.classes_1_apic + 1): valid_classes_set.add(f"1APIC{i}")
            for i in range(1, self.structure.classes_2_apic + 1): valid_classes_set.add(f"2APIC{i}")
            for i in range(1, self.structure.classes_3_apic + 1):
                valid_classes_set.add(f"3APIC{i}")
                if enable_3apic_grouping:
                    valid_classes_set.add(f"3APIC{i}-G1")
                    valid_classes_set.add(f"3APIC{i}-G2")
                    valid_classes_set.add(f"3APIC{i}-F1")
                    valid_classes_set.add(f"3APIC{i}-F2")
            all_students_set = valid_classes_set | {"الأولى إعدادي", "الثانية إعدادي", "الثالثة إعدادي"}

        lines.append('</Students_List>')
        lines.append('')

        # Teachers
        all_teachers = sorted(list(set([a.teacher_name for a in assignments if a.teacher_name])))
        all_teachers_set = set(all_teachers)
        
        valid_room_names = set([r.room_name for r in rooms])
        valid_subjects = set([a.subject for a in assignments if a.subject])

        def resolve_teacher(t_raw):
            if not t_raw:
                return None
            t_clean = str(t_raw).strip()
            if t_clean in all_teachers_set:
                return t_clean
            custom_map = getattr(self.institution, 'teacher_custom_names', {}) or {}
            if t_clean in custom_map:
                mapped = custom_map[t_clean].strip()
                if mapped in all_teachers_set:
                    return mapped
            for def_k, cust_v in custom_map.items():
                if cust_v and cust_v.strip() == t_clean:
                    if def_k in all_teachers_set:
                        return def_k
            return None

        def resolve_class(c_raw):
            if not c_raw:
                return None
            c_clean = str(c_raw).strip()
            if c_clean in all_students_set:
                return c_clean
            c_f = c_clean.replace("-BIOF-", "-F-")
            if c_f in all_students_set:
                return c_f
            m = re.match(r'^([123])\s*/\s*([0-9]+)$', c_clean)
            if m:
                cand = f"{m.group(1)}APIC{m.group(2)}"
                if cand in all_students_set:
                    return cand
            m2 = re.match(r'^([123])\s*APIC\s*[-_ ]*\s*([0-9]+)$', c_clean, re.I)
            if m2:
                cand = f"{m2.group(1)}APIC{m2.group(2)}"
                if cand in all_students_set:
                    return cand
            return None

        lines.append('<Teachers_List>')
        for t in all_teachers:
            lines.append('<Teacher>')
            lines.append(f'	<Name>{t}</Name>')
            lines.append('</Teacher>')
        lines.append('</Teachers_List>')
        lines.append('')

        # Subjects
        all_subjects = sorted(list(valid_subjects))
        lines.append('<Subjects_List>')
        for s in all_subjects:
            lines.append('<Subject>')
            lines.append(f'	<Name>{s}</Name>')
            lines.append('</Subject>')
        lines.append('</Subjects_List>')
        lines.append('')

        # Activity Tags
        lines.append('<Activity_Tags_List>')
        lines.append('</Activity_Tags_List>')
        lines.append('')

        # Activities Generation
        lines.append('<Activities_List>')
        act_id = 1
        group_id = 1
        min_days_constraints = []
        forbid_first_pm_activities = []
        actual_teacher_hours = {}
        class_all_activities = {}
        class_total_hours = {}
        teacher_all_activities = {}
        class_subject_activities = {}
        teacher_activity_groups = {}

        subj_cfg_list_early = self.get_subject_activity_constraints()
        subj_cfg_map_early = {item["subject"]: item for item in subj_cfg_list_early}

        grouping_same_start_constraints = []
        grouping_consecutive_constraints = []
        c3_pc_teacher = {}
        c3_svt_teacher = {}

        if enable_3apic_grouping:
            for a in assignments:
                s_c = (a.subject or "").strip()
                is_pc_cand = any(k in s_c for k in ["الفيزياء", "الكيمياء", "PC", "pc"])
                is_svt_cand = any(k in s_c for k in ["علوم الحياة", "SVT", "svt"])
                if not (is_pc_cand or is_svt_cand):
                    continue
                raw_c = re.split(r'[,،\s]+', (a.assigned_classes_str or "").strip())
                for rc in raw_c:
                    rc_clean = resolve_class(rc)
                    if rc_clean and ("3APIC" in rc_clean or "3_" in rc_clean):
                        m_cls = re.search(r'3APIC\d+', rc_clean)
                        cls_key = m_cls.group(0) if m_cls else rc_clean
                        if is_pc_cand and cls_key not in c3_pc_teacher:
                            c3_pc_teacher[cls_key] = (a.teacher_name, a.subject)
                        elif is_svt_cand and cls_key not in c3_svt_teacher:
                            c3_svt_teacher[cls_key] = (a.teacher_name, a.subject)

        # Lookup table for exact ministerial subject weekly hours per level
        level_hours_map = {
            "التربية الإسلامية": {1: 2, 2: 2, 3: 2},
            "اللغة العربية": {1: 4, 2: 4, 3: 4},
            "الاجتماعيات": {1: 3, 2: 3, 3: 3},
            "الرياضيات": {1: 5, 2: 4, 3: 5},
            "علوم الحياة و الأرض": {1: 2, 2: 2, 3: 3},
            "الكيمياء و الفيزياء": {1: 2, 2: 2, 3: 3},
            "اللغة الأجنبية الأولى (الفرنسية)": {1: 4, 2: 4, 3: 4},
            "التربية البدنية": {1: 2, 2: 2, 3: 2},
            "المعلوميات": {1: 1, 2: 1, 3: 1},
            "اللغة الأجنبية الثانية (الإنجليزية)": {1: 0, 2: 0, 3: 2},
            "التكنولوجيا الصناعية": {1: 0, 2: 0, 3: 0},
            "التربية الأسرية": {1: 0, 2: 0, 3: 0},
            "التربية التشكيلية / أو الموسيقية": {1: 0, 2: 0, 3: 0},
        }

        hs_class_subj_hours_map = {}
        if is_qualifying:
            hs_streams = getattr(self.structure, 'high_school_streams', {})
            try:
                from .high_school_curriculum import high_school_engine
            except (ImportError, ValueError):
                from high_school_curriculum import high_school_engine
            all_hs_cls = high_school_engine.generate_classes_list(hs_streams)
            for c in all_hs_cls:
                for scode, sinfo in c["subjects"].items():
                    sname = sinfo["name"].strip()
                    sh = sinfo["hours"]
                    hs_class_subj_hours_map[(c["code"], sname)] = sh
                    if "بدنية" in sname:
                        hs_class_subj_hours_map[(c["code"], "التربية البدنية")] = sh
                        hs_class_subj_hours_map[(c["code"], "التربية البدنية والرياضة")] = sh
                    if "فيزياء" in sname:
                        hs_class_subj_hours_map[(c["code"], "الفيزياء والكيمياء")] = sh
                        hs_class_subj_hours_map[(c["code"], "الكيمياء و الفيزياء")] = sh
                    if "حياة" in sname:
                        hs_class_subj_hours_map[(c["code"], "علوم الحياة والأرض")] = sh
                        hs_class_subj_hours_map[(c["code"], "علوم الحياة  والأرض")] = sh
                        hs_class_subj_hours_map[(c["code"], "علوم الحياة و الأرض")] = sh

        for a in assignments:
            if not a.assigned_classes_str or a.assigned_classes_str.strip() in ["-", ""]:
                continue
            
            raw_classes = re.split(r'[,،\s]+', a.assigned_classes_str.strip())
            classes_assigned = [c.strip() for c in raw_classes if c.strip() and c.strip() != "-"]
            
            for cls in classes_assigned:
                lvl = 1
                if "2_" in cls or "2APIC" in cls or "2 APIC" in cls or "1BAC" in cls or "1bac" in cls:
                    lvl = 2
                elif "3_" in cls or "3APIC" in cls or "3 APIC" in cls or "2BAC" in cls or "2bac" in cls:
                    lvl = 3
                elif "TC" in cls or "tc" in cls:
                    lvl = 1

                subj_clean = (a.subject or "").strip()
                is_pc_subj = any(k in subj_clean for k in ["الفيزياء", "الكيمياء", "PC", "pc"])
                is_svt_subj = any(k in subj_clean for k in ["علوم الحياة", "SVT", "svt"])
                if enable_3apic_grouping and lvl == 3 and (is_pc_subj or is_svt_subj):
                    continue  # handled in dedicated 3APIC grouping routine below
                
                weekly_h = 2
                if is_qualifying and (cls, subj_clean) in hs_class_subj_hours_map:
                    weekly_h = hs_class_subj_hours_map[(cls, subj_clean)]
                elif subj_clean in level_hours_map:
                    weekly_h = level_hours_map[subj_clean].get(lvl, 2)
                elif a.total_classes > 0:
                    weekly_h = max(1, round(a.total_hours / a.total_classes))

                # Check if subject_split_modes overrides the weekly hours for this subject & level (Middle School only)
                if not is_qualifying:
                    splits_cfg = getattr(self.institution, 'subject_split_modes', {}) or {}
                    s_cfg = None
                    for sk, sv in splits_cfg.items():
                        if sk == subj_clean or (sk in subj_clean) or (subj_clean in sk):
                            s_cfg = sv
                            break
                    if s_cfg:
                        mode_for_lvl = None
                        if lvl == 3 and "mode_l3" in s_cfg:
                            mode_for_lvl = s_cfg.get("mode_l3")
                        elif lvl == 2 and "mode_l2" in s_cfg:
                            mode_for_lvl = s_cfg.get("mode_l2")
                        elif lvl == 1 and "mode_l1" in s_cfg:
                            mode_for_lvl = s_cfg.get("mode_l1")
                        elif "mode" in s_cfg:
                            mode_for_lvl = s_cfg.get("mode")
                        
                        if mode_for_lvl:
                            m_str = str(mode_for_lvl).strip()
                            if "+" in m_str:
                                p_parts = [int(p.strip()) for p in m_str.split("+") if p.strip().isdigit()]
                                if p_parts:
                                    weekly_h = sum(p_parts)
                            elif m_str.isdigit():
                                weekly_h = int(m_str)

                if weekly_h <= 0:
                    continue

                act_group = []
                durations = self.get_subject_durations(a.subject, lvl, weekly_h, is_qualifying=is_qualifying)

                # Check if subject has forbid_first_pm_slot enabled
                cfg_pe = None
                for k, v in subj_cfg_map_early.items():
                    if k == subj_clean or (k in subj_clean) or (subj_clean in k):
                        cfg_pe = v
                        break
                is_pe_subj = ("بدن" in subj_clean or "EPS" in subj_clean)
                forbid_pm = cfg_pe.get("forbid_first_pm_slot") if cfg_pe else None
                should_forbid_pm = False
                if (is_pe_subj and forbid_pm is not False and (cfg_pe is None or cfg_pe.get("is_active", True))):
                    should_forbid_pm = True
                elif forbid_pm is True and (cfg_pe is None or cfg_pe.get("is_active", True)):
                    should_forbid_pm = True

                for dur in durations:
                    lines.append('<Activity>')
                    lines.append(f'	<Teacher>{a.teacher_name}</Teacher>')
                    lines.append(f'	<Subject>{a.subject}</Subject>')
                    lines.append(f'	<Students>{cls}</Students>')
                    lines.append(f'	<Duration>{dur}</Duration>')
                    lines.append(f'	<Total_Duration>{sum(durations)}</Total_Duration>')
                    lines.append(f'	<Id>{act_id}</Id>')
                    lines.append('	<Activity_Group_Id>0</Activity_Group_Id>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</Activity>')

                    if should_forbid_pm:
                        pe_w = int(cfg_pe.get("weight", 100)) if cfg_pe else 100
                        forbid_first_pm_activities.append({
                            "act_id": act_id,
                            "dur": dur,
                            "subject": a.subject,
                            "weight": pe_w
                        })

                    act_group.append(act_id)
                    actual_teacher_hours[a.teacher_name] = actual_teacher_hours.get(a.teacher_name, 0) + dur

                    if cls not in class_all_activities:
                        class_all_activities[cls] = []
                    class_all_activities[cls].append(act_id)
                    class_total_hours[cls] = class_total_hours.get(cls, 0) + dur

                    if a.teacher_name not in teacher_all_activities:
                        teacher_all_activities[a.teacher_name] = []
                    teacher_all_activities[a.teacher_name].append(act_id)

                    cs_key = (cls, a.subject)
                    if cs_key not in class_subject_activities:
                        class_subject_activities[cs_key] = []
                    class_subject_activities[cs_key].append((act_id, dur))

                    act_id += 1

                if a.teacher_name and durations:
                    if a.teacher_name not in teacher_activity_groups:
                        teacher_activity_groups[a.teacher_name] = []
                    teacher_activity_groups[a.teacher_name].append(list(durations))

                if len(act_group) > 1:
                    min_days_constraints.append({"subject": a.subject, "act_ids": act_group})
                group_id += 1

        # Dedicated 3APIC Grouping Activities Generation
        if enable_3apic_grouping:
            for i in range(1, self.structure.classes_3_apic + 1):
                cls_name = f"3APIC{i}"
                pc_info = c3_pc_teacher.get(cls_name)
                svt_info = c3_svt_teacher.get(cls_name)

                # Fallback to any assigned PC / SVT teacher if not explicitly mapped
                if not pc_info:
                    all_pc = [a for a in assignments if any(k in (a.subject or "") for k in ["الفيزياء", "الكيمياء", "PC", "pc"])]
                    avail_pc = [a for a in all_pc if actual_teacher_hours.get(a.teacher_name, 0) + 4 <= 24]
                    if avail_pc:
                        t_cand = min(avail_pc, key=lambda a: actual_teacher_hours.get(a.teacher_name, 0))
                        pc_info = (t_cand.teacher_name, t_cand.subject)
                    elif all_pc:
                        t_cand = all_pc[(i - 1) % len(all_pc)]
                        pc_info = (t_cand.teacher_name, t_cand.subject)
                if not svt_info:
                    all_svt = [a for a in assignments if any(k in (a.subject or "") for k in ["علوم الحياة", "SVT", "svt"])]
                    avail_svt = [a for a in all_svt if actual_teacher_hours.get(a.teacher_name, 0) + 4 <= 24]
                    if avail_svt:
                        t_cand = min(avail_svt, key=lambda a: actual_teacher_hours.get(a.teacher_name, 0))
                        svt_info = (t_cand.teacher_name, t_cand.subject)
                    elif all_svt:
                        t_cand = all_svt[(i - 1) % len(all_svt)]
                        svt_info = (t_cand.teacher_name, t_cand.subject)

                if pc_info and svt_info:
                    t_pc, s_pc = pc_info
                    t_svt, s_svt = svt_info

                    # 1. Act 1: PC for G1 (2h - TP block in PC lab)
                    aid_pc_g1 = act_id
                    lines.append('<Activity>')
                    lines.append(f'	<Teacher>{t_pc}</Teacher>')
                    lines.append(f'	<Subject>{s_pc}</Subject>')
                    lines.append(f'	<Students>{cls_name}-G1</Students>')
                    lines.append('	<Duration>2</Duration>')
                    lines.append('	<Total_Duration>4</Total_Duration>')
                    lines.append(f'	<Id>{aid_pc_g1}</Id>')
                    lines.append('	<Activity_Group_Id>0</Activity_Group_Id>')
                    lines.append('	<Active>true</Active>')
                    lines.append(f'	<Comments>{cls_name} - فيزياء فوج 1 (ساعتان بمختبر الفيزياء)</Comments>')
                    lines.append('</Activity>')

                    # 2. Act 2: SVT for G2 (2h - TP block in SVT lab, synchronized with Act 1)
                    aid_svt_g2 = act_id + 1
                    lines.append('<Activity>')
                    lines.append(f'	<Teacher>{t_svt}</Teacher>')
                    lines.append(f'	<Subject>{s_svt}</Subject>')
                    lines.append(f'	<Students>{cls_name}-G2</Students>')
                    lines.append('	<Duration>2</Duration>')
                    lines.append('	<Total_Duration>4</Total_Duration>')
                    lines.append(f'	<Id>{aid_svt_g2}</Id>')
                    lines.append('	<Activity_Group_Id>0</Activity_Group_Id>')
                    lines.append('	<Active>true</Active>')
                    lines.append(f'	<Comments>{cls_name} - علوم فوج 2 (ساعتان بمختبر العلوم)</Comments>')
                    lines.append('</Activity>')

                    # 3. Act 3: PC for G2 (2h - TP block in PC lab, on another day)
                    aid_pc_g2 = act_id + 2
                    lines.append('<Activity>')
                    lines.append(f'	<Teacher>{t_pc}</Teacher>')
                    lines.append(f'	<Subject>{s_pc}</Subject>')
                    lines.append(f'	<Students>{cls_name}-G2</Students>')
                    lines.append('	<Duration>2</Duration>')
                    lines.append('	<Total_Duration>4</Total_Duration>')
                    lines.append(f'	<Id>{aid_pc_g2}</Id>')
                    lines.append('	<Activity_Group_Id>0</Activity_Group_Id>')
                    lines.append('	<Active>true</Active>')
                    lines.append(f'	<Comments>{cls_name} - فيزياء فوج 2 (ساعتان بمختبر الفيزياء)</Comments>')
                    lines.append('</Activity>')

                    # 4. Act 4: SVT for G1 (2h - TP block in SVT lab, synchronized with Act 3)
                    aid_svt_g1 = act_id + 3
                    lines.append('<Activity>')
                    lines.append(f'	<Teacher>{t_svt}</Teacher>')
                    lines.append(f'	<Subject>{s_svt}</Subject>')
                    lines.append(f'	<Students>{cls_name}-G1</Students>')
                    lines.append('	<Duration>2</Duration>')
                    lines.append('	<Total_Duration>4</Total_Duration>')
                    lines.append(f'	<Id>{aid_svt_g1}</Id>')
                    lines.append('	<Activity_Group_Id>0</Activity_Group_Id>')
                    lines.append('	<Active>true</Active>')
                    lines.append(f'	<Comments>{cls_name} - علوم فوج 1 (ساعتان بمختبر العلوم)</Comments>')
                    lines.append('</Activity>')

                    # Record synchronized pair constraints (Duration 2 each)
                    grouping_same_start_constraints.append({
                        "act1": aid_pc_g1, "act2": aid_svt_g2,
                        "comment": f"{cls_name} - تزامن تفويج G1 فيزياء مع G2 علوم (ساعتان)"
                    })
                    grouping_same_start_constraints.append({
                        "act1": aid_pc_g2, "act2": aid_svt_g1,
                        "comment": f"{cls_name} - تزامن تفويج G2 فيزياء مع G1 علوم (ساعتان)"
                    })

                    # Spacing constraints: G1 and G2 for same subject on different days
                    min_days_constraints.append({"subject": s_pc, "act_ids": [aid_pc_g1, aid_pc_g2]})
                    min_days_constraints.append({"subject": s_svt, "act_ids": [aid_svt_g1, aid_svt_g2]})

                    actual_teacher_hours[t_pc] = actual_teacher_hours.get(t_pc, 0) + 4
                    actual_teacher_hours[t_svt] = actual_teacher_hours.get(t_svt, 0) + 4

                    teacher_all_activities.setdefault(t_pc, []).extend([aid_pc_g1, aid_pc_g2])
                    teacher_all_activities.setdefault(t_svt, []).extend([aid_svt_g1, aid_svt_g2])
                    teacher_activity_groups.setdefault(t_pc, []).append([2, 2])
                    teacher_activity_groups.setdefault(t_svt, []).append([2, 2])

                    class_all_activities.setdefault(f"{cls_name}-G1", []).extend([aid_pc_g1, aid_svt_g1])
                    class_all_activities.setdefault(f"{cls_name}-G2", []).extend([aid_pc_g2, aid_svt_g2])
                    class_total_hours[f"{cls_name}-G1"] = class_total_hours.get(f"{cls_name}-G1", 0) + 2
                    class_total_hours[f"{cls_name}-G2"] = class_total_hours.get(f"{cls_name}-G2", 0) + 2

                    act_id += 4

        lines.append('</Activities_List>')
        lines.append('')

        # Buildings
        lines.append('<Buildings_List>')
        lines.append('<Building>')
        lines.append('	<Name>المؤسسة</Name>')
        lines.append('</Building>')
        lines.append('</Buildings_List>')
        lines.append('')

        # Rooms
        lines.append('<Rooms_List>')
        for r in rooms:
            lines.append('<Room>')
            lines.append(f'	<Name>{r.room_name}</Name>')
            lines.append('	<Building>المؤسسة</Building>')
            lines.append(f'	<Capacity>{r.max_capacity_hours}</Capacity>')
            lines.append('</Room>')
        lines.append('</Rooms_List>')
        lines.append('')

        # Constraints Lookup Map: Only consider constraints that are active (or active in override)
        if active_constraints_override is not None:
            active_list = [c for c in active_constraints_override if c.get("is_active", True)]
        else:
            active_list = [c for c in self.all_available_constraints if c.get("is_active", True)]

        c_map = {}
        for c in active_list:
            c_map[c["code"]] = c
            if c.get("id"):
                c_map[c["id"]] = c
            if c.get("code_individual"):
                c_map[c["code_individual"]] = c

        # Time Constraints
        lines.append('<Time_Constraints_List>')
        lines.append('<ConstraintBasicCompulsoryTime>')
        lines.append('	<Weight_Percentage>100</Weight_Percentage>')
        lines.append('	<Active>true</Active>')
        lines.append('	<Comments></Comments>')
        lines.append('</ConstraintBasicCompulsoryTime>')

        # 3APIC Grouping Cross-Synchronized Same-Starting-Time Constraints
        for c_sync in grouping_same_start_constraints:
            lines.append('<ConstraintActivitiesSameStartingTime>')
            lines.append('	<Weight_Percentage>100</Weight_Percentage>')
            lines.append('	<Number_of_Activities>2</Number_of_Activities>')
            lines.append(f'	<Activity_Id>{c_sync["act1"]}</Activity_Id>')
            lines.append(f'	<Activity_Id>{c_sync["act2"]}</Activity_Id>')
            lines.append('	<Active>true</Active>')
            lines.append(f'	<Comments>{c_sync.get("comment", "")}</Comments>')
            lines.append('</ConstraintActivitiesSameStartingTime>')

        # 3APIC Grouping Consecutive Practical Hours
        for c_cons in grouping_consecutive_constraints:
            lines.append('<ConstraintTwoActivitiesConsecutive>')
            lines.append('	<Weight_Percentage>100</Weight_Percentage>')
            lines.append(f'	<First_Activity_Id>{c_cons["first"]}</First_Activity_Id>')
            lines.append(f'	<Second_Activity_Id>{c_cons["second"]}</Second_Activity_Id>')
            lines.append('	<Active>true</Active>')
            lines.append(f'	<Comments>{c_cons.get("comment", "")}</Comments>')
            lines.append('</ConstraintTwoActivitiesConsecutive>')

        # Teacher Max Daily Hours (In 12 half-day FET structure, each half-day has max 4 slots)
        if "ConstraintTeachersMaxHoursDaily" in c_map or "tc_t_8" in c_map:
            c = c_map.get("ConstraintTeachersMaxHoursDaily") or c_map.get("tc_t_8")
            val = c.get("param_val", 6)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                teachers_to_cap = [resolve_teacher(t) for t in selected_targets if resolve_teacher(t)]
            elif overrides:
                teachers_to_cap = sorted(all_teachers_set)
            else:
                teachers_to_cap = []

            if teachers_to_cap:
                for t_name in teachers_to_cap:
                    t_val = int(overrides.get(t_name, val))
                    fet_val = min(4, t_val) if t_val <= 4 else 4
                    lines.append('<ConstraintTeacherMaxHoursDaily>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Teacher_Name>{t_name}</Teacher_Name>')
                    lines.append(f'	<Maximum_Hours_Daily>{fet_val}</Maximum_Hours_Daily>')
                    lines.append('	<Active>true</Active>')
                    lines.append(f'	<Comments>{t_name} - أقصى {t_val} ساعات يومياً</Comments>')
                    lines.append('</ConstraintTeacherMaxHoursDaily>')
                    if t_name in teacher_all_activities and t_val < 8:
                        t_acts = teacher_all_activities[t_name]
                        for rd in ["الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة", "السبت"]:
                            lines.append('<ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')
                            lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                            lines.append(f'	<Number_of_Activities>{len(t_acts)}</Number_of_Activities>')
                            for aid in t_acts:
                                lines.append(f'	<Activity_Id>{aid}</Activity_Id>')
                            lines.append('	<Number_of_Selected_Time_Slots>8</Number_of_Selected_Time_Slots>')
                            for h in ["ح 1", "ح 2", "ح 3", "ح 4"]:
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} ص</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} م</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                            lines.append(f'	<Max_Number_of_Occupied_Time_Slots>{t_val}</Max_Number_of_Occupied_Time_Slots>')
                            lines.append('	<Active>true</Active>')
                            lines.append(f'	<Comments>{t_name} - أقصى {t_val} ساعات تدريس يوم {rd}</Comments>')
                            lines.append('</ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')
            else:
                fet_val = min(4, val) if val <= 4 else 4
                lines.append('<ConstraintTeachersMaxHoursDaily>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Maximum_Hours_Daily>{fet_val}</Maximum_Hours_Daily>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintTeachersMaxHoursDaily>')
                if val < 8:
                    for t_name, t_acts in teacher_all_activities.items():
                        if t_name not in all_teachers_set:
                            continue
                        for rd in ["الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة", "السبت"]:
                            lines.append('<ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')
                            lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                            lines.append(f'	<Number_of_Activities>{len(t_acts)}</Number_of_Activities>')
                            for aid in t_acts:
                                lines.append(f'	<Activity_Id>{aid}</Activity_Id>')
                            lines.append('	<Number_of_Selected_Time_Slots>8</Number_of_Selected_Time_Slots>')
                            for h in ["ح 1", "ح 2", "ح 3", "ح 4"]:
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} ص</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} م</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                            lines.append(f'	<Max_Number_of_Occupied_Time_Slots>{val}</Max_Number_of_Occupied_Time_Slots>')
                            lines.append('	<Active>true</Active>')
                            lines.append(f'	<Comments>{t_name} - أقصى {val} ساعات تدريس يوم {rd}</Comments>')
                            lines.append('</ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')

        # Teacher Min Daily Hours
        if "ConstraintTeachersMinHoursDaily" in c_map or "tc_t_10" in c_map:
            c = c_map.get("ConstraintTeachersMinHoursDaily") or c_map.get("tc_t_10")
            min_h = int(c.get("param_val", 2) or 2)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                teachers_list = [resolve_teacher(t) for t in selected_targets if resolve_teacher(t)]
            else:
                teachers_list = sorted(teacher_activity_groups.keys())

            for t_name in teachers_list:
                t_groups = teacher_activity_groups.get(t_name, [])
                t_min_h = int(overrides.get(t_name, min_h))
                t_total = sum(sum(g) for g in t_groups)
                min_weekly_threshold = 12 if t_min_h >= 2 else t_min_h
                if t_total < min_weekly_threshold:
                    continue
                if not self.can_teacher_satisfy_min_daily_hours(t_groups, t_min_h):
                    continue
                lines.append('<ConstraintTeacherMinHoursDaily>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Teacher_Name>{t_name}</Teacher_Name>')
                lines.append(f'	<Minimum_Hours_Daily>{t_min_h}</Minimum_Hours_Daily>')
                lines.append('	<Allow_Empty_Days>true</Allow_Empty_Days>')
                lines.append('	<Active>true</Active>')
                lines.append(f'	<Comments>{t_name} - نصاب كافٍ وموزع للحصة اليومية الدنيا ({t_min_h} س)</Comments>')
                lines.append('</ConstraintTeacherMinHoursDaily>')

        # Teacher Max Gaps Daily
        if "ConstraintTeachersMaxGapsPerDay" in c_map or "tc_t_6" in c_map or "tc_t_5" in c_map:
            c = c_map.get("ConstraintTeachersMaxGapsPerDay") or c_map.get("tc_t_6") or c_map.get("tc_t_5")
            gaps = c.get("param_val", 0)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                teachers_list = [resolve_teacher(t) for t in selected_targets if resolve_teacher(t)]
                for t_name in teachers_list:
                    t_gaps = int(overrides.get(t_name, gaps))
                    lines.append('<ConstraintTeacherMaxGapsPerDay>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Teacher_Name>{t_name}</Teacher_Name>')
                    lines.append(f'	<Max_Gaps>{t_gaps}</Max_Gaps>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintTeacherMaxGapsPerDay>')
            elif overrides:
                for t_name in sorted(all_teachers_set):
                    t_gaps = int(overrides.get(t_name, gaps))
                    lines.append('<ConstraintTeacherMaxGapsPerDay>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Teacher_Name>{t_name}</Teacher_Name>')
                    lines.append(f'	<Max_Gaps>{t_gaps}</Max_Gaps>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintTeacherMaxGapsPerDay>')
            else:
                lines.append('<ConstraintTeachersMaxGapsPerDay>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Max_Gaps>{gaps}</Max_Gaps>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintTeachersMaxGapsPerDay>')

        # Teacher Max Gaps Weekly
        if "ConstraintTeachersMaxGapsPerWeek" in c_map or "tc_t_4" in c_map or "tc_t_3" in c_map:
            c = c_map.get("ConstraintTeachersMaxGapsPerWeek") or c_map.get("tc_t_4") or c_map.get("tc_t_3")
            gaps = c.get("param_val", 0)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                teachers_list = [resolve_teacher(t) for t in selected_targets if resolve_teacher(t)]
                for t_name in teachers_list:
                    t_gaps = int(overrides.get(t_name, gaps))
                    lines.append('<ConstraintTeacherMaxGapsPerWeek>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Teacher_Name>{t_name}</Teacher_Name>')
                    lines.append(f'	<Max_Gaps>{t_gaps}</Max_Gaps>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintTeacherMaxGapsPerWeek>')
            elif overrides:
                for t_name in sorted(all_teachers_set):
                    t_gaps = int(overrides.get(t_name, gaps))
                    lines.append('<ConstraintTeacherMaxGapsPerWeek>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Teacher_Name>{t_name}</Teacher_Name>')
                    lines.append(f'	<Max_Gaps>{t_gaps}</Max_Gaps>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintTeacherMaxGapsPerWeek>')
            else:
                lines.append('<ConstraintTeachersMaxGapsPerWeek>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Max_Gaps>{gaps}</Max_Gaps>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintTeachersMaxGapsPerWeek>')

        # Teacher Max Days Weekly
        if "ConstraintTeachersMaxDaysPerWeek" in c_map or "tc_t_2" in c_map:
            c = c_map.get("ConstraintTeachersMaxDaysPerWeek") or c_map.get("tc_t_2")
            val = c.get("param_val", 5)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                teachers_list = [resolve_teacher(t) for t in selected_targets if resolve_teacher(t)]
            elif overrides:
                teachers_list = sorted(all_teachers_set)
            else:
                teachers_list = []

            if teachers_list:
                for t_name in teachers_list:
                    t_val = int(overrides.get(t_name, val))
                    t_days = t_val * 2 if t_val <= 6 else t_val
                    t_hours = actual_teacher_hours.get(t_name, 0)
                    min_needed = math.ceil(t_hours / 4)
                    safe_days = max(t_days, min_needed)
                    if safe_days < 12:
                        lines.append('<ConstraintTeacherMaxDaysPerWeek>')
                        lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                        lines.append(f'	<Teacher_Name>{t_name}</Teacher_Name>')
                        lines.append(f'	<Max_Days_Per_Week>{safe_days}</Max_Days_Per_Week>')
                        lines.append('	<Active>true</Active>')
                        lines.append(f'	<Comments>{t_name} - أقصى {safe_days // 2} أيام عمل</Comments>')
                        lines.append('</ConstraintTeacherMaxDaysPerWeek>')
            else:
                fet_days = val * 2 if val <= 6 else val
                if fet_days * 4 >= 24:
                    lines.append('<ConstraintTeachersMaxDaysPerWeek>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Max_Days_Per_Week>{fet_days}</Max_Days_Per_Week>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintTeachersMaxDaysPerWeek>')

        # Teacher Max Continuous Hours
        if "ConstraintTeachersMaxHoursContinuously" in c_map or "ConstraintTeachersMaxContinuousHours" in c_map or "tc_t_12" in c_map or "tc_t_11" in c_map:
            c = c_map.get("ConstraintTeachersMaxHoursContinuously") or c_map.get("ConstraintTeachersMaxContinuousHours") or c_map.get("tc_t_12") or c_map.get("tc_t_11")
            cont_h = c.get("param_val", 4)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                teachers_list = [resolve_teacher(t) for t in selected_targets if resolve_teacher(t)]
                for t_name in teachers_list:
                    t_cont = int(overrides.get(t_name, cont_h))
                    lines.append('<ConstraintTeacherMaxHoursContinuously>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Teacher_Name>{t_name}</Teacher_Name>')
                    lines.append(f'	<Maximum_Hours_Continuously>{t_cont}</Maximum_Hours_Continuously>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintTeacherMaxHoursContinuously>')
            elif overrides:
                for t_name in sorted(all_teachers_set):
                    t_cont = int(overrides.get(t_name, cont_h))
                    lines.append('<ConstraintTeacherMaxHoursContinuously>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Teacher_Name>{t_name}</Teacher_Name>')
                    lines.append(f'	<Maximum_Hours_Continuously>{t_cont}</Maximum_Hours_Continuously>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintTeacherMaxHoursContinuously>')
            else:
                lines.append('<ConstraintTeachersMaxHoursContinuously>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Maximum_Hours_Continuously>{cont_h}</Maximum_Hours_Continuously>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintTeachersMaxHoursContinuously>')

        # Teacher Early Max Beginnings at Second Hour
        if "ConstraintTeachersEarlyMaxBeginningsAtSecondHour" in c_map:
            c = c_map["ConstraintTeachersEarlyMaxBeginningsAtSecondHour"]
            w = int(c.get("def_weight", 100))
            max_sec = c.get("param_val", 0)
            lines.append('<ConstraintTeachersAfternoonsEarlyMaxBeginningsAtSecondHour>')
            lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
            lines.append(f'	<Max_Beginnings_At_Second_Hour>{max_sec}</Max_Beginnings_At_Second_Hour>')
            lines.append('	<Active>true</Active>')
            lines.append('	<Comments></Comments>')
            lines.append('</ConstraintTeachersAfternoonsEarlyMaxBeginningsAtSecondHour>')

        # Teacher Max Morning Periods / Half-Days (أقصى الفترات صباحاً للأساتذة)
        # Enforces that teachers work at most N morning half-days across the 6 Moroccan morning half-days
        morning_keys_all = [
            "ConstraintTeachersIntervalMaxDaysPerWeek",
            "ConstraintTeachersMaxMorningsPerWeek",
            "ConstraintTeachersOccupyMaxSetsOfTimeSlotsFromSelection",
            "tc_t_14",
            "max_mornings"
        ]
        morning_keys_indiv = [
            "ConstraintTeacherIntervalMaxDaysPerWeek",
            "ConstraintTeacherMaxMorningsPerWeek",
            "ConstraintTeacherOccupiesMaxSetsOfTimeSlotsFromSelection",
            "tc_t_13"
        ]

        c_indiv = None
        for k in morning_keys_indiv:
            if k in c_map and c_map[k].get("is_active", True):
                c_indiv = c_map[k]
                break

        c_all = None
        for k in morning_keys_all:
            if k in c_map and c_map[k].get("is_active", True):
                c_all = c_map[k]
                break

        morning_half_days = [d for d in days_names if "ص" in d] or ["الاثنين ص", "الثلاثاء ص", "الاربعاء ص", "الخميس ص", "الجمعة ص", "السبت ص"]
        morning_slot_hours = hours_names or ["ح 1", "ح 2", "ح 3", "ح 4"]
        individual_covered_teachers = set()

        if c_indiv and c_indiv.get("selected_targets"):
            val_indiv = int(c_indiv.get("param_val", 4))
            w_indiv = int(c_indiv.get("def_weight", 100))
            for t_raw in c_indiv["selected_targets"]:
                t_name = resolve_teacher(t_raw)
                if not t_name:
                    continue
                t_hours = actual_teacher_hours.get(t_name, 0)
                min_mornings = max(1, math.ceil(max(0, t_hours - 16) / 4)) if t_hours > 0 else 1
                safe_val = min(6, max(val_indiv, min_mornings))

                lines.append('<ConstraintTeacherOccupiesMaxSetsOfTimeSlotsFromSelection>')
                lines.append(f'	<Weight_Percentage>{w_indiv}</Weight_Percentage>')
                lines.append(f'	<Teacher>{t_name}</Teacher>')
                lines.append(f'	<Maximum_Number_of_Occupied_Sets>{safe_val}</Maximum_Number_of_Occupied_Sets>')
                lines.append(f'	<Number_of_Selected_Sets_of_Time_Slots>{len(morning_half_days)}</Number_of_Selected_Sets_of_Time_Slots>')
                for md in morning_half_days:
                    lines.append('	<Selected_Set_of_Time_Slots>')
                    lines.append(f'		<Number_of_Selected_Time_Slots>{len(morning_slot_hours)}</Number_of_Selected_Time_Slots>')
                    for h in morning_slot_hours:
                        lines.append('		<Selected_Time_Slot>')
                        lines.append(f'			<Day>{md}</Day>')
                        lines.append(f'			<Hour>{h}</Hour>')
                        lines.append('		</Selected_Time_Slot>')
                    lines.append('	</Selected_Set_of_Time_Slots>')
                lines.append('	<Active>true</Active>')
                lines.append(f'	<Comments>أقصى {safe_val} فترات صباحا للأستاذ {t_name}</Comments>')
                lines.append('</ConstraintTeacherOccupiesMaxSetsOfTimeSlotsFromSelection>')
                individual_covered_teachers.add(t_name)

        if c_all:
            val_raw = c_all.get("param_val")
            if val_raw is None:
                val_raw = getattr(self.institution, "max_morning_half_days_per_teacher", 4) or 4
            val_all = int(val_raw)
            w_all = int(c_all.get("def_weight", 100))
            overrides = c_all.get("target_overrides", {})

            if c_all.get("applies_to") == "selected" and c_all.get("selected_targets"):
                for t_raw in c_all["selected_targets"]:
                    t_name = resolve_teacher(t_raw)
                    if not t_name or t_name in individual_covered_teachers:
                        continue
                    t_hours = actual_teacher_hours.get(t_name, 0)
                    min_mornings = max(1, math.ceil(max(0, t_hours - 16) / 4)) if t_hours > 0 else 1
                    t_val = int(overrides.get(t_name, overrides.get(t_raw, val_all)))
                    safe_val = min(6, max(t_val, min_mornings))

                    lines.append('<ConstraintTeacherOccupiesMaxSetsOfTimeSlotsFromSelection>')
                    lines.append(f'	<Weight_Percentage>{w_all}</Weight_Percentage>')
                    lines.append(f'	<Teacher>{t_name}</Teacher>')
                    lines.append(f'	<Maximum_Number_of_Occupied_Sets>{safe_val}</Maximum_Number_of_Occupied_Sets>')
                    lines.append(f'	<Number_of_Selected_Sets_of_Time_Slots>{len(morning_half_days)}</Number_of_Selected_Sets_of_Time_Slots>')
                    for md in morning_half_days:
                        lines.append('	<Selected_Set_of_Time_Slots>')
                        lines.append(f'		<Number_of_Selected_Time_Slots>{len(morning_slot_hours)}</Number_of_Selected_Time_Slots>')
                        for h in morning_slot_hours:
                            lines.append('		<Selected_Time_Slot>')
                            lines.append(f'			<Day>{md}</Day>')
                            lines.append(f'			<Hour>{h}</Hour>')
                            lines.append('		</Selected_Time_Slot>')
                        lines.append('	</Selected_Set_of_Time_Slots>')
                    lines.append('	<Active>true</Active>')
                    lines.append(f'	<Comments>أقصى {safe_val} فترات صباحا للأستاذ {t_name}</Comments>')
                    lines.append('</ConstraintTeacherOccupiesMaxSetsOfTimeSlotsFromSelection>')
            else:
                for t_name in sorted(all_teachers_set):
                    if t_name in individual_covered_teachers:
                        continue
                    t_hours = actual_teacher_hours.get(t_name, 0)
                    min_mornings = max(1, math.ceil(max(0, t_hours - 16) / 4)) if t_hours > 0 else 1
                    t_val = int(overrides.get(t_name, val_all))
                    safe_val = min(6, max(t_val, min_mornings))

                    lines.append('<ConstraintTeacherOccupiesMaxSetsOfTimeSlotsFromSelection>')
                    lines.append(f'	<Weight_Percentage>{w_all}</Weight_Percentage>')
                    lines.append(f'	<Teacher>{t_name}</Teacher>')
                    lines.append(f'	<Maximum_Number_of_Occupied_Sets>{safe_val}</Maximum_Number_of_Occupied_Sets>')
                    lines.append(f'	<Number_of_Selected_Sets_of_Time_Slots>{len(morning_half_days)}</Number_of_Selected_Sets_of_Time_Slots>')
                    for md in morning_half_days:
                        lines.append('	<Selected_Set_of_Time_Slots>')
                        lines.append(f'		<Number_of_Selected_Time_Slots>{len(morning_slot_hours)}</Number_of_Selected_Time_Slots>')
                        for h in morning_slot_hours:
                            lines.append('		<Selected_Time_Slot>')
                            lines.append(f'			<Day>{md}</Day>')
                            lines.append(f'			<Hour>{h}</Hour>')
                            lines.append('		</Selected_Time_Slot>')
                        lines.append('	</Selected_Set_of_Time_Slots>')
                    lines.append('	<Active>true</Active>')
                    lines.append(f'	<Comments>الحد الأقصى للفترات الصباحية ({safe_val} فترات) للأستاذ {t_name}</Comments>')
                    lines.append('</ConstraintTeacherOccupiesMaxSetsOfTimeSlotsFromSelection>')

        # Students Max Daily Hours (In 12 half-day FET structure, each half-day has max 4 slots)
        if "ConstraintStudentsMaxHoursDaily" in c_map or "ConstraintStudentsSetMaxHoursDaily" in c_map or "tc_s_7" in c_map or "tc_s_6" in c_map:
            c = c_map.get("ConstraintStudentsMaxHoursDaily") or c_map.get("ConstraintStudentsSetMaxHoursDaily") or c_map.get("tc_s_7") or c_map.get("tc_s_6")
            val = c.get("param_val", 6)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                classes_list = [resolve_class(cls_raw) for cls_raw in selected_targets if resolve_class(cls_raw)]
            elif overrides:
                classes_list = sorted(valid_classes_set)
            else:
                classes_list = []

            if classes_list:
                for cls in classes_list:
                    cls_val = int(overrides.get(cls, val))
                    fet_val = min(4, cls_val) if cls_val <= 4 else 4
                    lines.append('<ConstraintStudentsSetMaxHoursDaily>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Students>{cls}</Students>')
                    lines.append(f'	<Maximum_Hours_Daily>{fet_val}</Maximum_Hours_Daily>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintStudentsSetMaxHoursDaily>')
                    if cls in class_all_activities and cls_val < 8:
                        c_acts = class_all_activities[cls]
                        cls_hours = class_total_hours.get(cls, 0)
                        eff_val = cls_val
                        if cls_hours > 32 and cls_val < 7:
                            eff_val = 7
                        for rd in ["الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة", "السبت"]:
                            lines.append('<ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')
                            lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                            lines.append(f'	<Number_of_Activities>{len(c_acts)}</Number_of_Activities>')
                            for aid in c_acts:
                                lines.append(f'	<Activity_Id>{aid}</Activity_Id>')
                            lines.append('	<Number_of_Selected_Time_Slots>8</Number_of_Selected_Time_Slots>')
                            for h in ["ح 1", "ح 2", "ح 3", "ح 4"]:
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} ص</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} م</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                            lines.append(f'	<Max_Number_of_Occupied_Time_Slots>{eff_val}</Max_Number_of_Occupied_Time_Slots>')
                            lines.append('	<Active>true</Active>')
                            lines.append(f'	<Comments>{cls} - أقصى {eff_val} ساعات دراسة يوم {rd}</Comments>')
                            lines.append('</ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')
            else:
                fet_val = min(4, val) if val <= 4 else 4
                lines.append('<ConstraintStudentsMaxHoursDaily>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Maximum_Hours_Daily>{fet_val}</Maximum_Hours_Daily>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintStudentsMaxHoursDaily>')
                if val < 8:
                    for cls, c_acts in class_all_activities.items():
                        if cls not in valid_classes_set:
                            continue
                        cls_hours = class_total_hours.get(cls, 0)
                        cls_val = val
                        if cls_hours > 32 and val < 7:
                            cls_val = 7
                        for rd in ["الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة", "السبت"]:
                            lines.append('<ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')
                            lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                            lines.append(f'	<Number_of_Activities>{len(c_acts)}</Number_of_Activities>')
                            for aid in c_acts:
                                lines.append(f'	<Activity_Id>{aid}</Activity_Id>')
                            lines.append('	<Number_of_Selected_Time_Slots>8</Number_of_Selected_Time_Slots>')
                            for h in ["ح 1", "ح 2", "ح 3", "ح 4"]:
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} ص</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} م</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                            lines.append(f'	<Max_Number_of_Occupied_Time_Slots>{cls_val}</Max_Number_of_Occupied_Time_Slots>')
                            lines.append('	<Active>true</Active>')
                            lines.append(f'	<Comments>{cls} - أقصى {cls_val} ساعات دراسة يوم {rd}</Comments>')
                            lines.append('</ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')

        # Students Min Daily Hours
        if "ConstraintStudentsMinHoursDaily" in c_map or "tc_s_9" in c_map:
            c = c_map.get("ConstraintStudentsMinHoursDaily") or c_map.get("tc_s_9")
            min_h = c.get("param_val", 2)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                classes_list = [resolve_class(cls_raw) for cls_raw in selected_targets if resolve_class(cls_raw)]
            elif overrides:
                classes_list = sorted(valid_classes_set)
            else:
                classes_list = []

            if classes_list:
                for cls in classes_list:
                    cls_min_h = int(overrides.get(cls, min_h))
                    lines.append('<ConstraintStudentsSetMinHoursDaily>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Students>{cls}</Students>')
                    lines.append(f'	<Minimum_Hours_Daily>{cls_min_h}</Minimum_Hours_Daily>')
                    lines.append('	<Allow_Empty_Days>true</Allow_Empty_Days>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintStudentsSetMinHoursDaily>')
            else:
                lines.append('<ConstraintStudentsMinHoursDaily>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Minimum_Hours_Daily>{min_h}</Minimum_Hours_Daily>')
                lines.append('	<Allow_Empty_Days>true</Allow_Empty_Days>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintStudentsMinHoursDaily>')

        # Students Max Gaps Daily
        if "ConstraintStudentsMaxGapsPerDay" in c_map or "ConstraintStudentsSetMaxGapsPerDay" in c_map or "tc_s_2" in c_map:
            c = c_map.get("ConstraintStudentsMaxGapsPerDay") or c_map.get("ConstraintStudentsSetMaxGapsPerDay") or c_map.get("tc_s_2")
            gaps = c.get("param_val", 0)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                classes_list = [resolve_class(cls_raw) for cls_raw in selected_targets if resolve_class(cls_raw)]
            elif overrides:
                classes_list = sorted(valid_classes_set)
            else:
                classes_list = []

            if classes_list:
                for cls in classes_list:
                    cls_gaps = int(overrides.get(cls, gaps))
                    lines.append('<ConstraintStudentsSetMaxGapsPerDay>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Students>{cls}</Students>')
                    lines.append(f'	<Max_Gaps>{cls_gaps}</Max_Gaps>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintStudentsSetMaxGapsPerDay>')
            else:
                lines.append('<ConstraintStudentsMaxGapsPerDay>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Max_Gaps>{gaps}</Max_Gaps>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintStudentsMaxGapsPerDay>')

        # Students Max Gaps Weekly
        if "ConstraintStudentsMaxGapsPerWeek" in c_map or "ConstraintStudentsSetMaxGapsPerWeek" in c_map or "tc_s_3" in c_map:
            c = c_map.get("ConstraintStudentsMaxGapsPerWeek") or c_map.get("ConstraintStudentsSetMaxGapsPerWeek") or c_map.get("tc_s_3")
            gaps = c.get("param_val", 0)
            w = int(c.get("def_weight", 100))
            overrides = c.get("target_overrides", {})
            applies_to = c.get("applies_to", "all")
            selected_targets = c.get("selected_targets", [])

            if applies_to == "selected" and selected_targets:
                classes_list = [resolve_class(cls_raw) for cls_raw in selected_targets if resolve_class(cls_raw)]
            elif overrides:
                classes_list = sorted(valid_classes_set)
            else:
                classes_list = []

            if classes_list:
                for cls in classes_list:
                    cls_gaps = int(overrides.get(cls, gaps))
                    lines.append('<ConstraintStudentsSetMaxGapsPerWeek>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Max_Gaps>{cls_gaps}</Max_Gaps>')
                    lines.append(f'	<Students>{cls}</Students>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintStudentsSetMaxGapsPerWeek>')
            else:
                lines.append('<ConstraintStudentsMaxGapsPerWeek>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Max_Gaps>{gaps}</Max_Gaps>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintStudentsMaxGapsPerWeek>')

        # Students Max Days Weekly (In 12 half-day structure, students study ~32 hours)
        if "ConstraintStudentsMaxDaysPerWeek" in c_map:
            c = c_map["ConstraintStudentsMaxDaysPerWeek"]
            val = c.get("param_val", 6)
            fet_days = val * 2 if val <= 6 else val
            if fet_days * 4 >= 32:
                lines.append('<ConstraintStudentsMaxDaysPerWeek>')
                lines.append(f'	<Weight_Percentage>{int(c["def_weight"])}</Weight_Percentage>')
                lines.append(f'	<Max_Days_Per_Week>{fet_days}</Max_Days_Per_Week>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintStudentsMaxDaysPerWeek>')

        # Students Max Continuous Hours
        if "ConstraintStudentsMaxHoursContinuously" in c_map or "ConstraintStudentsMaxContinuousHours" in c_map or "tc_s_11" in c_map or "tc_s_10" in c_map:
            c = c_map.get("ConstraintStudentsMaxHoursContinuously") or c_map.get("ConstraintStudentsMaxContinuousHours") or c_map.get("tc_s_11") or c_map.get("tc_s_10")
            cont_h = c.get("param_val", 4)
            w = int(c.get("def_weight", 100))
            if c.get("applies_to") == "selected" and c.get("selected_targets"):
                for cls_raw in c["selected_targets"]:
                    cls = resolve_class(cls_raw)
                    if not cls:
                        continue
                    lines.append('<ConstraintStudentsSetMaxHoursContinuously>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Students>{cls}</Students>')
                    lines.append(f'	<Maximum_Hours_Continuously>{cont_h}</Maximum_Hours_Continuously>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintStudentsSetMaxHoursContinuously>')
            else:
                lines.append('<ConstraintStudentsMaxHoursContinuously>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Maximum_Hours_Continuously>{cont_h}</Maximum_Hours_Continuously>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintStudentsMaxHoursContinuously>')

        # Students Early Max Beginnings at Second Hour
        if "ConstraintStudentsEarlyMaxBeginningsAtSecondHour" in c_map:
            c = c_map["ConstraintStudentsEarlyMaxBeginningsAtSecondHour"]
            w = int(c.get("def_weight", 100))
            max_sec = c.get("param_val", 0)
            if c.get("applies_to") == "selected" and c.get("selected_targets"):
                for cls_raw in c["selected_targets"]:
                    cls = resolve_class(cls_raw)
                    if not cls:
                        continue
                    lines.append('<ConstraintStudentsSetEarlyMaxBeginningsAtSecondHour>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Students>{cls}</Students>')
                    lines.append(f'	<Max_Beginnings_At_Second_Hour>{max_sec}</Max_Beginnings_At_Second_Hour>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintStudentsSetEarlyMaxBeginningsAtSecondHour>')
            else:
                lines.append('<ConstraintStudentsEarlyMaxBeginningsAtSecondHour>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Max_Beginnings_At_Second_Hour>{max_sec}</Max_Beginnings_At_Second_Hour>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintStudentsEarlyMaxBeginningsAtSecondHour>')

        # Activities Min/Max Days (Subject-specific custom spacing and Note 43 compliance)
        if "ConstraintMinDaysBetweenActivities" in c_map:
            subj_cfg_list = self.get_subject_activity_constraints()
            subj_cfg_map = {item["subject"]: item for item in subj_cfg_list}
            
            c_min_days = c_map["ConstraintMinDaysBetweenActivities"]
            global_min_d = int(c_min_days.get("param_val", 1))
            global_w = int(c_min_days.get("def_weight", 100))

            for item in min_days_constraints:
                act_ids = item["act_ids"]
                s_name = item.get("subject", "")
                
                cfg = None
                for k, v in subj_cfg_map.items():
                    if k == s_name or (k in s_name) or (s_name in k):
                        cfg = v
                        break

                min_d = int(cfg.get("min_days", global_min_d)) if (cfg and cfg.get("min_days")) else global_min_d
                w = int(cfg.get("weight", global_w)) if (cfg and "weight" in cfg) else global_w
                # Consecutive_If_Same_Day is strictly false to prevent repeating sessions on the same day!
                consec = "true" if (cfg and cfg.get("consecutive_if_same_day", False)) else "false"

                is_c_active = "true" if (cfg is None or cfg.get("is_active", True)) else "false"

                lines.append('<ConstraintMinDaysBetweenActivities>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Consecutive_If_Same_Day>{consec}</Consecutive_If_Same_Day>')
                lines.append(f'	<Number_of_Activities>{len(act_ids)}</Number_of_Activities>')
                for aid in act_ids:
                    lines.append(f'	<Activity_Id>{aid}</Activity_Id>')
                lines.append(f'	<MinDays>{min_d}</MinDays>')
                lines.append(f'	<Active>{is_c_active}</Active>')
                lines.append(f'	<Comments>{s_name} - تباعد {min_d} يوم</Comments>')
                lines.append('</ConstraintMinDaysBetweenActivities>')


                # Optional Max Days spacing per subject
                if cfg and cfg.get("max_days") and int(cfg["max_days"]) >= min_d:
                    max_d = int(cfg["max_days"])
                    lines.append('<ConstraintMaxDaysBetweenActivities>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Consecutive_If_Same_Day>false</Consecutive_If_Same_Day>')
                    lines.append(f'	<Number_of_Activities>{len(act_ids)}</Number_of_Activities>')
                    for aid in act_ids:
                        lines.append(f'	<Activity_Id>{aid}</Activity_Id>')
                    lines.append(f'	<MaxDays>{max_d}</MaxDays>')
                    lines.append(f'	<Active>{is_c_active}</Active>')
                    lines.append(f'	<Comments>{s_name} - أقصى تباعد {max_d} أيام</Comments>')
                    lines.append('</ConstraintMaxDaysBetweenActivities>')

            # Strict Moroccan Real-Day Non-Repetition: Prevent having 1 session in morning and 1 session in afternoon on the same real day
            # Applies to ALL classes and ALL subjects with >= 2 activities across all institutions
            all_real_days = ["الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة", "السبت"]
            for (cls_k, s_k), act_info_list in class_subject_activities.items():
                if len(act_info_list) > 1:
                    cfg_s = None
                    for k, v in subj_cfg_map.items():
                        if k == s_k or (k in s_k) or (s_k in k):
                            cfg_s = v
                            break
                    if cfg_s and not cfg_s.get("is_active", True):
                        continue
                    w_s = int(cfg_s.get("weight", global_w)) if (cfg_s and "weight" in cfg_s) else global_w
                    max_dur = max(d for _, d in act_info_list)
                    for rd in all_real_days:
                        lines.append('<ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')
                        lines.append(f'	<Weight_Percentage>{w_s}</Weight_Percentage>')
                        lines.append(f'	<Number_of_Activities>{len(act_info_list)}</Number_of_Activities>')
                        for aid, _ in act_info_list:
                            lines.append(f'	<Activity_Id>{aid}</Activity_Id>')
                        lines.append('	<Number_of_Selected_Time_Slots>8</Number_of_Selected_Time_Slots>')
                        for h in ["ح 1", "ح 2", "ح 3", "ح 4"]:
                            lines.append('	<Selected_Time_Slot>')
                            lines.append(f'		<Day>{rd} ص</Day>')
                            lines.append(f'		<Hour>{h}</Hour>')
                            lines.append('	</Selected_Time_Slot>')
                            lines.append('	<Selected_Time_Slot>')
                            lines.append(f'		<Day>{rd} م</Day>')
                            lines.append(f'		<Hour>{h}</Hour>')
                            lines.append('	</Selected_Time_Slot>')
                        lines.append(f'	<Max_Number_of_Occupied_Time_Slots>{max_dur}</Max_Number_of_Occupied_Time_Slots>')
                        lines.append('	<Active>true</Active>')
                        lines.append(f'	<Comments>{cls_k} - {s_k} - منع التكرار يوم {rd}</Comments>')
                        lines.append('</ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')

                    # If subject has multiple 1-hour sessions alongside a 2-hour session (e.g. 2+1+1),
                    # prevent the two 1-hour sessions from landing on the same day as well
                    single_hour_acts = [aid for aid, d in act_info_list if d == 1]
                    if len(single_hour_acts) > 1 and max_dur > 1:
                        for rd in all_real_days:
                            lines.append('<ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')
                            lines.append(f'	<Weight_Percentage>{w_s}</Weight_Percentage>')
                            lines.append(f'	<Number_of_Activities>{len(single_hour_acts)}</Number_of_Activities>')
                            for aid in single_hour_acts:
                                lines.append(f'	<Activity_Id>{aid}</Activity_Id>')
                            lines.append('	<Number_of_Selected_Time_Slots>8</Number_of_Selected_Time_Slots>')
                            for h in ["ح 1", "ح 2", "ح 3", "ح 4"]:
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} ص</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                                lines.append('	<Selected_Time_Slot>')
                                lines.append(f'		<Day>{rd} م</Day>')
                                lines.append(f'		<Hour>{h}</Hour>')
                                lines.append('	</Selected_Time_Slot>')
                            lines.append('	<Max_Number_of_Occupied_Time_Slots>1</Max_Number_of_Occupied_Time_Slots>')
                            lines.append('	<Active>true</Active>')
                            lines.append(f'	<Comments>{cls_k} - {s_k} - منع تكرار الحصص الفردية يوم {rd}</Comments>')
                            lines.append('</ConstraintActivitiesOccupyMaxTimeSlotsFromSelection>')

        # Break Times Constraint
        if "ConstraintBreakTimes" in c_map:
            c = c_map["ConstraintBreakTimes"]
            break_slots = self.institution.break_time_slots or []
            normalized_breaks = []
            for s in break_slots:
                d_norm = s.get("day", "").replace("الأربعاء", "الاربعاء").replace("الإثنين", "الاثنين")
                h_norm = s.get("hour", "")
                if d_norm and h_norm:
                    normalized_breaks.append({"day": d_norm, "hour": h_norm})
            if normalized_breaks:
                lines.append('<ConstraintBreakTimes>')
                lines.append(f'	<Weight_Percentage>{int(c.get("def_weight", 100))}</Weight_Percentage>')
                lines.append(f'	<Number_of_Break_Times>{len(normalized_breaks)}</Number_of_Break_Times>')
                for slot in normalized_breaks:
                    lines.append('	<Break_Time>')
                    lines.append(f'		<Day>{slot["day"]}</Day>')
                    lines.append(f'		<Hour>{slot["hour"]}</Hour>')
                    lines.append('	</Break_Time>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintBreakTimes>')
        # Activity Preferred Starting Times (Strictly forbid Afternoon 1st slot for Physical Education / selected subjects)
        m_days = ["الاثنين ص", "الثلاثاء ص", "الاربعاء ص", "الخميس ص", "الجمعة ص", "السبت ص"]
        all_e_days = ["الاثنين م", "الثلاثاء م", "الاربعاء م", "الخميس م", "الجمعة م"]
        break_days_set = set(s.get("day", "").replace("الأربعاء", "الاربعاء").replace("الإثنين", "الاثنين") for s in (self.institution.break_time_slots or []))
        e_days = [d for d in all_e_days if d not in break_days_set]

        for item in forbid_first_pm_activities:
            aid = item["act_id"]
            dur = item["dur"]
            w = item["weight"]
            s_name = item.get("subject", "")

            pref_times = []
            if dur == 2:
                for d in m_days:
                    pref_times.append((d, "ح 1"))
                    pref_times.append((d, "ح 2"))
                    pref_times.append((d, "ح 3"))
                for d in e_days:
                    pref_times.append((d, "ح 2"))
                    pref_times.append((d, "ح 3"))
            elif dur == 1:
                for d in m_days:
                    for h in ["ح 1", "ح 2", "ح 3", "ح 4"]:
                        pref_times.append((d, h))
                for d in e_days:
                    for h in ["ح 2", "ح 3", "ح 4"]:
                        pref_times.append((d, h))
            else:
                for d in m_days:
                    pref_times.append((d, "ح 1"))
                    pref_times.append((d, "ح 2"))
                for d in e_days:
                    pref_times.append((d, "ح 2"))

            if pref_times:
                lines.append('<ConstraintActivityPreferredStartingTimes>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Activity_Id>{aid}</Activity_Id>')
                lines.append(f'	<Number_of_Preferred_Starting_Times>{len(pref_times)}</Number_of_Preferred_Starting_Times>')
                for (d, h) in pref_times:
                    lines.append('	<Preferred_Starting_Time>')
                    lines.append(f'		<Preferred_Starting_Day>{d}</Preferred_Starting_Day>')
                    lines.append(f'		<Preferred_Starting_Hour>{h}</Preferred_Starting_Hour>')
                    lines.append('	</Preferred_Starting_Time>')
                lines.append('	<Active>true</Active>')
                lines.append(f'	<Comments>{s_name} - منع التوطين في الحصة الأولى مساء (14:30)</Comments>')
                lines.append('</ConstraintActivityPreferredStartingTimes>')

        lines.append('</Time_Constraints_List>')
        lines.append('')

        # Space Constraints - Optimized for Fast Generation & Complete Assignment
        lines.append('<Space_Constraints_List>')
        lines.append('<ConstraintBasicCompulsorySpace>')
        lines.append('	<Weight_Percentage>100</Weight_Percentage>')
        lines.append('	<Active>true</Active>')
        lines.append('	<Comments></Comments>')
        lines.append('</ConstraintBasicCompulsorySpace>')

        # Home Rooms for Teachers - Capacity-aware
        if "ConstraintTeacherHomeRoom" in c_map and not self.institution.float_all_general_teachers:
            c = c_map["ConstraintTeacherHomeRoom"]
            w = int(c.get("def_weight", 100))
            seen_teachers = set()
            room_assigned_hours = {r.room_name: 0 for r in rooms}
            teacher_hours_map = actual_teacher_hours
            teacher_subj_map = {resolve_teacher(a.teacher_name): a.subject for a in assignments if a.teacher_name}

            for r in rooms:
                if r.room_name not in valid_room_names:
                    continue
                # If custom room, verify teacher belongs to room's assigned_subject
                is_custom = getattr(r, 'is_custom', False) or r.room_type == "قاعة مخصصة"
                expected_subj = r.assigned_subject if (is_custom and r.assigned_subject != "عامة") else None

                # 1. Primary (Morning) Teacher Anchor
                if r.morning_teacher and "-" not in r.morning_teacher and "شاغر" not in r.morning_teacher:
                    m_teacher = resolve_teacher(r.morning_teacher)
                    if m_teacher and m_teacher in all_teachers_set and m_teacher not in seen_teachers:
                        m_h = teacher_hours_map.get(m_teacher, 20)
                        if m_h <= 40:
                            seen_teachers.add(m_teacher)
                            room_assigned_hours[r.room_name] += m_h
                            lines.append('<ConstraintTeacherHomeRoom>')
                            lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                            lines.append(f'	<Teacher>{m_teacher}</Teacher>')
                            lines.append(f'	<Room>{r.room_name}</Room>')
                            lines.append('	<Active>true</Active>')
                            lines.append('	<Comments>تثبيت صباحي</Comments>')
                            lines.append('</ConstraintTeacherHomeRoom>')

                # 2. Secondary (Afternoon) Teacher - only if within room 40h capacity
                if r.afternoon_teacher and "-" not in r.afternoon_teacher and "شاغر" not in r.afternoon_teacher:
                    e_teacher = resolve_teacher(r.afternoon_teacher)
                    if e_teacher and e_teacher in all_teachers_set and e_teacher not in seen_teachers:
                        e_h = teacher_hours_map.get(e_teacher, 20)
                        if room_assigned_hours[r.room_name] + e_h <= 40:
                            seen_teachers.add(e_teacher)
                            has_primary = (room_assigned_hours[r.room_name] > 0)
                            sec_w = min(w, 85) if has_primary else w
                            room_assigned_hours[r.room_name] += e_h
                            lines.append('<ConstraintTeacherHomeRoom>')
                            lines.append(f'	<Weight_Percentage>{sec_w}</Weight_Percentage>')
                            lines.append(f'	<Teacher>{e_teacher}</Teacher>')
                            lines.append(f'	<Room>{r.room_name}</Room>')
                            lines.append('	<Active>true</Active>')
                            lines.append('	<Comments>تثبيت مسائي</Comments>')
                            lines.append('</ConstraintTeacherHomeRoom>')
        elif self.institution.float_all_general_teachers:
            lines.append('<!-- تم تفعيل التعويم الشامل لجميع أساتذة التعليم العام -->')

        # Subject Preferred Rooms - Specialty Labs / Sports / Dedicated Custom Rooms
        if "ConstraintSubjectPreferredRooms" in c_map:
            c = c_map["ConstraintSubjectPreferredRooms"]
            w = int(c["def_weight"])
            specialty_subj_names = ["علوم الحياة و الأرض", "علوم الحياة والأرض", "الكيمياء و الفيزياء", "الفيزياء والكيمياء", "المعلوميات", "التربية البدنية"]
            for crt in self.institution.custom_room_types:
                c_subj = crt.get("subject")
                if c_subj and c_subj not in specialty_subj_names:
                    specialty_subj_names.append(c_subj)

            subj_rooms_map = {}
            for r in rooms:
                subj = r.assigned_subject
                if subj in specialty_subj_names:
                    if subj not in subj_rooms_map:
                        subj_rooms_map[subj] = []
                    if r.room_name in valid_room_names and r.room_name not in subj_rooms_map[subj]:
                        subj_rooms_map[subj].append(r.room_name)

            for subj, pref_rooms in subj_rooms_map.items():
                if pref_rooms and subj in valid_subjects:
                    lines.append('<ConstraintSubjectPreferredRooms>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Subject>{subj}</Subject>')
                    lines.append(f'	<Number_of_Preferred_Rooms>{len(pref_rooms)}</Number_of_Preferred_Rooms>')
                    for pr in pref_rooms:
                        lines.append(f'	<Preferred_Room>{pr}</Preferred_Room>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintSubjectPreferredRooms>')

        # Teacher Max Building Changes Per Day (Space Constraint)
        if "ConstraintTeacherMaxBuildingChangesPerDay" in c_map or "ConstraintTeachersMaxBuildingChangesPerDay" in c_map:
            c = c_map.get("ConstraintTeacherMaxBuildingChangesPerDay") or c_map.get("ConstraintTeachersMaxBuildingChangesPerDay")
            w = int(c.get("def_weight", 100))
            val = c.get("param_val", 0)
            if c.get("applies_to") == "selected" and c.get("selected_targets"):
                for t_raw in c["selected_targets"]:
                    t_name = resolve_teacher(t_raw)
                    if not t_name:
                        continue
                    lines.append('<ConstraintTeacherMaxBuildingChangesPerDay>')
                    lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                    lines.append(f'	<Teacher>{t_name}</Teacher>')
                    lines.append(f'	<Max_Building_Changes_Per_Day>{val}</Max_Building_Changes_Per_Day>')
                    lines.append('	<Active>true</Active>')
                    lines.append('	<Comments></Comments>')
                    lines.append('</ConstraintTeacherMaxBuildingChangesPerDay>')
            else:
                lines.append('<ConstraintTeachersMaxBuildingChangesPerDay>')
                lines.append(f'	<Weight_Percentage>{w}</Weight_Percentage>')
                lines.append(f'	<Max_Building_Changes_Per_Day>{val}</Max_Building_Changes_Per_Day>')
                lines.append('	<Active>true</Active>')
                lines.append('	<Comments></Comments>')
                lines.append('</ConstraintTeachersMaxBuildingChangesPerDay>')

        lines.append('</Space_Constraints_List>')
        lines.append('')
        lines.append('</fet>')
        raw_xml = "\n".join(lines)
        return self.sanitize_xml_constraints(raw_xml, all_teachers_set, all_students_set, valid_room_names, valid_subjects)

    @staticmethod
    def sanitize_xml_constraints(xml_content: str, valid_teachers: set, valid_students: set, valid_rooms: set, valid_subjects: set) -> str:
        """
        Ultimate bulletproof safety shield for FET Solver:
        Scans all generated time and space constraints and automatically removes
        any constraint that references an inactive teacher, unassigned class,
        or non-existent room/subject, preventing FET assertion failures (e.g. this->teacher_ID >= 0).
        """
        try:
            root = ET.fromstring(xml_content)
            
            # 1. Sanitize Time Constraints
            tc_list = root.find('Time_Constraints_List')
            if tc_list is not None:
                for c in list(tc_list):
                    bad = False
                    for tag in ['Teacher_Name', 'Teacher']:
                        for el in c.findall(tag):
                            if el is not None and el.text and el.text.strip() not in valid_teachers:
                                tc_list.remove(c)
                                bad = True
                                break
                        if bad:
                            break
                    if bad:
                        continue

                    for tag in ['Students', 'Students_Set']:
                        for el in c.findall(tag):
                            if el is not None and el.text and el.text.strip() not in valid_students:
                                tc_list.remove(c)
                                bad = True
                                break
                        if bad:
                            break
                    if bad:
                        continue

                    for tag in ['Subject']:
                        for el in c.findall(tag):
                            if el is not None and el.text and el.text.strip() not in valid_subjects:
                                tc_list.remove(c)
                                bad = True
                                break
                        if bad:
                            break

            # 2. Sanitize Space Constraints
            sc_list = root.find('Space_Constraints_List')
            if sc_list is not None:
                for c in list(sc_list):
                    bad = False
                    for tag in ['Teacher_Name', 'Teacher']:
                        for el in c.findall(tag):
                            if el is not None and el.text and el.text.strip() not in valid_teachers:
                                sc_list.remove(c)
                                bad = True
                                break
                        if bad:
                            break
                    if bad:
                        continue

                    for tag in ['Room', 'Room_Name', 'Preferred_Room']:
                        for el in c.findall(tag):
                            if el is not None and el.text and el.text.strip() not in valid_rooms:
                                sc_list.remove(c)
                                bad = True
                                break
                        if bad:
                            break
                    if bad:
                        continue

                    for tag in ['Subject']:
                        for el in c.findall(tag):
                            if el is not None and el.text and el.text.strip() not in valid_subjects:
                                sc_list.remove(c)
                                bad = True
                                break
                        if bad:
                            break

            return ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')
        except Exception as e:
            print("Error in sanitize_xml_constraints:", e)
            return xml_content
