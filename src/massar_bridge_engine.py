# -*- coding: utf-8 -*-
"""
محرك الربط المباشر مع منظومة مسار (Massar Absence Bridge Engine)
يقوم بحساب غيابات التلاميذ وفق تركيبة منظومة مسار الرسمية
ويولد كود الحقن التلقائي، وأزرار المفضلة السحرية (Bookmarklet)،
وملفات الإكسيل المتوافقة مع استيراد مسار.
"""

import os
import json
import time
import io
import urllib.parse
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

MONTHS_AR = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "ماي",
    6: "يونيو",
    7: "يوليوز",
    8: "غشت",
    9: "شتنبر",
    10: "أكتوبر",
    11: "نونبر",
    12: "دجنبر"
}

def calculate_massar_absence_data(
    db_loader_func,
    class_code,
    period_type="MONTHLY",
    month=None,
    year=None,
    date=None,
    start_date=None,
    end_date=None,
    hours_per_day=6.0,
    attendance_engine=None
):
    """
    حساب الغياب المجمع للتلاميذ لقسم وفترة محددة وفق متطلبات مسار:
    - الأيام المبررة والساعات المبررة
    - الأيام غير المبررة والساعات غير المبررة
    - تعيين 0 للحاضرين
    - توليد كود حقن مسار وBookmarklet بنقرة واحدة
    """
    db = db_loader_func() if callable(db_loader_func) else db_loader_func
    if not db or not isinstance(db, dict):
        return {"success": False, "error": "قاعدة بيانات الغياب غير متوفرة."}

    all_students = db.get("students", []) or []
    
    class_clean = str(class_code or "").replace("-", "").replace("_", "").replace(" ", "").upper()
    students_in_class = []
    for s in all_students:
        sc = str(s.get("classCode") or "").replace("-", "").replace("_", "").replace(" ", "").upper()
        if sc == class_clean or s.get("classCode") == class_code:
            students_in_class.append(s)
            
    def sort_key(st):
        try:
            return (int(st.get("rollNumber") or 999), st.get("fullName") or "")
        except Exception:
            return (999, st.get("fullName") or "")
    students_in_class.sort(key=sort_key)

    now = datetime.now()
    if not year:
        year = now.year
    else:
        try:
            year = int(year)
        except Exception:
            year = now.year

    if not month:
        month = now.month
    else:
        try:
            month = int(month)
        except Exception:
            month = now.month

    # Helper: date matches period
    def is_date_match(d_str):
        if not d_str:
            return False
        if period_type == "DAILY":
            target_date = date or now.strftime("%Y-%m-%d")
            return d_str == target_date
        elif period_type == "MONTHLY":
            prefix = f"{year}-{int(month):02d}"
            return d_str.startswith(prefix)
        elif period_type in ["WEEKLY", "CUSTOM"]:
            if start_date and end_date:
                return start_date <= d_str <= end_date
            elif start_date:
                return d_str >= start_date
            return True
        elif period_type == "TERM1":
            try:
                m = int(d_str.split("-")[1])
                return m in [9, 10, 11, 12, 1]
            except Exception:
                return True
        elif period_type == "TERM2":
            try:
                m = int(d_str.split("-")[1])
                return m in [2, 3, 4, 5, 6, 7]
            except Exception:
                return True
        return True

    sessions = db.get("attendanceSessions", {}) or {}
    justified_map = db.get("justifiedAbsences", {}) or {}

    absence_by_student = {}
    for st in students_in_class:
        m_code = st.get("massarCode") or st.get("studentId")
        absence_by_student[m_code] = {
            "just_hours": 0.0,
            "unjust_hours": 0.0,
            "just_dates": set(),
            "unjust_dates": set(),
            "details": []
        }

    # 1. Scan mobile attendance sessions
    for sess_id, sess in sessions.items():
        if not sess or not isinstance(sess, dict):
            continue
        s_cls = str(sess.get("classCode") or "").replace("-", "").replace("_", "").replace(" ", "").upper()
        if s_cls != class_clean and sess.get("classCode") != class_code:
            continue
        s_date = sess.get("date", "")
        if not is_date_match(s_date):
            continue

        hours = float(sess.get("hours") or 1.0)
        absent_ids = sess.get("absentStudentIds", []) or []

        for st in students_in_class:
            m_code = st.get("massarCode")
            s_id = st.get("studentId")
            f_name = st.get("fullName")

            is_absent = any(
                aid == m_code or aid == s_id or aid == f_name or aid == f"{st.get('classCode')}_{m_code}"
                for aid in absent_ids
            )
            if is_absent and m_code in absence_by_student:
                j_key = f"{sess_id}_{s_id}"
                j_key_m = f"{sess_id}_{m_code}"
                j_key_n = f"{sess_id}_{f_name}"
                is_just = bool(justified_map.get(j_key) or justified_map.get(j_key_m) or justified_map.get(j_key_n))

                rec = absence_by_student[m_code]
                if is_just:
                    rec["just_hours"] += hours
                    rec["just_dates"].add(s_date)
                else:
                    rec["unjust_hours"] += hours
                    rec["unjust_dates"].add(s_date)
                rec["details"].append({
                    "date": s_date,
                    "slotIndex": sess.get("slotIndex"),
                    "subject": sess.get("subject", ""),
                    "isJustified": is_just,
                    "hours": hours
                })

    # 2. Build final student list formatted for Massar
    students_list = []
    massar_map_for_js = {}
    total_just_hours = 0.0
    total_unjust_hours = 0.0
    total_just_days = 0
    total_unjust_days = 0
    absent_count = 0
    clean_count = 0

    for idx, st in enumerate(students_in_class, 1):
        m_code = st.get("massarCode") or f"ST_{idx}"
        rec = absence_by_student.get(m_code, {
            "just_hours": 0.0, "unjust_hours": 0.0,
            "just_dates": set(), "unjust_dates": set(), "details": []
        })
        j_h = rec["just_hours"]
        u_h = rec["unjust_hours"]
        j_d = len(rec["just_dates"])
        u_d = len(rec["unjust_dates"])
        tot_h = j_h + u_h

        if tot_h > 0:
            absent_count += 1
        else:
            clean_count += 1

        total_just_hours += j_h
        total_unjust_hours += u_h
        total_just_days += j_d
        total_unjust_days += u_d

        j_h_val = int(j_h) if j_h.is_integer() else round(j_h, 1)
        u_h_val = int(u_h) if u_h.is_integer() else round(u_h, 1)

        massar_map_for_js[m_code] = {
            "jD": j_d,
            "jH": j_h_val,
            "uD": u_d,
            "uH": u_h_val
        }

        students_list.append({
            "rollNumber": st.get("rollNumber") or idx,
            "massarCode": m_code,
            "fullName": st.get("fullName", ""),
            "gender": st.get("gender", "-"),
            "justDays": j_d,
            "justHours": j_h_val,
            "unjustDays": u_d,
            "unjustHours": u_h_val,
            "totalHours": int(tot_h) if tot_h.is_integer() else round(tot_h, 1),
            "isClean": (tot_h == 0),
            "details": rec["details"]
        })

    # Period label in Arabic
    period_label_ar = ""
    if period_type == "MONTHLY":
        period_label_ar = f"شهر {MONTHS_AR.get(month, month)} {year}"
    elif period_type == "DAILY":
        period_label_ar = f"يوم {date or now.strftime('%Y-%m-%d')}"
    elif period_type == "TERM1":
        period_label_ar = f"الدورة الأولى ({year})"
    elif period_type == "TERM2":
        period_label_ar = f"الدورة الثانية ({year})"
    elif period_type in ["WEEKLY", "CUSTOM"]:
        period_label_ar = f"الفترة: {start_date or '-'} إلى {end_date or '-'}"

    # Generate injection JavaScript code
    js_map_str = json.dumps(massar_map_for_js, ensure_ascii=False)
    injection_code = f"""(function(){{
  const dataMap = {js_map_str};
  let filled = 0, absCount = 0;
  const rows = document.querySelectorAll('table tbody tr');
  rows.forEach(function(row) {{
    const text = row.innerText || row.textContent || '';
    const m = text.match(/[A-Za-z]\\d{{8,9}}/);
    if (!m) return;
    const code = m[0].toUpperCase();
    const info = dataMap[code] || {{ jD: 0, jH: 0, uD: 0, uH: 0 }};
    const inputs = row.querySelectorAll('input[type="text"], input.Note-control');
    if (inputs.length >= 4) {{
      inputs[0].value = info.jD;
      inputs[1].value = info.jH;
      inputs[2].value = info.uD;
      inputs[3].value = info.uH;
      for (let i = 0; i < 4; i++) {{
        inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
        inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
      }}
      if (info.uH > 0 || info.jH > 0) {{
        row.style.backgroundColor = '#fef3c7';
        absCount++;
      }} else {{
        row.style.backgroundColor = '#ecfdf5';
      }}
      filled++;
    }}
  }});
  alert('✅ تم بنجاح حقن غيابات مسار لقسم {class_code} ({period_label_ar}) بواسطة RzzakFet!\\n\\n• عدد التلاميذ الذين تم مسكهم: ' + filled + '\\n• التلاميذ المتغيبون: ' + absCount + '\\n• التلاميذ الحاضرون (تم وضع 0): ' + (filled - absCount) + '\\n\\nيرجى مراجعة الجدول والضغط على زر حفظ.');
}})();"""

    bookmarklet = "javascript:" + urllib.parse.quote(injection_code)

    return {
        "success": True,
        "classCode": class_code,
        "periodType": period_type,
        "periodLabel": period_label_ar,
        "month": month,
        "year": year,
        "date": date,
        "students": students_list,
        "kpi": {
            "totalStudents": len(students_in_class),
            "cleanStudents": clean_count,
            "absentStudents": absent_count,
            "totalJustHours": int(total_just_hours) if total_just_hours.is_integer() else round(total_just_hours, 1),
            "totalUnjustHours": int(total_unjust_hours) if total_unjust_hours.is_integer() else round(total_unjust_hours, 1),
            "totalJustDays": total_just_days,
            "totalUnjustDays": total_unjust_days
        },
        "injection_script": injection_code,
        "bookmarklet": bookmarklet
    }


def generate_massar_absence_excel(data, inst_name="الثانوية التأهيلية أنفك"):
    """
    توليد ملف إكسيل مطابق لنموذج منظومة مسار الرسمي لاستيراد وتصدير الغياب
    مع تعبئة الأيام والساعات المبررة وغير المبررة والأصفار للحاضرين.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "غياب مسار"
    ws.sheet_view.rightToLeft = True

    # Styles
    f_title = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    f_sub = Font(name="Calibri", size=11, bold=True, color="334155")
    f_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    f_body = Font(name="Calibri", size=10, color="0F172A")
    f_bold = Font(name="Calibri", size=10, bold=True, color="0F172A")
    f_absent = Font(name="Calibri", size=10, bold=True, color="991B1B")

    fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_header_sub = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_absent = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid")
    fill_clean = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    border_all = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_bottom = Border(bottom=Side(border_style="medium", color="1E3A8A"))

    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center")

    # Header Titles
    class_code = data.get("classCode", "")
    period_label = data.get("periodLabel", "")

    ws.merge_cells("A1:G1")
    ws["A1"] = f"المملكة المغربية — وزارة التربية الوطنية والتعليم الأولي والرياضة"
    ws["A1"].font = f_sub
    ws["A1"].alignment = align_center

    ws.merge_cells("A2:G2")
    ws["A2"] = f"لائحة مسك غياب التلاميذ بمنظومة مسار — {inst_name}"
    ws["A2"].font = f_title
    ws["A2"].alignment = align_center

    ws.merge_cells("A3:G3")
    ws["A3"] = f"القسم: {class_code} | الفترة: {period_label} | تاريخ الاستخراج: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws["A3"].font = f_sub
    ws["A3"].alignment = align_center

    ws.row_dimensions[1].height = 20
    ws.row_dimensions[2].height = 25
    ws.row_dimensions[3].height = 20
    ws.row_dimensions[4].height = 10  # blank space

    # Table Column Headers (Matches Massar table)
    headers = [
        ("ر.ت", 8),
        ("رقم التلميذ (رمز مسار)", 20),
        ("الاسم والنسب", 28),
        ("الغياب مبرر (الأيام)", 16),
        ("الغياب مبرر (عدد الساعات)", 18),
        ("الغياب غير مبرر (الأيام)", 18),
        ("الغياب غير مبرر (عدد الساعات)", 20),
    ]

    header_row = 5
    ws.row_dimensions[header_row].height = 28
    for col_idx, (h_title, h_width) in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_idx, value=h_title)
        cell.font = f_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_all
        ws.column_dimensions[get_column_letter(col_idx)].width = h_width

    # Data Rows
    students = data.get("students", [])
    current_row = header_row + 1

    for st in students:
        ws.row_dimensions[current_row].height = 20
        is_clean = st.get("isClean", True)
        row_fill = fill_clean if is_clean else fill_absent

        c_roll = ws.cell(row=current_row, column=1, value=st.get("rollNumber"))
        c_roll.alignment = align_center
        c_roll.font = f_bold
        c_roll.fill = row_fill
        c_roll.border = border_all

        c_code = ws.cell(row=current_row, column=2, value=st.get("massarCode"))
        c_code.alignment = align_center
        c_code.font = f_bold
        c_code.fill = row_fill
        c_code.border = border_all

        c_name = ws.cell(row=current_row, column=3, value=st.get("fullName"))
        c_name.alignment = align_right
        c_name.font = f_body
        c_name.fill = row_fill
        c_name.border = border_all

        c_jd = ws.cell(row=current_row, column=4, value=st.get("justDays", 0))
        c_jd.alignment = align_center
        c_jd.font = f_bold if st.get("justDays", 0) > 0 else f_body
        c_jd.fill = row_fill
        c_jd.border = border_all

        c_jh = ws.cell(row=current_row, column=5, value=st.get("justHours", 0))
        c_jh.alignment = align_center
        c_jh.font = f_bold if st.get("justHours", 0) > 0 else f_body
        c_jh.fill = row_fill
        c_jh.border = border_all

        c_ud = ws.cell(row=current_row, column=6, value=st.get("unjustDays", 0))
        c_ud.alignment = align_center
        c_ud.font = f_absent if st.get("unjustDays", 0) > 0 else f_body
        c_ud.fill = row_fill
        c_ud.border = border_all

        c_uh = ws.cell(row=current_row, column=7, value=st.get("unjustHours", 0))
        c_uh.alignment = align_center
        c_uh.font = f_absent if st.get("unjustHours", 0) > 0 else f_body
        c_uh.fill = row_fill
        c_uh.border = border_all

        current_row += 1

    # Total Summary Row
    ws.row_dimensions[current_row].height = 24
    c_tot_label = ws.cell(row=current_row, column=1, value="المجموع")
    c_tot_label.alignment = align_center
    c_tot_label.font = f_header
    c_tot_label.fill = fill_header_sub
    c_tot_label.border = border_all

    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)

    kpi = data.get("kpi", {})
    ws.cell(row=current_row, column=4, value=kpi.get("totalJustDays", 0)).font = f_header
    ws.cell(row=current_row, column=4).fill = fill_header_sub
    ws.cell(row=current_row, column=4).alignment = align_center
    ws.cell(row=current_row, column=4).border = border_all

    ws.cell(row=current_row, column=5, value=kpi.get("totalJustHours", 0)).font = f_header
    ws.cell(row=current_row, column=5).fill = fill_header_sub
    ws.cell(row=current_row, column=5).alignment = align_center
    ws.cell(row=current_row, column=5).border = border_all

    ws.cell(row=current_row, column=6, value=kpi.get("totalUnjustDays", 0)).font = f_header
    ws.cell(row=current_row, column=6).fill = fill_header_sub
    ws.cell(row=current_row, column=6).alignment = align_center
    ws.cell(row=current_row, column=6).border = border_all

    ws.cell(row=current_row, column=7, value=kpi.get("totalUnjustHours", 0)).font = f_header
    ws.cell(row=current_row, column=7).fill = fill_header_sub
    ws.cell(row=current_row, column=7).alignment = align_center
    ws.cell(row=current_row, column=7).border = border_all

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
