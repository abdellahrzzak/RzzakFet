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

import sys
import shutil

def get_mobility_data_file(filename: str = 'student_mobility_state.json') -> str:
    appdata_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "RzzakFet", "data")
    appdata_path = os.path.join(appdata_dir, filename)
    candidates = [
        appdata_path,
        os.path.join(os.getcwd(), 'data', filename),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', filename),
    ]
    if getattr(sys, '_MEIPASS', None):
        candidates.append(os.path.join(sys._MEIPASS, 'data', filename))
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, 'data', filename))
        candidates.append(os.path.join(exe_dir, '_internal', 'data', filename))

    for cand in candidates:
        if cand != appdata_path and os.path.exists(cand) and os.path.getsize(cand) > 10:
            try:
                os.makedirs(appdata_dir, exist_ok=True)
                if not os.path.exists(appdata_path) or os.path.getsize(appdata_path) < 10:
                    shutil.copy2(cand, appdata_path)
            except Exception:
                pass
            return appdata_path

    os.makedirs(appdata_dir, exist_ok=True)
    return appdata_path

STATE_FILE = get_mobility_data_file('student_mobility_state.json')

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
        self.is_custom_generated: bool = False
        self.load_state()

    def load_state(self):
        filename = 'student_mobility_state.json'
        appdata_path = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "RzzakFet", "data", filename)
        candidates = [
            self.state_file,
            appdata_path,
            os.path.join(os.getcwd(), 'data', filename),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', filename),
        ]
        if getattr(sys, '_MEIPASS', None):
            candidates.append(os.path.join(sys._MEIPASS, 'data', filename))
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            candidates.append(os.path.join(exe_dir, 'data', filename))
            candidates.append(os.path.join(exe_dir, '_internal', 'data', filename))

        loaded = False
        for path in candidates:
            if path and os.path.exists(path) and os.path.getsize(path) > 10:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.initial_students = data.get("initial_students", [])
                        self.current_students = data.get("current_students", [])
                        self.overrides = data.get("overrides", {})
                        self.institution_info = data.get("institution_info", self.institution_info)
                        self.is_custom_generated = data.get("is_custom_generated", False)
                        loaded = True
                        self.state_file = appdata_path
                        break
                except Exception as e:
                    print(f"Error loading student mobility state from {path}: {e}")

        if not loaded:
            self.state_file = appdata_path

    def save_state(self):
        appdata_path = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "RzzakFet", "data", "student_mobility_state.json")
        save_targets = [self.state_file, appdata_path]
        if not getattr(sys, 'frozen', False):
            repo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'student_mobility_state.json')
            if repo_path not in save_targets:
                save_targets.append(repo_path)

        data = {
            "initial_students": self.initial_students,
            "current_students": self.current_students,
            "overrides": self.overrides,
            "institution_info": self.institution_info,
            "is_custom_generated": self.is_custom_generated
        }

        for target in set(save_targets):
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                pass

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

    def _get_level_int(self, class_name: str) -> int:
        """استخراج رقم المستوى (1 أو 2 أو 3) من اسم القسم في الإعدادي والتأهيلي"""
        cn = str(class_name or '').strip().upper()
        if "TC" in cn or "جذع" in cn:
            return 1
        elif "1BAC" in cn or "أولى باك" in cn or "1-BAC" in cn:
            return 2
        elif "2BAC" in cn or "ثانية باك" in cn or "2-BAC" in cn:
            return 3
        elif cn.startswith("1") or "1APIC" in cn or "1AC" in cn or "الأولى" in cn:
            return 1
        elif cn.startswith("2") or "2APIC" in cn or "2AC" in cn or "الثانية" in cn:
            return 2
        elif cn.startswith("3") or "3APIC" in cn or "3AC" in cn or "الثالثة" in cn:
            return 3
        return 0

    def _extract_level(self, class_name: str) -> str:
        """استخراج المستوى الدراسي من اسم القسم بالصيغة المغربية الموحدة"""
        cn = str(class_name or '').strip().upper()
        if "TC" in cn or "جذع" in cn:
            return "الجذوع المشتركة (TC)"
        elif "1BAC" in cn or "أولى باك" in cn or "1-BAC" in cn:
            return "السنة الأولى باكالوريا (1BAC)"
        elif "2BAC" in cn or "ثانية باك" in cn or "2-BAC" in cn:
            return "السنة الثانية باكالوريا (2BAC)"
        elif cn.startswith("1") or "الأولى" in cn or "1AC" in cn or "1APIC" in cn:
            return "السنة الأولى إعدادي (1APIC)"
        elif cn.startswith("2") or "الثانية" in cn or "2AC" in cn or "2APIC" in cn:
            return "السنة الثانية إعدادي (2APIC)"
        elif cn.startswith("3") or "الثالثة" in cn or "3AC" in cn or "3APIC" in cn:
            return "السنة الثالثة إعدادي (3APIC)"
        return "التعليم المدرسي"

    def generate_virtual_students_for_level(self, level_int: int, class_names: List[str], cycle: str = "middle") -> Dict[str, Any]:
        """
        توليد لائحة افتراضية متوازنة لتلاميذ مستوى معين (1 أو 2 أو 3):
        - يتراوح عدد التلاميذ في كل قسم بدقة بين 30 و 40 تلميذاً.
        - أسماء مغربية أصيلة، رموز مسار صحيحة، ر-ت مرتب تصاعدياً داخل كل قسم.
        - تحديث القائمة الأولية والحالية للمستوى.
        """
        import random
        if cycle == "qualifying":
            level_map = {
                1: "الجذوع المشتركة (TC)",
                2: "السنة الأولى باكالوريا (1BAC)",
                3: "السنة الثانية باكالوريا (2BAC)"
            }
        else:
            level_map = {
                1: "السنة الأولى إعدادي (1APIC)",
                2: "السنة الثانية إعدادي (2APIC)",
                3: "السنة الثالثة إعدادي (3APIC)"
            }
        level_name = level_map.get(level_int, f"المستوى {level_int}")
        
        first_names_m = [
            "محمد", "أحمد", "يوسف", "حمزة", "أنس", "أيوب", "عمر", "إلياس", "سعد", "بلال", 
            "عثمان", "رضا", "ياسين", "مهدي", "أمين", "علي", "وليد", "أيمن", "زياد", "طه", 
            "إسماعيل", "زكرياء", "سامي", "سفيان", "معاد", "آدم", "حاتم", "بدر"
        ]
        first_names_f = [
            "فاطمة الزهراء", "مريم", "إيمان", "سلمى", "خديجة", "آية", "زينب", "سارة", "هبة", 
            "دعاء", "وئام", "بسمة", "سناء", "نهيلة", "حفصة", "مروة", "شيماء", "ياسمين", 
            "صفاء", "رانيا", "كوثر", "نور", "إكرام", "غيثة", "أميمة", "ريم"
        ]
        last_names = [
            "العلوي", "الإدريسي", "العماري", "التازي", "المرابط", "الناصري", "الصديقي", 
            "بنعلي", "البقالي", "الفاسي", "الشريف", "الداودي", "البركة", "المنصوري", 
            "الورتي", "الشاوي", "الخطابي", "العلمي", "الودغيري", "الزهراوي", "الصقلي", 
            "المريني", "أمغار", "بنجلون", "العمراني", "الجعفري", "الصباحي"
        ]
        letters = ["K", "M", "G", "J", "L", "R", "D"]

        # إزالة تلاميذ هذا المستوى السابقين للحفاظ على التناسق التام
        self.initial_students = [s for s in self.initial_students if self._get_level_int(s.get("student_class", "")) != level_int]
        self.current_students = [s for s in self.current_students if self._get_level_int(s.get("student_class", "")) != level_int]
        curr_codes = {s["massar_code"] for s in self.current_students} | {s["massar_code"] for s in self.initial_students}
        self.overrides = {k: v for k, v in self.overrides.items() if k in curr_codes}

        new_students = []
        classes_breakdown = {}
        total_level_students = 0

        # سنة الازدياد حسب المستوى
        birth_year = 2013 if level_int == 1 else (2012 if level_int == 2 else 2011)

        for cls in class_names:
            cls_count = random.randint(30, 40)
            classes_breakdown[cls] = cls_count
            total_level_students += cls_count
            for order_i in range(1, cls_count + 1):
                gender = "ذكر" if random.random() < 0.50 else "أنثى"
                fn = random.choice(first_names_m if gender == "ذكر" else first_names_f)
                ln = random.choice(last_names)
                prefix = random.choice(letters)
                c_code = f"{prefix}13{random.randint(1000000, 9999999)}"
                while any(s["massar_code"] == c_code for s in new_students) or c_code in curr_codes:
                    c_code = f"{prefix}13{random.randint(1000000, 9999999)}"
                
                b_month = random.randint(1, 12)
                b_day = random.randint(1, 28)
                dob = f"{birth_year}-{b_month:02d}-{b_day:02d}"

                st = {
                    "order_num": order_i,
                    "massar_code": c_code,
                    "first_name": fn,
                    "last_name": ln,
                    "full_name": f"{fn} {ln}",
                    "gender": gender,
                    "dob": dob,
                    "student_class": cls,
                    "level": level_name
                }
                new_students.append(st)

        for s in new_students:
            self.initial_students.append(dict(s))
            self.current_students.append(dict(s))

        self.is_custom_generated = True
        self.save_state()
        return {
            "success": True,
            "level_int": level_int,
            "level_name": level_name,
            "total_students": total_level_students,
            "classes_count": len(class_names),
            "classes_breakdown": classes_breakdown,
            "students_sample": new_students[:5]
        }

    def export_level_students_excel(self, level_int: int, cycle: str = "middle") -> io.BytesIO:
        """
        توليد ملف إكسيل للائحة تلاميذ مستوى معين مطابق تماماً للترويسة الرسمية المطلوبة:
        | ر - ت | رقم مسار | الإسم الكامل | القسم الحالي |
        """
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"المستوى {level_int}"
        ws.views.sheetView[0].rightToLeft = True

        if cycle == "qualifying":
            level_titles = {
                1: "الجذوع المشتركة (Troncs Communs)",
                2: "السنة الأولى باكالوريا (1BAC)",
                3: "السنة الثانية باكالوريا (2BAC)"
            }
        else:
            level_titles = {
                1: "السنة الأولى إعدادي (1APIC)",
                2: "السنة الثانية إعدادي (2APIC)",
                3: "السنة الثالثة إعدادي (3APIC)"
            }
        lvl_title = level_titles.get(level_int, f"المستوى {level_int}")
        inst = self.institution_info

        # ألوان وتنسيقات الترويسة المطابقة للصورة (لون فوشيا/أرجواني مميز مع خط داكن)
        header_fill = PatternFill(start_color="FF66FF", end_color="FF66FF", fill_type="solid")
        header_font = Font(name="Calibri", size=13, bold=True, color="000000")
        title_font = Font(name="Calibri", size=14, bold=True, color="0F172A")
        sub_font = Font(name="Calibri", size=10, bold=False, color="475569")
        data_font = Font(name="Calibri", size=11, bold=False, color="000000")
        bold_data_font = Font(name="Calibri", size=11, bold=True, color="000000")
        
        border_side = Side(style='medium', color='000000')
        thin_side = Side(style='thin', color='4B5563')
        
        header_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        # الترويسة المؤسساتية في الأعلى
        ws.merge_cells("A1:D1")
        ws["A1"] = f"المملكة المغربية — وزارة التربية الوطنية والتعليم الأولي والرياضة — {inst.get('school_name', '')}"
        ws["A1"].font = sub_font
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

        ws.merge_cells("A2:D2")
        ws["A2"] = f"لائحة تلاميذ {lvl_title} — الموسم الدراسي {inst.get('academic_year', '2026-2027')}"
        ws["A2"].font = title_font
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 28

        # سطر الترويسة الرسمي (السطر 4)
        headers = ["ر - ت", "رقم مسار", "الإسم الكامل", "القسم الحالي"]
        ws.row_dimensions[4].height = 30
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = header_border

        # استخراج وفرز تلاميذ المستوى
        level_students = [
            s for s in self.current_students 
            if self._get_level_int(s.get("student_class", "")) == level_int
        ]
        def sort_key(s):
            cls = s.get("student_class", "")
            order = s.get("order_num", 999)
            return (cls, order, s.get("full_name", ""))

        level_students.sort(key=sort_key)

        cur_row = 5
        last_cls = None
        cls_order_counter = 1

        for s in level_students:
            cls = s.get("student_class", "")
            if cls != last_cls:
                cls_order_counter = 1
                last_cls = cls

            ws.row_dimensions[cur_row].height = 22
            # ر - ت
            c1 = ws.cell(row=cur_row, column=1, value=cls_order_counter)
            c1.font = bold_data_font
            c1.alignment = Alignment(horizontal="center", vertical="center")
            c1.border = cell_border

            # رقم مسار
            c2 = ws.cell(row=cur_row, column=2, value=s.get("massar_code", ""))
            c2.font = data_font
            c2.alignment = Alignment(horizontal="center", vertical="center")
            c2.border = cell_border

            # الإسم الكامل
            c3 = ws.cell(row=cur_row, column=3, value=s.get("full_name", ""))
            c3.font = data_font
            c3.alignment = Alignment(horizontal="right", vertical="center")
            c3.border = cell_border

            # القسم الحالي
            c4 = ws.cell(row=cur_row, column=4, value=cls)
            c4.font = bold_data_font
            c4.alignment = Alignment(horizontal="center", vertical="center")
            c4.border = cell_border

            cur_row += 1
            cls_order_counter += 1

        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 22
        ws.column_dimensions['C'].width = 36
        ws.column_dimensions['D'].width = 20

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def get_class_occupancy(self, level_int: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        حساب نسبة شغل كل قسم بالأعداد الحية للتلاميذ لتحديد القسم الأقل عدداً بدقة
        """
        all_classes_set = set()
        for s in self.current_students:
            if s.get("student_class"):
                all_classes_set.add(s["student_class"])
        for s in self.initial_students:
            if s.get("student_class"):
                all_classes_set.add(s["student_class"])

        def cls_sort(c):
            lvl = self._get_level_int(c)
            return (lvl, c)

        sorted_classes = sorted(list(all_classes_set), key=cls_sort)

        results = []
        for c in sorted_classes:
            c_lvl = self._get_level_int(c)
            if level_int is not None and c_lvl != level_int:
                continue

            curr_count = sum(1 for s in self.current_students if s.get("student_class") == c)
            init_count = sum(1 for s in self.initial_students if s.get("student_class") == c)

            results.append({
                "class_name": c,
                "level_int": c_lvl,
                "level_name": self._extract_level(c),
                "current_count": curr_count,
                "initial_count": init_count,
                "difference": curr_count - init_count,
                "is_lowest": False
            })

        # تحديد الأقل عدداً لكل مستوى
        by_level = {}
        for r in results:
            lvl = r["level_int"]
            by_level.setdefault(lvl, []).append(r)

        for lvl, clist in by_level.items():
            if clist:
                min_c = min(r["current_count"] for r in clist)
                for r in clist:
                    if r["current_count"] == min_c:
                        r["is_lowest"] = True

        return results

    def add_incoming_student(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        إضافة تلميذ وافد جديد وإلحاقه بقسم محدد مع الحفاظ على التوازن الرياضي
        """
        code = str(data.get("massar_code", "")).strip()
        full_name = str(data.get("full_name", "")).strip()
        student_class = str(data.get("student_class", "")).strip()
        gender = str(data.get("gender", "ذكر")).strip()
        dob = str(data.get("dob", "")).strip()
        status = str(data.get("status", "وافد")).strip()
        if status not in ["وافد", "مدمج"]:
            status = "وافد"

        if not code:
            import random
            code = f"W13{random.randint(1000000, 9999999)}"
        if not full_name:
            full_name = f"تلميذ وافد ({code})"

        level = self._extract_level(student_class)
        cls_count = sum(1 for s in self.current_students if s.get("student_class") == student_class)

        new_student = {
            "order_num": cls_count + 1,
            "massar_code": code,
            "first_name": full_name.split()[0] if " " in full_name else full_name,
            "last_name": " ".join(full_name.split()[1:]) if " " in full_name else "",
            "full_name": full_name,
            "gender": gender,
            "dob": dob,
            "student_class": student_class,
            "level": level
        }

        self.current_students = [s for s in self.current_students if s["massar_code"] != code]
        self.current_students.append(new_student)
        self.overrides[code] = status
        self.save_state()

        return {
            "success": True,
            "student": new_student,
            "status": status,
            "summary": self.compute_mobility_analysis(),
            "occupancy": self.get_class_occupancy(self._get_level_int(student_class))
        }

    def record_departure(self, massar_code: str, status: str = "مغادر") -> Dict[str, Any]:
        """
        تسجيل مغادرة أو عدم التحاق أو انقطاع تلميذ ونقصه من قسمه الفعلي
        """
        valid_statuses = ["مغادر", "غير ملتحق", "منقطع"]
        if status not in valid_statuses:
            status = "مغادر"

        code = str(massar_code).strip()
        student_obj = next((s for s in self.current_students if s["massar_code"] == code), None)
        if not student_obj:
            student_obj = next((s for s in self.initial_students if s["massar_code"] == code), None)

        if not student_obj:
            return {"success": False, "error": f"لم يتم العثور على التلميذ برقم مسار {code}"}

        # إزالة التلميذ من القائمة الحالية (Current Students) لنقص عدده من القسم
        self.current_students = [s for s in self.current_students if s["massar_code"] != code]

        # التأكد من وجوده في القائمة الأولية لضمان توازن المعادلة الرياضية
        if not any(s["massar_code"] == code for s in self.initial_students):
            self.initial_students.append(dict(student_obj))

        self.overrides[code] = status
        self.save_state()

        return {
            "success": True,
            "massar_code": code,
            "status": status,
            "student_class": student_obj.get("student_class", ""),
            "summary": self.compute_mobility_analysis(),
            "occupancy": self.get_class_occupancy(self._get_level_int(student_obj.get("student_class", "")))
        }

    def transfer_student_class(self, massar_code: str, new_class: str) -> Dict[str, Any]:
        """
        تغيير قسم التلميذ داخلياً ونقله من قسمه السابق إلى القسم الجديد
        """
        code = str(massar_code).strip()
        student_obj = next((s for s in self.current_students if s["massar_code"] == code), None)
        if not student_obj:
            return {"success": False, "error": f"لم يتم العثور على التلميذ {code} في القائمة الحالية"}

        old_class = student_obj.get("student_class", "")
        if old_class == new_class:
            return {"success": False, "error": "القسم الجديد هو نفسه القسم الحالي للتلميذ"}

        # التأكد من حفظ حالته الأولية بالقسم القديم إن لم تكن مسجلة
        init_s = next((s for s in self.initial_students if s["massar_code"] == code), None)
        if not init_s:
            init_record = dict(student_obj)
            init_record["student_class"] = old_class
            self.initial_students.append(init_record)

        # تحديث قسم التلميذ في القائمة الحالية
        student_obj["student_class"] = new_class
        student_obj["level"] = self._extract_level(new_class)
        self.save_state()

        return {
            "success": True,
            "massar_code": code,
            "old_class": old_class,
            "new_class": new_class,
            "summary": self.compute_mobility_analysis(),
            "occupancy": self.get_class_occupancy(self._get_level_int(new_class))
        }

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
            # إذا لم تكن هناك بيانات مسار حقيقية أو لوائح مولدة مسبقاً، ننشئ عينة تطابق بدقة أعداد البنية
            if not self.is_custom_generated and total_struct > 0 and (not self.initial_students or len(self.initial_students) in [622, 850]):
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
