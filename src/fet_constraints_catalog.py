# -*- coding: utf-8 -*-
from typing import List, Dict

def get_68_constraints() -> List[Dict]:
    constraints = [
        # =========================================================================
        # 1. القيود الزمنية (TIME CONSTRAINTS) - 44 قيداً
        # =========================================================================
        
        # --- أ. القيود الزمنية الأساسية (2 قيود) ---
        {
            "id": "tc_base_1", "scope": "common", "main_cat": "time", "sub_cat": "basic",
            "name": "القيد الزمني الأساسي الإجباري",
            "name_en": "Basic Compulsory Time Constraints",
            "code": "ConstraintBasicCompulsoryTime",
            "code_individual": "ConstraintBasicCompulsoryTime",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "target_type": "none", "applies_to": "all", "selected_targets": [],
            "desc": "يمنع تدريس الأستاذ لحصتين في نفس الوقت ويمنع تلقي القسم لأكثر من حصة واحدة في الفترة."
        },
        {
            "id": "tc_base_2", "scope": "common", "main_cat": "time", "sub_cat": "basic",
            "name": "فترات التوقف والاستراحة العامة (الإيقاف)",
            "name_en": "Break (All Teachers + All Students Not Available)",
            "code": "ConstraintBreakTimes",
            "code_individual": "ConstraintBreakTimes",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "param_name": "break_hours", "param_label": "حصص التوقف الأسبوعية",
            "param_val": 8, "param_min": 0, "param_max": 24, "param_unit": "حصص",
            "target_type": "none", "applies_to": "all", "selected_targets": [],
            "desc": "تفريغ فترات التوقف الرسمية لكافة الأساتذة والطلاب (مثل الأربعاء والسبت مساء)."
        },

        # --- ب. القيود الزمنية الخاصة بالأساتذة (14 قيداً) ---
        {
            "id": "tc_t_1", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "تفريغ مدرس (أوقات غير متاحة)",
            "name_en": "Not Available Teacher",
            "code": "ConstraintTeacherNotAvailableTimes",
            "code_individual": "ConstraintTeacherNotAvailableTimes",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "حظر إسناد حصص لمدرس معين في فترات أو أيام محددة."
        },
        {
            "id": "tc_t_2", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأقصى من أيام العمل الأسبوعي لمدرس",
            "name_en": "Max Days Per Week for a Teacher",
            "code": "ConstraintTeachersMaxDaysPerWeek",
            "code_individual": "ConstraintTeacherMaxDaysPerWeek",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_days_week", "param_label": "أقصى أيام عمل",
            "param_val": 5, "param_min": 3, "param_max": 6, "param_unit": "أيام",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "تحديد سقف أيام الحضور الأسبوعية للأستاذ لمنحه يوم أو نصف يوم راحة."
        },
        {
            "id": "tc_t_3", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأقصى من الفراغات في الأسبوع لمدرس",
            "name_en": "Max Gaps Per Week for a Teacher",
            "code": "ConstraintTeacherMaxGapsPerWeek",
            "code_individual": "ConstraintTeacherMaxGapsPerWeek",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_gaps_weekly", "param_label": "أقصى فجوات أسبوعية",
            "param_val": 0, "param_min": 0, "param_max": 8, "param_unit": "فجوات",
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "حصر الساعات البينية الفارغة لأستاذ محدد طيلة الأسبوع."
        },
        {
            "id": "tc_t_4", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأقصى من الفراغات في الأسبوع للمدرسين",
            "name_en": "Max Gaps Per Week for All Teachers",
            "code": "ConstraintTeachersMaxGapsPerWeek",
            "code_individual": "ConstraintTeacherMaxGapsPerWeek",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_gaps_weekly", "param_label": "أقصى فجوات أسبوعية",
            "param_val": 0, "param_min": 0, "param_max": 8, "param_unit": "فجوات",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "حصر الساعات البينية الفارغة لجميع الأساتذة طيلة الأسبوع."
        },
        {
            "id": "tc_t_5", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأقصى من الفراغات في اليوم لمدرس",
            "name_en": "Max Gaps Per Day for a Teacher",
            "code": "ConstraintTeacherMaxGapsPerDay",
            "code_individual": "ConstraintTeacherMaxGapsPerDay",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_gaps_daily", "param_label": "أقصى فجوات يومية",
            "param_val": 0, "param_min": 0, "param_max": 4, "param_unit": "فجوات",
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "منع أو تقييد الساعات الفارغة لأستاذ معين خلال اليوم الواحد."
        },
        {
            "id": "tc_t_6", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأقصى من الفراغات في اليوم للمدرسين (منع الساعات الفارغة)",
            "name_en": "Max Gaps Per Day for All Teachers",
            "code": "ConstraintTeachersMaxGapsPerDay",
            "code_individual": "ConstraintTeacherMaxGapsPerDay",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "param_name": "max_gaps_daily", "param_label": "أقصى فجوات في اليوم",
            "param_val": 0, "param_min": 0, "param_max": 4, "param_unit": "فجوات",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "منع الساعات الفارغة لكافة الأساتذة في اليوم الواحد."
        },
        {
            "id": "tc_t_7", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأقصى من الحصص اليومية لمدرس",
            "name_en": "Max Hours Daily for a Teacher",
            "code": "ConstraintTeacherMaxHoursDaily",
            "code_individual": "ConstraintTeacherMaxHoursDaily",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_hours_daily", "param_label": "أقصى ساعات يومية",
            "param_val": 6, "param_min": 4, "param_max": 8, "param_unit": "ساعات",
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "تحديد سقف ساعات التدريس اليومية لأستاذ معين."
        },
        {
            "id": "tc_t_8", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأقصى من الحصص اليومية للمدرسين (عدم تجاوز 6 ساعات)",
            "name_en": "Max Hours Daily for All Teachers",
            "code": "ConstraintTeachersMaxHoursDaily",
            "code_individual": "ConstraintTeacherMaxHoursDaily",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "param_name": "max_hours_daily", "param_label": "الحد الأقصى للساعات",
            "param_val": 6, "param_min": 4, "param_max": 8, "param_unit": "ساعات",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "منع تجاوز 6 ساعات تدريس يومياً لكافة الأساتذة لضمان السلامة البيداغوجية."
        },
        {
            "id": "tc_t_9", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأدنى من الحصص اليومية لمدرس",
            "name_en": "Min Hours Daily for a Teacher",
            "code": "ConstraintTeacherMinHoursDaily",
            "code_individual": "ConstraintTeacherMinHoursDaily",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "min_hours_daily", "param_label": "أدنى ساعات يومية",
            "param_val": 2, "param_min": 1, "param_max": 4, "param_unit": "ساعات",
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "اشتراط ألا يحضر المدرس للمؤسسة لأقل من عدد محدد من الساعات في اليوم."
        },
        {
            "id": "tc_t_10", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأدنى من الحصص اليومية للمدرسين",
            "name_en": "Min Hours Daily for All Teachers",
            "code": "ConstraintTeachersMinHoursDaily",
            "code_individual": "ConstraintTeacherMinHoursDaily",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "min_hours_daily", "param_label": "أدنى ساعات يومية",
            "param_val": 2, "param_min": 1, "param_max": 4, "param_unit": "ساعات",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "ضمان حد أدنى من ساعات العمل لجميع الأساتذة في الأيام التي يحضرون فيها."
        },
        {
            "id": "tc_t_11", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأقصى من الحصص المتصلة لمدرس",
            "name_en": "Max Hours Continuously for a Teacher",
            "code": "ConstraintTeacherMaxHoursContinuously",
            "code_individual": "ConstraintTeacherMaxHoursContinuously",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_continuous", "param_label": "أقصى ساعات متصلة",
            "param_val": 4, "param_min": 2, "param_max": 6, "param_unit": "ساعات",
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "منع تدريس الأستاذ لأكثر من ساعات محددة دون استراحة."
        },
        {
            "id": "tc_t_12", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "العدد الأقصى من الحصص المتصلة للمدرسين",
            "name_en": "Max Hours Continuously for All Teachers",
            "code": "ConstraintTeachersMaxHoursContinuously",
            "code_individual": "ConstraintTeacherMaxHoursContinuously",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "param_name": "max_continuous", "param_label": "أقصى ساعات متصلة",
            "param_val": 4, "param_min": 2, "param_max": 6, "param_unit": "ساعات",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "تحديد سقف 4 ساعات متصلة لكافة الأساتذة منعاً للإنهاك البدني والذهني."
        },
        {
            "id": "tc_t_13", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "الحد الأقصى للفترات الصباحية في الأسبوع لمدرس (أقصى فترات صباحا)",
            "name_en": "Max Morning Half-Days Per Week for a Teacher",
            "code": "ConstraintTeacherIntervalMaxDaysPerWeek",
            "code_individual": "ConstraintTeacherIntervalMaxDaysPerWeek",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_mornings", "param_label": "أقصى فترات صباحا",
            "param_val": 4, "param_min": 1, "param_max": 6, "param_unit": "فترات",
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "تحديد سقف الفترات الصباحية لأستاذ معين (من أصل 6 فترات صباحية في الأسبوع) لضمان فترات راحة صباحية."
        },
        {
            "id": "tc_t_14", "scope": "teachers", "main_cat": "time", "sub_cat": "teachers",
            "name": "الحد الأقصى للفترات الصباحية في الأسبوع لكافة الأساتذة (أقصى فترات صباحا)",
            "name_en": "Max Morning Half-Days Per Week for All Teachers",
            "code": "ConstraintTeachersIntervalMaxDaysPerWeek",
            "code_individual": "ConstraintTeacherIntervalMaxDaysPerWeek",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "param_name": "max_mornings", "param_label": "أقصى فترات صباحا",
            "param_val": 4, "param_min": 1, "param_max": 6, "param_unit": "فترات",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "تحديد سقف الفترات الصباحية لكافة الأساتذة (4 فترات كحد أقصى افتراضياً) لمنح كل أستاذ فترتي راحة صباحية على الأقل."
        },

        # --- ج. القيود الزمنية الخاصة بالطلاب (11 قيداً) ---
        {
            "id": "tc_s_1", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "تفريغ طلاب معينين (أوقات غير متاحة للقسم)",
            "name_en": "A Students Set is Not Available",
            "code": "ConstraintStudentsSetNotAvailableTimes",
            "code_individual": "ConstraintStudentsSetNotAvailableTimes",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "حظر جدولة حصص لقسم معين في فترات محددة (مثل أوقات الرياضة الخارجية أو التداريب)."
        },
        {
            "id": "tc_s_2", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "العدد الأقصى من الفراغات في الأسبوع لطلاب معينين",
            "name_en": "Max Gaps Per Week for a Students Set",
            "code": "ConstraintStudentsSetMaxGapsPerWeek",
            "code_individual": "ConstraintStudentsSetMaxGapsPerWeek",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_gaps_weekly", "param_label": "أقصى فجوات أسبوعية",
            "param_val": 0, "param_min": 0, "param_max": 4, "param_unit": "فجوات",
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "تقييد الساعات البينية الفارغة لقسم أو فوج معين خلال الأسبوع."
        },
        {
            "id": "tc_s_3", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "العدد الأقصى من الفراغات في الأسبوع للطلاب (منع الفراغ نهائياً)",
            "name_en": "Max Gaps Per Week for All Students",
            "code": "ConstraintStudentsMaxGapsPerWeek",
            "code_individual": "ConstraintStudentsSetMaxGapsPerWeek",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "param_name": "max_gaps_weekly", "param_label": "أقصى فجوات أسبوعية",
            "param_val": 0, "param_min": 0, "param_max": 2, "param_unit": "فجوات",
            "target_type": "students", "applies_to": "all", "selected_targets": [],
            "desc": "منع الفجوات والساعات الفارغة لكافة تلاميذ المؤسسة احتراماً للقانون المدرسي."
        },
        {
            "id": "tc_s_4", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "طلاب معينين يبدأون باكراً",
            "name_en": "A Students Set Begins Early",
            "code": "ConstraintStudentsSetEarlyMaxBeginningsAtSecondHour",
            "code_individual": "ConstraintStudentsSetEarlyMaxBeginningsAtSecondHour",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_second_hour", "param_label": "أقصى بدايات بالساعة 2",
            "param_val": 0, "param_min": 0, "param_max": 2, "param_unit": "مرات",
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "إلزام قسم معين بالبدء دائماً من الحصة الأولى الصباحية."
        },
        {
            "id": "tc_s_5", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "كل الطلاب يبدأون باكراً",
            "name_en": "All Students Begin Early",
            "code": "ConstraintStudentsEarlyMaxBeginningsAtSecondHour",
            "code_individual": "ConstraintStudentsSetEarlyMaxBeginningsAtSecondHour",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_second_hour", "param_label": "أقصى بدايات بالساعة 2",
            "param_val": 0, "param_min": 0, "param_max": 2, "param_unit": "مرات",
            "target_type": "students", "applies_to": "all", "selected_targets": [],
            "desc": "إلزام جميع الفصول بالانطلاق في الحصة الأولى يومياً (مثالي للنقل المدرسي الموحد)."
        },
        {
            "id": "tc_s_6", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "العدد الأقصى من الحصص اليومية لطلاب معينين",
            "name_en": "Max Hours Daily for a Students Set",
            "code": "ConstraintStudentsSetMaxHoursDaily",
            "code_individual": "ConstraintStudentsSetMaxHoursDaily",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_hours_daily", "param_label": "أقصى ساعات يومية",
            "param_val": 6, "param_min": 4, "param_max": 8, "param_unit": "ساعات",
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "تحديد سقف ساعات الدراسة اليومية لقسم أو مستوى معين."
        },
        {
            "id": "tc_s_7", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "العدد الأقصى من الحصص اليومية للطلاب (عدم تجاوز 6 ساعات)",
            "name_en": "Max Hours Daily for All Students",
            "code": "ConstraintStudentsMaxHoursDaily",
            "code_individual": "ConstraintStudentsSetMaxHoursDaily",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "param_name": "max_hours_daily", "param_label": "الحد الأقصى للساعات",
            "param_val": 6, "param_min": 4, "param_max": 8, "param_unit": "ساعات",
            "target_type": "students", "applies_to": "all", "selected_targets": [],
            "desc": "منع تجاوز 6 ساعات دراسية في اليوم الواحد لجميع التلاميذ."
        },
        {
            "id": "tc_s_8", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "العدد الأدنى من الحصص اليومية لطلاب معينين",
            "name_en": "Min Hours Daily for a Students Set",
            "code": "ConstraintStudentsSetMinHoursDaily",
            "code_individual": "ConstraintStudentsSetMinHoursDaily",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "min_hours_daily", "param_label": "أدنى ساعات يومية",
            "param_val": 3, "param_min": 2, "param_max": 5, "param_unit": "ساعات",
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "ضمان حد أدنى من الساعات اليومية لقسم معين."
        },
        {
            "id": "tc_s_9", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "العدد الأدنى من الحصص اليومية للطلاب",
            "name_en": "Min Hours Daily for All Students",
            "code": "ConstraintStudentsMinHoursDaily",
            "code_individual": "ConstraintStudentsSetMinHoursDaily",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "min_hours_daily", "param_label": "أدنى ساعات يومية",
            "param_val": 3, "param_min": 2, "param_max": 5, "param_unit": "ساعات",
            "target_type": "students", "applies_to": "all", "selected_targets": [],
            "desc": "ضمان توزيع متوازن لحصص اليوم ومنع الدوام من أجل حصة يتيمة."
        },
        {
            "id": "tc_s_10", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "العدد الأقصى من الحصص المتصلة لطلاب معينين",
            "name_en": "Max Hours Continuously a Students Set",
            "code": "ConstraintStudentsSetMaxHoursContinuously",
            "code_individual": "ConstraintStudentsSetMaxHoursContinuously",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_continuous", "param_label": "أقصى ساعات متصلة",
            "param_val": 4, "param_min": 2, "param_max": 6, "param_unit": "ساعات",
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "تحديد سقف الحصص المتتالية دون استراحة لقسم محدد."
        },
        {
            "id": "tc_s_11", "scope": "students", "main_cat": "time", "sub_cat": "students",
            "name": "العدد الأقصى من الحصص المتصلة للطلاب",
            "name_en": "Max Hours Continuously for All Students",
            "code": "ConstraintStudentsMaxHoursContinuously",
            "code_individual": "ConstraintStudentsSetMaxHoursContinuously",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_continuous", "param_label": "أقصى ساعات متصلة",
            "param_val": 4, "param_min": 2, "param_max": 6, "param_unit": "ساعات",
            "target_type": "students", "applies_to": "all", "selected_targets": [],
            "desc": "منع استمرار الدراسة لأكثر من 4 ساعات متصلة لكافة التلاميذ دون استراحة كافية."
        },

        # --- د. قيود المهام والأنشطة الزمنية (17 قيداً) ---
        {
            "id": "tc_a_1", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "وقت بدء مفضل لمهمة",
            "name_en": "An Activity Has a Preferred Starting Time",
            "code": "ConstraintActivityPreferredStartingTime",
            "code_individual": "ConstraintActivityPreferredStartingTime",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "تحديد موعد زمني دقيق (اليوم والحصة) لانطلاق حصة معينة."
        },
        {
            "id": "tc_a_2", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "فترات زمنية مفضلة لمهمة",
            "name_en": "An Activity Has a Set of Preferred Time Slots",
            "code": "ConstraintActivityPreferredTimeSlots",
            "code_individual": "ConstraintActivityPreferredTimeSlots",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "تحديد قائمة الفترات الزمنية المسموح تموضع النشاط فيها."
        },
        {
            "id": "tc_a_3", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "فترات زمنية مفضلة لمجموعة مهام",
            "name_en": "A Set of Activities Has a Set of Preferred Time Slots",
            "code": "ConstraintActivitiesPreferredTimeSlots",
            "code_individual": "ConstraintActivitiesPreferredTimeSlots",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "all", "selected_targets": [],
            "desc": "تخصيص فترات زمنية مسموحة لمجموعة من الأنشطة المتجانسة."
        },
        {
            "id": "tc_a_4", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "فترات زمنية مفضلة لمهام فرعية",
            "name_en": "A Set of Subactivities Has a Set of Preferred Time Slots",
            "code": "ConstraintSubactivitiesPreferredTimeSlots",
            "code_individual": "ConstraintSubactivitiesPreferredTimeSlots",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "تخصيص فترات زمنية للحصص الجزئية التابعة لنفس النشاط المفكك."
        },
        {
            "id": "tc_a_5", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "أوقات بدء مفضلة لمهمة",
            "name_en": "An Activity Has a Set of Preferred Starting Times",
            "code": "ConstraintActivityPreferredStartingTimes",
            "code_individual": "ConstraintActivityPreferredStartingTimes",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "تحديد ساعات انطلاق مسموحة لحصة معينة."
        },
        {
            "id": "tc_a_6", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "أوقات بدء مفضلة لمجموعة مهام",
            "name_en": "A Set of Activities Has a Set of Preferred Starting Times",
            "code": "ConstraintActivitiesPreferredStartingTimes",
            "code_individual": "ConstraintActivitiesPreferredStartingTimes",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "all", "selected_targets": [],
            "desc": "تحديد ساعات انطلاق مسموحة لعدة مهام (مثل برمجة حصص الصباح فقط)."
        },
        {
            "id": "tc_a_7", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "أوقات بدء مفضلة لمهام فرعية",
            "name_en": "A Set of Subactivities Has a Set of Preferred Starting Times",
            "code": "ConstraintSubactivitiesPreferredStartingTimes",
            "code_individual": "ConstraintSubactivitiesPreferredStartingTimes",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "تحديد ساعات انطلاق للحصص المجزأة لمادة معينة."
        },
        {
            "id": "tc_a_8", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "العدد الأدنى من الأيام بين مهام معينة (التباعد البيداغوجي)",
            "name_en": "Min n Days Between a Set of Activities",
            "code": "ConstraintMinDaysBetweenActivities",
            "code_individual": "ConstraintMinDaysBetweenActivities",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "param_name": "min_days", "param_label": "أدنى تباعد بين الحصص",
            "param_val": 1, "param_min": 1, "param_max": 3, "param_unit": "يوم",
            "target_type": "none", "applies_to": "all", "selected_targets": [],
            "desc": "ضمان نشر حصص المادة الواحدة على أيام متباعدة في الأسبوع وعدم حشرها في يوم واحد."
        },
        {
            "id": "tc_a_9", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "الحصة الأخيرة لمهمة",
            "name_en": "An Activity Ends Students Day",
            "code": "ConstraintActivityEndsStudentsDay",
            "code_individual": "ConstraintActivityEndsStudentsDay",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "إلزام حصة معينة بأن تكون ختام اليوم الدراسي للتلاميذ (مثل أنشطة الدعم)."
        },
        {
            "id": "tc_a_10", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "الحصة الأخيرة لمجموعة مهام أو مادة",
            "name_en": "A Set of Activities Ends Students Day",
            "code": "ConstraintActivitiesEndStudentsDay",
            "code_individual": "ConstraintActivitiesEndStudentsDay",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "all", "selected_targets": [],
            "desc": "إلزام مجموعة أنشطة بأن تكون دائماً في نهاية اليوم للقسم."
        },
        {
            "id": "tc_a_11", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "مهام تبدأ في نفس اليوم والساعة (البدء في نفس الوقت)",
            "name_en": "A Set of Activities Has Same Starting Time (Day+Hour)",
            "code": "ConstraintActivitiesSameStartingTime",
            "code_individual": "ConstraintActivitiesSameStartingTime",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "all", "selected_targets": [],
            "desc": "تزامن تام لعدة مهام (مثل حصص التربية البدنية لقسمين في نفس الملعب في آن واحد)."
        },
        {
            "id": "tc_a_12", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "مهام تبدأ في نفس اليوم (أي حصة)",
            "name_en": "A Set of Activities Has Same Starting Day (Any Hour)",
            "code": "ConstraintActivitiesSameStartingDay",
            "code_individual": "ConstraintActivitiesSameStartingDay",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "all", "selected_targets": [],
            "desc": "إلزام أنشطة معينة بأن تتم في نفس اليوم أياً كانت ساعتها."
        },
        {
            "id": "tc_a_13", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "مهام لها نفس الوقت والأيام قد تتغير",
            "name_en": "A Set of Activities Has Same Starting Hour (Any Day)",
            "code": "ConstraintActivitiesSameStartingHour",
            "code_individual": "ConstraintActivitiesSameStartingHour",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "all", "selected_targets": [],
            "desc": "توحيد توقيت الحصة (مثلاً الحصة الأولى) عبر أيام مختلفة."
        },
        {
            "id": "tc_a_14", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "مهمتان متعاقبتان (بالترتيب الزمني)",
            "name_en": "2 Activities Are Ordered",
            "code": "ConstraintTwoActivitiesOrdered",
            "code_individual": "ConstraintTwoActivitiesOrdered",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "اشتراط تقديم الحصة النظرية/الاستماع أولاً قبل حصة التطبيق/التمارين في الأسبوع."
        },
        {
            "id": "tc_a_15", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "مهمتان متتاليتان (حصتان متصلتان في نفس اليوم)",
            "name_en": "2 Activities Are Consecutive",
            "code": "ConstraintTwoActivitiesConsecutive",
            "code_individual": "ConstraintTwoActivitiesConsecutive",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "اشتراط تدريس حصتين مباشرة وراء بعضهما في نفس اليوم دون أي فاصل زمني."
        },
        {
            "id": "tc_a_16", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "مهام ليست في نفس التوقيت (عدم التداخل)",
            "name_en": "A Set of Activities Are Not Overlapping",
            "code": "ConstraintActivitiesNotOverlapping",
            "code_individual": "ConstraintActivitiesNotOverlapping",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "all", "selected_targets": [],
            "desc": "منع تزامن حصص محددة لأسباب إدارية أو لوجستية حتى لو اختلفت أسماء الأساتذة والقاعات."
        },
        {
            "id": "tc_a_17", "scope": "activities", "main_cat": "time", "sub_cat": "activities",
            "name": "أقل فراغات (حصص) بين مهام معينة",
            "name_en": "Min Gaps (Hours) Between a Set of Activities",
            "code": "ConstraintMinGapsBetweenActivities",
            "code_individual": "ConstraintMinGapsBetweenActivities",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "min_gaps_between", "param_label": "أدنى فجوة بالساعات",
            "param_val": 1, "param_min": 1, "param_max": 4, "param_unit": "حصص",
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "فرض فاصل زمني محدد من الساعات بين حصتين لنفس القسم."
        },

        # =========================================================================
        # 2. القيود المكانية (SPACE CONSTRAINTS) - 24 قيداً
        # =========================================================================
        
        # --- هـ. القيود المكانية الأساسية والقاعات (2 قيود) ---
        {
            "id": "sc_base_1", "scope": "common", "main_cat": "space", "sub_cat": "basic",
            "name": "القيد المكاني الأساسي الإجباري",
            "name_en": "Basic Compulsory Space Constraints",
            "code": "ConstraintBasicCompulsorySpace",
            "code_individual": "ConstraintBasicCompulsorySpace",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "target_type": "none", "applies_to": "all", "selected_targets": [],
            "desc": "يمنع حجز القاعة الواحدة لأكثر من نشاط واحد في نفس الفترة الزمنية."
        },
        {
            "id": "sc_room_1", "scope": "common", "main_cat": "space", "sub_cat": "rooms",
            "name": "تفريغ قاعة (أوقات غير متاحة لقاعة)",
            "name_en": "A Room is Not Available",
            "code": "ConstraintRoomNotAvailableTimes",
            "code_individual": "ConstraintRoomNotAvailableTimes",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "rooms", "applies_to": "selected", "selected_targets": [],
            "desc": "حظر استعمال قاعة معينة في أوقات محددة (مثل أوقات الصيانة أو التشارك مع مؤسسة أخرى)."
        },

        # --- و. قيود الأساتذة المكانية (8 قيود) ---
        {
            "id": "sc_t_1", "scope": "teachers", "main_cat": "space", "sub_cat": "teachers",
            "name": "مدرس له قاعة خاصة (توطين الأستاذ في القاعة الأم)",
            "name_en": "A Teacher Has a Home Room",
            "code": "ConstraintTeacherHomeRoom",
            "code_individual": "ConstraintTeacherHomeRoom",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "تخصيص قاعة قارة وثابتة للأستاذ يُدرس فيها جميع حصصه النظرية."
        },
        {
            "id": "sc_t_2", "scope": "teachers", "main_cat": "space", "sub_cat": "teachers",
            "name": "مدرس له قاعات معينة (مجموعة قاعات)",
            "name_en": "A Teacher Has a Set of Home Rooms",
            "code": "ConstraintTeacherHomeRooms",
            "code_individual": "ConstraintTeacherHomeRooms",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "تخصيص مجموعة محددة من القاعات يتناوب عليها الأستاذ."
        },
        {
            "id": "sc_t_3", "scope": "teachers", "main_cat": "space", "sub_cat": "teachers",
            "name": "العدد الأقصى لتغيير البنايات في اليوم لمدرس",
            "name_en": "Max Building Changes Per Day for a Teacher",
            "code": "ConstraintTeacherMaxBuildingChangesPerDay",
            "code_individual": "ConstraintTeacherMaxBuildingChangesPerDay",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_changes", "param_label": "أقصى تنقل بين بنايات",
            "param_val": 0, "param_min": 0, "param_max": 3, "param_unit": "مرات",
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "حصر تنقل الأستاذ بين المباني المتباعدة في اليوم الواحد."
        },
        {
            "id": "sc_t_4", "scope": "teachers", "main_cat": "space", "sub_cat": "teachers",
            "name": "العدد الأقصى لتغيير البنايات في اليوم للمدرسين",
            "name_en": "Max Building Changes Per Day for All Teachers",
            "code": "ConstraintTeachersMaxBuildingChangesPerDay",
            "code_individual": "ConstraintTeacherMaxBuildingChangesPerDay",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_changes", "param_label": "أقصى تنقل بين بنايات",
            "param_val": 0, "param_min": 0, "param_max": 3, "param_unit": "مرات",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "تطبيق حد أقصى عام لتنقل الأساتذة بين المباني يومياً."
        },
        {
            "id": "sc_t_5", "scope": "teachers", "main_cat": "space", "sub_cat": "teachers",
            "name": "العدد الأقصى لتغيير البنايات في الأسبوع لمدرس",
            "name_en": "Max Building Changes Per Week for a Teacher",
            "code": "ConstraintTeacherMaxBuildingChangesPerWeek",
            "code_individual": "ConstraintTeacherMaxBuildingChangesPerWeek",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_changes_week", "param_label": "أقصى تنقل أسبوعي",
            "param_val": 2, "param_min": 0, "param_max": 6, "param_unit": "مرات",
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "سقف أسبوعي لانتقال المدرس بين المباني."
        },
        {
            "id": "sc_t_6", "scope": "teachers", "main_cat": "space", "sub_cat": "teachers",
            "name": "العدد الأقصى لتغيير البنايات في الأسبوع للمدرسين",
            "name_en": "Max Building Changes Per Week for All Teachers",
            "code": "ConstraintTeachersMaxBuildingChangesPerWeek",
            "code_individual": "ConstraintTeacherMaxBuildingChangesPerWeek",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_changes_week", "param_label": "أقصى تنقل أسبوعي",
            "param_val": 2, "param_min": 0, "param_max": 6, "param_unit": "مرات",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "سقف أسبوعي عام لانتقال الأساتذة بين أجنحة ومباني المؤسسة."
        },
        {
            "id": "sc_t_7", "scope": "teachers", "main_cat": "space", "sub_cat": "teachers",
            "name": "العدد الأدنى من الفراغات بين تغيير البنايات لمدرس",
            "name_en": "Min Gaps Between Building Changes for a Teacher",
            "code": "ConstraintTeacherMinGapsBetweenBuildingChanges",
            "code_individual": "ConstraintTeacherMinGapsBetweenBuildingChanges",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "min_gaps_building", "param_label": "فراغ الانتقال بين المباني",
            "param_val": 1, "param_min": 1, "param_max": 2, "param_unit": "حصص",
            "target_type": "teachers", "applies_to": "selected", "selected_targets": [],
            "desc": "توفير مهلة زمنية كافية للأستاذ للمشي والانتقال بين مبنيين متباعدين."
        },
        {
            "id": "sc_t_8", "scope": "teachers", "main_cat": "space", "sub_cat": "teachers",
            "name": "العدد الأدنى من الفراغات بين تغيير البنايات للمدرسين",
            "name_en": "Min Gaps Between Building Changes for All Teachers",
            "code": "ConstraintTeachersMinGapsBetweenBuildingChanges",
            "code_individual": "ConstraintTeacherMinGapsBetweenBuildingChanges",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "min_gaps_building", "param_label": "فراغ الانتقال بين المباني",
            "param_val": 1, "param_min": 1, "param_max": 2, "param_unit": "حصص",
            "target_type": "teachers", "applies_to": "all", "selected_targets": [],
            "desc": "توفير مهلة زمنية فاصلة لجميع الأساتذة عند تغيير المبنى."
        },

        # --- ز. قيود الطلاب المكانية (8 قيود) ---
        {
            "id": "sc_s_1", "scope": "students", "main_cat": "space", "sub_cat": "students",
            "name": "قاعة خاصة لطلاب معينين (قاعة قارة لقسم)",
            "name_en": "A Set of Students Has a Home Room",
            "code": "ConstraintStudentsSetHomeRoom",
            "code_individual": "ConstraintStudentsSetHomeRoom",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "تخصيص حجرة دراسية ثابتة لقسم محدد طيلة الأسبوع."
        },
        {
            "id": "sc_s_2", "scope": "students", "main_cat": "space", "sub_cat": "students",
            "name": "عدة قاعات معينة لطلاب معينين",
            "name_en": "A Set of Students Has a Set of Home Rooms",
            "code": "ConstraintStudentsSetHomeRooms",
            "code_individual": "ConstraintStudentsSetHomeRooms",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "تحديد قاعات محددة مسموحة لقسم طلابي."
        },
        {
            "id": "sc_s_3", "scope": "students", "main_cat": "space", "sub_cat": "students",
            "name": "العدد الأقصى لتغيير البنايات في اليوم لطلاب معينين",
            "name_en": "Max Building Changes Per Day for a Set of Students",
            "code": "ConstraintStudentsSetMaxBuildingChangesPerDay",
            "code_individual": "ConstraintStudentsSetMaxBuildingChangesPerDay",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_changes", "param_label": "أقصى تنقل بين بنايات",
            "param_val": 0, "param_min": 0, "param_max": 3, "param_unit": "مرات",
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "حصر تنقل تلاميذ قسم معين بين المباني في اليوم الواحد."
        },
        {
            "id": "sc_s_4", "scope": "students", "main_cat": "space", "sub_cat": "students",
            "name": "العدد الأقصى لتغيير البنايات في اليوم للطلاب",
            "name_en": "Max Building Changes Per Day for All Students",
            "code": "ConstraintStudentsMaxBuildingChangesPerDay",
            "code_individual": "ConstraintStudentsSetMaxBuildingChangesPerDay",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_changes", "param_label": "أقصى تنقل بين بنايات",
            "param_val": 0, "param_min": 0, "param_max": 3, "param_unit": "مرات",
            "target_type": "students", "applies_to": "all", "selected_targets": [],
            "desc": "حصر تنقل جميع فصول المؤسسة بين المباني في اليوم الواحد."
        },
        {
            "id": "sc_s_5", "scope": "students", "main_cat": "space", "sub_cat": "students",
            "name": "العدد الأقصى لتغيير البنايات في الأسبوع لطلاب معينين",
            "name_en": "Max Building Changes Per Week for a Set of Students",
            "code": "ConstraintStudentsSetMaxBuildingChangesPerWeek",
            "code_individual": "ConstraintStudentsSetMaxBuildingChangesPerWeek",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_changes_week", "param_label": "أقصى تنقل أسبوعي",
            "param_val": 2, "param_min": 0, "param_max": 6, "param_unit": "مرات",
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "سقف أسبوعي لتنقلات قسم محدد بين المباني."
        },
        {
            "id": "sc_s_6", "scope": "students", "main_cat": "space", "sub_cat": "students",
            "name": "العدد الأقصى لتغيير البنايات في الأسبوع للطلاب",
            "name_en": "Max Building Changes Per Week for All Students",
            "code": "ConstraintStudentsMaxBuildingChangesPerWeek",
            "code_individual": "ConstraintStudentsSetMaxBuildingChangesPerWeek",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "max_changes_week", "param_label": "أقصى تنقل أسبوعي",
            "param_val": 2, "param_min": 0, "param_max": 6, "param_unit": "مرات",
            "target_type": "students", "applies_to": "all", "selected_targets": [],
            "desc": "سقف تنقلات أسبوعي لكافة تلاميذ وأقسام المؤسسة."
        },
        {
            "id": "sc_s_7", "scope": "students", "main_cat": "space", "sub_cat": "students",
            "name": "العدد الأدنى من الفراغات بين تغيير البنايات لطلاب معينين",
            "name_en": "Min Gaps Between Building Changes for a Set of Students",
            "code": "ConstraintStudentsSetMinGapsBetweenBuildingChanges",
            "code_individual": "ConstraintStudentsSetMinGapsBetweenBuildingChanges",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "min_gaps_building", "param_label": "فراغ الانتقال بين المباني",
            "param_val": 1, "param_min": 1, "param_max": 2, "param_unit": "حصص",
            "target_type": "students", "applies_to": "selected", "selected_targets": [],
            "desc": "فاصل زمني للقسم عند الانتقال من مبنى لآخر."
        },
        {
            "id": "sc_s_8", "scope": "students", "main_cat": "space", "sub_cat": "students",
            "name": "العدد الأدنى من الفراغات بين تغيير البنايات للطلاب",
            "name_en": "Min Gaps Between Building Changes for All Students",
            "code": "ConstraintStudentsMinGapsBetweenBuildingChanges",
            "code_individual": "ConstraintStudentsSetMinGapsBetweenBuildingChanges",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "param_name": "min_gaps_building", "param_label": "فراغ الانتقال بين المباني",
            "param_val": 1, "param_min": 1, "param_max": 2, "param_unit": "حصص",
            "target_type": "students", "applies_to": "all", "selected_targets": [],
            "desc": "تعميم الفاصل الزمني للتنقل بين المباني على كافة التلاميذ."
        },

        # --- ح. قيود المواد والوسوم والمهام المكانية (6 قيود) ---
        {
            "id": "sc_sub_1", "scope": "subjects", "main_cat": "space", "sub_cat": "subjects",
            "name": "قاعة خاصة لمادة معينة",
            "name_en": "A Subject Has a Preferred Room",
            "code": "ConstraintSubjectPreferredRoom",
            "code_individual": "ConstraintSubjectPreferredRoom",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "subjects", "applies_to": "selected", "selected_targets": [],
            "desc": "تخصيص قاعة واحدة ثابتة للمادة (مثل قاعة المعلوميات أو الرسم)."
        },
        {
            "id": "sc_sub_2", "scope": "subjects", "main_cat": "space", "sub_cat": "subjects",
            "name": "عدة قاعات معينة لمادة معينة (تخصيص المختبرات والملاعب)",
            "name_en": "A Subject Has a Set of Preferred Rooms",
            "code": "ConstraintSubjectPreferredRooms",
            "code_individual": "ConstraintSubjectPreferredRooms",
            "def_weight": 100.0, "is_active": True, "is_primary": True,
            "target_type": "subjects", "applies_to": "all", "selected_targets": [],
            "desc": "تحديد مجموعة قاعات مخصصة للمادة (مختبرات علوم الحياة والأرض، مختبرات الفيزياء، وملاعب الرياضة)."
        },
        {
            "id": "sc_tag_1", "scope": "subjects", "main_cat": "space", "sub_cat": "subjects_tags",
            "name": "قاعة مفضلة لمادة ووسم مشترك",
            "name_en": "A Subject + Activity Tag Have a Preferred Room",
            "code": "ConstraintSubjectActivityTagPreferredRoom",
            "code_individual": "ConstraintSubjectActivityTagPreferredRoom",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "subjects", "applies_to": "selected", "selected_targets": [],
            "desc": "ربط مادة مع نوع النشاط بقاعة محددة (مثل: مادة الفيزياء + وسم 'أشغال تطبيقية' -> مختبر الفيزياء)."
        },
        {
            "id": "sc_tag_2", "scope": "subjects", "main_cat": "space", "sub_cat": "subjects_tags",
            "name": "عدة قاعات مفضلة لمادة ووسم مشترك",
            "name_en": "A Subject + Activity Tag Have a Set of Preferred Rooms",
            "code": "ConstraintSubjectActivityTagPreferredRooms",
            "code_individual": "ConstraintSubjectActivityTagPreferredRooms",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "subjects", "applies_to": "all", "selected_targets": [],
            "desc": "ربط مادة ونوع نشاط بمجموعة قاعات متوفرة."
        },
        {
            "id": "sc_act_1", "scope": "activities", "main_cat": "space", "sub_cat": "activities",
            "name": "قاعة مفضلة لمهمة معينة",
            "name_en": "An Activity Has a Preferred Room",
            "code": "ConstraintActivityPreferredRoom",
            "code_individual": "ConstraintActivityPreferredRoom",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "تعيين قاعة مخصصة لنشاط أو حصة واحدة بعينها دون غيرها."
        },
        {
            "id": "sc_act_2", "scope": "activities", "main_cat": "space", "sub_cat": "activities",
            "name": "قاعات مفضلة لمهمة معينة",
            "name_en": "An Activity Has a Set of Preferred Rooms",
            "code": "ConstraintActivityPreferredRooms",
            "code_individual": "ConstraintActivityPreferredRooms",
            "def_weight": 100.0, "is_active": False, "is_primary": False,
            "target_type": "activities", "applies_to": "selected", "selected_targets": [],
            "desc": "إتاحة خيارات من قاعات معينة لحصة واحدة محددة."
        }
    ]
    return constraints

if __name__ == "__main__":
    cl = get_68_constraints()
    print(f"Total constraints: {len(cl)}")
    time_c = [c for c in cl if c['main_cat'] == 'time']
    space_c = [c for c in cl if c['main_cat'] == 'space']
    primary_c = [c for c in cl if c.get('is_primary')]
    print(f"Time: {len(time_c)} (Basic: {len([c for c in time_c if c['sub_cat']=='basic'])}, Teachers: {len([c for c in time_c if c['sub_cat']=='teachers'])}, Students: {len([c for c in time_c if c['sub_cat']=='students'])}, Activities: {len([c for c in time_c if c['sub_cat']=='activities'])})")
    print(f"Space: {len(space_c)} (Basic: {len([c for c in space_c if c['sub_cat']=='basic'])}, Rooms: {len([c for c in space_c if c['sub_cat']=='rooms'])}, Teachers: {len([c for c in space_c if c['sub_cat']=='teachers'])}, Students: {len([c for c in space_c if c['sub_cat']=='students'])}, Subjects: {len([c for c in space_c if c['sub_cat']=='subjects'])}, Subj+Tags: {len([c for c in space_c if c['sub_cat']=='subjects_tags'])}, Activities: {len([c for c in space_c if c['sub_cat']=='activities'])})")
    print(f"Primary Core: {len(primary_c)}")
