# -*- coding: utf-8 -*-
"""
محرك مسك وتتبع غياب التلاميذ (Student Attendance Engine)
برنامج RzzakFet - متوافق مع منظومة «مسار» بوزارة التربية الوطنية والتعليم الأولي والرياضة.
يدعم:
- استيراد لوائح التلاميذ من ملفات مسار المتعددة الأوراق (Multi-sheet Excel).
- الإدخال اليدوي المباشر لأسماء التلاميذ وترتيبهم.
- الإدخال السريع (Bulk Paste) للوائح الاسمية.
- مسك الغياب اليومي والحصصي (صباح/مساء، حصص 1-4، أو ساعات محددة).
- تبرير الغياب وتحديد الأسباب.
- الإحصائيات الشاملة، التقارير الفردية، وتصدير لوائح الغياب بصيغة Excel والطباعة الرسمية.
"""

import os
import io
import json
import uuid
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import sys
import shutil

def get_attendance_data_file(filename: str = 'students_attendance_state.json') -> str:
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

STATE_FILE = get_attendance_data_file('students_attendance_state.json')

# فترات الحصص المدرسية المغربية القياسية
DEFAULT_PERIODS = [
    {"id": "M_ALL", "name": "الفترة الصباحية كاملة (4 ساعات)", "session": "morning", "hours": 4},
    {"id": "M_1", "name": "الحصة 1 صباحاً (08:30 - 09:30)", "session": "morning", "hours": 1},
    {"id": "M_2", "name": "الحصة 2 صباحاً (09:30 - 10:30)", "session": "morning", "hours": 1},
    {"id": "M_3", "name": "الحصة 3 صباحاً (10:30 - 11:30)", "session": "morning", "hours": 1},
    {"id": "M_4", "name": "الحصة 4 صباحاً (11:30 - 12:30)", "session": "morning", "hours": 1},
    {"id": "A_ALL", "name": "الفترة المسائية كاملة (4 ساعات)", "session": "afternoon", "hours": 4},
    {"id": "A_1", "name": "الحصة 1 مساءً (14:30 - 15:30)", "session": "afternoon", "hours": 1},
    {"id": "A_2", "name": "الحصة 2 مساءً (15:30 - 16:30)", "session": "afternoon", "hours": 1},
    {"id": "A_3", "name": "الحصة 3 مساءً (16:30 - 17:30)", "session": "afternoon", "hours": 1},
    {"id": "A_4", "name": "الحصة 4 مساءً (17:30 - 18:30)", "session": "afternoon", "hours": 1},
    {"id": "DAY_ALL", "name": "اليوم الدراسي كاملاً (8 ساعات)", "session": "full_day", "hours": 8}
]

import re

def normalize_class_name(cname: str) -> str:
    """
    توحيد وتطبيع صيغ وأكواد الأقسام بمرونة تامة للربط الثنائي التام بين:
    - تسميات منظومة مسار (مثل: 1BACSEF-1, 1BACSHF-1, 2BACSPF-1, 2BACSVTF-1, 2BACLF-1, 2BACSHF-1, TCSF-1, TCLSHF-1)
    - تسميات الجداول والبنية التربوية FET (مثل: 1BAC-EXP-F-1, 1BAC-LSH-F-1, 2BAC-PC-F-1, 2BAC-SVT-F-1, 2BAC-L-F-1, 2BAC-SH-F-1, TC-SC-F-1, TC-LSH-F-1)
    - وتسميات السلك الإعدادي (مثل: 1/1, 1APIC-1, 1AC-1, 2/1, 3/1...)
    """
    if not cname:
        return ""
    c = str(cname).strip().upper()
    
    # 1. نمط السلك الإعدادي (مثل 1/1 أو 2-3 أو 3/2)
    m_slash = re.match(r'^([123])[\s/_-]+(\d+)$', c)
    if m_slash:
        return f"{m_slash.group(1)}AC-{m_slash.group(2)}"

    # استخراج رقم الفوج / القسم من النهاية إن وجد
    m_num = re.search(r'[-_ /]?(\d+)$', c)
    num = m_num.group(1) if m_num else ''
    stem = c[:m_num.start()] if m_num else c
    stem_clean = re.sub(r'[^A-Z0-9]', '', stem)

    # جداول التطابق القياسية للتعليم الثانوي التأهيلي والإعدادي بالمغرب
    mappings = [
        # الجذوع المشتركة
        (['TCSC', 'TCS', 'TCSCF', 'TCSF', 'TCSCBIOF'], 'TC-SC-F'),
        (['TCLSH', 'TCL', 'TCLSHF', 'TCLF', 'TCLSHBIOF', 'TCLBIOF'], 'TC-LSH-F'),
        (['TCTECH', 'TCT', 'TCTECHBIOF', 'TCTBIOF'], 'TC-TECH-F'),
        (['TCORIG', 'TCO'], 'TC-ORIG'),

        # الأولى باكالوريا
        (['1BACEXP', '1BACSE', '1BACEXPF', '1BACSEF', '1BACEXPBIOF', '1BACSEBIOF'], '1BAC-EXP-F'),
        (['1BACLSH', '1BACSH', '1BACLSHF', '1BACSHF', '1BACL', '1BACLF', '1BACLSHBIOF', '1BACLBIOF'], '1BAC-LSH-F'),
        (['1BACSM', '1BACSMF', '1BACSMBIOF'], '1BAC-SM-F'),
        (['1BACSEG', '1BACSEGF', '1BACECO', '1BACECOF'], '1BAC-SEG-F'),
        (['1BACSTE', '1BACSTEF'], '1BAC-STE-F'),
        (['1BACSTM', '1BACSTMF'], '1BAC-STM-F'),

        # الثانية باكالوريا
        (['2BACPC', '2BACSP', '2BACPCF', '2BACSPF', '2BACPCBIOF', '2BACSPBIOF'], '2BAC-PC-F'),
        (['2BACSVT', '2BACSVTF', '2BACSVTBIOF'], '2BAC-SVT-F'),
        (['2BACL', '2BACLF', '2BACLBIOF'], '2BAC-L-F'),
        (['2BACSH', '2BACSHF', '2BACSHBIOF'], '2BAC-SH-F'),
        (['2BACSMA', '2BACSMAF', '2BACSMABIOF'], '2BAC-SMA-F'),
        (['2BACSMB', '2BACSMBF', '2BACSMBBIOF'], '2BAC-SMB-F'),
        (['2BACECO', '2BACECOF', '2BACSEG', '2BACSEGF'], '2BAC-ECO-F'),
        (['2BACSTE', '2BACSTEF'], '2BAC-STE-F'),
        (['2BACSTM', '2BACSTMF'], '2BAC-STM-F'),

        # السلك الإعدادي
        (['1AC', '1APIC', '1ASC'], '1AC'),
        (['2AC', '2APIC', '2ASC'], '2AC'),
        (['3AC', '3APIC', '3ASC'], '3AC'),
    ]

    for syns, canon in mappings:
        syn_cleans = [re.sub(r'[^A-Z0-9]', '', s) for s in syns]
        if stem_clean in syn_cleans:
            return f"{canon}-{num}" if num else canon

    return f"{stem_clean}-{num}" if num else stem_clean

class StudentAttendanceEngine:
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.students_by_class: Dict[str, List[Dict[str, Any]]] = {}
        self.attendance_records: List[Dict[str, Any]] = []
        self.institution_info: Dict[str, str] = {
            "academy": "الأكاديمية الجهوية للتربية والتكوين",
            "province": "المديرية الإقليمية",
            "school_name": "المؤسسة التعليمية",
            "academic_year": "2026/2027"
        }
        self.load_state()

    def resolve_class_name(self, class_name: str) -> str:
        """
        حل وتطابق أسماء الأقسام بمرونة تامة وربط رمزي ثنائي الاتجاه بين:
        - تسميات مسار (مثل 1BACSEF-1, TCSF-1, 2BACSPF-1)
        - وتسميات الجداول والبنية التربوية FET (مثل 1BAC-EXP-F-1, TC-SC-F-1, 2BAC-PC-F-1)
        - والتسميات العادية ذات الشخطات أو بدونها (1/1 <-> 1APIC-1).
        """
        if not class_name:
            return ""
        # 1. التطابق المباشر التام
        if class_name in self.students_by_class:
            return class_name

        c_clean = str(class_name).strip()
        # 2. التطابق مع تجاهل حالة الأحرف والفراغات
        for key in self.students_by_class:
            if key.lower() == c_clean.lower():
                return key

        # 3. التطابق الرمزي عبر التحويل والتطبيع القياسي (Canonical Normalized Match)
        norm_target = normalize_class_name(c_clean)
        for key in self.students_by_class:
            if normalize_class_name(key) == norm_target:
                return key

        # 4. إذا لم يعثر على تطابق في القائمة الحالية، إرجاع الاسم كما هو
        return class_name

    def load_state(self):
        filename = 'students_attendance_state.json'
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
                        self.students_by_class = data.get("students_by_class", {})
                        self.attendance_records = data.get("attendance_records", [])
                        self.institution_info = data.get("institution_info", self.institution_info)
                        loaded = True
                        self.state_file = appdata_path
                        break
                except Exception as e:
                    print(f"[AttendanceEngine] Error loading state from {path}: {e}")

        if not loaded:
            self.state_file = appdata_path

    def save_state(self):
        appdata_path = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "RzzakFet", "data", "students_attendance_state.json")
        save_targets = [self.state_file, appdata_path]
        if not getattr(sys, 'frozen', False):
            repo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'students_attendance_state.json')
            if repo_path not in save_targets:
                save_targets.append(repo_path)

        data = {
            "students_by_class": self.students_by_class,
            "attendance_records": self.attendance_records,
            "institution_info": self.institution_info,
            "last_updated": datetime.now().isoformat()
        }

        for target in set(save_targets):
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                pass

    # =========================================================================
    # استيراد لوائح مسار من ملف إكسيل متعدد الأوراق (Massar Multi-sheet Excel)
    # =========================================================================
    def parse_massar_excel(self, file_content_or_path, clear_existing: bool = True) -> Dict[str, Any]:
        """
        قراءة وتفكيك ملف لوائح التلاميذ الصادر من منظومة مسار (ListEleve_*.xlsx).
        يدعم الملفات متعددة الأوراق (Multi-sheet) حيث تمثل كل ورقة قسماً مستقلاً،
        وكذلك الملفات ذات الورقة الواحدة.
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

        imported_classes = {}
        total_students_count = 0
        detected_inst = {}

        for sheet_idx, sheet_name in enumerate(wb.sheetnames):
            ws = wb[sheet_name]
            
            # محاولة قراءة بيانات المؤسسة من أول ورقة إن وجدت
            if sheet_idx == 0:
                for r in range(1, 10):
                    for c in range(1, 10):
                        v = str(ws.cell(r, c).value or '').strip()
                        if "الأكاديمية" in v or "أكاديمية" in v:
                            adj = str(ws.cell(r, c+1).value or '').strip() or str(ws.cell(r, c+2).value or '').strip()
                            if adj: detected_inst["academy"] = adj
                        elif "المديرية" in v:
                            adj = str(ws.cell(r, c+1).value or '').strip() or str(ws.cell(r, c+2).value or '').strip()
                            if adj: detected_inst["province"] = adj
                        elif "المؤسسة" in v or "مؤسسة" in v:
                            adj = str(ws.cell(r, c+1).value or '').strip() or str(ws.cell(r, c+2).value or '').strip()
                            if adj: detected_inst["school_name"] = adj
                        elif "السنة الدراسية" in v:
                            adj = str(ws.cell(r, c+1).value or '').strip() or str(ws.cell(r, c+2).value or '').strip()
                            if adj: detected_inst["academic_year"] = adj

            # 1. تحديد اسم القسم
            class_name = sheet_name.strip()
            for r in range(1, 12):
                for c in range(1, 10):
                    val = str(ws.cell(r, c).value or '').strip()
                    if "القسم" in val or "الفصل" in val or "classe" in val.lower():
                        adj = str(ws.cell(r, c+1).value or '').strip() or str(ws.cell(r, c+2).value or '').strip()
                        if adj and len(adj) >= 2:
                            class_name = adj
                            break

            # 2. البحث عن صف الترويسة والأعمدة
            header_row = -1
            order_col = 1
            code_col = 2
            lname_col = 3
            fname_col = 4
            gender_col = 5
            dob_col = 6
            birth_place_col = 7

            for r in range(1, 18):
                vals = [str(ws.cell(r, c).value or '').strip() for c in range(1, 15)]
                found_match = False
                for c_idx, val in enumerate(vals, 1):
                    val_l = val.lower()
                    if any(k in val_l for k in ['ر.ت', 'ترتيب', 'رقم الترتيب', 'n°', 'ordre']):
                        order_col = c_idx
                        found_match = True
                    elif any(k in val_l for k in ['الرمز', 'رقم مسار', 'code massar', 'massar', 'cne']):
                        code_col = c_idx
                        found_match = True
                    elif any(k in val_l for k in ['النسب', 'nom', 'الاسم العائلي']):
                        lname_col = c_idx
                        found_match = True
                    elif any(k in val_l for k in ['الإسم', 'الاسم', 'prenom', 'الاسم الشخصي']):
                        fname_col = c_idx
                        found_match = True
                    elif any(k in val_l for k in ['النوع', 'الجنس', 'sexe']):
                        gender_col = c_idx
                    elif any(k in val_l for k in ['تاريخ', 'naissance', 'né le']):
                        dob_col = c_idx
                    elif any(k in val_l for k in ['مكان الازدياد', 'lieu']):
                        birth_place_col = c_idx

                if found_match and (lname_col != -1 or fname_col != -1 or code_col != -1):
                    header_row = r
                    break

            if header_row == -1:
                header_row = 10  # الترويسة النموذجية لمسار

            sheet_students = []
            for r in range(header_row + 1, ws.max_row + 1):
                order_val = ws.cell(r, order_col).value
                code_val = ws.cell(r, code_col).value
                lname_val = str(ws.cell(r, lname_col).value or '').strip() if lname_col else ''
                fname_val = str(ws.cell(r, fname_col).value or '').strip() if fname_col else ''
                gender_val = str(ws.cell(r, gender_col).value or '').strip() if gender_col else ''
                dob_val = str(ws.cell(r, dob_col).value or '').strip() if dob_col else ''
                birth_place_val = str(ws.cell(r, birth_place_col).value or '').strip() if birth_place_col else ''

                # تخطي الصفوف الفارغة تماماً
                if not order_val and not code_val and not lname_val and not fname_val:
                    continue

                full_name = f"{lname_val} {fname_val}".strip() or f"{fname_val} {lname_val}".strip()
                if not full_name and code_val:
                    full_name = f"تلميذ {code_val}"

                # حساب رقم الترتيب
                try:
                    s_order = int(order_val)
                except (ValueError, TypeError):
                    s_order = len(sheet_students) + 1

                student_id = f"st_{uuid.uuid4().hex[:8]}"

                student_obj = {
                    "id": student_id,
                    "order": s_order,
                    "massar_code": str(code_val or '').strip(),
                    "last_name": lname_val,
                    "first_name": fname_val,
                    "full_name": full_name,
                    "gender": gender_val if gender_val in ['ذكر', 'أنثى'] else ('أنثى' if 'أنث' in gender_val or gender_val.lower() == 'f' else 'ذكر'),
                    "dob": dob_val,
                    "birth_place": birth_place_val,
                    "class_name": class_name
                }
                sheet_students.append(student_obj)

            if sheet_students:
                # فرز التلاميذ حسب رقم الترتيب
                sheet_students.sort(key=lambda s: s["order"])
                imported_classes[class_name] = sheet_students
                total_students_count += len(sheet_students)

        # تحديث بيانات المؤسسة إن توفرت
        if detected_inst:
            for k, v in detected_inst.items():
                if v: self.institution_info[k] = v

        # استبدال لوائح الأقسام بالملف المستورد حديثاً بالكامل لمنع تراكم الأقسام الوهمية
        if clear_existing or not self.students_by_class:
            self.students_by_class = imported_classes
        else:
            for cname, s_list in imported_classes.items():
                self.students_by_class[cname] = s_list

        # تنظيف فوري لأي أقسام وهمية فارغة ذات 0 تلميذ
        if any(len(sl) > 0 for sl in self.students_by_class.values()):
            self.students_by_class = {c: sl for c, sl in self.students_by_class.items() if len(sl) > 0}

        self.save_state()

        return {
            "success": True,
            "classes_count": len(self.students_by_class),
            "students_count": total_students_count,
            "classes": list(self.students_by_class.keys()),
            "institution_info": self.institution_info
        }

    # =========================================================================
    # استيراد تلقائي من مسار مجلد التحميلات C:\Users\Hp\Downloads\check
    # =========================================================================
    def import_from_check_folder(self, folder_path: str = r"C:\Users\Hp\Downloads\check") -> Dict[str, Any]:
        """
        فحص المجلد المذكور واستيراد أول ملف Excel متواجد به تلقائياً.
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"المجلد غير موجود: {folder_path}")

        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.xlsx', '.xls', '.xlsm'))]
        if not files:
            raise FileNotFoundError(f"لم يتم العثور على أي ملف Excel في المجلد: {folder_path}")

        # نختار أحدث ملف أو الملف الذي يبدأ بـ ListEleve
        target_file = None
        for f in files:
            if f.lower().startswith('listeleve'):
                target_file = os.path.join(folder_path, f)
                break
        if not target_file:
            target_file = os.path.join(folder_path, files[0])

        return self.parse_massar_excel(target_file, clear_existing=True)

    # =========================================================================
    # العمليات المباشرة على التلاميذ (إضافة، تعديل، حذف، مسح)
    # =========================================================================
    def get_classes_summary(self) -> List[Dict[str, Any]]:
        """إرجاع ملخص بكافة الأقسام وعدد التلاميذ في كل قسم ونسب الذكور والإناث"""
        summary = []
        for cname, s_list in self.students_by_class.items():
            males = sum(1 for s in s_list if s.get("gender") == "ذكر")
            females = sum(1 for s in s_list if s.get("gender") == "أنثى")
            summary.append({
                "class_name": cname,
                "total_students": len(s_list),
                "males": males,
                "females": females
            })
        summary.sort(key=lambda x: x["class_name"])
        return summary

    def get_students_for_class(self, class_name: str) -> List[Dict[str, Any]]:
        """إرجاع قائمة تلاميذ قسم معين مرتبين برقم الترتيب، مع دعم حل الأسماء البديلة تلقائياً"""
        resolved = self.resolve_class_name(class_name)
        s_list = self.students_by_class.get(resolved, [])
        return sorted(s_list, key=lambda s: s.get("order", 0))

    def add_student(self, class_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """إضافة تلميذ جديد لقسم معين"""
        if not class_name:
            raise ValueError("يجب تحديد القسم.")
        resolved = self.resolve_class_name(class_name)
        if resolved not in self.students_by_class:
            self.students_by_class[resolved] = []

        c_students = self.students_by_class[resolved]
        next_order = len(c_students) + 1
        custom_order = data.get("order")
        try:
            order_val = int(custom_order) if custom_order else next_order
        except (ValueError, TypeError):
            order_val = next_order

        full_name = data.get("full_name", "").strip()
        last_name = data.get("last_name", "").strip()
        first_name = data.get("first_name", "").strip()

        if not full_name and (last_name or first_name):
            full_name = f"{last_name} {first_name}".strip()
        elif full_name and not last_name and not first_name:
            parts = full_name.split()
            if len(parts) >= 2:
                last_name = parts[0]
                first_name = " ".join(parts[1:])
            else:
                last_name = full_name
                first_name = ""

        if not full_name:
            raise ValueError("يجب إدخال اسم التلميذ.")

        student_id = data.get("id") or f"st_{uuid.uuid4().hex[:8]}"

        new_student = {
            "id": student_id,
            "order": order_val,
            "massar_code": data.get("massar_code", "").strip(),
            "last_name": last_name,
            "first_name": first_name,
            "full_name": full_name,
            "gender": data.get("gender", "ذكر"),
            "dob": data.get("dob", ""),
            "birth_place": data.get("birth_place", ""),
            "class_name": resolved
        }

        c_students.append(new_student)
        c_students.sort(key=lambda s: s.get("order", 0))
        self.save_state()

        return {"success": True, "student": new_student, "total": len(c_students)}

    def bulk_add_students(self, class_name: str, raw_text: str) -> Dict[str, Any]:
        """
        إضافة سريعة لمجموعة من التلاميذ عن طريق لصق أسمائهم سطر بسطر.
        السطر يمكن أن يكون:
        - الاسم والنسب فقط
        - أو: رقم الترتيب - الاسم والنسب
        - أو: رقم الترتيب [tab] الرمز [tab] النسب [tab] الاسم
        """
        if not class_name:
            raise ValueError("يجب تحديد القسم.")
        resolved = self.resolve_class_name(class_name)
        if resolved not in self.students_by_class:
            self.students_by_class[resolved] = []

        c_students = self.students_by_class[resolved]
        lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]
        
        added_count = 0
        curr_order = len(c_students) + 1

        for line in lines:
            parts = line.split('\t') if '\t' in line else line.split(';') if ';' in line else [line]
            
            s_order = curr_order
            s_code = ""
            s_name = ""
            s_gender = "ذكر"
            s_dob = ""

            if len(parts) >= 4:
                # نمط جدول: ر.ت / رمز / نسب / إسم
                try: s_order = int(parts[0])
                except: s_order = curr_order
                s_code = parts[1].strip()
                s_name = f"{parts[2].strip()} {parts[3].strip()}"
                if len(parts) >= 5: s_gender = parts[4].strip()
                if len(parts) >= 6: s_dob = parts[5].strip()
            elif len(parts) >= 2 and parts[0].isdigit():
                s_order = int(parts[0])
                s_name = parts[1].strip()
            else:
                # سطر عادي: قد يبدأ برقم ترتيب متبوع بنقطة أو خط مائل (مثال: "1. علي بناني" أو "1 - علي")
                cleaned = line
                import re
                m = re.match(r'^(\d+)[\.\-\s]+(.+)$', line)
                if m:
                    s_order = int(m.group(1))
                    s_name = m.group(2).strip()
                else:
                    s_name = line.strip()

            if s_name:
                student_id = f"st_{uuid.uuid4().hex[:8]}"
                new_student = {
                    "id": student_id,
                    "order": s_order,
                    "massar_code": s_code,
                    "last_name": "",
                    "first_name": "",
                    "full_name": s_name,
                    "gender": s_gender if s_gender in ['ذكر', 'أنثى'] else 'ذكر',
                    "dob": s_dob,
                    "birth_place": "",
                    "class_name": resolved
                }
                c_students.append(new_student)
                added_count += 1
                curr_order += 1

        c_students.sort(key=lambda s: s.get("order", 0))
        self.save_state()

        return {"success": True, "added_count": added_count, "total_class": len(c_students)}

    def update_student(self, class_name: str, student_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """تحديث بيانات تلميذ"""
        resolved = self.resolve_class_name(class_name)
        if resolved not in self.students_by_class:
            raise ValueError(f"القسم غير موجود: {class_name}")

        c_students = self.students_by_class[resolved]
        found = None
        for s in c_students:
            if s.get("id") == student_id or s.get("massar_code") == student_id:
                found = s
                break

        if not found:
            raise ValueError("التلميذ غير موجود.")

        for key in ["order", "massar_code", "last_name", "first_name", "full_name", "gender", "dob", "birth_place"]:
            if key in data:
                found[key] = data[key]

        if "full_name" in data and not data.get("last_name") and not data.get("first_name"):
            found["full_name"] = data["full_name"]

        c_students.sort(key=lambda s: s.get("order", 0))
        self.save_state()

        return {"success": True, "student": found}

    def delete_student(self, class_name: str, student_id: str) -> Dict[str, Any]:
        """حذف تلميذ من القسم"""
        resolved = self.resolve_class_name(class_name)
        if resolved not in self.students_by_class:
            raise ValueError(f"القسم غير موجود: {class_name}")

        before = len(self.students_by_class[resolved])
        self.students_by_class[resolved] = [
            s for s in self.students_by_class[resolved]
            if s.get("id") != student_id and s.get("massar_code") != student_id
        ]
        after = len(self.students_by_class[resolved])

        self.save_state()
        return {"success": True, "deleted": before > after, "remaining": after}

    def delete_class(self, class_name: str) -> Dict[str, Any]:
        """حذف قسم كامل مع تلاميذه"""
        resolved = self.resolve_class_name(class_name)
        if resolved in self.students_by_class:
            del self.students_by_class[resolved]
            self.save_state()
            return {"success": True, "deleted_class": resolved}
        return {"success": False, "message": "القسم غير موجود"}

    def add_new_class(self, class_name: str) -> Dict[str, Any]:
        """إنشاء قسم جديد فارغ"""
        class_name = class_name.strip()
        if not class_name:
            raise ValueError("يجب تحديد اسم القسم.")
        resolved = self.resolve_class_name(class_name)
        if resolved not in self.students_by_class:
            self.students_by_class[resolved] = []
            self.save_state()
        return {"success": True, "class_name": resolved}

    # =========================================================================
    # مسك وتتبع الغياب (Attendance Recording)
    # =========================================================================
    def save_attendance_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        حفظ جلسة مسك غياب لقسم معين في تاريخ وفترة محددة.
        session_data:
        {
            "class_name": "TCSF-1",
            "date": "2026-10-14",
            "period_id": "M_1",
            "period_label": "الحصة 1 صباحاً (08:30 - 09:30)",
            "hours": 1,
            "subject": "الرياضيات",
            "teacher": "أستاذ أحمد",
            "records": {
                "st_123": {"status": "absent", "justified": False, "reason": "", "note": ""},
                "st_456": {"status": "late", "justified": True, "reason": "تأخر في النقل المدرسي", "note": ""}
            }
        }
        """
        class_name = session_data.get("class_name")
        date_str = session_data.get("date")
        period_id = session_data.get("period_id", "M_ALL")

        if not class_name or not date_str:
            raise ValueError("يجب تحديد القسم والتاريخ.")

        canonical_cname = self.resolve_class_name(class_name)
        target_norm = normalize_class_name(class_name)

        # العثور على الجلسة السابقة إن وجدت لتحديثها، أو إنشاء جلسة جديدة
        existing_idx = -1
        for idx, rec in enumerate(self.attendance_records):
            if rec.get("date") == date_str and rec.get("period_id") == period_id:
                rec_c = rec.get("class_name", "")
                if rec_c == class_name or rec_c == canonical_cname or normalize_class_name(rec_c) == target_norm:
                    existing_idx = idx
                    break

        # احتساب ساعات الغياب الافتراضية للفترة
        hours = session_data.get("hours")
        if not hours:
            for p in DEFAULT_PERIODS:
                if p["id"] == period_id:
                    hours = p["hours"]
                    break
        if not hours:
            hours = 1

        session_id = session_data.get("id") or (self.attendance_records[existing_idx]["id"] if existing_idx != -1 else f"att_{uuid.uuid4().hex[:8]}")

        record_entry = {
            "id": session_id,
            "class_name": canonical_cname,
            "date": date_str,
            "period_id": period_id,
            "period_label": session_data.get("period_label", period_id),
            "hours": hours,
            "subject": session_data.get("subject", ""),
            "teacher": session_data.get("teacher", ""),
            "records": {},
            "updated_at": datetime.now().isoformat()
        }

        # الدمج الذكي لسجلات الغياب حتى لا تلغى تسجيلات سابقة لنفس الحصة
        merged_records = {}
        if existing_idx != -1 and not session_data.get("replace_all", False):
            merged_records.update(self.attendance_records[existing_idx].get("records", {}))
        merged_records.update(session_data.get("records", {}))
        record_entry["records"] = merged_records

        if existing_idx != -1:
            self.attendance_records[existing_idx] = record_entry
        else:
            self.attendance_records.append(record_entry)

        self.save_state()

        return {
            "success": True,
            "session_id": session_id,
            "absent_count": sum(1 for r in record_entry["records"].values() if r.get("status") == "absent"),
            "late_count": sum(1 for r in record_entry["records"].values() if r.get("status") == "late")
        }

    def get_attendance_session(self, class_name: str, date_str: str, period_id: str) -> Optional[Dict[str, Any]]:
        """جلب بيانات مسك غياب سابق لقسم وتاريخ وفترة معينة"""
        canonical_cname = self.resolve_class_name(class_name)
        target_norm = normalize_class_name(class_name)
        for rec in self.attendance_records:
            if rec.get("date") == date_str and rec.get("period_id") == period_id:
                rec_c = rec.get("class_name", "")
                if rec_c == class_name or rec_c == canonical_cname or normalize_class_name(rec_c) == target_norm:
                    return rec
        return None

    def get_attendance_history(self, class_name: Optional[str] = None, date_str: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """سجل الجلسات السابقة مفرزة من الأحدث للأقدم"""
        target_norm = normalize_class_name(class_name) if class_name else None
        canonical_cname = self.resolve_class_name(class_name) if class_name else None
        res = []
        for rec in reversed(self.attendance_records):
            if class_name:
                rec_c = rec.get("class_name", "")
                if rec_c != class_name and rec_c != canonical_cname and normalize_class_name(rec_c) != target_norm:
                    continue
            if date_str and rec.get("date") != date_str:
                continue
            
            abs_cnt = sum(1 for r in rec.get("records", {}).values() if r.get("status") == "absent")
            late_cnt = sum(1 for r in rec.get("records", {}).values() if r.get("status") == "late")
            
            res.append({
                "id": rec.get("id"),
                "class_name": rec.get("class_name"),
                "date": rec.get("date"),
                "period_id": rec.get("period_id"),
                "period_label": rec.get("period_label"),
                "hours": rec.get("hours", 1),
                "subject": rec.get("subject", ""),
                "teacher": rec.get("teacher", ""),
                "absent_count": abs_cnt,
                "late_count": late_cnt,
                "updated_at": rec.get("updated_at")
            })
            if len(res) >= limit:
                break
        return res

    def delete_attendance_session(self, session_id: str) -> Dict[str, Any]:
        """حذف جلسة مسك غياب بالمعرف"""
        before = len(self.attendance_records)
        self.attendance_records = [r for r in self.attendance_records if r.get("id") != session_id]
        after = len(self.attendance_records)
        self.save_state()
        return {"success": True, "deleted": before > after}

    def get_daily_students_attendance(self, date_str: str) -> Dict[str, Any]:
        """
        استخراج تقرير تركيبي مفصل لغيابات وتأخرات المتعلمين لتاريخ محدد،
        مرتبط مباشرة بواجهة تقرير الحراسة العامة اليومية.
        يبين:
        - رقم ترتيب المتعلم في اللائحة (order)
        - قسمه (class_name)
        - اسمه الكامل (full_name)
        - رقم مسار (massar_code)
        - عدد حصص الغياب (absent_sessions_count) وساعاته (absent_hours)
        - التأخرات المرصودة (late_sessions_count)
        - تفاصيل الحصص، المبررات، وأسباب الغياب أو التأخر.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        sessions_today = [r for r in self.attendance_records if r.get("date") == date_str]

        students_map = {}
        for s in sessions_today:
            cname = s.get("class_name", "")
            c_students = {st["id"]: st for st in self.get_students_for_class(cname)}
            for st in self.get_students_for_class(cname):
                if st.get("massar_code"):
                    c_students[st["massar_code"]] = st

            period_label = s.get("period_label") or s.get("period_id") or "حصة"
            hours = int(s.get("hours", 1))
            subject = s.get("subject", "")

            for st_id, rec in s.get("records", {}).items():
                status = rec.get("status")
                if status not in ("absent", "late"):
                    continue

                st_info = c_students.get(st_id, {})
                full_name = st_info.get("full_name") or st_info.get("name") or st_id
                order_val = st_info.get("order")
                try:
                    order_val = int(order_val)
                except (ValueError, TypeError):
                    order_val = "-"
                m_code = st_info.get("massar_code", "")

                key = (cname, st_info.get("id", st_id))
                if key not in students_map:
                    students_map[key] = {
                        "id": st_info.get("id", st_id),
                        "order": order_val,
                        "class_name": cname,
                        "full_name": full_name,
                        "massar_code": m_code,
                        "absent_sessions_count": 0,
                        "absent_hours": 0,
                        "absent_periods": [],
                        "late_sessions_count": 0,
                        "late_periods": [],
                        "justified_count": 0,
                        "unjustified_count": 0,
                        "reasons": []
                    }

                entry = students_map[key]
                reason = rec.get("reason", "").strip()
                justified = bool(rec.get("justified", False))

                period_desc = f"{period_label}"
                if subject:
                    period_desc += f" ({subject})"
                if reason:
                    period_desc += f" [{reason}]"

                if status == "absent":
                    entry["absent_sessions_count"] += 1
                    entry["absent_hours"] += hours
                    entry["absent_periods"].append(period_desc)
                    if justified:
                        entry["justified_count"] += 1
                    else:
                        entry["unjustified_count"] += 1
                    if reason and reason not in entry["reasons"]:
                        entry["reasons"].append(reason)
                elif status == "late":
                    entry["late_sessions_count"] += 1
                    entry["late_periods"].append(period_desc)
                    if reason and reason not in entry["reasons"]:
                        entry["reasons"].append(f"تأخر: {reason}")

        def _sort_key(item):
            ord_v = item["order"]
            ord_num = ord_v if isinstance(ord_v, int) else 9999
            return (item["class_name"], ord_num, item["full_name"])

        sorted_students = sorted(students_map.values(), key=_sort_key)

        total_absent_students = sum(1 for s in sorted_students if s["absent_sessions_count"] > 0)
        total_late_students = sum(1 for s in sorted_students if s["late_sessions_count"] > 0)
        total_absent_sessions = sum(s["absent_sessions_count"] for s in sorted_students)
        total_absent_hours = sum(s["absent_hours"] for s in sorted_students)
        total_late_sessions = sum(s["late_sessions_count"] for s in sorted_students)

        return {
            "success": True,
            "date": date_str,
            "total_students_recorded": len(sorted_students),
            "total_absent_students": total_absent_students,
            "total_absent_sessions": total_absent_sessions,
            "total_absent_hours": total_absent_hours,
            "total_late_students": total_late_students,
            "total_late_sessions": total_late_sessions,
            "students": sorted_students
        }

    # =========================================================================
    # إحصائيات الغياب والملف الفردي للتلميذ (Student Absence Profile & Stats)
    # =========================================================================
    def get_student_profile(self, student_id: str) -> Dict[str, Any]:
        """جلب السجل التفصيلي لغياب تلميذ معين"""
        # البحث عن التلميذ في جميع الأقسام
        student_obj = None
        for cname, s_list in self.students_by_class.items():
            for s in s_list:
                if s.get("id") == student_id or s.get("massar_code") == student_id:
                    student_obj = s
                    break
            if student_obj: break

        if not student_obj:
            raise ValueError("التلميذ غير موجود.")

        target_id = student_obj.get("id")
        massar_code = student_obj.get("massar_code")

        history = []
        total_absent_hours = 0
        total_absent_sessions = 0
        justified_hours = 0
        unjustified_hours = 0
        total_late = 0

        for rec in self.attendance_records:
            recs = rec.get("records", {})
            st_rec = recs.get(target_id) or (recs.get(massar_code) if massar_code else None)
            if st_rec:
                status = st_rec.get("status")
                if status in ["absent", "late"]:
                    hours = rec.get("hours", 1)
                    is_just = st_rec.get("justified", False)
                    
                    if status == "absent":
                        total_absent_sessions += 1
                        total_absent_hours += hours
                        if is_just: justified_hours += hours
                        else: unjustified_hours += hours
                    elif status == "late":
                        total_late += 1

                    history.append({
                        "session_id": rec.get("id"),
                        "date": rec.get("date"),
                        "period_label": rec.get("period_label"),
                        "hours": hours,
                        "status": status,
                        "justified": is_just,
                        "reason": st_rec.get("reason", ""),
                        "note": st_rec.get("note", ""),
                        "subject": rec.get("subject", ""),
                        "teacher": rec.get("teacher", "")
                    })

        # فرز الغيابات من الأحدث للأقدم
        history.sort(key=lambda x: x.get("date", ""), reverse=True)

        return {
            "student": student_obj,
            "total_absent_hours": total_absent_hours,
            "total_absent_sessions": total_absent_sessions,
            "justified_hours": justified_hours,
            "unjustified_hours": unjustified_hours,
            "total_late": total_late,
            "history": history
        }

    def get_attendance_statistics(self) -> Dict[str, Any]:
        """إحصائيات عامة وشاملة حول الغياب بالمؤسسة"""
        total_students = sum(len(s_list) for s_list in self.students_by_class.values())
        total_sessions_recorded = len(self.attendance_records)

        # حساب مجموع ساعات الغياب ومجموع التأخرات
        total_absent_hours = 0
        total_justified_hours = 0
        total_unjustified_hours = 0
        total_late_count = 0

        # احتساب الغياب لكل تلميذ لتحديد قائمة الأكثر غياباً
        student_abs_map = {} # student_id -> { hours, count, justified, name, class, massar }

        for rec in self.attendance_records:
            hours = rec.get("hours", 1)
            cname = rec.get("class_name")
            for st_id, st_rec in rec.get("records", {}).items():
                status = st_rec.get("status")
                is_just = st_rec.get("justified", False)

                if status == "absent":
                    total_absent_hours += hours
                    if is_just: total_justified_hours += hours
                    else: total_unjustified_hours += hours

                    if st_id not in student_abs_map:
                        # جلب اسم التلميذ
                        s_name = st_id
                        m_code = ""
                        for s in self.get_students_for_class(cname):
                            if s.get("id") == st_id or s.get("massar_code") == st_id:
                                s_name = s.get("full_name")
                                m_code = s.get("massar_code")
                                break

                        student_abs_map[st_id] = {
                            "id": st_id,
                            "name": s_name,
                            "class_name": cname,
                            "massar_code": m_code,
                            "hours": 0,
                            "sessions": 0,
                            "justified_hours": 0,
                            "unjustified_hours": 0
                        }

                    student_abs_map[st_id]["hours"] += hours
                    student_abs_map[st_id]["sessions"] += 1
                    if is_just:
                        student_abs_map[st_id]["justified_hours"] += hours
                    else:
                        student_abs_map[st_id]["unjustified_hours"] += hours

                elif status == "late":
                    total_late_count += 1

        # ترتيب التلاميذ الأكثر غياباً
        top_absent = sorted(student_abs_map.values(), key=lambda x: x["hours"], reverse=True)[:15]

        # إحصائيات لكل قسم
        class_stats = []
        for cname, s_list in self.students_by_class.items():
            c_hours = sum(rec.get("hours", 1) * sum(1 for st in rec.get("records", {}).values() if st.get("status") == "absent")
                          for rec in self.attendance_records if rec.get("class_name") == cname)
            class_stats.append({
                "class_name": cname,
                "students_count": len(s_list),
                "absent_hours": c_hours
            })
        class_stats.sort(key=lambda x: x["absent_hours"], reverse=True)

        return {
            "total_classes": len(self.students_by_class),
            "total_students": total_students,
            "total_sessions_recorded": total_sessions_recorded,
            "total_absent_hours": total_absent_hours,
            "total_justified_hours": total_justified_hours,
            "total_unjustified_hours": total_unjustified_hours,
            "total_late_count": total_late_count,
            "top_absent": top_absent,
            "class_stats": class_stats
        }

    # =========================================================================
    # تصدير ورقة غياب الحصة / اليوم إلى Excel مهيأ للطباعة (Excel Export)
    # =========================================================================
    def generate_attendance_sheet_excel(self, class_name: str, date_str: str, period_id: str = "M_ALL") -> io.BytesIO:
        """
        توليد ورقة تسجيل غياب رسمية أنيقة بصيغة Excel لقسم وتاريخ وفترة محددة،
        تحتوي على الترويسة المغربية الرسمية، قائمة التلاميذ بأسماءهم وترتيبهم ورموزهم،
        وحالة الحضور والغياب مع خانة الملاحظات والتوقيع.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"غياب {class_name}"
        ws.views.sheetView[0].rightToLeft = True

        # الألوان والخطوط الرسمية
        font_header = Font(name="Calibri", size=11, bold=True, color="1E293B")
        font_title = Font(name="Calibri", size=14, bold=True, color="0F172A")
        font_table_head = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_body = Font(name="Calibri", size=10, color="000000")
        fill_table_head = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        fill_absent = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        fill_late = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        fill_alt = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        # الترويسة الرسمية
        inst = self.institution_info
        ws["A1"] = f"المملكة المغربية - وزارة التربية الوطنية والتعليم الأولي والرياضة"
        ws["A1"].font = font_header
        ws.merge_cells("A1:G1")
        ws["A1"].alignment = Alignment(horizontal="center")

        ws["A2"] = f"{inst.get('academy', 'الأكاديمية الجهوية')} | {inst.get('province', 'المديرية الإقليمية')}"
        ws["A2"].font = font_header
        ws.merge_cells("A2:G2")
        ws["A2"].alignment = Alignment(horizontal="center")

        ws["A3"] = f"المؤسسة: {inst.get('school_name', '')}  |  السنة الدراسية: {inst.get('academic_year', '2026/2027')}"
        ws["A3"].font = font_header
        ws.merge_cells("A3:G3")
        ws["A3"].alignment = Alignment(horizontal="center")

        # عنوان الورقة
        period_name = period_id
        for p in DEFAULT_PERIODS:
            if p["id"] == period_id:
                period_name = p["name"]
                break

        ws["A5"] = f"ورقة تسجيل ومسك غياب التلاميذ - القسم: {class_name}"
        ws["A5"].font = font_title
        ws.merge_cells("A5:G5")
        ws["A5"].alignment = Alignment(horizontal="center")

        ws["A6"] = f"التاريخ: {date_str}  |  الحصة/الفترة: {period_name}"
        ws["A6"].font = font_header
        ws.merge_cells("A6:G6")
        ws["A6"].alignment = Alignment(horizontal="center")

        # ترويسة الجدول
        headers = ["ر.ت", "رقم مسار", "النسب والإسم", "النوع", "حالة الحضور", "مبرر / غير مبرر", "ملاحظات"]
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(8, col_idx, h)
            cell.font = font_table_head
            cell.fill = fill_table_head
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        ws.row_dimensions[8].height = 25

        # جلب الجلسة المسجلة إن وجدت
        session = self.get_attendance_session(class_name, date_str, period_id)
        session_recs = session.get("records", {}) if session else {}

        # صفوف التلاميذ
        students = self.get_students_for_class(class_name)
        row_curr = 9

        for st in students:
            st_id = st.get("id")
            rec = session_recs.get(st_id) or session_recs.get(st.get("massar_code")) or {}
            status = rec.get("status", "present")
            justified = rec.get("justified", False)
            reason = rec.get("reason", "")
            note = rec.get("note", "")

            status_text = "حاضر"
            if status == "absent": status_text = "غائب"
            elif status == "late": status_text = "تأخر"

            just_text = "-"
            if status == "absent":
                just_text = "مبرر" if justified else "غير مبرر"
                if reason: just_text += f" ({reason})"

            ws.cell(row_curr, 1, st.get("order", row_curr - 8)).alignment = Alignment(horizontal="center")
            ws.cell(row_curr, 2, st.get("massar_code", "")).alignment = Alignment(horizontal="center")
            ws.cell(row_curr, 3, st.get("full_name", "")).alignment = Alignment(horizontal="right")
            ws.cell(row_curr, 4, st.get("gender", "")).alignment = Alignment(horizontal="center")
            ws.cell(row_curr, 5, status_text).alignment = Alignment(horizontal="center")
            ws.cell(row_curr, 6, just_text).alignment = Alignment(horizontal="center")
            ws.cell(row_curr, 7, note).alignment = Alignment(horizontal="right")

            # تنسيق الصف
            for c in range(1, 8):
                cell = ws.cell(row_curr, c)
                cell.font = font_body
                cell.border = thin_border
                if status == "absent":
                    cell.fill = fill_absent
                elif status == "late":
                    cell.fill = fill_late
                elif (row_curr % 2 == 0):
                    cell.fill = fill_alt

            ws.row_dimensions[row_curr].height = 20
            row_curr += 1

        # تذييل الورقة والتوقيع
        row_curr += 1
        ws.cell(row_curr, 2, "توقيع الأستاذ(ة):").font = font_header
        ws.cell(row_curr, 6, "تأشيرة الحراسة العامة / الإدارة:").font = font_header

        # ضبط عرض الأعمدة
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 16
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 10
        ws.column_dimensions['E'].width = 14
        ws.column_dimensions['F'].width = 22
        ws.column_dimensions['G'].width = 25

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    # =========================================================================
    # المزامنة الشاملة مع البنية التربوية، حركية التلاميذ، ولوحة القيادة
    # =========================================================================
    def sync_with_educational_structure(self, app_state, mobility_engine=None) -> Dict[str, Any]:
        """
        مزامنة لوائح التلاميذ والأقسام المستوردة تلقائياً مع البنية التربوية للمؤسسة،
        وحركية التلاميذ، ولوحة القيادة.
        """
        if not self.students_by_class:
            return {"success": False, "message": "لا توجد لوائح تلاميذ محملة حالياً."}

        import re

        def _map_class_to_stream(cname):
            clean = re.sub(r'[-\s_]*\d+$', '', cname.strip()).upper()
            clean = clean.replace(' ', '').replace('-', '').replace('_', '')
            # TC
            if 'TCSF' in clean or 'TCSCBIOF' in clean or 'TCSCF' in clean or clean == 'TCSC':
                if 'F' in clean or 'BIOF' in clean:
                    return 'tc_sc_biof', 'TC', 1
                return 'tc_sc', 'TC', 1
            if 'TCLSHF' in clean or 'TCLSHBIOF' in clean or 'TCLF' in clean or 'TCLSH' in clean or 'TCL' in clean:
                if 'F' in clean or 'BIOF' in clean:
                    return 'tc_lsh_biof', 'TC', 1
                return 'tc_lsh', 'TC', 1
            if 'TCS' in clean or 'TCSC' in clean:
                return 'tc_sc', 'TC', 1
            if 'TCT' in clean:
                return ('tc_tech_biof' if ('F' in clean or 'BIOF' in clean) else 'tc_tech'), 'TC', 1
            if 'TCORIG' in clean or 'TCO' in clean:
                return 'tc_orig', 'TC', 1

            # 1BAC
            if '1BACSEF' in clean or '1BACEXPBIOF' in clean or '1BACSEBIOF' in clean or '1BACEXPF' in clean:
                return '1bac_exp_biof', '1BAC', 2
            if '1BACSE' in clean or '1BACEXP' in clean:
                if 'F' in clean or 'BIOF' in clean:
                    return '1bac_exp_biof', '1BAC', 2
                return '1bac_exp', '1BAC', 2
            if '1BACSMF' in clean or '1BACSMBIOF' in clean:
                return '1bac_sm_biof', '1BAC', 2
            if '1BACSM' in clean:
                return ('1bac_sm_biof' if ('F' in clean or 'BIOF' in clean) else '1bac_sm'), '1BAC', 2
            if '1BACSHF' in clean or '1BACSHBIOF' in clean or '1BACLSHBIOF' in clean or '1BACLSHF' in clean or '1BACLF' in clean or '1BACLBIOF' in clean:
                return '1bac_lsh_biof', '1BAC', 2
            if '1BACSH' in clean or '1BACLSH' in clean or '1BACL' in clean:
                if 'F' in clean or 'BIOF' in clean:
                    return '1bac_lsh_biof', '1BAC', 2
                return '1bac_lsh', '1BAC', 2
            if '1BACSEG' in clean or '1BACECO' in clean:
                return ('1bac_seg_biof' if ('F' in clean or 'BIOF' in clean) else '1bac_seg'), '1BAC', 2
            if '1BACSTE' in clean:
                return ('1bac_ste_biof' if ('F' in clean or 'BIOF' in clean) else '1bac_ste'), '1BAC', 2
            if '1BACSTM' in clean:
                return ('1bac_stm_biof' if ('F' in clean or 'BIOF' in clean) else '1bac_stm'), '1BAC', 2

            # 2BAC
            if '2BACSPF' in clean or '2BACPCBIOF' in clean or '2BACPCF' in clean or '2BACSPBIOF' in clean:
                return '2bac_pc_biof', '2BAC', 3
            if '2BACPC' in clean or '2BACSP' in clean:
                if 'F' in clean or 'BIOF' in clean:
                    return '2bac_pc_biof', '2BAC', 3
                return '2bac_pc', '2BAC', 3
            if '2BACSVTF' in clean or '2BACSVTBIOF' in clean:
                return '2bac_svt_biof', '2BAC', 3
            if '2BACSVT' in clean:
                if 'F' in clean or 'BIOF' in clean:
                    return '2bac_svt_biof', '2BAC', 3
                return '2bac_svt', '2BAC', 3
            if '2BACSMAF' in clean or '2BACSMABIOF' in clean or '2BACSMA' in clean:
                return '2bac_sma_biof', '2BAC', 3
            if '2BACSMBF' in clean or '2BACSMBBIOF' in clean or '2BACSMB' in clean or '2BACB' in clean:
                return '2bac_smb_biof', '2BAC', 3
            if '2BACLF' in clean or '2BACLBIOF' in clean:
                return '2bac_l_biof', '2BAC', 3
            if '2BACL' in clean:
                if 'F' in clean or 'BIOF' in clean:
                    return '2bac_l_biof', '2BAC', 3
                return '2bac_l', '2BAC', 3
            if '2BACSHF' in clean or '2BACSHBIOF' in clean:
                return '2bac_sh_biof', '2BAC', 3
            if '2BACSH' in clean:
                if 'F' in clean or 'BIOF' in clean:
                    return '2bac_sh_biof', '2BAC', 3
                return '2bac_sh', '2BAC', 3

            # Middle School
            if '1AC' in clean or '1APIC' in clean or '1ASC' in clean or clean.startswith('1/'):
                return '1apic', '1AC', 1
            if '2AC' in clean or '2APIC' in clean or '2ASC' in clean or clean.startswith('2/'):
                return '2apic', '2AC', 2
            if '3AC' in clean or '3APIC' in clean or '3ASC' in clean or clean.startswith('3/'):
                return '3apic', '3AC', 3
            return clean.lower(), 'OTHER', 0

        # تنظيف أي أقسام وهمية فارغة ذات 0 تلميذ عند وجود أقسام حقيقية بها تلاميذ
        has_students_any = any(len(slist) > 0 for slist in self.students_by_class.values())
        if has_students_any:
            self.students_by_class = {c: slist for c, slist in self.students_by_class.items() if len(slist) > 0}
            self.save_state()

        stream_counts = {}
        stream_students = {}
        level_classes = {'TC': 0, '1BAC': 0, '2BAC': 0, '1AC': 0, '2AC': 0, '3AC': 0, 'OTHER': 0}
        level_students = {'TC': 0, '1BAC': 0, '2BAC': 0, '1AC': 0, '2AC': 0, '3AC': 0, 'OTHER': 0}

        for cname, slist in self.students_by_class.items():
            sid, lvl, num = _map_class_to_stream(cname)
            stream_counts[sid] = stream_counts.get(sid, 0) + 1
            cnt = len(slist)
            stream_students[sid] = stream_students.get(sid, 0) + cnt
            level_classes[lvl] = level_classes.get(lvl, 0) + 1
            level_students[lvl] = level_students.get(lvl, 0) + cnt

        total_classes = len(self.students_by_class)
        total_students = sum(len(sl) for sl in self.students_by_class.values())

        is_qualifying = (level_classes['TC'] > 0 or level_classes['1BAC'] > 0 or level_classes['2BAC'] > 0)
        cycle = 'qualifying' if is_qualifying else 'middle'

        # 1. Update Institution
        app_state.institution.institution_cycle = cycle
        app_state.institution.cycle = cycle
        if self.institution_info.get("school_name"):
            app_state.institution.institution_name = self.institution_info["school_name"]
        if self.institution_info.get("academy"):
            app_state.institution.academy = self.institution_info["academy"]
        if self.institution_info.get("province"):
            app_state.institution.province = self.institution_info["province"]
        if self.institution_info.get("academic_year"):
            app_state.institution.academic_year = self.institution_info["academic_year"]

        # 2. Update Structure
        app_state.structure.cycle = cycle
        if is_qualifying:
            # High School
            filtered_streams = {k: v for k, v in stream_counts.items() if not k.startswith('1apic') and not k.startswith('2apic') and not k.startswith('3apic')}
            app_state.structure.high_school_streams = filtered_streams
            app_state.structure.high_school_students = {k: stream_students[k] for k in filtered_streams}
            app_state.structure.classes_1_apic = level_classes.get('TC', 0)
            app_state.structure.classes_2_apic = level_classes.get('1BAC', 0)
            app_state.structure.classes_3_apic = level_classes.get('2BAC', 0)
            app_state.structure.students_1_apic = level_students.get('TC', 0)
            app_state.structure.students_2_apic = level_students.get('1BAC', 0)
            app_state.structure.students_3_apic = level_students.get('2BAC', 0)
        else:
            # Middle School
            app_state.structure.classes_1_apic = level_classes.get('1AC', 0) or level_classes.get('1APIC', 0)
            app_state.structure.classes_2_apic = level_classes.get('2AC', 0) or level_classes.get('2APIC', 0)
            app_state.structure.classes_3_apic = level_classes.get('3AC', 0) or level_classes.get('3APIC', 0)
            app_state.structure.students_1_apic = level_students.get('1AC', 0) or level_students.get('1APIC', 0)
            app_state.structure.students_2_apic = level_students.get('2AC', 0) or level_students.get('2APIC', 0)
            app_state.structure.students_3_apic = level_students.get('3AC', 0) or level_students.get('3APIC', 0)

        # 3. Synchronize Mobility Engine
        if mobility_engine:
            all_students = []
            for cname, sl in self.students_by_class.items():
                for s in sl:
                    all_students.append({
                        "massar_code": s.get("massar_code", ""),
                        "full_name": s.get("full_name", ""),
                        "first_name": s.get("first_name", ""),
                        "last_name": s.get("last_name", ""),
                        "gender": s.get("gender", "ذكر"),
                        "dob": s.get("dob", ""),
                        "birth_place": s.get("birth_place", ""),
                        "class_name": cname,
                        "status": "متمدرس"
                    })
            mobility_engine.current_students = all_students
            if not mobility_engine.initial_students:
                mobility_engine.initial_students = list(all_students)
            mobility_engine.institution_info["school_name"] = app_state.institution.institution_name
            mobility_engine.institution_info["academy"] = app_state.institution.academy
            mobility_engine.institution_info["province"] = app_state.institution.province
            mobility_engine.institution_info["academic_year"] = app_state.institution.academic_year
            mobility_engine.save_state()

        # 4. Save App State
        app_state.save_to_disk()

        return {
            "success": True,
            "cycle": cycle,
            "total_classes": total_classes,
            "total_students": total_students,
            "level_classes": level_classes,
            "level_students": level_students,
            "stream_counts": stream_counts,
            "stream_students": stream_students
        }

# نسخة منفردة مشتركة للمحرك (Singleton)
attendance_engine = StudentAttendanceEngine()
