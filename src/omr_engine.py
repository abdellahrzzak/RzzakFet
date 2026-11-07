# -*- coding: utf-8 -*-
"""
محرك ورقة ضبط الغياب الآلية بتقنية OMR (Optical Mark Recognition)
يتكامل مباشرة مع جداول الحصص العامة ولوائح التلاميذ وقاعدة بيانات الغياب
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

SUBJECT_ABBR = {
    "اللغة الفرنسية": "Fr",
    "الفرنسية": "Fr",
    "اللغة العربية": "Ar",
    "العربية": "Ar",
    "الرياضيات": "Mat",
    "التاريخ والجغرافيا": "HG",
    "التاريخ و الجغرافيا": "HG",
    "الاجتماعيات": "HG",
    "التربية الإسلامية": "EI",
    "الإسلاميات": "EI",
    "اللغة الإنجليزية": "Ang",
    "الإنجليزية": "Ang",
    "الفيزياء والكيمياء": "PC",
    "الفيزياء و الكيمياء": "PC",
    "علوم الحياة والأرض": "SVT",
    "علوم الحياة و الأرض": "SVT",
    "الفلسفة": "Philo",
    "التربية البدنية": "EPS",
    "التربية البدنية والرياضية": "EPS",
    "المعلوميات": "Info",
    "الإعلاميات": "Info",
    "التكنولوجيا الصناعية": "Tech",
    "التكنولوجيا": "Tech",
    "اللغة الألمانية": "All",
    "الألمانية": "All",
    "اللغة الإسبانية": "Esp",
    "الإسبانية": "Esp",
    "اللغة الإيطالية": "Ita",
    "الإيطالية": "Ita"
}

DAYS_MAP = {
    "الاثنين": {"name_ar": "الإثنين", "name_fr": "Lundi", "order": 1},
    "الثلاثاء": {"name_ar": "الثلاثاء", "name_fr": "Mardi", "order": 2},
    "الاربعاء": {"name_ar": "الأربعاء", "name_fr": "Mercredi", "order": 3},
    "الخميس": {"name_ar": "الخميس", "name_fr": "Jeudi", "order": 4},
    "الجمعة": {"name_ar": "الجمعة", "name_fr": "Vendredi", "order": 5},
    "السبت": {"name_ar": "السبت", "name_fr": "Samedi", "order": 6}
}


def normalize_code(c: str) -> str:
    """توحيد كود القسم لإزالة الفواصل والشرطات والتطابق التلقائي"""
    if not c:
        return ""
    s = str(c).upper().replace("-", "").replace("_", "").replace(" ", "")
    s = s.replace("EXP", "SE").replace("PC", "SP").replace("SC", "S").replace("LSH", "SH")
    return s


def get_subject_abbr(subject_name: str) -> str:
    """استخراج الرمز المختصر للمادة التعليمية"""
    if not subject_name:
        return "-"
    s = subject_name.strip()
    if s in SUBJECT_ABBR:
        return SUBJECT_ABBR[s]
    # مطابقة بالكلمات المفتاحية
    for k, abbr in SUBJECT_ABBR.items():
        if k in s or s in k:
            return abbr
    if "فرنس" in s: return "Fr"
    if "عرب" in s: return "Ar"
    if "رياض" in s: return "Mat"
    if "تاريخ" in s or "اجتماع" in s: return "HG"
    if "إسلام" in s or "اسلام" in s: return "EI"
    if "إنجليز" in s or "انجليز" in s: return "Ang"
    if "فيزياء" in s: return "PC"
    if "حياة" in s: return "SVT"
    if "فلسف" in s: return "Philo"
    if "بدني" in s: return "EPS"
    if "معلوم" in s or "إعلام" in s: return "Info"
    if "تكنو" in s: return "Tech"
    # إذا لم تطابق أي مادة، نأخذ أول 4 أحرف
    return s[:4]


class OMRAttendanceEngine:
    """محرك توليد وقراءة أوراق الغياب الآلية"""

    def __init__(self):
        pass

    def get_classes_catalog(self, app_state, attendance_engine) -> List[Dict[str, Any]]:
        """استخراج قائمة الأقسام مع أعداد التلاميذ"""
        res = []
        classes_data = getattr(attendance_engine, "students_by_class", {})
        cached_tt = app_state.timetable_engine.get_cached_timetable() or {}
        tt_classes = cached_tt.get("classes_list", []) or list(cached_tt.get("student_timetables", {}).keys())

        # دمج وتنسيق الأقسام
        all_class_names = set(classes_data.keys()) | set(tt_classes)

        for cname in sorted(all_class_names):
            norm = normalize_code(cname)
            # مطابقة مع لائحة التلاميذ
            slist = []
            for k, sl in classes_data.items():
                if k == cname or normalize_code(k) == norm:
                    slist = sl
                    break

            res.append({
                "class_code": cname,
                "norm_code": norm,
                "students_count": len(slist),
                "has_timetable": any(k == cname or normalize_code(k) == norm for k in tt_classes)
            })

        return res

    def generate_sheet_data(
        self,
        app_state,
        attendance_engine,
        class_code: str,
        mode: str = "3days_1",
        day_base: str = "الاثنين",
        week_number: str = "12",
        date_str: str = ""
    ) -> Dict[str, Any]:
        """
        توليد بيانات ورقة الغياب OMR الكاملة:
        - الترويسة وشعار المؤسسة
        - قائمة المتعلمين من قاعدة بيانات المؤسسة
        - شبكة الحصص والمواد والحصص المقفلة من جدول الحصص الفعلي
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        norm_target = normalize_code(class_code)

        # 1. استخراج التلاميذ
        classes_data = getattr(attendance_engine, "students_by_class", {})
        students_list = []
        actual_class_key = class_code

        for k, sl in classes_data.items():
            if k == class_code or normalize_code(k) == norm_target:
                students_list = sl
                actual_class_key = k
                break

        formatted_students = []
        for idx, s in enumerate(students_list, start=1):
            formatted_students.append({
                "order": s.get("order", idx),
                "id": s.get("id", f"st_{idx}"),
                "massar_code": s.get("massar_code", ""),
                "full_name": s.get("full_name") or f"{s.get('last_name', '')} {s.get('first_name', '')}".strip() or f"تلميذ(ة) {idx}",
                "gender": s.get("gender", "")
            })

        # 2. استخراج جدول الحصص
        cached_tt = app_state.timetable_engine.get_cached_timetable() or {}
        student_timetables = cached_tt.get("student_timetables", {})
        tt_class_data = {}

        for k, cdata in student_timetables.items():
            if k == class_code or normalize_code(k) == norm_target:
                tt_class_data = cdata
                break

        # 3. تحديد الأيام حسب النمط
        if mode == "3days_1":
            days_selected = ["الاثنين", "الثلاثاء", "الاربعاء"]
            sheet_title = "ورقة ضبط الغياب الآلية (الإثنين - الأربعاء)"
        elif mode == "3days_2":
            days_selected = ["الخميس", "الجمعة", "السبت"]
            sheet_title = "ورقة ضبط الغياب الآلية (الخميس - السبت)"
        else: # daily
            days_selected = [day_base if day_base in DAYS_MAP else "الاثنين"]
            sheet_title = f"ورقة ضبط الغياب اليومية الآلية ({DAYS_MAP.get(days_selected[0], {}).get('name_ar', days_selected[0])})"

        # 4. بناء الأعمدة والحصص المقفلة (blockedCols)
        columns = []
        blocked_cols = []
        col_idx = 0

        # أوقات الحصص الافتراضية
        m_labels = ["08", "09", "10", "11"]
        a_labels = ["14", "15", "16", "17"]

        # محاولة استخراج توقيت المؤسسة إن وجد
        try:
            m_times = getattr(app_state.institution, "morning_period_times", []) or []
            if len(m_times) >= 4:
                m_labels = [t.split("-")[0].strip().split(":")[0] for t in m_times[:4]]
            a_times = getattr(app_state.institution, "afternoon_period_times", []) or []
            if len(a_times) >= 4:
                a_labels = [t.split("-")[0].strip().split(":")[0] for t in a_times[:4]]
        except Exception:
            pass

        days_headers = []

        for d in days_selected:
            d_info = DAYS_MAP.get(d, {"name_ar": d, "name_fr": "", "order": 1})
            days_headers.append({
                "day_key": d,
                "name_ar": d_info["name_ar"],
                "name_fr": d_info["name_fr"],
                "columns_span": 8
            })

            # صباح: 4 حصص (حصة 1 إلى 4)
            m_day_key = f"{d} ص"
            m_hours = tt_class_data.get(m_day_key, {})

            for h_idx in range(1, 5):
                slot = m_hours.get(f"ح {h_idx}") or m_hours.get(f"حصة {h_idx}")
                subj = (slot.get("subject") or "").strip() if slot else ""
                teacher = (slot.get("teacher") or "").strip() if slot else ""
                room = (slot.get("room") or "").strip() if slot else ""
                is_blocked = not bool(subj)

                if is_blocked:
                    blocked_cols.append(col_idx)

                columns.append({
                    "col_index": col_idx,
                    "day_key": d,
                    "day_name_ar": d_info["name_ar"],
                    "period_id": f"M_{h_idx}",
                    "period_type": "morning",
                    "period_label": f"حصة {h_idx} ص",
                    "hour_label": m_labels[h_idx - 1] if h_idx - 1 < len(m_labels) else f"0{7+h_idx}",
                    "subject_name": subj,
                    "subject_abbr": get_subject_abbr(subj),
                    "teacher": teacher,
                    "room": room,
                    "is_blocked": is_blocked
                })
                col_idx += 1

            # مساء: 4 حصص (حصة 1 إلى 4)
            a_day_key = f"{d} م"
            a_hours = tt_class_data.get(a_day_key, {})

            for h_idx in range(1, 5):
                slot = a_hours.get(f"ح {h_idx}") or a_hours.get(f"حصة {h_idx}")
                subj = (slot.get("subject") or "").strip() if slot else ""
                teacher = (slot.get("teacher") or "").strip() if slot else ""
                room = (slot.get("room") or "").strip() if slot else ""
                is_blocked = not bool(subj)

                if is_blocked:
                    blocked_cols.append(col_idx)

                columns.append({
                    "col_index": col_idx,
                    "day_key": d,
                    "day_name_ar": d_info["name_ar"],
                    "period_id": f"A_{h_idx}",
                    "period_type": "afternoon",
                    "period_label": f"حصة {h_idx} م",
                    "hour_label": a_labels[h_idx - 1] if h_idx - 1 < len(a_labels) else str(13 + h_idx),
                    "subject_name": subj,
                    "subject_abbr": get_subject_abbr(subj),
                    "teacher": teacher,
                    "room": room,
                    "is_blocked": is_blocked
                })
                col_idx += 1

        # معلومات المؤسسة
        inst = getattr(app_state, "institution", None)
        inst_name = getattr(inst, "institution_name", "المؤسسة التعليمية") if inst else "المؤسسة التعليمية"
        if not inst_name or inst_name == "المؤسسة التعليمية":
            inst_name = "الثانوية التأهيلية أنفك"
        academy = getattr(inst, "academy", "") if inst else ""
        province = getattr(inst, "province", "") if inst else ""
        academic_year = getattr(inst, "academic_year", "2026/2027") if inst else "2026/2027"
        logo_b64 = getattr(inst, "logo_base64", "") if inst else ""

        return {
            "success": True,
            "class_code": class_code,
            "actual_class_key": actual_class_key,
            "mode": mode,
            "sheet_title": sheet_title,
            "week_number": week_number or "12",
            "date_str": date_str,
            "header": {
                "institution_name": inst_name,
                "academy": academy,
                "province": province,
                "academic_year": academic_year,
                "logo_base64": logo_b64
            },
            "days_headers": days_headers,
            "columns": columns,
            "blocked_cols": blocked_cols,
            "total_columns": len(columns),
            "students": formatted_students,
            "students_count": len(formatted_students),
            "grid_rows": 45  # المعيار البصري لورقة OMR (45 صفاً)
        }

    def save_attendance_from_omr(
        self,
        app_state,
        attendance_engine,
        class_code: str,
        date_str: str,
        week_number: str,
        mode: str,
        absences_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        حفظ واعتماد الغياب المسجل أو المرصود ضوئياً في قاعدة بيانات التطبيق
        """
        if not class_code:
            return {"success": False, "error": "رمز القسم مطلوب"}

        norm_target = normalize_code(class_code)
        canonical_cname = attendance_engine.resolve_class_name(class_code)

        # استخراج خريطة التلاميذ
        students_map = {}
        for s in attendance_engine.students_by_class.get(canonical_cname, []):
            order = s.get("order")
            st_id = s.get("id")
            if order:
                students_map[order] = s
            if st_id:
                students_map[st_id] = s

        # تجميع الغيابات حسب التاريخ والحصة
        # key: (day_key, period_id)
        grouped_sessions = {}

        # خريطة تواريخ الأيام حسب الأسبوع
        # نفترض أن date_str يمثل يوم الإثنين لهذا الأسبوع
        try:
            base_date = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            base_date = datetime.now()

        # إيجاد يوم الاثنين
        monday_offset = base_date.weekday() # 0 = Monday
        monday_date = base_date - timedelta(days=monday_offset)

        day_date_map = {
            "الاثنين": (monday_date + timedelta(days=0)).strftime("%Y-%m-%d"),
            "الثلاثاء": (monday_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "الاربعاء": (monday_date + timedelta(days=2)).strftime("%Y-%m-%d"),
            "الخميس": (monday_date + timedelta(days=3)).strftime("%Y-%m-%d"),
            "الجمعة": (monday_date + timedelta(days=4)).strftime("%Y-%m-%d"),
            "السبت": (monday_date + timedelta(days=5)).strftime("%Y-%m-%d")
        }

        recorded_count = 0

        for item in absences_list:
            student_num = item.get("student_number")
            day_key = item.get("day_key", "الاثنين")
            period_id = item.get("period_id", "M_1")
            period_label = item.get("period_label", period_id)
            subject = item.get("subject_name", "")
            teacher = item.get("teacher", "")

            st_obj = students_map.get(student_num)
            if not st_obj:
                continue

            session_date = day_date_map.get(day_key, date_str)
            group_key = (session_date, period_id)

            if group_key not in grouped_sessions:
                grouped_sessions[group_key] = {
                    "class_name": canonical_cname,
                    "date": session_date,
                    "period_id": period_id,
                    "period_label": period_label,
                    "hours": 1,
                    "subject": subject,
                    "teacher": teacher,
                    "records": {}
                }

            student_id = st_obj.get("id")
            grouped_sessions[group_key]["records"][student_id] = {
                "status": "absent",
                "justified": False,
                "reason": "غياب مرصود عبر ورقة الغياب الآلية (OMR)",
                "note": f"رقم التلميذ في الورقة: {student_num}"
            }
            recorded_count += 1

        # حفظ الحصص في attendance_engine
        saved_sessions_count = 0
        for g_data in grouped_sessions.values():
            try:
                attendance_engine.save_attendance_session(g_data)
                saved_sessions_count += 1
            except Exception as e:
                print(f"[OMR Save Session Error]: {e}")

        # مزامنة الحالة وحفظها
        try:
            attendance_engine.save_state()
            from .desktop_server import sync_attendance_mobile_db_from_attendance_engine, sync_attendance_with_cloud
            sync_attendance_mobile_db_from_attendance_engine()
            import threading
            threading.Thread(target=sync_attendance_with_cloud, daemon=True).start()
        except Exception as e:
            print(f"[OMR Post-save Sync Error]: {e}")

        return {
            "success": True,
            "recorded_absences": recorded_count,
            "saved_sessions": saved_sessions_count,
            "message": f"تم بنجاح تسجيل {recorded_count} حالة غياب موزعة على {saved_sessions_count} حصة دراسية في قاعدة البيانات."
        }

    def render_sheet_html(self, data: Dict[str, Any], autoprint: bool = True) -> str:
        """
        توليد كود HTML مستقل ومتكامل وجاهز للطباعة على ورقة A4 عمودية (Portrait)
        مع علامات OMR الدقيقة في الزوايا، الترويسة، جدول الحصص والتلاميذ، والتذييل الرسمي.
        """
        if not data or not data.get("success"):
            err_msg = (data or {}).get("error", "بيانات ورقة الغياب غير متوفرة")
            return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>خطأ في ورقة الغياب</title></head>
<body style="font-family:sans-serif;text-align:center;padding:50px;">
  <h2>تعذر توليد ورقة الغياب</h2>
  <p style="color:red;">{err_msg}</p>
</body>
</html>"""

        header = data.get("header", {})
        inst_name = header.get("institution_name", "المملكة المغربية — وزارة التربية الوطنية")
        academic_year = header.get("academic_year", "2026/2027")
        logo_b64 = header.get("logo_base64", "")
        class_code = data.get("class_code", "")
        week_no = data.get("week_number", "12")
        sheet_title = data.get("sheet_title", "ورقة ضبط الغياب الآلية (OMR)")
        date_str = data.get("date_str", "")

        days_headers = data.get("days_headers", [])
        columns = data.get("columns", [])
        blocked_cols = set(data.get("blocked_cols", []))
        students = data.get("students", [])
        grid_rows = data.get("grid_rows", 45)

        # 1. Build Header Days Row
        days_row_parts = []
        for d_idx, d in enumerate(days_headers):
            bg_cls = "#f1f5f9" if d_idx % 2 == 0 else "#e2e8f0"
            fr_label = f"({d.get('name_fr', '')})" if d.get('name_fr') else ""
            days_row_parts.append(
                f'<th colspan="{d.get("columns_span", 8)}" class="day-title" style="background-color: {bg_cls} !important;">'
                f'{d.get("name_ar", "")} {fr_label}</th>'
            )
        days_row_html = "".join(days_row_parts)

        # 2. Build Hours Row
        hours_row_parts = []
        for col in columns:
            hours_row_parts.append(
                f'<th style="width: 20px; font-size: 7.5px; font-weight: bold; background-color: #f8fafc !important;">'
                f'{col.get("hour_label", "")}</th>'
            )
        hours_row_html = "".join(hours_row_parts)

        # 3. Build Subjects Row
        subj_row_parts = []
        for col in columns:
            if col.get("is_blocked"):
                subj_row_parts.append('<th style="background-color: #e2e8f0 !important; color: #64748b !important; font-size: 7.5px;">-</th>')
            else:
                title_attr = f'{col.get("subject_name", "")} ({col.get("teacher", "")})'
                subj_row_parts.append(
                    f'<th style="font-size: 7.5px; font-weight: 800; background-color: #ffffff !important;" title="{title_attr}">'
                    f'{col.get("subject_abbr", "")}</th>'
                )
        subj_row_html = "".join(subj_row_parts)

        # 4. Build Table Body Rows (45 rows standard)
        tbody_parts = []
        for r in range(1, grid_rows + 1):
            st = students[r - 1] if r - 1 < len(students) else None
            st_name = st.get("full_name", "") if st else ""
            st_order = r

            row_cells = [
                f'<td style="font-weight: bold; font-size: 8px; width: 22px;">{st_order}</td>',
                f'<td style="text-align: right; padding-right: 4px; font-weight: 600; white-space: nowrap; font-size: 8px; width: 125px; overflow: hidden; text-overflow: ellipsis;">{st_name}</td>'
            ]

            for c_idx in range(len(columns)):
                if c_idx in blocked_cols:
                    row_cells.append('<td><div class="omr-cell-box blocked"></div></td>')
                else:
                    row_cells.append(f'<td><div class="omr-cell-box" data-number="{st_order}" data-row="{st_order}" data-col="{c_idx}">{st_order}</div></td>')

            row_cells.append(f'<td id="omr-sum-{st_order}" style="font-weight: bold; color: #dc2626 !important; font-size: 8.5px; width: 24px;">0</td>')
            tbody_parts.append(f'<tr>{"".join(row_cells)}</tr>')

        tbody_html = "".join(tbody_parts)

        # Logo element
        if logo_b64 and logo_b64.strip():
            logo_src = logo_b64 if logo_b64.startswith("data:") else f"data:image/png;base64,{logo_b64}"
            logo_html = f'''<div style="width: 46px; height: 46px; display: flex; align-items: center; justify-content: center;">
                <img src="{logo_src}" alt="شعار المؤسسة" style="max-height: 44px; max-width: 44px; object-fit: contain;">
              </div>'''
        else:
            logo_html = f'''<div class="omr-qr-placeholder">
                <span>QR-CODE<br>{class_code}</span>
              </div>'''

        autoprint_script = """
    <script>
      window.addEventListener('DOMContentLoaded', function() {
        var params = new URLSearchParams(window.location.search);
        var auto = params.get('autoprint');
        if (auto === '1' || auto === 'true' || auto === null) {
          setTimeout(function() {
            try {
              window.focus();
              window.print();
            } catch(e) {
              console.warn("Autoprint error:", e);
            }
          }, 450);
        }
      });
    </script>
        """ if autoprint else ""

        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ورقة ضبط الغياب الآلية OMR — {class_code}</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 4mm 5mm;
    }}
    * {{
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }}
    body {{
      margin: 0;
      padding: 0;
      background: #f1f5f9;
      color: #000000 !important;
      font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
      direction: rtl;
    }}
    @media print {{
      body {{
        background: #ffffff !important;
        padding: 0 !important;
        margin: 0 !important;
      }}
      .no-print {{
        display: none !important;
      }}
      .omr-sheet-wrapper {{
        box-shadow: none !important;
        border: none !important;
        margin: 0 !important;
        width: 100% !important;
        min-height: auto !important;
        page-break-inside: avoid !important;
      }}
    }}
    .no-print.omr-print-toolbar {{
      max-width: 200mm;
      margin: 12px auto;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      padding: 8px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    .btn-print {{
      background: #0284c7;
      color: #ffffff;
      border: none;
      border-radius: 6px;
      padding: 8px 16px;
      font-size: 13px;
      font-weight: bold;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background 0.15s ease;
    }}
    .btn-print:hover {{ background: #0369a1; }}
    .btn-close {{
      background: #f1f5f9;
      color: #334155;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 8px 14px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}
    .btn-close:hover {{ background: #e2e8f0; }}

    /* OMR Sheet Wrapper */
    .omr-sheet-wrapper {{
      width: 200mm;
      min-height: 285mm;
      background: #ffffff;
      margin: 10px auto;
      padding: 5mm 7mm;
      border: 1px solid #cbd5e1;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
      position: relative;
      color: #000000 !important;
    }}

    /* علامات الزوايا الأربع (OMR Fiducials) */
    .omr-mark {{
      position: absolute;
      width: 7.5mm;
      height: 7.5mm;
      background: #000000 !important;
    }}
    .omr-mark-tl {{ top: 3.5mm; right: 3.5mm; }}
    .omr-mark-tr {{ top: 3.5mm; left: 3.5mm; }}
    .omr-mark-bl {{ bottom: 3.5mm; right: 3.5mm; }}
    .omr-mark-br {{ bottom: 3.5mm; left: 3.5mm; }}

    /* Header */
    .omr-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid #000000;
      padding-bottom: 4px;
      margin-bottom: 4px;
      padding-right: 25px;
      padding-left: 25px;
    }}
    .omr-header-info {{ text-align: right; }}
    .omr-header-info h2 {{ margin: 0; font-size: 11px; font-weight: 800; color: #000000; }}
    .omr-header-info h1 {{ margin: 2px 0; font-size: 13px; font-weight: 900; color: #000000; }}
    .omr-header-info p {{ margin: 0; font-size: 9.5px; color: #334155; }}

    .omr-class-card {{
      border: 1.5px solid #000000;
      border-radius: 4px;
      padding: 2px 10px;
      text-align: center;
      background: #f8fafc;
    }}
    .omr-class-card .title {{ font-size: 8.5px; color: #475569; display: block; }}
    .omr-class-card .name {{ font-size: 13px; font-weight: 900; color: #000000; }}

    .omr-qr-placeholder {{
      width: 44px;
      height: 44px;
      border: 1.5px solid #000000;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 7.5px;
      font-weight: bold;
      text-align: center;
      background: #f8fafc;
      color: #000000;
    }}

    /* Table */
    table.omr-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 8px;
      text-align: center;
      table-layout: fixed;
    }}
    table.omr-table th, table.omr-table td {{
      border: 1.1px solid #1e293b !important;
      padding: 0.5px 0;
      height: 15px;
      color: #000000 !important;
    }}
    table.omr-table th.day-title {{
      font-size: 9.5px;
      font-weight: 900;
      padding: 2px 0;
      background-color: #f1f5f9 !important;
    }}

    /* Cells */
    .omr-cell-box {{
      width: 19px;
      height: 14px;
      margin: 0 auto;
      border: none !important;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 8px;
      font-weight: 800;
      color: #0f172a;
    }}
    .omr-cell-box.blocked {{
      background-color: #e2e8f0 !important;
      border: none !important;
    }}
    .omr-cell-box.marked {{
      border: none !important;
      background-color: #334155 !important;
      color: #ffffff !important;
    }}

    /* Footer */
    .omr-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid #000000;
      padding-top: 3px;
      margin-top: 4px;
      font-size: 8px;
      padding-right: 25px;
      padding-left: 25px;
    }}
  </style>
</head>
<body>

  <!-- شريط التحكم العلوي أثناء المعاينة (يختفي تلقائياً عند الطباعة) -->
  <div class="no-print omr-print-toolbar">
    <div style="display: flex; align-items: center; gap: 10px;">
      <button type="button" onclick="window.print()" class="btn-print">
        <span style="font-size: 16px;">🖨️</span>
        <strong>طباعة ورقة الغياب فوراً (A4)</strong>
      </button>
      <button type="button" onclick="window.close()" class="btn-close">
        <span>❌</span>
        <span>إغلاق النافذة</span>
      </button>
    </div>
    <div style="font-size: 11.5px; color: #475569; text-align: left; line-height: 1.4;">
      <span>📌 <strong>إرشادات الطباعة:</strong> اختر حجم الورق <strong>A4</strong>، واضبط الهوامش على <strong>أدنى حد (Minimum)</strong> مع تفعيل <strong>الرسومات في الخلفية (Background graphics)</strong>.</span>
    </div>
  </div>

  <div class="omr-sheet-wrapper" id="sheetArea">
    <!-- علامات المحاذاة الأربع في الزوايا (Fiducial Marks) -->
    <div class="omr-mark omr-mark-tl"></div>
    <div class="omr-mark omr-mark-tr"></div>
    <div class="omr-mark omr-mark-bl"></div>
    <div class="omr-mark omr-mark-br"></div>

    <!-- الترويسة الرسمية وشعار المؤسسة -->
    <div class="omr-header">
      <div class="omr-header-info">
        <h2>المملكة المغربية — وزارة التربية الوطنية والتعليم الأولي والرياضة</h2>
        <h1>{inst_name}</h1>
        <p>{sheet_title}</p>
        <p>نظام التوقيت: مرن (يبدأ من الساعة 08:00 صباحاً) — الموسم الدراسي: {academic_year}</p>
      </div>

      <div class="omr-class-card">
        <span class="title">القسم / CLASSE</span>
        <span class="name">{class_code}</span>
        <span style="font-size: 8.5px; display: block; margin-top: 1px; font-weight: bold;">الأسبوع: {week_no}</span>
      </div>

      {logo_html}
    </div>

    <!-- جدول الحصص والتلاميذ -->
    <table class="omr-table">
      <thead>
        <tr style="background: #e2e8f0; font-weight: bold;">
          <th rowspan="3" style="width: 22px;">N°</th>
          <th rowspan="3" style="width: 125px; text-align: right; padding-right: 5px;">اسم التلميذ(ة)</th>
          {days_row_html}
          <th rowspan="3" style="width: 24px;">م.غ</th>
        </tr>
        <tr style="font-size: 7.5px; background: #f8fafc; font-weight: bold;">
          {hours_row_html}
        </tr>
        <tr style="font-size: 7.5px; font-weight: 800;">
          {subj_row_html}
        </tr>
      </thead>
      <tbody id="omrTableBody">
        {tbody_html}
      </tbody>
    </table>

    <!-- التذييل والتوقيعات -->
    <div class="omr-footer">
      <div>
        <strong>طريقة المسك:</strong> ضع علامة <strong>[ ✕ ]</strong> واضحة بقلم أزرق أو أسود جاف داخل خانة التلميذ المتغيب.
      </div>
      <div>
        تأشيرة الحراسة العامة وإدارة المؤسسة: ............................................................
      </div>
    </div>
  </div>

  {autoprint_script}
</body>
</html>"""
        return html


omr_engine = OMRAttendanceEngine()
