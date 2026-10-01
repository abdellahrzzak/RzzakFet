# -*- coding: utf-8 -*-
"""
محرك «المعين في ضبط حركية التلاميذ»
مستوحى من النموذج المعتمد للأستاذ محمد أهلمين
متوافق مع بنية ومخرجات منظومة «مسار» بوزارة التربية الوطنية والتعليم الأولي والرياضة.
"""

import os
import json
import io
import openpyxl
from typing import Dict, List, Any, Optional

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'student_mobility_state.json')

class StudentMobilityEngine:
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.initial_students: List[Dict[str, Any]] = []
        self.current_students: List[Dict[str, Any]] = []
        self.overrides: Dict[str, str] = {} # massar_code -> custom status
        self.institution_info: Dict[str, str] = {
            "academy": "أكاديمية جهة الرباط - سلا - القنيطرة",
            "province": "المديرية الإقليمية بالصخيرات - تمارة",
            "school_name": "الثانوية الإعدادية ابن خلدون",
            "academic_year": "2026-2027",
            "snapshot_date": "2026-09-28"
        }
        self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.initial_students = data.get("initial_students", [])
                    self.current_students = data.get("current_students", [])
                    self.overrides = data.get("overrides", {})
                    self.institution_info = data.get("institution_info", self.institution_info)
            except Exception as e:
                print(f"Error loading student mobility state: {e}")

    def save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "initial_students": self.initial_students,
                    "current_students": self.current_students,
                    "overrides": self.overrides,
                    "institution_info": self.institution_info
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving student mobility state: {e}")

    def parse_massar_excel(self, file_content_or_path, is_initial: bool = True) -> Dict[str, Any]:
        """
        قراءة وتفكيك ملف لوائح التلاميذ المصدر من مسار تلقائياً (.xlsx, .xls, .xlsm).
        يكتشف الأعمدة بذكاء (رقم مسار، الاسم، النسب، النوع، تاريخ الازدياد، القسم).
        """
        wb = None
        if isinstance(file_content_or_path, (str, bytes, io.BytesIO)):
            if isinstance(file_content_or_path, str) and os.path.exists(file_content_or_path):
                wb = openpyxl.load_workbook(file_content_or_path, data_only=True)
            elif isinstance(file_content_or_path, bytes):
                wb = openpyxl.load_workbook(io.BytesIO(file_content_or_path), data_only=True)
            elif isinstance(file_content_or_path, io.BytesIO):
                wb = openpyxl.load_workbook(file_content_or_path, data_only=True)

        if not wb:
            raise ValueError("تعذر فتح ملف الإكسيل المحدد.")

        sheet = wb.active
        # فحص الصفوف للعثور على ترويسة الجدول أو البيانات
        headers_row = -1
        code_idx = -1
        fname_idx = -1
        lname_idx = -1
        gender_idx = -1
        dob_idx = -1
        class_idx = -1

        academy = ""
        province = ""
        school_name = ""
        academic_year = ""

        # استخراج بيانات المؤسسة من الترويسة الأولى إن وجدت
        for r in range(1, 15):
            for c in range(1, 15):
                val = str(sheet.cell(r, c).value or '').strip()
                if "أكاديمية" in val or "الأكاديمية" in val:
                    academy = val
                elif "المديرية" in val:
                    province = val
                elif "مؤسسة" in val or "المؤسسة" in val or "ثانوية" in val:
                    school_name = val
                elif "202" in val and ("-" in val or "/" in val):
                    academic_year = val

        # البحث عن أعمدة الجدول
        for r in range(1, 18):
            row_vals = [str(sheet.cell(r, c).value or '').strip() for c in range(1, 20)]
            for idx, val in enumerate(row_vals):
                val_l = val.lower()
                if any(k in val for k in ["رقم مسار", "الرمز", "رمز التلميذ", "code massar"]):
                    code_idx = idx + 1
                    headers_row = r
                if any(k in val for k in ["الاسم الشخصي", "الاسم", "prenom"]):
                    fname_idx = idx + 1
                if any(k in val for k in ["النسب", "الاسم العائلي", "nom"]):
                    lname_idx = idx + 1
                if any(k in val for k in ["النوع", "الجنس", "sexe", "ج"]):
                    gender_idx = idx + 1
                if any(k in val for k in ["تاريخ الازدياد", "تاريخ الميلاد", "date naiss"]):
                    dob_idx = idx + 1
                if any(k in val for k in ["القسم", "الفصل", "classe"]):
                    class_idx = idx + 1

            if code_idx != -1 and (fname_idx != -1 or lname_idx != -1 or class_idx != -1):
                headers_row = r
                break

        # إذا لم يتم العثور على ترويسة صريحة، نعتمد الترتيب القياسي لنموذج أهلمين ومسار:
        # Col 3: رقم مسار, Col 4: النسب/الاسم, Col 5: الاسم, Col 6: النوع, Col 7: تاريخ الازدياد, Col 10: القسم
        if code_idx == -1:
            headers_row = 10
            code_idx = 3
            lname_idx = 4
            fname_idx = 5
            gender_idx = 6
            dob_idx = 7
            class_idx = 10

        students = []
        for r in range(headers_row + 1, sheet.max_row + 1):
            code = str(sheet.cell(r, code_idx).value or '').strip()
            if not code or code.lower() in ["x", "none", "0", "الرمز", "رقم مسار"]:
                continue

            fname = str(sheet.cell(r, fname_idx).value or '').strip() if fname_idx != -1 else ""
            lname = str(sheet.cell(r, lname_idx).value or '').strip() if lname_idx != -1 else ""
            gender = str(sheet.cell(r, gender_idx).value or '').strip() if gender_idx != -1 else "ذكر"
            # توحيد صيغة الجنس
            if any(k in gender.lower() for k in ["أنثى", "f", "انثى", "female"]):
                gender = "أنثى"
            else:
                gender = "ذكر"

            dob = str(sheet.cell(r, dob_idx).value or '').strip() if dob_idx != -1 else ""
            if " 00:00:00" in dob:
                dob = dob.replace(" 00:00:00", "")

            student_class = str(sheet.cell(r, class_idx).value or '').strip() if class_idx != -1 else "1/1"

            students.append({
                "massar_code": code,
                "first_name": fname,
                "last_name": lname,
                "full_name": f"{fname} {lname}".strip() or code,
                "gender": gender,
                "dob": dob,
                "student_class": student_class,
                "level": self._extract_level(student_class)
            })

        if is_initial:
            self.initial_students = students
        else:
            self.current_students = students

        if school_name:
            self.institution_info["school_name"] = school_name
        if academy:
            self.institution_info["academy"] = academy
        if province:
            self.institution_info["province"] = province
        if academic_year:
            self.institution_info["academic_year"] = academic_year

        self.save_state()
        return {
            "success": True,
            "count": len(students),
            "is_initial": is_initial,
            "institution": self.institution_info
        }

    def _extract_level(self, class_name: str) -> str:
        """استخراج المستوى الدراسي من اسم القسم"""
        cn = class_name.strip()
        if cn.startswith("1") or "الأولى" in cn or "1AC" in cn or "1APIC" in cn:
            return "الأولى إعدادي (1AC)"
        elif cn.startswith("2") or "الثانية" in cn or "2AC" in cn or "2APIC" in cn:
            return "الثانية إعدادي (2AC)"
        elif cn.startswith("3") or "الثالثة" in cn or "3AC" in cn or "3APIC" in cn:
            return "الثالثة إعدادي (3AC)"
        elif "جذع" in cn or "TC" in cn or "TCS" in cn or "TCL" in cn:
            return "الجذع المشترك (TC)"
        elif "1BAC" in cn or "أولى باك" in cn:
            return "الأولى بكالوريا (1BAC)"
        elif "2BAC" in cn or "ثانية باك" in cn:
            return "الثانية بكالوريا (2BAC)"
        return "سلك التعليم الثانوي الإعدادي"

    def set_student_override(self, massar_code: str, status: str):
        """
        تعديل التصنيف الفردي للتلميذ:
        للجدد: 'وافد' أو 'مدمج'
        للمغادرين: 'مغادر' أو 'غير ملتحق' أو 'منقطع'
        """
        valid_statuses = ["وافد", "مدمج", "مغادر", "غير ملتحق", "منقطع"]
        if status in valid_statuses:
            self.overrides[massar_code] = status
            self.save_state()
            return True
        return False

    def compute_mobility_analysis(self) -> Dict[str, Any]:
        """
        المحرك الرئيسي لمطابقة المعطيات الأولية بالحالية:
        1. الوافدون (وافد / مدمج)
        2. غير المتواجدين حالياً (مغادر / غير ملتحق / منقطع)
        3. مغيرو الأقسام (تغيير القسم الداخلي)
        4. المستمرون
        5. جدول الإحصاء الإجمالي الرسمي المتوازن
        """
        init_map = {s["massar_code"]: s for s in self.initial_students}
        curr_map = {s["massar_code"]: s for s in self.current_students}

        incoming_wafid = []
        incoming_moudmaj = []
        departed_moughadir = []
        departed_ghair_moultahaq = []
        departed_mounqatia = []
        class_changers = []
        stable_students = []

        # 1. التلاميذ الجدد (المتواجدون حالياً وغير الموجودين في البداية)
        for code, curr_s in curr_map.items():
            if code not in init_map:
                override = self.overrides.get(code, "وافد")
                record = dict(curr_s)
                record["mobility_status"] = override
                if override == "مدمج":
                    incoming_moudmaj.append(record)
                else:
                    incoming_wafid.append(record)
            else:
                # تلميذ موجود في القائمتين: فحص هل غير قسمه؟
                init_s = init_map[code]
                if init_s.get("student_class") != curr_s.get("student_class"):
                    record = dict(curr_s)
                    record["old_class"] = init_s.get("student_class")
                    record["new_class"] = curr_s.get("student_class")
                    record["mobility_status"] = "تغيير القسم"
                    class_changers.append(record)
                else:
                    stable_students.append(curr_s)

        # 2. التلاميذ غير الموجودين حالياً (كانوا في البداية واختفوا)
        for code, init_s in init_map.items():
            if code not in curr_map:
                override = self.overrides.get(code, "مغادر")
                record = dict(init_s)
                record["mobility_status"] = override
                if override == "غير ملتحق":
                    departed_ghair_moultahaq.append(record)
                elif override == "منقطع":
                    departed_mounqatia.append(record)
                else:
                    departed_moughadir.append(record)

        # 3. إحصائيات الدخول المدرسي المتوقع (Initial Baseline)
        expected_total = len(self.initial_students)
        expected_male = sum(1 for s in self.initial_students if s.get("gender") == "ذكر")
        expected_female = expected_total - expected_male

        # إحصائيات الوضعية الحالية (Current Actual)
        actual_total = len(self.current_students)
        actual_male = sum(1 for s in self.current_students if s.get("gender") == "ذكر")
        actual_female = actual_total - actual_male

        # إحصائيات الحركية حسب الجنس
        wafid_m = sum(1 for s in incoming_wafid if s.get("gender") == "ذكر")
        wafid_f = len(incoming_wafid) - wafid_m

        moudmaj_m = sum(1 for s in incoming_moudmaj if s.get("gender") == "ذكر")
        moudmaj_f = len(incoming_moudmaj) - moudmaj_m

        moughadir_m = sum(1 for s in departed_moughadir if s.get("gender") == "ذكر")
        moughadir_f = len(departed_moughadir) - moughadir_m

        ghair_m = sum(1 for s in departed_ghair_moultahaq if s.get("gender") == "ذكر")
        ghair_f = len(departed_ghair_moultahaq) - ghair_m

        mounqatia_m = sum(1 for s in departed_mounqatia if s.get("gender") == "ذكر")
        mounqatia_f = len(departed_mounqatia) - mounqatia_m

        # المعادلة الرياضية الرسمية:
        # المحسوب = (المتوقع + الوافدون + المدمجون) - (المغادرون + غير الملتحقين + المنقطعون)
        calc_male = (expected_male + wafid_m + moudmaj_m) - (moughadir_m + ghair_m + mounqatia_m)
        calc_female = (expected_female + wafid_f + moudmaj_f) - (moughadir_f + ghair_f + mounqatia_f)
        calc_total = calc_male + calc_female

        is_balanced = (calc_total == actual_total) and (calc_male == actual_male) and (calc_female == actual_female)

        # 4. جدول التوزيع حسب المستويات الدراسية مرتباً بيداغوجياً (الأولى ثم الثانية ثم الثالثة)
        def level_sort_order(lvl: str) -> int:
            if "1" in lvl or "أولى" in lvl:
                return 1
            if "2" in lvl or "ثانية" in lvl:
                return 2
            if "3" in lvl or "ثالثة" in lvl:
                return 3
            if "جدع" in lvl or "TC" in lvl:
                return 4
            if "1BAC" in lvl:
                return 5
            if "2BAC" in lvl:
                return 6
            return 99

        unique_levels = list(set(
            [s.get("level", "أخرى") for s in self.initial_students] +
            [s.get("level", "أخرى") for s in self.current_students]
        ))
        levels_set = sorted(unique_levels, key=level_sort_order)

        level_stats = []
        for lvl in levels_set:
            l_init = [s for s in self.initial_students if s.get("level") == lvl]
            l_curr = [s for s in self.current_students if s.get("level") == lvl]
            l_wafid = [s for s in incoming_wafid if s.get("level") == lvl]
            l_moudmaj = [s for s in incoming_moudmaj if s.get("level") == lvl]
            l_moughadir = [s for s in departed_moughadir if s.get("level") == lvl]
            l_ghair = [s for s in departed_ghair_moultahaq if s.get("level") == lvl]
            l_mounqatia = [s for s in departed_mounqatia if s.get("level") == lvl]
            l_changers = [s for s in class_changers if s.get("level") == lvl]

            level_stats.append({
                "level_name": lvl,
                "initial_count": len(l_init),
                "wafid_count": len(l_wafid),
                "moudmaj_count": len(l_moudmaj),
                "moughadir_count": len(l_moughadir),
                "ghair_count": len(l_ghair),
                "mounqatia_count": len(l_mounqatia),
                "changers_count": len(l_changers),
                "current_count": len(l_curr)
            })

        return {
            "success": True,
            "institution": self.institution_info,
            "summary_kpis": {
                "initial_total": expected_total,
                "initial_male": expected_male,
                "initial_female": expected_female,
                "current_actual_total": actual_total,
                "current_actual_male": actual_male,
                "current_actual_female": actual_female,
                "current_calc_total": calc_total,
                "current_calc_male": calc_male,
                "current_calc_female": calc_female,
                "is_balanced": is_balanced,
                "total_wafid": len(incoming_wafid),
                "total_moudmaj": len(incoming_moudmaj),
                "total_moughadir": len(departed_moughadir),
                "total_ghair_moultahaq": len(departed_ghair_moultahaq),
                "total_mounqatia": len(departed_mounqatia),
                "total_class_changers": len(class_changers)
            },
            "master_balance_table": {
                "rows": [
                    {
                        "category": "الأعداد المتوقعة في الدخول المدرسي",
                        "male": expected_male,
                        "female": expected_female,
                        "total": expected_total
                    },
                    {
                        "category": "(+) الوافدون",
                        "male": wafid_m,
                        "female": wafid_f,
                        "total": len(incoming_wafid)
                    },
                    {
                        "category": "(+) المدمجون (المرجعون بعد انقطاع)",
                        "male": moudmaj_m,
                        "female": moudmaj_f,
                        "total": len(incoming_moudmaj)
                    },
                    {
                        "category": "(-) المغادرون",
                        "male": moughadir_m,
                        "female": moughadir_f,
                        "total": len(departed_moughadir)
                    },
                    {
                        "category": "(-) غير الملتحقين",
                        "male": ghair_m,
                        "female": ghair_f,
                        "total": len(departed_ghair_moultahaq)
                    },
                    {
                        "category": "(-) المنقطعون",
                        "male": mounqatia_m,
                        "female": mounqatia_f,
                        "total": len(departed_mounqatia)
                    },
                    {
                        "category": "(=) العدد الحالي المحسوب بالتوازن",
                        "male": calc_male,
                        "female": calc_female,
                        "total": calc_total,
                        "is_highlight": True
                    },
                    {
                        "category": "العدد الحالي الفعلي المستخرج من مسار",
                        "male": actual_male,
                        "female": actual_female,
                        "total": actual_total,
                        "is_verified": is_balanced
                    }
                ],
                "formula_note": "القاعدة الرسمية: العدد الحالي = (المتوقع + الوافدون + المدمجون) - (المغادرون + غير الملتحقين + المنقطعون)"
            },
            "level_stats": level_stats,
            "lists": {
                "wafid": incoming_wafid,
                "moudmaj": incoming_moudmaj,
                "moughadir": departed_moughadir,
                "ghair_moultahaq": departed_ghair_moultahaq,
                "mounqatia": departed_mounqatia,
                "class_changers": class_changers
            }
        }

    def sync_with_institution_and_structure(self, institution=None, structure=None):
        """مزامنة بيانات المؤسسة والبنية التربوية تلقائياً مع محرك حركية التلاميذ"""
        import time
        if institution:
            name = getattr(institution, 'institution_name', None) or (institution.get('institution_name') if isinstance(institution, dict) else None)
            if name:
                self.institution_info["school_name"] = name
            acad = getattr(institution, 'academy', None) or (institution.get('academy') if isinstance(institution, dict) else None)
            if acad:
                self.institution_info["academy"] = acad
            prov = getattr(institution, 'province', None) or (institution.get('province') if isinstance(institution, dict) else None)
            if prov:
                self.institution_info["province"] = prov
            year = getattr(institution, 'academic_year', None) or (institution.get('academic_year') if isinstance(institution, dict) else None)
            if year:
                self.institution_info["academic_year"] = year
            self.institution_info["snapshot_date"] = time.strftime("%Y-%m-%d")

        if structure:
            s1 = getattr(structure, 'students_1_apic', None) or (structure.get('students_1_apic') or structure.get('s1') if isinstance(structure, dict) else None) or 0
            s2 = getattr(structure, 'students_2_apic', None) or (structure.get('students_2_apic') or structure.get('s2') if isinstance(structure, dict) else None) or 0
            s3 = getattr(structure, 'students_3_apic', None) or (structure.get('students_3_apic') or structure.get('s3') if isinstance(structure, dict) else None) or 0
            total_struct = s1 + s2 + s3
            # إذا لم تكن هناك بيانات مسار حقيقية محملة، ننشئ عينة تطابق بدقة أعداد البنية
            if total_struct > 0 and (not self.initial_students or len(self.initial_students) in [622, 850]):
                self.load_demo_sample_data(structure=structure, institution=institution)

    def load_demo_sample_data(self, structure=None, institution=None):
        """
        تحميل عينة بيانات واقعية تحاكي البنية التربوية للمؤسسة،
        تتضمن وافدين، مدمجين، مغادرين، غير ملتحقين، ومنقطعين ومغيري أقسام.
        """
        import random, time
        random.seed(42)

        if institution:
            name = getattr(institution, 'institution_name', None) or (institution.get('institution_name') if isinstance(institution, dict) else None)
            if name: self.institution_info["school_name"] = name
            acad = getattr(institution, 'academy', None) or (institution.get('academy') if isinstance(institution, dict) else None)
            if acad: self.institution_info["academy"] = acad
            prov = getattr(institution, 'province', None) or (institution.get('province') if isinstance(institution, dict) else None)
            if prov: self.institution_info["province"] = prov
            year = getattr(institution, 'academic_year', None) or (institution.get('academic_year') if isinstance(institution, dict) else None)
            if year: self.institution_info["academic_year"] = year
            self.institution_info["snapshot_date"] = time.strftime("%Y-%m-%d")

        # استخراج أعداد الأقسام والتلاميذ حسب البنية التربوية الفعلية
        c1_count = getattr(structure, 'classes_1_apic', 4) or 4
        c2_count = getattr(structure, 'classes_2_apic', 3) or 3
        c3_count = getattr(structure, 'classes_3_apic', 4) or 4
        s1_count = getattr(structure, 'students_1_apic', 444) or 444
        s2_count = getattr(structure, 'students_2_apic', 372) or 372
        s3_count = getattr(structure, 'students_3_apic', 550) or 550

        classes_1ac = [f"1/{i}" for i in range(1, c1_count + 1)]
        classes_2ac = [f"2/{i}" for i in range(1, c2_count + 1)]
        classes_3ac = [f"3/{i}" for i in range(1, c3_count + 1)]

        all_classes = classes_1ac + classes_2ac + classes_3ac
        students_init = []

        first_names_m = ["محمد", "أحمد", "يوسف", "حمزة", "أنس", "أيوب", "عمر", "إلياس", "سعد", "بلال", "عثمان", "رضا", "ياسين", "مهدي", "أمين", "علي"]
        first_names_f = ["فاطمة الزهراء", "مريم", "إيمان", "سلمى", "خديجة", "آية", "زينب", "سارة", "هبة", "دعاء", "وئام", "بسمة", "سناء", "نهيلة", "حفصة"]
        last_names = ["العلوي", "الإدريسي", "العماري", "التازي", "المرابط", "الناصري", "الصديقي", "بنعلي", "البقالي", "الفاسي", "الشريف", "الداودي", "البركة", "المنصوري", "الورتي"]

        code_counter = 10001
        
        # توزيع التلاميذ بدقة حسب أعداد البنية لكل مستوى
        def add_level_students(cls_list, total_count):
            nonlocal code_counter
            if not cls_list or total_count <= 0: return
            base_each = total_count // len(cls_list)
            rem = total_count % len(cls_list)
            for idx, cls in enumerate(cls_list):
                this_count = base_each + (1 if idx < rem else 0)
                for _ in range(this_count):
                    gender = "ذكر" if random.random() < 0.52 else "أنثى"
                    fn = random.choice(first_names_m if gender == "ذكر" else first_names_f)
                    ln = random.choice(last_names)
                    c_code = f"G{code_counter}"
                    code_counter += 1
                    dob = f"201{random.randint(1, 3)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                    students_init.append({
                        "massar_code": c_code,
                        "first_name": fn,
                        "last_name": ln,
                        "full_name": f"{fn} {ln}",
                        "gender": gender,
                        "dob": dob,
                        "student_class": cls,
                        "level": self._extract_level(cls)
                    })

        add_level_students(classes_1ac, s1_count)
        add_level_students(classes_2ac, s2_count)
        add_level_students(classes_3ac, s3_count)

        if not students_init:
            for cls in all_classes:
                count = 34 if "3/" in cls else 38
                for _ in range(count):
                    gender = "ذكر" if random.random() < 0.52 else "أنثى"
                    fn = random.choice(first_names_m if gender == "ذكر" else first_names_f)
                    ln = random.choice(last_names)
                    c_code = f"G{code_counter}"
                    code_counter += 1
                    dob = f"201{random.randint(1, 3)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                    students_init.append({
                        "massar_code": c_code,
                        "first_name": fn,
                        "last_name": ln,
                        "full_name": f"{fn} {ln}",
                        "gender": gender,
                        "dob": dob,
                        "student_class": cls,
                        "level": self._extract_level(cls)
                    })

        # إنشاء الوضعية الحالية مع الحركية الواقعية
        students_curr = []
        self.overrides = {}

        # 1. معظم التلاميذ مستمرون
        missing_count = 0
        for s in students_init:
            r = random.random()
            if r < 0.02:
                # مغادر
                self.overrides[s["massar_code"]] = "مغادر"
                missing_count += 1
            elif r < 0.03:
                # غير ملتحق
                self.overrides[s["massar_code"]] = "غير ملتحق"
                missing_count += 1
            elif r < 0.04:
                # منقطع
                self.overrides[s["massar_code"]] = "منقطع"
                missing_count += 1
            elif r < 0.065:
                # غير قسمه داخلياً!
                curr_s = dict(s)
                same_level_classes = [c for c in all_classes if c[0] == s["student_class"][0] and c != s["student_class"]]
                if same_level_classes:
                    curr_s["student_class"] = random.choice(same_level_classes)
                students_curr.append(curr_s)
            else:
                students_curr.append(dict(s))

        # 2. إضافة وافدين ومدمجين جدد
        for i in range(18):
            gender = "ذكر" if random.random() < 0.5 else "أنثى"
            fn = random.choice(first_names_m if gender == "ذكر" else first_names_f)
            ln = random.choice(last_names)
            c_code = f"G{code_counter}"
            code_counter += 1
            cls = random.choice(all_classes)
            dob = f"201{random.randint(1, 3)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            new_s = {
                "massar_code": c_code,
                "first_name": fn,
                "last_name": ln,
                "full_name": f"{fn} {ln}",
                "gender": gender,
                "dob": dob,
                "student_class": cls,
                "level": self._extract_level(cls)
            }
            if i < 4:
                self.overrides[c_code] = "مدمج"
            else:
                self.overrides[c_code] = "وافد"
            students_curr.append(new_s)

        self.initial_students = students_init
        self.current_students = students_curr
        self.save_state()
        return self.compute_mobility_analysis()

    def generate_excel_export(self) -> io.BytesIO:
        """
        توليد مصنف إكسيل متكامل ومطابق لنموذج أهلمين يضم:
        - ورقة الإحصاء الإجمالي لحركية التلاميذ
        - ورقة الوافدين
        - ورقة المدمجين
        - ورقة المغادرين
        - ورقة غير الملتحقين
        - ورقة المنقطعين
        - ورقة تغيير الأقسام
        """
        wb = openpyxl.Workbook()
        wb.remove(wb.active) # remove default sheet

        analysis = self.compute_mobility_analysis()
        inst = self.institution_info

        # الأنماط والتنسيقات
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=14, bold=True, color="0F172A")
        sub_font = Font(name="Calibri", size=10, bold=False, color="475569")
        bold_font = Font(name="Calibri", size=10, bold=True)
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )
        highlight_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        green_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")

        # 1. ورقة الإحصاء الإجمالي
        ws_sum = wb.create_sheet(title="الإحصاء الإجمالي")
        ws_sum.views.sheetView[0].rightToLeft = True

        ws_sum.merge_cells("A1:D1")
        ws_sum["A1"] = f"المملكة المغربية — وزارة التربية الوطنية — {inst.get('school_name', '')}"
        ws_sum["A1"].font = sub_font
        ws_sum["A1"].alignment = Alignment(horizontal="center")

        ws_sum.merge_cells("A2:D2")
        ws_sum["A2"] = "جدول الإحصاء الإجمالي لحركية التلاميذ (المعين في ضبط حركية التلاميذ)"
        ws_sum["A2"].font = title_font
        ws_sum["A2"].alignment = Alignment(horizontal="center")

        headers = ["البيان / الفئة", "ذكور", "إناث", "المجموع"]
        for col_num, h in enumerate(headers, 1):
            c = ws_sum.cell(row=4, column=col_num, value=h)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = thin_border

        cur_row = 5
        for r_data in analysis["master_balance_table"]["rows"]:
            ws_sum.cell(row=cur_row, column=1, value=r_data["category"]).border = thin_border
            ws_sum.cell(row=cur_row, column=2, value=r_data["male"]).border = thin_border
            ws_sum.cell(row=cur_row, column=3, value=r_data["female"]).border = thin_border
            ws_sum.cell(row=cur_row, column=4, value=r_data["total"]).border = thin_border

            ws_sum.cell(row=cur_row, column=1).font = bold_font if r_data.get("is_highlight") else Font(name="Calibri", size=10)
            for c_i in [2, 3, 4]:
                ws_sum.cell(row=cur_row, column=c_i).alignment = Alignment(horizontal="center")

            if r_data.get("is_highlight"):
                for c_i in range(1, 5):
                    ws_sum.cell(row=cur_row, column=c_i).fill = highlight_fill
            elif r_data.get("is_verified"):
                for c_i in range(1, 5):
                    ws_sum.cell(row=cur_row, column=c_i).fill = green_fill
            cur_row += 1

        # مسافة ثم جدول المستويات
        cur_row += 2
        ws_sum.merge_cells(f"A{cur_row}:H{cur_row}")
        ws_sum[f"A{cur_row}"] = "توزيع حركية التلاميذ حسب المستويات الدراسية"
        ws_sum[f"A{cur_row}"].font = Font(name="Calibri", size=12, bold=True)
        ws_sum[f"A{cur_row}"].alignment = Alignment(horizontal="center")
        cur_row += 1

        lvl_headers = ["المستوى الدراسي", "المتوقع", "الوافدون", "المدمجون", "المغادرون", "غير الملتحقين", "المنقطعون", "العدد الحالي"]
        for c_idx, lh in enumerate(lvl_headers, 1):
            c = ws_sum.cell(row=cur_row, column=c_idx, value=lh)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center")
            c.border = thin_border
        cur_row += 1

        for ls in analysis["level_stats"]:
            vals = [ls["level_name"], ls["initial_count"], ls["wafid_count"], ls["moudmaj_count"], ls["moughadir_count"], ls["ghair_count"], ls["mounqatia_count"], ls["current_count"]]
            for c_idx, v in enumerate(vals, 1):
                c = ws_sum.cell(row=cur_row, column=c_idx, value=v)
                c.border = thin_border
                c.alignment = Alignment(horizontal="center" if c_idx > 1 else "right")
            cur_row += 1

        # سطر المجموع الإجمالي لكافة المستويات
        total_vals = [
            "المجموع الإجمالي للمؤسسة",
            sum(ls["initial_count"] for ls in analysis["level_stats"]),
            sum(ls["wafid_count"] for ls in analysis["level_stats"]),
            sum(ls["moudmaj_count"] for ls in analysis["level_stats"]),
            sum(ls["moughadir_count"] for ls in analysis["level_stats"]),
            sum(ls["ghair_count"] for ls in analysis["level_stats"]),
            sum(ls["mounqatia_count"] for ls in analysis["level_stats"]),
            sum(ls["current_count"] for ls in analysis["level_stats"])
        ]
        for c_idx, v in enumerate(total_vals, 1):
            c = ws_sum.cell(row=cur_row, column=c_idx, value=v)
            c.border = thin_border
            c.font = bold_font
            c.fill = highlight_fill
            c.alignment = Alignment(horizontal="center" if c_idx > 1 else "right")
        cur_row += 1

        # 2. أوراق اللوائح الاسمية التفصيلية
        sheets_def = [
            ("الوافدون", analysis["lists"]["wafid"]),
            ("المدمجون", analysis["lists"]["moudmaj"]),
            ("المغادرون", analysis["lists"]["moughadir"]),
            ("غير الملتحقون", analysis["lists"]["ghair_moultahaq"]),
            ("المنقطعون", analysis["lists"]["mounqatia"]),
            ("تغيير الأقسام", analysis["lists"]["class_changers"])
        ]

        for s_title, s_list in sheets_def:
            ws = wb.create_sheet(title=s_title)
            ws.views.sheetView[0].rightToLeft = True

            ws.merge_cells("A1:G1")
            ws["A1"] = f"لائحة {s_title} — {inst.get('school_name', '')} ({inst.get('academic_year', '')})"
            ws["A1"].font = title_font
            ws["A1"].alignment = Alignment(horizontal="center")

            if s_title == "تغيير الأقسام":
                cols = ["ر.ت", "رقم مسار", "الاسم والنسب", "النوع", "القسم السابق", "القسم الجديد", "المستوى"]
            else:
                cols = ["ر.ت", "رقم مسار", "الاسم الكامل", "النوع", "تاريخ الازدياد", "القسم", "المستوى"]

            for c_num, col_name in enumerate(cols, 1):
                c = ws.cell(row=3, column=c_num, value=col_name)
                c.font = header_font
                c.fill = header_fill
                c.alignment = Alignment(horizontal="center")
                c.border = thin_border

            for r_idx, item in enumerate(s_list, 1):
                if s_title == "تغيير الأقسام":
                    row_data = [r_idx, item["massar_code"], item["full_name"], item["gender"], item.get("old_class", ""), item.get("new_class", ""), item["level"]]
                else:
                    row_data = [r_idx, item["massar_code"], item["full_name"], item["gender"], item.get("dob", ""), item.get("student_class", ""), item["level"]]

                for c_num, val in enumerate(row_data, 1):
                    c = ws.cell(row=3 + r_idx, column=c_num, value=val)
                    c.border = thin_border
                    c.alignment = Alignment(horizontal="center" if c_num in [1, 2, 4, 5, 6, 7] else "right")

        # ضبط عرض الأعمدة
        for s in wb.worksheets:
            for col in s.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                s.column_dimensions[col_letter].width = max(max_len + 3, 12)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

# Singleton instance
mobility_engine = StudentMobilityEngine()
