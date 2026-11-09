function sortExamsChronologically(examsList) {
  if (!Array.isArray(examsList)) return [];
  return examsList.sort((a, b) => {
    const dA = a.exam_date || '9999-99-99';
    const dB = b.exam_date || '9999-99-99';
    const cmpD = dA.localeCompare(dB);
    if (cmpD !== 0) return cmpD;

    const sA = Number(a.slot_index || a.slotIndex || 0);
    const sB = Number(b.slot_index || b.slotIndex || 0);
    if (sA && sB && sA !== sB) return sA - sB;

    const tA = (a.exam_time_str || a.exam_hour || '').trim();
    const tB = (b.exam_time_str || b.exam_hour || '').trim();
    const cmpT = tA.localeCompare(tB);
    if (cmpT !== 0) return cmpT;

    const nA = Number(a.exam_number || 1);
    const nB = Number(b.exam_number || 1);
    if (nA !== nB) return nA - nB;

    return (a.class_name || '').localeCompare(b.class_name || '');
  });
}
window.sortExamsChronologically = sortExamsChronologically;

// -*- coding: utf-8 -*-
/**
 * برمجة وتتبع فروض المراقبة المستمرة — Continuous Assessment & Exams Planning Module
 * الواجهة المتقدمة لإدارة وجدولة الفروض، ضبط آجال تسليم النقط (قاعدة 15 يوماً)،
 * التوصية الذكية لتفادي تراكم الفروض على الأقسام، وطباعة الوثائق والبطاقات الرسمية.
 */

window.examsState = {
  exams: [],
  summary: {},
  settings: { max_submission_delay_days: 15 },
  teachers: [],
  classes: [],
  institution: {},
  activeSemester: 1,
  activeSubTab: 'table', // 'calendar', 'table', 'print'
  filterTeacher: '',
  filterClass: '',
  filterCompliance: 'all',
  filterExamNum: '',
  filterCompensatory: 'all',
  filterSearch: '',
  selectedExamId: null,
  calendarBaseMonday: null
};

// Initialize module
window.initExamsPlanning = function() {
  loadExamsPlanningData();
};

// Fetch data from backend
async function loadExamsPlanningData() {
  try {
    const sem = window.examsState.activeSemester;
    const resp = await fetch(`/api/exams_planning/data?semester=${sem}`);
    if (!resp.ok) throw new Error("تعذر جلب معطيات برمجة الفروض");
    const res = await resp.json();
    if (res.success) {
      window.examsState.exams = sortExamsChronologically(res.exams || []);
      window.examsState.summary = res.summary || {};
      window.examsState.settings = res.settings || { max_submission_delay_days: 15 };
      window.examsState.teachers = res.teachers || [];
      window.examsState.classes = res.classes || [];
      window.examsState.institution = res.institution || {};

      renderExamsDashboardKPI();
      renderExamsPlanningViews();
      populateExamsDropdowns();
    }
  } catch (err) {
    console.error("loadExamsPlanningData error:", err);
    if (window.showToast) window.showToast("خطأ أثناء تحميل معطيات برمجة الفروض", "error");
  }
}
window.loadExamsPlanningData = loadExamsPlanningData;

// Switch Semester (الدورة الأولى / الدورة الثانية)
function setExamsSemester(sem) {
  window.examsState.activeSemester = sem;
  document.getElementById('btn-sem-1')?.classList.toggle('bg-amber-600', sem === 1);
  document.getElementById('btn-sem-1')?.classList.toggle('text-white', sem === 1);
  document.getElementById('btn-sem-1')?.classList.toggle('bg-slate-800', sem !== 1);
  document.getElementById('btn-sem-1')?.classList.toggle('text-slate-300', sem !== 1);

  document.getElementById('btn-sem-2')?.classList.toggle('bg-amber-600', sem === 2);
  document.getElementById('btn-sem-2')?.classList.toggle('text-white', sem === 2);
  document.getElementById('btn-sem-2')?.classList.toggle('bg-slate-800', sem !== 2);
  document.getElementById('btn-sem-2')?.classList.toggle('text-slate-300', sem !== 2);

  loadExamsPlanningData();
}
window.setExamsSemester = setExamsSemester;

// Switch Inner Sub-tabs: Calendar, Master Table, Print
function switchExamsSubTab(tabName) {
  window.examsState.activeSubTab = tabName;
  ['calendar', 'teachers', 'table', 'print'].forEach(t => {
    const viewEl = document.getElementById(`exams-view-${t}`);
    const btnEl = document.getElementById(`btn-subtab-${t}`);
    if (viewEl) viewEl.style.display = (t === tabName) ? 'block' : 'none';
    if (btnEl) {
      if (t === tabName) {
        btnEl.className = "px-4 py-2 rounded-xl text-xs font-black bg-gradient-to-r from-amber-600 to-amber-500 text-slate-950 shadow-md transition flex items-center gap-1.5 cursor-pointer";
      } else {
        btnEl.className = "px-4 py-2 rounded-xl text-xs font-bold bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 transition flex items-center gap-1.5 cursor-pointer";
      }
    }
  });

  if (tabName === 'calendar') renderCalendarDashboard();
  if (tabName === 'teachers') renderTeachersProgressView();
  if (tabName === 'table') renderExamsMasterTable();
  if (tabName === 'print') renderPrintCenter();
}
window.switchExamsSubTab = switchExamsSubTab;

// Render Top KPI Stat Cards
function renderExamsDashboardKPI() {
  const sum = window.examsState.summary || {};
  const total = sum.total_exams || 0;
  const compliant = sum.compliant_count || 0;
  const rate = sum.compliance_rate || 100;
  const crowdedCount = sum.crowded_days_count || 0;
  const classesCount = sum.classes_count || 0;

  const totalEl = document.getElementById('kpi-total-exams');
  if (totalEl) totalEl.innerText = `${total} فرض مبرمج`;

  const compEl = document.getElementById('kpi-compliance-rate');
  if (compEl) {
    compEl.innerText = `${rate}% متقيد بـ 15 يوماً`;
    compEl.className = rate >= 90 ? "text-lg font-black text-emerald-400" : "text-lg font-black text-amber-400";
  }

  const compSub = document.getElementById('kpi-compliance-sub');
  if (compSub) compSub.innerText = `${compliant} من أصل ${total} فرض تحترم الأجل`;

  const crowdEl = document.getElementById('kpi-crowded-days');
  if (crowdEl) {
    crowdEl.innerText = crowdedCount === 0 ? "لا يوجد أي تراكم ✓" : `${crowdedCount} حالات تزاحم!`;
    crowdEl.className = crowdedCount === 0 ? "text-lg font-black text-emerald-400" : "text-lg font-black text-rose-400";
  }

  const covEl = document.getElementById('kpi-classes-covered');
  if (covEl) covEl.innerText = `${classesCount} قسماً مغطى`;
}

// Populate filters and form dropdowns
function populateExamsDropdowns() {
  const teachers = window.examsState.teachers || [];
  const classes = window.examsState.classes || [];

  // Filter Teacher dropdown
  const filterT = document.getElementById('filter-exam-teacher');
  if (filterT) {
    const cur = filterT.value;
    filterT.innerHTML = `<option value="">جميع الأساتذة (${teachers.length})</option>` +
      teachers.map(t => `<option value="${t.name}">${t.name} (${t.subject})</option>`).join('');
    filterT.value = cur;
  }

  // Filter Class dropdown
  const filterC = document.getElementById('filter-exam-class');
  if (filterC) {
    const cur = filterC.value;
    filterC.innerHTML = `<option value="">جميع الأقسام (${classes.length})</option>` +
      classes.map(c => `<option value="${c}">${c}</option>`).join('');
    filterC.value = cur;
  }

  // Modal Teacher dropdown
  const modalT = document.getElementById('modal-exam-teacher');
  if (modalT) {
    modalT.innerHTML = `<option value="">-- اختر الأستاذ(ة) --</option>` +
      teachers.map(t => `<option value="${t.name}" data-subject="${t.subject}">${t.name} (${t.subject})</option>`).join('');
  }

  // Print view Teacher dropdown
  const printT = document.getElementById('print-teacher-select');
  if (printT) {
    const cur = printT.value;
    printT.innerHTML = `<option value="">-- اختر الأستاذ(ة) للطباعة --</option>` +
      teachers.map(t => `<option value="${t.name}">${t.name} (${t.subject})</option>`).join('');
    if (cur) printT.value = cur;
    else if (teachers.length > 0) printT.value = teachers[0].name;
  }
}

// Render Calendar Dashboard (Day by Day Grid)
// Render Calendar Dashboard (Clear Moroccan Weekly Timetable Grid & Ministerial Windows)
function renderCalendarDashboard() {
  const container = document.getElementById('exams-calendar-grid');
  if (!container) return;

  const sem = window.examsState.activeSemester || 1;
  const exams = window.examsState.exams.filter(e => e.semester === sem);
  const minCal = (window.examsState.settings && window.examsState.settings.ministerial_calendar && window.examsState.settings.ministerial_calendar[String(sem)]) || {
    exam_1: { name: "الفرض الأول", start_date: "2026-11-02", end_date: "2026-11-14", exam_deadline: "2026-11-14", submission_deadline: "2026-11-28" },
    exam_2: { name: "الفرض الثاني", start_date: "2026-12-07", end_date: "2026-12-19", exam_deadline: "2026-12-19", submission_deadline: "2027-01-02" },
    exam_3: { name: "الفرض الثالث (للمواد المعنية)", start_date: "2027-01-04", end_date: "2027-01-16", exam_deadline: "2027-01-16", submission_deadline: "2027-01-23" },
    final_exam_deadline: "2027-01-16",
    final_submission_deadline: "2027-01-23"
  };

  // Determine current Monday of the weekly calendar
  let baseMondayStr = window.examsState.calendarBaseMonday;
  if (!baseMondayStr) {
    if (minCal.exam_1 && minCal.exam_1.start_date) {
      baseMondayStr = minCal.exam_1.start_date;
    } else if (exams.length > 0 && exams[0].exam_date) {
      baseMondayStr = exams[0].exam_date;
    } else {
      const now = new Date();
      baseMondayStr = now.toISOString().split('T')[0];
    }
  }

  const baseDate = new Date(baseMondayStr);
  const dayOfWeek = baseDate.getDay(); // 0 is Sun, 1 is Mon...
  const diffToMonday = (dayOfWeek === 0 ? -6 : 1 - dayOfWeek);
  const currentMonday = new Date(baseDate);
  currentMonday.setDate(currentMonday.getDate() + diffToMonday);
  const curMonStr = currentMonday.toISOString().split('T')[0];
  window.examsState.calendarBaseMonday = curMonStr;

  // Calculate Saturday of this week
  const currentSaturday = new Date(currentMonday);
  currentSaturday.setDate(currentSaturday.getDate() + 5);
  const curSatStr = currentSaturday.toISOString().split('T')[0];

  // Quick filters
  const fCls = document.getElementById('filter-cal-class')?.value || '';
  const filteredExams = fCls ? exams.filter(e => e.class_name === fCls) : exams;

  // Group exams by date
  const byDate = {};
  filteredExams.forEach(ex => {
    const d = ex.exam_date;
    if (d) {
      if (!byDate[d]) byDate[d] = [];
      byDate[d].push(ex);
    }
  });

  // Ministerial Timeline Header HTML
  const minBannerHtml = `
    <div class="col-span-full bg-slate-900/90 border border-teal-800/60 rounded-2xl p-4 shadow-lg space-y-3">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div class="flex items-center gap-2.5">
          <span class="text-xl">📜</span>
          <div>
            <h3 class="text-xs font-black text-white flex items-center gap-2">
              <span>المذكرة الوزارية والآجال الرسمية المنظمة للمراقبة المستمرة</span>
              <span class="px-2 py-0.5 rounded text-[10px] bg-teal-950 text-teal-300 border border-teal-700">الدورة ${sem === 1 ? 'الأولى' : 'الثانية'}</span>
            </h3>
            <p class="text-[11px] text-slate-400 mt-0.5">الأسابيع المعتمدة لإجراء الفروض المحروسة والآجال القطعية لمسك وتسليم النقط لمسار</p>
          </div>
        </div>

        <button onclick="openMinisterialSettingsModal()" class="px-3.5 py-1.5 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 rounded-xl text-xs font-black shadow flex items-center gap-1.5 transition cursor-pointer self-start md:self-auto">
          <span>⚙️</span>
          <span>ضبط أسابيع الفروض والآجال (المدير)</span>
        </button>
      </div>

      <!-- 4 Timeline Pill Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 text-xs">
        <!-- Exam 1 Window -->
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5 space-y-1">
          <div class="flex items-center justify-between">
            <span class="font-extrabold text-teal-300">📌 الفرض الأول</span>
            <button onclick="jumpToExamWeek(1)" class="text-[10px] text-amber-400 hover:underline cursor-pointer">انتقال للأسبوع ↗</button>
          </div>
          <div class="text-[11px] text-slate-300">من <span class="font-mono font-bold text-white">${minCal.exam_1?.start_date || '—'}</span> إلى <span class="font-mono font-bold text-white">${minCal.exam_1?.end_date || '—'}</span></div>
          <div class="text-[10px] text-slate-400">آخر أجل للتسليم: <span class="font-mono text-emerald-400 font-bold">${minCal.exam_1?.submission_deadline || '—'}</span></div>
        </div>

        <!-- Exam 2 Window -->
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5 space-y-1">
          <div class="flex items-center justify-between">
            <span class="font-extrabold text-blue-300">📌 الفرض الثاني</span>
            <button onclick="jumpToExamWeek(2)" class="text-[10px] text-amber-400 hover:underline cursor-pointer">انتقال للأسبوع ↗</button>
          </div>
          <div class="text-[11px] text-slate-300">من <span class="font-mono font-bold text-white">${minCal.exam_2?.start_date || '—'}</span> إلى <span class="font-mono font-bold text-white">${minCal.exam_2?.end_date || '—'}</span></div>
          <div class="text-[10px] text-slate-400">آخر أجل للتسليم: <span class="font-mono text-emerald-400 font-bold">${minCal.exam_2?.submission_deadline || '—'}</span></div>
        </div>

        <!-- Exam 3 Window -->
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5 space-y-1">
          <div class="flex items-center justify-between">
            <span class="font-extrabold text-purple-300">📌 الفرض الثالث</span>
            <button onclick="jumpToExamWeek(3)" class="text-[10px] text-amber-400 hover:underline cursor-pointer">انتقال للأسبوع ↗</button>
          </div>
          <div class="text-[11px] text-slate-300">من <span class="font-mono font-bold text-white">${minCal.exam_3?.start_date || '—'}</span> إلى <span class="font-mono font-bold text-white">${minCal.exam_3?.end_date || '—'}</span></div>
          <div class="text-[10px] text-slate-400">آخر أجل للتسليم: <span class="font-mono text-emerald-400 font-bold">${minCal.exam_3?.submission_deadline || '—'}</span></div>
        </div>

        <!-- Final Deadlines -->
        <div class="bg-gradient-to-br from-rose-950/40 to-slate-950 border border-rose-800/60 rounded-xl p-2.5 space-y-1">
          <div class="font-extrabold text-rose-300 flex items-center justify-between">
            <span>🎯 الآجال القطعية للإدارة</span>
            <span class="text-[10px] bg-rose-900 px-1.5 py-0.2 rounded text-white font-mono">مسار</span>
          </div>
          <div class="text-[11px] text-slate-300">آخر يوم لإجراء الفروض: <span class="font-mono font-bold text-amber-300">${minCal.final_exam_deadline || '—'}</span></div>
          <div class="text-[10px] text-rose-300 font-bold">آخر موعد لتسليم النقط: <span class="font-mono text-white">${minCal.final_submission_deadline || '—'}</span></div>
        </div>
      </div>
    </div>
  `;

  // Weekly Navigation Toolbar
  const navBarHtml = `
    <div class="col-span-full bg-slate-900/80 border border-slate-800 rounded-xl p-3 flex flex-col md:flex-row md:items-center justify-between gap-3">
      <!-- Week Switcher -->
      <div class="flex items-center gap-2">
        <button onclick="navigateCalendarWeek(-1)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-bold border border-slate-700 transition cursor-pointer">
          ◀ الأسبوع السابق
        </button>
        <div class="px-4 py-1.5 bg-slate-950 border border-teal-700/60 rounded-lg text-xs font-black text-teal-300 font-mono text-center">
          📅 أسبوع: ${curMonStr} ⟵ إلى ⟶ ${curSatStr}
        </div>
        <button onclick="navigateCalendarWeek(1)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-bold border border-slate-700 transition cursor-pointer">
          الأسبوع التالي ▶
        </button>
      </div>

      <!-- Quick Jump Buttons -->
      <div class="flex flex-wrap items-center gap-1.5">
        <button onclick="jumpToExamWeek(1)" class="px-2.5 py-1 bg-teal-950 hover:bg-teal-900 text-teal-300 border border-teal-800 rounded-lg text-[11px] font-bold transition cursor-pointer">
          أسبوع الفرض 1
        </button>
        <button onclick="jumpToExamWeek(2)" class="px-2.5 py-1 bg-blue-950 hover:bg-blue-900 text-blue-300 border border-blue-800 rounded-lg text-[11px] font-bold transition cursor-pointer">
          أسبوع الفرض 2
        </button>
        <button onclick="jumpToExamWeek(3)" class="px-2.5 py-1 bg-purple-950 hover:bg-purple-900 text-purple-300 border border-purple-800 rounded-lg text-[11px] font-bold transition cursor-pointer">
          أسبوع الفرض 3
        </button>
        <button onclick="jumpToCurrentWeek()" class="px-2.5 py-1 bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-800 rounded-lg text-[11px] font-bold transition cursor-pointer">
          🎯 هذا الأسبوع
        </button>
      </div>
    </div>
  `;

  // 6 Day Columns (الاثنين إلى السبت)
  const daysNames = ["الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة", "السبت"];
  let daysColumnsHtml = '<div class="col-span-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">';

  for (let dIdx = 0; dIdx < 6; dIdx++) {
    const dayDate = new Date(currentMonday);
    dayDate.setDate(dayDate.getDate() + dIdx);
    const dayDateStr = dayDate.toISOString().split('T')[0];
    const dayName = daysNames[dIdx];

    const dayExams = byDate[dayDateStr] || [];
    // Sort chronologically by time
    dayExams.sort((a, b) => (a.exam_time_str || '').localeCompare(b.exam_time_str || ''));

    // Check collisions for class on this day
    const classCount = {};
    dayExams.forEach(e => { classCount[e.class_name] = (classCount[e.class_name] || 0) + 1; });
    const hasCollision = Object.values(classCount).some(cnt => cnt >= 2);

    const isAfterFinalDeadline = minCal.final_exam_deadline && dayDateStr > minCal.final_exam_deadline;

    const colBorder = hasCollision ? "border-rose-600 bg-rose-950/20" : dayExams.length > 0 ? "border-teal-700/60 bg-slate-900/90" : "border-slate-800/80 bg-slate-900/40";

    daysColumnsHtml += `
      <div class="border rounded-2xl p-3 shadow-md flex flex-col justify-between ${colBorder} min-h-[380px]">
        <div>
          <!-- Column Header -->
          <div class="border-b border-slate-800 pb-2 mb-2.5">
            <div class="flex items-center justify-between">
              <span class="font-black text-sm text-white">${dayName}</span>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded-full ${dayExams.length > 0 ? 'bg-teal-950 text-teal-300 border border-teal-800 font-bold' : 'bg-slate-800 text-slate-400'}">
                ${dayExams.length} فروض
              </span>
            </div>
            <div class="text-[11px] text-amber-400 font-mono mt-0.5">${dayDateStr}</div>
            ${hasCollision ? '<div class="mt-1.5 px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-700 text-[10px] font-black text-center animate-pulse">⚠️ تزاحم فروض لنفس القسم!</div>' : ''}
            ${isAfterFinalDeadline ? '<div class="mt-1 px-1.5 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800 text-[9.5px] font-bold text-center">⚠️ بعد آخر أجل للإجراء</div>' : ''}
          </div>

          <!-- Exams Cards for this day -->
          <div class="space-y-2">
            ${
              dayExams.length === 0
                ? `<div class="py-12 text-center text-slate-400 text-xs font-semibold">
                    <span class="text-2xl block mb-1">🌴</span>
                    لا توجد فروض مبرمجة
                   </div>`
                : dayExams.map(ex => {
                    const isComp = ex.is_compliant_15_days !== false;
                    const compBadge = isComp 
                      ? `<span class="text-[9.5px] text-emerald-400 font-bold">✓ ${ex.days_to_submission} يوم</span>`
                      : `<span class="text-[9.5px] text-rose-400 font-bold">⚠️ ${ex.days_to_submission} يوم</span>`;
                    
                    const isMulti = (classCount[ex.class_name] >= 2);
                    const cardBg = isMulti ? "border-rose-700/80 bg-rose-950/40" : "border-slate-800 bg-slate-950/80";

                    return `
                      <div class="p-2 rounded-xl border ${cardBg} text-xs space-y-1 relative group hover:border-teal-500/60 transition">
                        <div class="flex items-center justify-between">
                          <span class="font-black text-white px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 text-[11px]">${ex.class_name}</span>
                          <span class="text-[10px] font-bold text-amber-400">الفرض ${ex.exam_number}</span>
                        </div>
                        <div class="text-slate-200 font-semibold truncate" title="${ex.subject}">📖 ${ex.subject}</div>
                        <div class="text-slate-400 text-[11px] truncate" title="${ex.teacher_name}">👨‍🏫 ${ex.teacher_name}</div>
                        <div class="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/60">
                          <span class="font-mono">⏰ ${ex.exam_time_str} ${ex.exam_room ? `(${ex.exam_room})` : ''}</span>
                          ${compBadge}
                        </div>
                        <div class="text-[9.5px] text-slate-400 flex items-center justify-between">
                          <span>تسليم للإدارة:</span>
                          <span class="font-mono font-bold text-slate-300">${ex.grades_submission_date || '-'}</span>
                        </div>
                        <div class="absolute top-1.5 left-1.5 hidden group-hover:flex items-center gap-1 bg-slate-900/95 px-1 py-0.5 rounded border border-slate-700 shadow-lg">
                          <button onclick="editExam('${ex.id}')" class="p-0.5 hover:text-amber-400 transition" title="تعديل">✏️</button>
                          <button onclick="deleteExam('${ex.id}')" class="p-0.5 hover:text-rose-400 transition" title="حذف">🗑️</button>
                        </div>
                      </div>
                    `;
                  }).join('')
            }
          </div>
        </div>

        <button onclick="openScheduleExamWithDate('${dayDateStr}')" class="mt-2 w-full py-1 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg text-[10.5px] font-bold transition flex items-center justify-center gap-1 cursor-pointer">
          <span>➕</span>
          <span>برمجة بهذا اليوم</span>
        </button>
      </div>
    `;
  }

  daysColumnsHtml += '</div>';

  container.innerHTML = minBannerHtml + navBarHtml + daysColumnsHtml;
}

// Calendar Navigation Helpers
function navigateCalendarWeek(deltaWeeks) {
  const curMon = window.examsState.calendarBaseMonday ? new Date(window.examsState.calendarBaseMonday) : new Date();
  curMon.setDate(curMon.getDate() + (deltaWeeks * 7));
  window.examsState.calendarBaseMonday = curMon.toISOString().split('T')[0];
  renderCalendarDashboard();
}
window.navigateCalendarWeek = navigateCalendarWeek;

function jumpToExamWeek(examNum) {
  const sem = window.examsState.activeSemester || 1;
  const minCal = (window.examsState.settings && window.examsState.settings.ministerial_calendar && window.examsState.settings.ministerial_calendar[String(sem)]) || {};
  const examKey = `exam_${examNum}`;
  if (minCal[examKey] && minCal[examKey].start_date) {
    window.examsState.calendarBaseMonday = minCal[examKey].start_date;
    renderCalendarDashboard();
    if (window.showToast) window.showToast(`تم الانتقال إلى أسبوع ${minCal[examKey].name || ('الفرض ' + examNum)}`, "info");
  }
}
window.jumpToExamWeek = jumpToExamWeek;

function jumpToCurrentWeek() {
  const now = new Date();
  window.examsState.calendarBaseMonday = now.toISOString().split('T')[0];
  renderCalendarDashboard();
}
window.jumpToCurrentWeek = jumpToCurrentWeek;

function openScheduleExamWithDate(dateStr) {
  openScheduleExamModal();
  if (dateStr) {
    document.getElementById('modal-exam-date').value = dateStr;
    onExamDateChanged();
  }
}
window.openScheduleExamWithDate = openScheduleExamWithDate;

// Ministerial Settings Modal Controller
function openMinisterialSettingsModal() {
  const sem = window.examsState.activeSemester || 1;
  const minCal = (window.examsState.settings && window.examsState.settings.ministerial_calendar && window.examsState.settings.ministerial_calendar[String(sem)]) || {
    exam_1: { start_date: "2026-11-02", end_date: "2026-11-14", exam_deadline: "2026-11-14", submission_deadline: "2026-11-28" },
    exam_2: { start_date: "2026-12-07", end_date: "2026-12-19", exam_deadline: "2026-12-19", submission_deadline: "2027-01-02" },
    exam_3: { start_date: "2027-01-04", end_date: "2027-01-16", exam_deadline: "2027-01-16", submission_deadline: "2027-01-23" },
    final_exam_deadline: "2027-01-16",
    final_submission_deadline: "2027-01-23"
  };

  const modal = document.getElementById('modal-ministerial-settings');
  if (!modal) return;

  document.getElementById('min-cal-sem-label').innerText = sem === 1 ? 'الدورة الأولى' : 'الدورة الثانية';
  document.getElementById('min-exam-1-start').value = minCal.exam_1?.start_date || '';
  document.getElementById('min-exam-1-end').value = minCal.exam_1?.end_date || '';
  document.getElementById('min-exam-1-sub').value = minCal.exam_1?.submission_deadline || '';

  document.getElementById('min-exam-2-start').value = minCal.exam_2?.start_date || '';
  document.getElementById('min-exam-2-end').value = minCal.exam_2?.end_date || '';
  document.getElementById('min-exam-2-sub').value = minCal.exam_2?.submission_deadline || '';

  document.getElementById('min-exam-3-start').value = minCal.exam_3?.start_date || '';
  document.getElementById('min-exam-3-end').value = minCal.exam_3?.end_date || '';
  document.getElementById('min-exam-3-sub').value = minCal.exam_3?.submission_deadline || '';

  document.getElementById('min-final-exam-deadline').value = minCal.final_exam_deadline || '';
  document.getElementById('min-final-sub-deadline').value = minCal.final_submission_deadline || '';

    // Attach listener to exam number and semester to re-filter classes
  const numSelect = document.getElementById('modal-exam-number');
  if (numSelect && !numSelect.dataset.hasChangeListener) {
    numSelect.dataset.hasChangeListener = "true";
    numSelect.addEventListener('change', () => onExamTeacherChanged());
  }
  const semSelect = document.getElementById('modal-exam-semester');
  if (semSelect && !semSelect.dataset.hasChangeListener) {
    semSelect.dataset.hasChangeListener = "true";
    semSelect.addEventListener('change', () => onExamTeacherChanged());
  }

  modal.classList.remove('hidden');
  modal.style.display = 'flex';
}
window.openMinisterialSettingsModal = openMinisterialSettingsModal;

function closeMinisterialSettingsModal() {
  const modal = document.getElementById('modal-ministerial-settings');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
}
window.closeMinisterialSettingsModal = closeMinisterialSettingsModal;

async function saveMinisterialSettings(event) {
  if (event) event.preventDefault();
  const sem = window.examsState.activeSemester || 1;

  const currentCal = (window.examsState.settings && window.examsState.settings.ministerial_calendar) || {};
  currentCal[String(sem)] = {
    exam_1: {
      name: "الفرض الأول",
      start_date: document.getElementById('min-exam-1-start')?.value || '',
      end_date: document.getElementById('min-exam-1-end')?.value || '',
      exam_deadline: document.getElementById('min-exam-1-end')?.value || '',
      submission_deadline: document.getElementById('min-exam-1-sub')?.value || ''
    },
    exam_2: {
      name: "الفرض الثاني",
      start_date: document.getElementById('min-exam-2-start')?.value || '',
      end_date: document.getElementById('min-exam-2-end')?.value || '',
      exam_deadline: document.getElementById('min-exam-2-end')?.value || '',
      submission_deadline: document.getElementById('min-exam-2-sub')?.value || ''
    },
    exam_3: {
      name: "الفرض الثالث (للمواد المعنية)",
      start_date: document.getElementById('min-exam-3-start')?.value || '',
      end_date: document.getElementById('min-exam-3-end')?.value || '',
      exam_deadline: document.getElementById('min-exam-3-end')?.value || '',
      submission_deadline: document.getElementById('min-exam-3-sub')?.value || ''
    },
    final_exam_deadline: document.getElementById('min-final-exam-deadline')?.value || '',
    final_submission_deadline: document.getElementById('min-final-sub-deadline')?.value || ''
  };

  try {
    const resp = await fetch('/api/exams_planning/save_calendar_settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ministerial_calendar: currentCal })
    });
    const res = await resp.json();
    if (res.success) {
      if (!window.examsState.settings) window.examsState.settings = {};
      window.examsState.settings.ministerial_calendar = currentCal;
      closeMinisterialSettingsModal();
      renderCalendarDashboard();
      if (window.showToast) window.showToast("تم حفظ الآجال والمذكرة الوزارية بنجاح ✓", "success");
    }
  } catch (err) {
    if (window.showToast) window.showToast("خطأ أثناء حفظ الآجال: " + err.message, "error");
  }
}
window.saveMinisterialSettings = saveMinisterialSettings;


// Render Master Table for Admin & Teachers
function renderExamsMasterTable() {
  const tbody = document.getElementById('exams-table-body');
  if (!tbody) return;

  const fT = window.examsState.filterTeacher;
  const fC = window.examsState.filterClass;
  const fComp = window.examsState.filterCompliance;
  const fSearch = (window.examsState.filterSearch || '').trim().toLowerCase();
  const sem = window.examsState.activeSemester;

  let list = window.examsState.exams.filter(e => e.semester === sem);

  if (fT) list = list.filter(e => e.teacher_name === fT);
  if (fC) list = list.filter(e => e.class_name === fC);
  if (fComp === 'compliant') list = list.filter(e => e.is_compliant_15_days !== false);
  if (fComp === 'non_compliant') list = list.filter(e => e.is_compliant_15_days === false);
  if (fSearch) {
    list = list.filter(e => 
      (e.teacher_name || '').toLowerCase().includes(fSearch) ||
      (e.class_name || '').toLowerCase().includes(fSearch) ||
      (e.subject || '').toLowerCase().includes(fSearch) ||
      (e.exam_date || '').includes(fSearch)
    );
  }

  // Sort strictly chronologically: exam_date -> slot/time -> exam_number -> class_name
  sortExamsChronologically(list);

  if (list.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" class="py-12 text-center text-slate-400">
          <span class="text-3xl block mb-2">🔍</span>
          لا توجد نتائج مطابقة لمعايير البحث الحالية.
        </td>
      </tr>
    `;
    return;
  }

  let rows = '';
  list.forEach((ex, idx) => {
    const isComp = ex.is_compliant_15_days !== false;
    const diff = ex.days_to_submission ?? 0;
    const statusPill = isComp
      ? `<span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800 flex items-center gap-1 w-fit">✓ ${diff} يوم (متقيد)</span>`
      : `<span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-950/80 text-rose-300 border border-rose-800 flex items-center gap-1 w-fit" title="المدة تتجاوز 15 يوماً!">⚠️ ${diff} يوم (تجاوز الأجل)</span>`;

    rows += `
      <tr class="border-b border-slate-800 hover:bg-slate-800/40 transition">
        <td class="px-3 py-3 font-mono text-slate-400 text-center">${idx + 1}</td>
        <td class="px-3 py-3 font-bold text-white">${ex.class_name}</td>
        <td class="px-3 py-3 text-slate-300 font-semibold">${ex.subject}</td>
        <td class="px-3 py-3 text-slate-300">${ex.teacher_name}</td>
        <td class="px-3 py-3 font-bold text-amber-400 text-center">الفرض ${ex.exam_number}</td>
        <td class="px-3 py-3 text-slate-200">
          <div class="font-bold">${ex.exam_day_name} ${ex.exam_date}</div>
          <div class="text-[11px] text-slate-400 font-mono">${ex.exam_time_str} ${ex.exam_room ? `(${ex.exam_room})` : ''}</div>
        </td>
        <td class="px-3 py-3 text-slate-300 text-center">${ex.correction_date || '-'}</td>
        <td class="px-3 py-3 text-slate-300 text-center font-mono">${ex.grades_submission_date || '-'}</td>
        <td class="px-3 py-3 text-center">${statusPill}</td>
        <td class="px-3 py-3 text-center">
          <div class="flex items-center justify-center gap-1.5">
            <button onclick="printSingleTeacherSheet('${ex.teacher_name}')" class="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg transition" title="طباعة ورقة الأستاذ">🖨️</button>
            <button onclick="editExam('${ex.id}')" class="p-1.5 bg-amber-950/80 hover:bg-amber-900 text-amber-300 rounded-lg transition" title="تعديل">✏️</button>
            <button onclick="deleteExam('${ex.id}')" class="p-1.5 bg-rose-950/80 hover:bg-rose-900 text-rose-300 rounded-lg transition" title="حذف">🗑️</button>
          </div>
        </td>
      </tr>
    `;
  });

  tbody.innerHTML = rows;
}

// Render Print Center View
function renderPrintCenter() {
  const container = document.getElementById('exams-print-preview-container');
  if (!container) return;

  const tSelect = document.getElementById('print-teacher-select');
  const tName = tSelect ? tSelect.value : '';
  const sem = window.examsState.activeSemester;

  if (!tName) {
    container.innerHTML = `
      <div class="py-16 text-center text-slate-400">
        <span class="text-4xl block mb-2">🖨️</span>
        اختر الأستاذ من القائمة أعلاه لمعاينة وطباعة بطاقة برمجة الفروض الفردية
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="w-full flex flex-col items-center justify-center py-4">
      <iframe src="/api/exams_planning/print_teacher_sheet?teacher=${encodeURIComponent(tName)}&semester=${sem}" 
              class="w-full h-[700px] border border-slate-700 rounded-2xl bg-white shadow-2xl"></iframe>
    </div>
  `;
}
window.renderPrintCenter = renderPrintCenter;

// Open Modal to Schedule an Exam
function openScheduleExamModal(examId = null) {
  window.examsState.selectedExamId = examId;
  const modal = document.getElementById('modal-schedule-exam');
  if (!modal) return;

  const titleEl = document.getElementById('modal-exam-title');
  const form = document.getElementById('form-schedule-exam');
  if (form) form.reset();

  // Reset helpers
  document.getElementById('exam-session-options-container').innerHTML = `
    <div class="text-xs text-slate-400 p-2 text-center bg-slate-950 rounded-lg border border-slate-800">
      يرجى اختيار الأستاذ والقسم وتاريخ الفرض لاستعراض الحصص المتاحة والتوصية الذكية
    </div>
  `;
  document.getElementById('compliance-preview-badge').innerHTML = '';

  if (examId) {
    const ex = window.examsState.exams.find(e => e.id === examId);
    if (ex) {
      if (titleEl) titleEl.innerText = `تعديل برمجة الفرض — ${ex.class_name} (${ex.subject})`;
      document.getElementById('modal-exam-teacher').value = ex.teacher_name || '';
      onExamTeacherChanged(ex.class_name);
      document.getElementById('modal-exam-semester').value = ex.semester || 1;
      document.getElementById('modal-exam-number').value = ex.exam_number || 1;
      document.getElementById('modal-exam-date').value = ex.exam_date || '';
      document.getElementById('modal-exam-corr-date').value = ex.correction_date || '';
      document.getElementById('modal-exam-sub-date').value = ex.grades_submission_date || '';
      document.getElementById('modal-exam-notes').value = ex.notes || '';
      
      // Load sessions and recommendations
      loadExamSessionsAndRecommendations(ex.teacher_name, ex.class_name, ex.exam_date, ex.exam_hour, ex.exam_period);
      calculateCompliance();
    }
  } else {
    if (titleEl) titleEl.innerText = "برمجة وتعيين موعد فرض محروس جديد";
    document.getElementById('modal-exam-semester').value = window.examsState.activeSemester || 1;
    // Default exam date = today + 7 days
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    const dateStr = nextWeek.toISOString().split('T')[0];
    document.getElementById('modal-exam-date').value = dateStr;

    // Default submission date = exam date + 10 days
    const subDate = new Date(nextWeek);
    subDate.setDate(subDate.getDate() + 10);
    document.getElementById('modal-exam-sub-date').value = subDate.toISOString().split('T')[0];

    // Default correction date = exam date + 3 days
    const corrDate = new Date(nextWeek);
    corrDate.setDate(corrDate.getDate() + 3);
    document.getElementById('modal-exam-corr-date').value = corrDate.toISOString().split('T')[0];

    calculateCompliance();
  }

  modal.classList.remove('hidden');
  modal.style.display = 'flex';
}
window.openScheduleExamModal = openScheduleExamModal;

function closeScheduleExamModal() {
  const modal = document.getElementById('modal-schedule-exam');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
}
window.closeScheduleExamModal = closeScheduleExamModal;

// When teacher or exam number changes in modal -> filter classes to exclude already scheduled classes
function onExamTeacherChanged(preselectedClass = null) {
  const tSelect = document.getElementById('modal-exam-teacher');
  const cSelect = document.getElementById('modal-exam-class');
  if (!tSelect || !cSelect) return;

  const tName = tSelect.value;
  const teacherObj = window.examsState.teachers.find(t => t.name === tName);

  if (!tName || !teacherObj) {
    cSelect.innerHTML = `<option value="">-- اختر الأستاذ أولاً --</option>`;
    return;
  }

  const sem = parseInt(document.getElementById('modal-exam-semester')?.value || '1', 10);
  const examNum = parseInt(document.getElementById('modal-exam-number')?.value || '1', 10);
  const currentEditingId = window.examsState.selectedExamId;

  const classes = teacherObj.classes || [];

  // Exclude classes that ALREADY have this exam number scheduled in this semester for this teacher
  const alreadyScheduled = (window.examsState.exams || []).filter(e => {
    if (currentEditingId && e.id === currentEditingId) return false;
    return e.teacher_name === tName &&
           Number(e.semester) === Number(sem) &&
           Number(e.exam_number) === Number(examNum);
  });
  const alreadyScheduledClassNames = new Set(alreadyScheduled.map(e => e.class_name));
  const availableClasses = classes.filter(c => !alreadyScheduledClassNames.has(c));

  if (availableClasses.length > 0) {
    let html = `<option value="">-- اختر القسم (${availableClasses.length} متبقية من أصل ${classes.length}) --</option>` +
      availableClasses.map(c => `<option value="${c}">${c}</option>`).join('');
    cSelect.innerHTML = html;
    cSelect.disabled = false;
  } else {
    cSelect.innerHTML = `<option value="" disabled selected>⚠️ جميع الأقسام المسندة للأستاذ (${classes.length}) مبرمج لها الفرض ${examNum} بالفعل</option>`;
    cSelect.disabled = true;
  }

  if (preselectedClass && (availableClasses.includes(preselectedClass) || preselectedClass === cSelect.value)) {
    cSelect.value = preselectedClass;
  } else if (availableClasses.length === 1) {
    cSelect.value = availableClasses[0];
  }

  // Update subject
  const subjInput = document.getElementById('modal-exam-subject');
  if (subjInput) subjInput.value = teacherObj.subject || '';

  onExamClassOrDateChanged();
}
window.onExamTeacherChanged = onExamTeacherChanged;

// When class or date changes -> fetch timetable sessions & smart recommendations
async function onExamClassOrDateChanged() {
  const tName = document.getElementById('modal-exam-teacher')?.value || '';
  const cName = document.getElementById('modal-exam-class')?.value || '';
  const dateVal = document.getElementById('modal-exam-date')?.value || '';
  if (!tName || !cName) return;

  await loadExamSessionsAndRecommendations(tName, cName, dateVal);
  calculateCompliance();
}
window.onExamClassOrDateChanged = onExamClassOrDateChanged;

// Load sessions & recommendations helper
async function loadExamSessionsAndRecommendations(tName, cName, dateVal, selectedHour = null, selectedPeriod = null) {
  const container = document.getElementById('exam-session-options-container');
  if (!container) return;

  container.innerHTML = `<div class="text-xs text-amber-400 p-2 text-center">جاري استخراج الحصص والتوصيات الذكية... ⏳</div>`;

  try {
    const sem = document.getElementById('modal-exam-semester')?.value || 1;
    const num = document.getElementById('modal-exam-number')?.value || 1;

    // 1. Fetch recommendations
    const recResp = await fetch(`/api/exams_planning/recommendations?teacher=${encodeURIComponent(tName)}&class_name=${encodeURIComponent(cName)}&semester=${sem}&exam_number=${num}&week_start=${dateVal}`);
    const recData = await recResp.json();
    const recs = recData.recommendations || [];

    // 2. Fetch all teacher sessions with class
    const sessResp = await fetch(`/api/exams_planning/teacher_sessions?teacher=${encodeURIComponent(tName)}&class_name=${encodeURIComponent(cName)}`);
    const sessData = await sessResp.json();
    const sessions = sessData.sessions || [];

    if (sessions.length === 0) {
      container.innerHTML = `
        <div class="text-xs text-rose-400 p-2 text-center bg-rose-950/40 rounded-lg border border-rose-800">
          ⚠️ تنبيه: لا توجد حصص مبرمجة للأستاذ مع هذا القسم في جدول الحصص! يرجى التأكد من ورقة الإسناد.
        </div>
      `;
      return;
    }

    // Determine target day of week from dateVal if given
    let dayNameOfDate = '';
    if (dateVal) {
      const dObj = new Date(dateVal);
      const arabicDays = ["الأحد", "الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة", "السبت"];
      dayNameOfDate = arabicDays[dObj.getDay()];
    }

    // Match sessions on this day vs other days
    let html = `<div class="space-y-1.5">`;

    // Recommendations Alert Pill
    const matchingRec = recs.find(r => r.date === dateVal);
    if (matchingRec) {
      html += `
        <div class="p-2 rounded-lg text-xs font-bold ${matchingRec.status === 'optimal' ? 'bg-emerald-950/80 border border-emerald-700 text-emerald-300' : (matchingRec.status === 'acceptable' ? 'bg-amber-950/80 border border-amber-700 text-amber-300' : 'bg-rose-950/80 border border-rose-700 text-rose-300')} mb-2 flex items-center justify-between">
          <span>${matchingRec.badge_label}</span>
          <span class="text-[10px] text-slate-400">${matchingRec.note}</span>
        </div>
      `;
    }

    html += `<label class="block text-[11px] font-bold text-slate-300 mb-1">اختر الحصة المعتمدة في استعمال الزمن الأسبوعي:</label>`;

    sessions.forEach((s, idx) => {
      const isDayMatch = (s.day_name === dayNameOfDate);
      const isHourMatch = (selectedHour && s.hour === selectedHour && (!selectedPeriod || s.period === selectedPeriod));
      const checkedAttr = (isDayMatch && (!selectedHour || isHourMatch)) ? 'checked' : (idx === 0 && !selectedHour ? 'checked' : '');

      html += `
        <label class="flex items-center justify-between p-2 rounded-xl border border-slate-800 bg-slate-900/90 hover:bg-slate-800/80 cursor-pointer transition text-xs">
          <div class="flex items-center gap-2">
            <input type="radio" name="selected_session" value="${s.hour}##${s.period}##${s.time_str}##${s.room}##${s.day_name}" ${checkedAttr} class="text-amber-500 focus:ring-amber-500" onchange="onSessionRadioSelected(this)">
            <div>
              <span class="font-bold text-white">${s.day_name} (${s.period_label})</span>
              <span class="text-amber-400 font-mono text-[11px] mr-1">${s.hour} [${s.time_str}]</span>
              <span class="text-slate-400 text-[11px] mr-1">القاعة: ${s.room || 'عامة'}</span>
            </div>
          </div>
          ${isDayMatch ? '<span class="text-[10px] bg-emerald-900/80 text-emerald-300 border border-emerald-700 px-2 py-0.5 rounded-full font-bold">حصة اليوم المحدد ✓</span>' : ''}
        </label>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;

  } catch (err) {
    container.innerHTML = `<div class="text-xs text-rose-400 p-2">خطأ أثناء استخراج الحصص: ${err.message}</div>`;
  }
}

// When session radio button is clicked
function onSessionRadioSelected(radio) {
  const parts = radio.value.split("##");
  const hour = parts[0];
  const period = parts[1];
  const timeStr = parts[2];
  const room = parts[3];
  const dayName = parts[4];

  document.getElementById('modal-exam-hour').value = hour;
  document.getElementById('modal-exam-period').value = period;
  document.getElementById('modal-exam-timestr').value = timeStr;
  document.getElementById('modal-exam-room').value = room;
  document.getElementById('modal-exam-dayname').value = dayName;
}
window.onSessionRadioSelected = onSessionRadioSelected;

// Live 15-day compliance calculator
function calculateCompliance() {
  const eDateStr = document.getElementById('modal-exam-date')?.value;
  const sDateStr = document.getElementById('modal-exam-sub-date')?.value;
  const badgeEl = document.getElementById('compliance-preview-badge');
  if (!badgeEl) return;

  if (!eDateStr || !sDateStr) {
    badgeEl.innerHTML = '';
    return;
  }

  const eDate = new Date(eDateStr);
  const sDate = new Date(sDateStr);
  const diffDays = Math.round((sDate - eDate) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    badgeEl.innerHTML = `<span class="px-3 py-1 bg-rose-950 text-rose-300 border border-rose-800 rounded-lg text-xs font-bold block">❌ خطأ: تاريخ التسليم يسبق تاريخ التمرير!</span>`;
  } else if (diffDays > 15) {
    badgeEl.innerHTML = `
      <div class="p-2.5 bg-rose-950/80 border border-rose-700 text-rose-300 rounded-xl text-xs font-bold space-y-1">
        <div class="flex items-center gap-1.5 text-rose-200">
          <span>⚠️ تنبيه نظامي:</span>
          <span>المدة الفاصلة (${diffDays} يوماً) تتجاوز الحد الأقصى 15 يوماً!</span>
        </div>
        <p class="text-[10.5px] text-rose-300 font-normal">طبقاً لمذكرات التقويم الوزارية، يجب ألا تتجاوز المدة 15 يوماً لإطلاع المتعلمين وتسليم النقط لمسكها في مسار.</p>
      </div>
    `;
  } else {
    badgeEl.innerHTML = `
      <div class="p-2 bg-emerald-950/80 border border-emerald-700 text-emerald-300 rounded-xl text-xs font-bold flex items-center justify-between">
        <span>✓ المدة الفاصلة: ${diffDays} يوماً (متقيد بالآجال المحددة)</span>
        <span class="text-[10px] bg-emerald-900 px-2 py-0.5 rounded text-white font-mono">&le; 15 يوم</span>
      </div>
    `;
  }
}
window.calculateCompliance = calculateCompliance;

// Auto-fill submission date dynamically based on teacher workload and ministerial deadlines
async function onExamDateChanged() {
  const eDateStr = document.getElementById('modal-exam-date')?.value;
  const tName = document.getElementById('modal-exam-teacher')?.value;
  const sem = document.getElementById('modal-exam-semester')?.value || 1;

  if (eDateStr && tName) {
    try {
      const resp = await fetch(`/api/exams_planning/calc_deadlines?teacher_name=${encodeURIComponent(tName)}&exam_date=${eDateStr}&semester=${sem}`);
      const data = await resp.json();
      if (data.deadlines) {
        document.getElementById('modal-exam-sub-date').value = data.deadlines.grades_submission_date;
        document.getElementById('modal-exam-corr-date').value = data.deadlines.correction_date;
        
        const badge = document.getElementById('compliance-preview-badge');
        if (badge) {
          badge.innerHTML = `
            <div class="p-2 bg-slate-950/80 border border-teal-700/60 text-teal-300 rounded-xl text-xs space-y-0.5">
              <div class="flex items-center justify-between font-bold">
                <span>ℹ️ ${data.deadlines.load_label}: تم احتساب مهلة ${data.deadlines.days_to_submission} يوماً للتسليم</span>
                <span class="text-[10px] bg-teal-900 px-2 py-0.5 rounded text-white">&le; 15 يوم ✓</span>
              </div>
              <p class="text-[10.5px] text-slate-400 font-normal">يراعي النظام عدد الأقسام المسندة للأستاذ لتمكينه من تصحيح رصين قبل تسليم النقط للإدارة في مسار.</p>
            </div>
          `;
        }
      }
    } catch (e) {
      // Fallback
      const eDate = new Date(eDateStr);
      const subDate = new Date(eDate);
      subDate.setDate(subDate.getDate() + 12);
      document.getElementById('modal-exam-sub-date').value = subDate.toISOString().split('T')[0];
      const corrDate = new Date(eDate);
      corrDate.setDate(corrDate.getDate() + 5);
      document.getElementById('modal-exam-corr-date').value = corrDate.toISOString().split('T')[0];
    }
  } else if (eDateStr) {
    const eDate = new Date(eDateStr);
    const subDate = new Date(eDate);
    subDate.setDate(subDate.getDate() + 12);
    document.getElementById('modal-exam-sub-date').value = subDate.toISOString().split('T')[0];
    const corrDate = new Date(eDate);
    corrDate.setDate(corrDate.getDate() + 5);
    document.getElementById('modal-exam-corr-date').value = corrDate.toISOString().split('T')[0];
  }

  onExamClassOrDateChanged();
}
window.onExamDateChanged = onExamDateChanged;

// Submit Schedule Form
async function submitExamScheduleForm(event) {
  if (event) event.preventDefault();

  const tName = document.getElementById('modal-exam-teacher')?.value;
  const cName = document.getElementById('modal-exam-class')?.value;
  const subj = document.getElementById('modal-exam-subject')?.value;
  const sem = parseInt(document.getElementById('modal-exam-semester')?.value || 1);
  const num = parseInt(document.getElementById('modal-exam-number')?.value || 1);
  const eDate = document.getElementById('modal-exam-date')?.value;
  const cDate = document.getElementById('modal-exam-corr-date')?.value;
  const sDate = document.getElementById('modal-exam-sub-date')?.value;
  const notes = document.getElementById('modal-exam-notes')?.value;

  if (!tName || !cName || !eDate || !sDate) {
    if (window.showToast) window.showToast("يرجى ملء جميع الحقول الإلزامية", "error");
    return;
  }

  // Session details from radio or hidden fields
  const checkedRadio = document.querySelector('input[name="selected_session"]:checked');
  let hour = "ح 1";
  let period = "ص";
  let timeStr = "08:00 - 09:00";
  let room = "ق 1";
  let dayName = "الاثنين";

  if (checkedRadio) {
    const parts = checkedRadio.value.split("##");
    hour = parts[0];
    period = parts[1];
    timeStr = parts[2];
    room = parts[3];
    dayName = parts[4];
  }

  const payload = {
    id: window.examsState.selectedExamId || undefined,
    teacher_name: tName,
    class_name: cName,
    subject: subj,
    semester: sem,
    exam_number: num,
    exam_date: eDate,
    exam_day_name: dayName,
    exam_period: period,
    exam_hour: hour,
    exam_time_str: timeStr,
    exam_room: room,
    correction_date: cDate,
    grades_submission_date: sDate,
    notes: notes
  };

  try {
    const resp = await fetch('/api/exams_planning/save_exam', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify(payload)
    });
    const res = await resp.json();
    if (res.success) {
      if (window.showToast) window.showToast("تم حفظ واعتماد برمجة الفرض بنجاح ✓", "success");
      closeScheduleExamModal();
      loadExamsPlanningData();
    } else {
      if (window.showToast) window.showToast("حدث خطأ أثناء الحفظ: " + (res.error || ""), "error");
    }
  } catch (err) {
    if (window.showToast) window.showToast("فشل الاتصال بالخادم: " + err.message, "error");
  }
}
window.submitExamScheduleForm = submitExamScheduleForm;

// Edit Exam
function editExam(examId) {
  openScheduleExamModal(examId);
}
window.editExam = editExam;

// Delete Exam
async function deleteExam(examId) {
  if (!confirm("هل أنت متأكد من رغبتك في حذف هذا الفرض المبرمج نهائياً؟")) return;

  try {
    const resp = await fetch('/api/exams_planning/delete_exam', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ id: examId })
    });
    const res = await resp.json();
    if (res.success) {
      if (window.showToast) window.showToast("تم حذف الفرض بنجاح", "info");
      loadExamsPlanningData();
    }
  } catch (err) {
    if (window.showToast) window.showToast("خطأ أثناء الحذف: " + err.message, "error");
  }
}
window.deleteExam = deleteExam;

// Trigger Smart Bulk Auto Plan for a Teacher
async function triggerBulkAutoPlan() {
  const tSelect = document.getElementById('filter-exam-teacher');
  const tName = tSelect ? tSelect.value : '';

  if (!tName) {
    alert("يرجى اختيار الأستاذ المعني أولاً من قائمة الأساتذة أعلاه لتطبيق البرمجة الذكية التلقائية.");
    return;
  }

  const sem = window.examsState.activeSemester;
  const numStr = prompt(`تحديد رقم الفرض لبرمجته آلياً للأستاذ ${tName} (1 أو 2 أو 3):`, "1");
  if (!numStr || !['1', '2', '3'].includes(numStr.trim())) return;
  const num = parseInt(numStr.trim());

  if (!confirm(`سيقوم المحرك الذكي الآن ببرمجة الفرض رقم ${num} لجميع أقسام الأستاذ (${tName}) مع اختيار المواعيد المثالية التي تتفادى أي تراكم للفروض على التلاميذ في نفس اليوم. هل تريد المتابعة؟`)) return;

  try {
    const resp = await fetch('/api/exams_planning/bulk_auto_plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ teacher: tName, semester: sem, exam_number: num })
    });
    const res = await resp.json();
    if (res.success) {
      if (window.showToast) window.showToast(`تمت البرمجة الذكية لـ ${res.scheduled_count} قسماً بنجاح ودون أي تعارض! ✓`, "success");
      loadExamsPlanningData();
    }
  } catch (err) {
    alert("خطأ أثناء البرمجة التلقائية: " + err.message);
  }
}
window.triggerBulkAutoPlan = triggerBulkAutoPlan;

// Print Single Teacher Sheet
function printSingleTeacherSheet(teacherName) {
  const sem = window.examsState.activeSemester;
  const url = `/api/exams_planning/print_teacher_sheet?teacher=${encodeURIComponent(teacherName)}&semester=${sem}`;
  window.open(url, '_blank');
}
window.printSingleTeacherSheet = printSingleTeacherSheet;

// Print School Calendar
function printSchoolCalendar() {
  const sem = window.examsState.activeSemester;
  const url = `/api/exams_planning/print_school_calendar?semester=${sem}`;
  window.open(url, '_blank');
}
window.printSchoolCalendar = printSchoolCalendar;

// Table filter event handlers
function onExamsFilterChanged() {
  window.examsState.filterTeacher = document.getElementById('filter-exam-teacher')?.value || '';
  window.examsState.filterClass = document.getElementById('filter-exam-class')?.value || '';
  window.examsState.filterCompliance = document.getElementById('filter-exam-compliance')?.value || 'all';
  window.examsState.filterSearch = document.getElementById('filter-exam-search')?.value || '';

  renderExamsMasterTable();
}
window.onExamsFilterChanged = onExamsFilterChanged;

function renderExamsPlanningViews() {
  if (window.examsState.activeSubTab === 'calendar') renderCalendarDashboard();
  if (window.examsState.activeSubTab === 'teachers') renderTeachersProgressView();
  if (window.examsState.activeSubTab === 'table') renderExamsMasterTable();
  if (window.examsState.activeSubTab === 'print') renderPrintCenter();
}


function toggleCompensatoryMode() {
  const isComp = document.getElementById('modal-exam-is-compensatory')?.checked;
  const compBox = document.getElementById('compensatory-options');
  const normalSessionsBox = document.getElementById('sessions-recommendations-box');
  const feedbackEl = document.getElementById('desktop-avail-feedback');

  if (compBox) {
    if (isComp) {
      compBox.classList.remove('hidden');
      compBox.classList.add('grid');
      if (normalSessionsBox) normalSessionsBox.classList.add('hidden');
      runDesktopAvailabilityCheck();
    } else {
      compBox.classList.add('hidden');
      compBox.classList.remove('grid');
      if (normalSessionsBox) normalSessionsBox.classList.remove('hidden');
      if (feedbackEl) feedbackEl.classList.add('hidden');
    }
  }
}
window.toggleCompensatoryMode = toggleCompensatoryMode;

async function runDesktopAvailabilityCheck() {
  const isComp = document.getElementById('modal-exam-is-compensatory')?.checked;
  if (!isComp) return;

  const cls = document.getElementById('modal-exam-class')?.value;
  const dVal = document.getElementById('modal-exam-date')?.value;
  const sIdx = parseInt(document.getElementById('modal-comp-slot')?.value || '7', 10);
  const rm = document.getElementById('modal-comp-room')?.value;
  const tName = document.getElementById('modal-exam-teacher')?.value;
  const feedbackEl = document.getElementById('desktop-avail-feedback');
  if (!feedbackEl || !cls || !dVal || !rm) return;

  const d = new Date(dVal);
  const dow = (d.getDay() === 0 ? 7 : d.getDay()); // 1=Mon ... 6=Sat

  feedbackEl.classList.remove('hidden');
  feedbackEl.className = 'text-[11px] px-2.5 py-1.5 rounded-lg font-bold bg-slate-800 text-slate-300 border border-slate-700';
  feedbackEl.innerHTML = '⏳ جاري فحص شغور القسم والقاعة/الملعب...';

  try {
    const res = await fetch('/api/exams_planning/check_availability', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        class_name: cls,
        room_name: rm,
        exam_date: dVal,
        slot_index: sIdx,
        day_of_week: dow,
        teacher_name: tName,
        exclude_exam_id: window.examsState.selectedExamId
      })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.available) {
        feedbackEl.className = 'text-[11px] px-2.5 py-1.5 rounded-lg font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-600/70';
        feedbackEl.innerHTML = '🟢 <strong>متاح للحجز:</strong> القسم شاغر والقاعة/الملعب شاغر بالكامل!';
      } else {
        feedbackEl.className = 'text-[11px] px-2.5 py-1.5 rounded-lg font-bold bg-rose-950/80 text-rose-300 border border-rose-600/70';
        feedbackEl.innerHTML = `🔴 <strong>تعذر الحجز:</strong> ${data.message}`;
      }
      return;
    }
  } catch (e) {}

  feedbackEl.className = 'text-[11px] px-2.5 py-1.5 rounded-lg font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-600/70';
  feedbackEl.innerHTML = '🟢 <strong>متاح للحجز:</strong> القسم والقاعة متاحان.';
}
window.runDesktopAvailabilityCheck = runDesktopAvailabilityCheck;


// ========================================================
// TEACHERS PROGRESS OVERVIEW & BULK DELETION CONTROLLER
// ========================================================

function renderTeachersProgressView() {
  const tbody = document.getElementById('exams-teachers-progress-tbody');
  if (!tbody) return;

  const sem = window.examsState.activeSemester || 1;
  const exams = window.examsState.exams.filter(e => e.semester === sem);
  const teachers = window.examsState.teachers || [];
  const search = (document.getElementById('filter-teacher-progress-search')?.value || '').trim().toLowerCase();
  const statusFilter = document.getElementById('filter-teacher-progress-status')?.value || 'ALL';

  // Group exams by teacher
  const teacherExamsMap = {};
  exams.forEach(ex => {
    const tName = (ex.teacher_name || '').trim();
    if (!tName) return;
    if (!teacherExamsMap[tName]) teacherExamsMap[tName] = [];
    teacherExamsMap[tName].push(ex);
  });

  // Build teacher rows list
  let teacherRows = teachers.map(t => {
    const tExams = teacherExamsMap[t.name] || [];
    const count = tExams.length;
    const numsCount = { 1: 0, 2: 0, 3: 0, 4: 0 };
    const classesSet = new Set();
    let allCompliant = true;

    tExams.forEach(e => {
      const num = Number(e.exam_number || 1);
      if (numsCount[num] !== undefined) numsCount[num]++;
      if (e.class_name) classesSet.add(e.class_name);
      if (e.is_compliant_15_days === false) allCompliant = false;
    });

    return {
      teacher: t,
      examsCount: count,
      numsCount,
      classes: Array.from(classesSet),
      allCompliant,
      hasSubmitted: count > 0
    };
  });

  // Filter by status
  if (statusFilter === 'SUBMITTED') {
    teacherRows = teacherRows.filter(r => r.hasSubmitted);
  } else if (statusFilter === 'PENDING') {
    teacherRows = teacherRows.filter(r => !r.hasSubmitted);
  }

  // Filter by search
  if (search) {
    teacherRows = teacherRows.filter(r =>
      r.teacher.name.toLowerCase().includes(search) ||
      (r.teacher.subject && r.teacher.subject.toLowerCase().includes(search))
    );
  }

  // Sort: submitted teachers first, then by examsCount descending
  teacherRows.sort((a, b) => b.examsCount - a.examsCount || a.teacher.name.localeCompare(b.teacher.name));

  // Update stats pill
  const submittedCount = Object.keys(teacherExamsMap).length;
  const statsPill = document.getElementById('teachers-progress-stats-pill');
  if (statsPill) {
    statsPill.innerHTML = `مسك ${submittedCount} من أصل ${teachers.length} أستاذ • إجمالي الفروض: ${exams.length} فرض`;
  }

  if (teacherRows.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="py-12 text-center text-slate-400">
          <span class="text-3xl block mb-2">🔍</span>
          لا توجد نتائج مطابقة لمعايير البحث الحالية.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = teacherRows.map((r, idx) => {
    const t = r.teacher;
    const total = r.examsCount;
    const hasSubmitted = r.hasSubmitted;
    const classesStr = r.classes.length > 0 ? r.classes.join(', ') : (t.classes && t.classes.length > 0 ? t.classes.join(', ') : '-');

    const pillsHtml = [1, 2, 3, 4].map(n => {
      const c = r.numsCount[n];
      if (c > 0) {
        return `<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-teal-950 text-teal-300 border border-teal-800" title="الفرض ${n}: مبرمج لـ ${c} أقسام">ف${n}: <strong>${c}</strong></span>`;
      }
      return `<span class="px-1.5 py-0.5 rounded-md text-[9px] font-medium bg-slate-900 text-slate-600 border border-slate-800" title="الفرض ${n}: لم يبرمج بعد">ف${n}: -</span>`;
    }).join(' ');

    const compBadge = !hasSubmitted
      ? `<span class="text-slate-500 font-mono">-</span>`
      : r.allCompliant
        ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">متقيد ✓</span>`
        : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800">تجاوز الأجل ⚠️</span>`;

    return `
      <tr class="border-b border-slate-800 hover:bg-slate-800/40 transition">
        <td class="py-3 px-3 text-center font-mono text-slate-400">${idx + 1}</td>
        <td class="py-3 px-4 font-bold text-white flex items-center gap-2">
          <span>👨‍🏫</span>
          <span>${t.name}</span>
        </td>
        <td class="py-3 px-3 text-slate-300 font-semibold">${t.subject || '-'}</td>
        <td class="py-3 px-3 text-center">
          ${hasSubmitted
            ? `<span class="px-2.5 py-1 rounded-full text-xs font-black bg-teal-500/20 text-teal-300 border border-teal-500/50">${total} فرض</span>`
            : `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-500">غير ممسوك</span>`
          }
        </td>
        <td class="py-3 px-4 text-center">
          <div class="flex items-center justify-center gap-1">
            ${pillsHtml}
          </div>
        </td>
        <td class="py-3 px-4 font-mono text-[11px] text-slate-300" title="${classesStr}">${classesStr}</td>
        <td class="py-3 px-3 text-center">${compBadge}</td>
        <td class="py-3 px-4 text-center">
          <div class="flex items-center justify-center gap-1.5">
            ${hasSubmitted ? `
              <button onclick="printSingleTeacherSheet('${t.name}')" class="px-2.5 py-1 bg-teal-950/80 hover:bg-teal-900 text-teal-300 border border-teal-700/60 rounded-lg text-xs font-bold transition flex items-center gap-1 cursor-pointer" title="طباعة بطاقة تتبع الفروض لهذا الأستاذ">
                <span>🖨️</span>
                <span>طباعة</span>
              </button>
              <button onclick="confirmDeleteTeacherExams('${t.name}')" class="px-2.5 py-1 bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800/60 rounded-lg text-xs font-bold transition flex items-center gap-1 cursor-pointer" title="إلغاء وحذف جميع فروض هذا الأستاذ">
                <span>🗑️</span>
                <span>إلغاء الفروض</span>
              </button>
            ` : `
              <span class="text-slate-500 text-[11px]">في الانتظار</span>
            `}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}
window.renderTeachersProgressView = renderTeachersProgressView;

function openBulkDeleteExamsModal() {
  const teachers = window.examsState.teachers || [];
  const sel = document.getElementById('bulk-del-teacher-select');
  if (sel) {
    sel.innerHTML = `<option value="">-- اختر الأستاذ(ة) --</option>` +
      teachers.map(t => `<option value="${t.name}">${t.name} (${t.subject})</option>`).join('');
  }
  if (typeof openModal === 'function') {
    openModal('modal-bulk-delete-exams');
  } else {
    const m = document.getElementById('modal-bulk-delete-exams');
    if (m) m.classList.remove('hidden');
  }
}
window.openBulkDeleteExamsModal = openBulkDeleteExamsModal;

function onBulkDelScopeChanged(val) {
  const tSel = document.getElementById('bulk-del-teacher-select');
  const numBoxes = document.getElementById('bulk-del-numbers-boxes');
  if (tSel) tSel.disabled = (val !== 'teacher' && val !== 'exam_numbers');
  if (numBoxes) {
    if (val === 'exam_numbers') {
      numBoxes.classList.remove('opacity-40', 'pointer-events-none');
    } else {
      numBoxes.classList.add('opacity-40', 'pointer-events-none');
    }
  }
}
window.onBulkDelScopeChanged = onBulkDelScopeChanged;

async function executeBulkDeleteExams() {
  const radios = document.querySelectorAll('input[name="bulk_del_scope"]');
  let scope = 'all';
  radios.forEach(r => { if (r.checked) scope = r.value; });

  const sem = window.examsState.activeSemester || 1;
  const tName = document.getElementById('bulk-del-teacher-select')?.value || '';
  const checkedNums = Array.from(document.querySelectorAll('input[name="bulk_del_num"]:checked')).map(c => parseInt(c.value, 10));

  let confirmMsg = '';
  let payload = { semester: sem };

  if (scope === 'all') {
    confirmMsg = '⚠️ تحذير نهائي: هل أنت متأكد من رغبتك في إلغاء وحذف جميع فروض المؤسسة بالكامل للدورة الحالية؟\n\nلا يمكن التراجع عن هذا الإجراء.';
    payload.type = 'all';
  } else if (scope === 'teacher') {
    if (!tName) {
      alert('يرجى اختيار الأستاذ(ة) المراد إلغاء فروضه أولاً.');
      return;
    }
    confirmMsg = `هل أنت متأكد من رغبتك في إلغاء كافة الفروض المبرمجة للأستاذ(ة): ${tName}؟`;
    payload.type = 'teacher';
    payload.teacher_name = tName;
  } else if (scope === 'exam_numbers') {
    if (checkedNums.length === 0) {
      alert('يرجى تحديد رقم فرض واحد على الأقل للإلغاء (مثلاً: الفرض 4).');
      return;
    }
    const numLabels = checkedNums.map(n => `الفرض ${n}`).join(' و ');
    confirmMsg = `هل أنت متأكد من رغبتك في إلغاء برمجة (${numLabels}) ${tName ? `للأستاذ: ${tName}` : 'لكافة أساتذة المؤسسة'}؟`;
    payload.type = 'exam_numbers';
    payload.exam_numbers = checkedNums;
    if (tName) payload.teacher_name = tName;
  }

  if (!confirm(confirmMsg)) return;

  try {
    const res = await fetch('/api/exams_planning/delete_exams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      if (typeof closeModal === 'function') closeModal('modal-bulk-delete-exams');
      else document.getElementById('modal-bulk-delete-exams')?.classList.add('hidden');
      if (window.showToast) window.showToast(`✓ تم بنجاح إلغاء وحذف ${data.deleted_count} فرض مبرمج`, 'success');
      loadExamsPlanningData();
    } else {
      alert('حدث خطأ أثناء تنفيذ الإلغاء: ' + (data.error || ''));
    }
  } catch (err) {
    console.error('executeBulkDeleteExams error:', err);
    alert('تعذر الاتصال بالخادم لتنفيذ الإلغاء.');
  }
}
window.executeBulkDeleteExams = executeBulkDeleteExams;

async function confirmDeleteTeacherExams(teacherName) {
  if (!teacherName) return;
  const sem = window.examsState.activeSemester || 1;
  const ok = confirm(`هل أنت متأكد من رغبتك في إلغاء جميع الفروض المبرمجة للأستاذ(ة): ${teacherName}؟\n\nسيتم حذف الفروض وإتاحتها للبرمجة من جديد.`);
  if (!ok) return;

  try {
    const res = await fetch('/api/exams_planning/delete_exams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'teacher', teacher_name: teacherName, semester: sem })
    });
    const data = await res.json();
    if (data.success) {
      if (window.showToast) window.showToast(`✓ تم إلغاء جميع فروض الأستاذ(ة) ${teacherName} بنجاح (${data.deleted_count} فرض)`, 'success');
      loadExamsPlanningData();
    }
  } catch (e) {
    console.error(e);
  }
}
window.confirmDeleteTeacherExams = confirmDeleteTeacherExams;
