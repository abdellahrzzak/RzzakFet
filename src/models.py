# -*- coding: utf-8 -*-
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

@dataclass
class CustomRoomType:
    id: str
    name: str
    subject: str
    room_type: str = "قاعة مخصصة"
    count: int = 1

@dataclass
class InstitutionData:
    institution_name: str = "الثانوية الإعدادية بئر انزران"
    province: str = "مديرية مولاي رشيد"
    academy: str = "أكاديمية جهة الدار البيضاء - سطات"
    academic_year: str = "2026-2027"
    gresa_code: str = "045892P"
    principal_name: str = "ذ. محمد الإدريسي"
    
    # Session / Period Timing Settings (Editable in Tab 2)
    morning_start_hour: str = "08:30"
    morning_period_times: List[str] = field(default_factory=lambda: [
        "08:30-09:30", "09:30-10:30", "10:30-11:30", "11:30-12:30"
    ])
    afternoon_start_hour: str = "14:30"
    afternoon_period_times: List[str] = field(default_factory=lambda: [
        "14:30-15:30", "15:30-16:30", "16:30-17:30", "17:30-18:30"
    ])
    
    general_rooms_count: int = 14
    svt_labs_count: int = 2
    pc_labs_count: int = 2
    multimedia_rooms_count: int = 1
    tech_labs_count: int = 0
    family_ed_rooms_count: int = 0
    art_rooms_count: int = 0
    sports_fields_count: int = 2

    # Room custom renaming map: {"default_name": "custom_name"}
    room_custom_names: Dict[str, str] = field(default_factory=dict)

    # Teacher custom renaming map: {"default_name": "real_name"}
    teacher_custom_names: Dict[str, str] = field(default_factory=dict)

    # Global floating mode for general teachers
    float_all_general_teachers: bool = False

    # Custom added room types list
    custom_room_types: List[Dict] = field(default_factory=list)

    # Break time slots list
    break_time_slots: List[Dict[str, str]] = field(default_factory=lambda: [
        {"day": "الاربعاء م", "hour": "ح 1"},
        {"day": "الاربعاء م", "hour": "ح 2"},
        {"day": "الاربعاء م", "hour": "ح 3"},
        {"day": "الاربعاء م", "hour": "ح 4"},
        {"day": "السبت م", "hour": "ح 1"},
        {"day": "السبت م", "hour": "ح 2"},
        {"day": "السبت م", "hour": "ح 3"},
        {"day": "السبت م", "hour": "ح 4"},
    ])

    # Per-subject activity spacing constraints (min/max days, weight, etc.)
    subject_activity_constraints: Dict[str, Dict] = field(default_factory=dict)

    # Per-subject activity duration splits (e.g. PE: "2" vs "1+1", Math: "1+1+1+1+1")
    subject_split_modes: Dict[str, Dict] = field(default_factory=lambda: {
        "التربية البدنية": {"mode": "2", "desc": "حصة واحدة من ساعتين بالملاعب (النمط الرسمي)"},
        "اللغة العربية": {"mode": "1+1+1+1", "desc": "4 حصص فردية على 4 أيام (المذكرة 43)"},
        "اللغة الفرنسية": {"mode": "1+1+1+1", "desc": "4 حصص فردية على 4 أيام (المذكرة 43)"},
        "الرياضيات": {"mode": "1+1+1+1+1", "mode_l1": "1+1+1+1+1", "mode_l2": "1+1+1+1", "mode_l3": "1+1+1+1+1", "desc": "حصص فردية يومية (5 للأولى والثالثة، 4 للثانية)"},
        "الاجتماعيات": {"mode": "1+1+1", "desc": "3 حصص فردية على 3 أيام مختلفة"},
        "التربية الإسلامية": {"mode": "1+1", "desc": "حصتان فرديتان على يومين متباعدين"},
        "علوم الحياة و الأرض": {"mode": "2", "mode_l3": "2+1", "desc": "ساعتان متصلتان بالمختبر (2+1 للثالثة إعدادي)"},
        "الكيمياء و الفيزياء": {"mode": "2", "mode_l3": "2+1", "desc": "ساعتان متصلتان بالمختبر (2+1 للثالثة إعدادي)"}
    })

    # Custom teachers count by subject (actual teachers available in institution)
    teacher_counts_by_subject: Dict[str, int] = field(default_factory=dict)

    # Wednesday Afternoon Special Activities (ASS & Support)
    pe_wednesday_label: str = "أنشطة الجمعية الرياضية المدرسية (ASS)"
    general_wednesday_label: str = "الأنشطة الموازية والدعم التربوي"
    enable_wednesday_labels: bool = True

    # Fair distribution of morning/afternoon half-days for teachers
    max_morning_half_days_per_teacher: int = 4

    @property
    def total_rooms(self) -> int:
        base = (self.general_rooms_count + self.svt_labs_count + 
                self.pc_labs_count + self.multimedia_rooms_count + 
                self.tech_labs_count + self.family_ed_rooms_count + 
                self.art_rooms_count + self.sports_fields_count)
        custom_sum = sum(int(crt.get("count", 1)) for crt in self.custom_room_types)
        return base + custom_sum

    @property
    def max_room_capacity_hours(self) -> int:
        total_breaks = len(self.break_time_slots)
        return max(20, 48 - total_breaks)

@dataclass
class EducationalStructure:
    classes_1_apic: int = 12
    classes_2_apic: int = 10
    classes_3_apic: int = 10

    students_1_apic: int = 420
    students_2_apic: int = 350
    students_3_apic: int = 350

    @property
    def total_classes(self) -> int:
        return self.classes_1_apic + self.classes_2_apic + self.classes_3_apic

    @property
    def total_students(self) -> int:
        return self.students_1_apic + self.students_2_apic + self.students_3_apic

@dataclass
class NonGeneralizedSubjectConfig:
    name: str
    is_active: bool
    hours_1_apic: int
    hours_2_apic: int
    hours_3_apic: int
    room_type: str

@dataclass
class SubjectQuotaCalc:
    name: str
    is_generalized: bool
    hours_1: int
    hours_2: int
    hours_3: int
    total_hours: int
    required_rooms: int
    required_teachers: int
    hours_level_1: int
    hours_level_2: int
    hours_level_3: int

@dataclass
class TeacherAssignment:
    row_id: int
    subject: str
    teacher_name: str
    classes_1: int
    classes_2: int
    classes_3: int
    assigned_classes_str: str
    total_classes: int
    levels_count: int
    two_levels_satisfied: bool
    total_hours: int
    status_note: str
    def_teacher_name: str = ""

@dataclass
class CustomRoom:
    room_id: int
    room_name: str
    room_type: str
    assigned_subject: str = "عامة"
    morning_teacher: str = "شاغر (صباحي)"
    afternoon_teacher: str = "شاغر (مسائي)"
    total_hours: int = 0
    max_capacity_hours: int = 40
    utilization_pct: float = 0.0
    status: str = "استثمار تام ✓"
    is_custom: bool = False
