// نظام «مسك الغياب» — الثانوية التأهيلية أنفك
const STORAGE_KEY = 'mask_alghiyab_anfg_v3';

// توليد رقم تعريفي عشوائي من 8 حروف وأرقام (بدون الحروف المتشابهة مثل 0/O و 1/I)
function generateRandom8CharCode(existingCodesSet = new Set()) {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  while (true) {
    let code = '';
    for (let i = 0; i < 8; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    if (!existingCodesSet.has(code)) {
      existingCodesSet.add(code);
      return code;
    }
  }
}

// الربط التلقائي بين رموز أقسام مسار (ListEleve) ورموز أقسام جدول الحصص
const MASSAR_TO_TIMETABLE_CLASS = {
  'TCSF-1': 'TC-SC-F-1',
  'TCLSHF-1': 'TC-LSH-F-1',
  'TCLSHF-2': 'TC-LSH-F-2',
  '1BACSEF-1': '1BAC-EXP-F-1',
  '1BACSEF-2': '1BAC-EXP-F-2',
  '1BACSHF-1': '1BAC-LSH-F-1',
  '1BACSHF-2': '1BAC-LSH-F-2',
  '2BACLF-1': '2BAC-L-F-1',
  '2BACSHF-1': '2BAC-SH-F-1',
  '2BACSPF-1': '2BAC-PC-F-1',
  '2BACSVTF-1': '2BAC-SVT-F-1'
};

function normalizeMassarClassCode(rawCode) {
  const clean = String(rawCode || '').trim().toUpperCase();
  return MASSAR_TO_TIMETABLE_CLASS[clean] || clean;
}

const DAYS_AR = {
  1: 'الاثنين',
  2: 'الثلاثاء',
  3: 'الأربعاء',
  4: 'الخميس',
  5: 'الجمعة',
  6: 'السبت',
  0: 'الأحد'
};

// المواقيت الافتراضية المرنة (قابلة للتعديل من طرف المدير)
const DEFAULT_TIME_SLOTS = [
  { slotIndex: 1, period: 'MORNING', periodNumber: 1, label: 'صباحية 1', startTime: '08:00', endTime: '09:00' },
  { slotIndex: 2, period: 'MORNING', periodNumber: 2, label: 'صباحية 2', startTime: '09:00', endTime: '10:00' },
  { slotIndex: 3, period: 'MORNING', periodNumber: 3, label: 'صباحية 3', startTime: '10:00', endTime: '11:00' },
  { slotIndex: 4, period: 'MORNING', periodNumber: 4, label: 'صباحية 4', startTime: '11:00', endTime: '12:00' },
  { slotIndex: 5, period: 'AFTERNOON', periodNumber: 1, label: 'مسائية 1', startTime: '14:00', endTime: '15:00' },
  { slotIndex: 6, period: 'AFTERNOON', periodNumber: 2, label: 'مسائية 2', startTime: '15:00', endTime: '16:00' },
  { slotIndex: 7, period: 'AFTERNOON', periodNumber: 3, label: 'مسائية 3', startTime: '16:00', endTime: '17:00' },
  { slotIndex: 8, period: 'AFTERNOON', periodNumber: 4, label: 'مسائية 4', startTime: '17:00', endTime: '18:00' }
];

function generateDefaultStudents(classes) {
  return [];
}

// الحصول على التاريخ والوقت الحاليين حسب التوقيت المغربي الرسمي (Africa/Casablanca)
function getMoroccanDateTime() {
  try {
    const now = new Date();
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Africa/Casablanca',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }).formatToParts(now);
    const map = {};
    parts.forEach(p => {
      map[p.type] = p.value;
    });
    const dateStr = `${map.year}-${map.month}-${map.day}`;
    const hour = map.hour === '24' ? '00' : map.hour;
    const timeStr = `${hour}:${map.minute}`;
    return { dateStr, timeStr };
  } catch (e) {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');
    return { dateStr: `${yyyy}-${mm}-${dd}`, timeStr: `${hh}:${min}` };
  }
}

function loadState() {
  const schoolData = window.ANFG_SCHOOL_DATA || {
    classes: [],
    students: [],
    teachers: [],
    timetable: []
  };
  const moroccanNow = getMoroccanDateTime();

  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      // ضمان توفر رقم مسار وتاريخ الازدياد لجميع التلاميذ من بيانات المؤسسة الأصلية
      if (parsed.students && schoolData.students && schoolData.students.length > 0) {
        parsed.students = parsed.students.map(st => {
          if (st.massarCode) return st;
          const match =
            schoolData.students.find(x => x.studentId === st.studentId) ||
            schoolData.students.find(x => x.classCode === st.classCode && x.fullName === st.fullName) ||
            schoolData.students.find(x => x.classCode === st.classCode && x.rollNumber === st.rollNumber);
          return match ? { ...match, ...st, massarCode: match.massarCode, birthDate: match.birthDate, gender: match.gender } : st;
        });
      }
      if (parsed.ui) {
        parsed.ui.manualTimeOverride = false;
        parsed.ui.simDate = moroccanNow.dateStr;
        parsed.ui.simTime = moroccanNow.timeStr;
        parsed.ui.selectedSessionOverride = null;
      }
      return parsed;
    } catch (e) {
      console.error(e);
    }
  }

  const usedSet = new Set(['ADMIN888']);
  const teachersWith8Char = (schoolData.teachers || []).map(t => {
    const code = t.loginCode && t.loginCode.length === 8 ? t.loginCode : generateRandom8CharCode(usedSet);
    usedSet.add(code);
    return { ...t, loginCode: code };
  });

  return {
    settings: {
      schoolName: 'الثانوية التأهيلية أنفك — مديرية سيدي إفني (045892P)',
      principalName: 'عبدالله الرزاق',
      principalCode: 'ADMIN888',
      lateEntryMaxDays: 7,
      scheduleMode: 'NORMAL'
    },
    timeSlots: DEFAULT_TIME_SLOTS,
    teachers: teachersWith8Char,
    classes: schoolData.classes,
    students: schoolData.students,
    timetable: schoolData.timetable,
    attendanceSessions: {},
    ui: {
      isLoggedIn: false, // يبدأ التطبيق بصفحة تسجيل الدخول
      role: 'TEACHER', // TEACHER | PRINCIPAL
      currentTeacherId: teachersWith8Char[0]?.teacherId || 'T01',
      showDemoCodesOnLogin: false,
      showAbsentTodayPanel: false,
      manualTimeOverride: false,
      simDate: moroccanNow.dateStr,
      simTime: moroccanNow.timeStr,
      selectedSessionOverride: null,
      showMissedDrawer: false,
      principalTab: 'LIVE',
      principalFilterStatus: 'ALL',
      selectedStudentClass: schoolData.classes[0]?.classCode || 'TC-SC-F-1'
    }
  };
}

let state = loadState();

// دالة ذكية لاسترجاع بيانات التلميذ الكاملة (الاسم، رقم مسار، القسم) من معرفه
function resolveStudentById(stId, fallbackClassCode = '') {
  let st = state.students.find(s => s.studentId === stId);
  if (st) return st;

  // في حال كان المعرف بصيغة القسم_رقم الترتيب مثل TC-SC-F-1_S02 أو TC-SC-F-1_J170005630
  const parts = String(stId || '').split('_');
  if (parts.length >= 2) {
    const cls = parts.slice(0, -1).join('_');
    const tail = parts[parts.length - 1];
    // بحث برقم مسار
    st = state.students.find(s => s.massarCode === tail);
    if (st) return st;
    // بحث برقم الترتيب داخل القسم
    const rollMatch = tail.match(/^S?(\d+)$/i);
    if (rollMatch) {
      const rollNum = Number(rollMatch[1]);
      st = state.students.find(s => s.classCode === cls && s.rollNumber === rollNum);
      if (st) return st;
    }
  }

  return {
    studentId: stId,
    rollNumber: '-',
    massarCode: String(stId || '').split('_').pop() || 'غير متوفر',
    fullName: stId,
    gender: '-',
    birthDate: '-',
    classCode: fallbackClassCode || '-'
  };
}

let lastServerSyncAt = 0;

function saveState(isConfigUpdate = false) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  pushStateToServer(isConfigUpdate);
}

async function pushStateToServer(isConfigUpdate = false) {
  try {
    const payload = {
      attendanceSessions: state.attendanceSessions || {},
      justifiedAbsences: state.justifiedAbsences || {},
      isConfigUpdate: Boolean(isConfigUpdate || state.ui?.role === 'PRINCIPAL')
    };
    if (payload.isConfigUpdate) {
      payload.settings = state.settings;
      payload.timeSlots = state.timeSlots;
      payload.teachers = state.teachers;
      payload.classes = state.classes;
      payload.students = state.students;
      payload.timetable = state.timetable;
    }
    const res = await fetch('/api/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const serverData = await res.json();
      applyServerSharedData(serverData, false);
    }
  } catch (e) {
    // في حال عدم الاتصال بالخادم يستمر العمل محلياً دون مشكلة
  }
}

function applyServerSharedData(serverData, shouldRender = true) {
  if (!serverData || typeof serverData !== 'object') return;
  let changed = false;

  if (serverData.attendanceSessions && typeof serverData.attendanceSessions === 'object') {
    if (!state.attendanceSessions) state.attendanceSessions = {};
    for (const [k, rec] of Object.entries(serverData.attendanceSessions)) {
      const localRec = state.attendanceSessions[k];
      if (!localRec || JSON.stringify(localRec) !== JSON.stringify(rec)) {
        state.attendanceSessions[k] = rec;
        changed = true;
      }
    }
  }

  if (serverData.justifiedAbsences && typeof serverData.justifiedAbsences === 'object') {
    if (!state.justifiedAbsences) state.justifiedAbsences = {};
    for (const [k, val] of Object.entries(serverData.justifiedAbsences)) {
      if (state.justifiedAbsences[k] !== val) {
        state.justifiedAbsences[k] = val;
        changed = true;
      }
    }
  }

  if (serverData.settings && JSON.stringify(state.settings) !== JSON.stringify(serverData.settings)) {
    state.settings = serverData.settings;
    changed = true;
  }
  if (serverData.timeSlots && JSON.stringify(state.timeSlots) !== JSON.stringify(serverData.timeSlots)) {
    state.timeSlots = serverData.timeSlots;
    changed = true;
  }
  if (serverData.teachers && JSON.stringify(state.teachers) !== JSON.stringify(serverData.teachers)) {
    state.teachers = serverData.teachers;
    changed = true;
  }

  if (serverData.updatedAt) {
    lastServerSyncAt = serverData.updatedAt;
  }

  if (changed) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    const activeTag = document.activeElement ? document.activeElement.tagName : '';
    if (shouldRender && activeTag !== 'INPUT' && activeTag !== 'SELECT') {
      renderApp();
    }
  }
}

async function pullStateFromServer() {
  try {
    const res = await fetch('/api/sync?t=' + Date.now(), { cache: 'no-store' });
    if (!res.ok) return;
    const serverData = await res.json();

    // إذا كان الهاتف يحتوي على حصص محفوظة محلياً غير موجودة في الخادم بعد، نرفعها تلقائياً
    const localKeys = Object.keys(state.attendanceSessions || {});
    const serverSessions = serverData.attendanceSessions || {};
    const hasUnsyncedLocal = localKeys.some(k => !serverSessions[k]);
    if (hasUnsyncedLocal) {
      await pushStateToServer(false);
      return;
    }

    applyServerSharedData(serverData, true);
  } catch (e) {
    // تجاهل الخطأ عند انقطاع الشبكة
  }
}

function showToast(msg) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2600);
}

// تحويل التاريخ YYYY-MM-DD إلى رقم اليوم في الأسبوع (1=الاثنين .. 6=السبت)
function getDayOfWeek(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  return dt.getDay();
}

function timeToMinutes(t) {
  const [h, m] = (t || '08:00').split(':').map(Number);
  return h * 60 + m;
}

// مزامنة الساعة مع التوقيت المغربي الرسمي ما لم يقم المدير بتفعيل وضع التجربة اليدوي
function syncWithMoroccanClock() {
  if (!state.ui.manualTimeOverride) {
    const m = getMoroccanDateTime();
    state.ui.simDate = m.dateStr;
    state.ui.simTime = m.timeStr;
  }
}

// إيجاد الحصة الموافقة للوقت الحالي بالضبط (تُرجع null إذا كان الوقت خارج أوقات الحصص)
function getExactSlotForTime(timeStr) {
  const mins = timeToMinutes(timeStr);
  for (const s of state.timeSlots) {
    const start = timeToMinutes(s.startTime);
    const end = timeToMinutes(s.endTime);
    if (mins >= start && mins < end) {
      return s;
    }
  }
  return null;
}

// حساب الحصص السابقة التي مرت ولم يُمسك غيابها بعد (الحصص التي تم مسك غيابها لا تظهر هنا)
function getMissedSessionsForTeacher(teacherId) {
  syncWithMoroccanClock();
  const maxDays = Number(state.settings.lateEntryMaxDays);
  const lookback = maxDays === -1 ? 14 : maxDays;
  const [cy, cm, cd] = state.ui.simDate.split('-').map(Number);
  const currentDt = new Date(cy, cm - 1, cd);
  const currentMins = timeToMinutes(state.ui.simTime);

  const missed = [];

  for (let offset = 0; offset <= lookback; offset++) {
    const d = new Date(currentDt);
    d.setDate(d.getDate() - offset);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const dateStr = `${yyyy}-${mm}-${dd}`;
    const dow = d.getDay();
    if (dow === 0) continue; // الأحد عطلة

    const teacherSlots = state.timetable
      .filter(t => t.teacherId === teacherId && t.dayOfWeek === dow)
      .sort((a, b) => b.slotIndex - a.slotIndex);

    teacherSlots.forEach(ts => {
      const timeSlot = state.timeSlots.find(s => s.slotIndex === ts.slotIndex);
      if (!timeSlot) return;

      // في نفس اليوم: لا نعتبر الحصة فائتة إلا إذا انتهى وقتها (أو بدأت ومضى وقتها دون أن تكون هي الحصة الجارية)
      if (offset === 0 && timeToMinutes(timeSlot.endTime) > currentMins) {
        return;
      }

      const sessionId = `${dateStr}_${ts.slotIndex}_${ts.classCode}`;
      // إذا كان الأستاذ قد أمسك فيها الغياب فلا داعي لأن تظهر له
      if (!state.attendanceSessions[sessionId]) {
        missed.push({
          date: dateStr,
          dayOfWeek: dow,
          slotIndex: ts.slotIndex,
          classCode: ts.classCode,
          room: ts.room,
          startTime: timeSlot.startTime,
          endTime: timeSlot.endTime,
          label: timeSlot.label
        });
      }
    });
  }

  return missed;
}

// الحالة المؤقتة للغائبين في الشاشة الحالية للأستاذ
let activeDraftAbsentIds = null;
let activeDraftKey = null;

function getActiveTeacherSessionContext() {
  syncWithMoroccanClock();
  const teacher = state.teachers.find(t => t.teacherId === state.ui.currentTeacherId) || state.teachers[0];
  const ov = state.ui.selectedSessionOverride;

  if (ov) {
    const ovKey = `${ov.date}_${ov.slotIndex}_${ov.classCode}`;
    // إذا كان قد تم مسك غياب هذه الحصة السابقة، نلغي عرضها ونعود للحصة الحالية
    if (state.attendanceSessions[ovKey]) {
      state.ui.selectedSessionOverride = null;
    } else {
      const timeSlot = state.timeSlots.find(s => s.slotIndex === ov.slotIndex) || state.timeSlots[0];
      return {
        teacher,
        date: ov.date,
        dayOfWeek: ov.dayOfWeek,
        slotIndex: ov.slotIndex,
        classCode: ov.classCode,
        room: ov.room || teacher.defaultRoom,
        timeSlot,
        isPastSession: true
      };
    }
  }

  const dow = getDayOfWeek(state.ui.simDate);
  const exactSlot = getExactSlotForTime(state.ui.simTime);

  // نبحث فقط عن الحصة التي يوجد فيها الأستاذ بالضبط في هذه الساعة وفق التوقيت المغربي
  const scheduledNow = exactSlot
    ? state.timetable.find(
        t => t.teacherId === teacher.teacherId && t.dayOfWeek === dow && t.slotIndex === exactSlot.slotIndex
      )
    : null;

  if (!scheduledNow) {
    // البحث عن الحصة القادمة للأستاذ في نفس اليوم (لتذكيره بموعدها فقط دون عرض لائحتها)
    const nowMins = timeToMinutes(state.ui.simTime);
    const upcomingToday = state.timetable
      .filter(t => t.teacherId === teacher.teacherId && t.dayOfWeek === dow)
      .map(t => ({
        ...t,
        timeSlot: state.timeSlots.find(s => s.slotIndex === t.slotIndex)
      }))
      .filter(t => t.timeSlot && timeToMinutes(t.timeSlot.startTime) > nowMins)
      .sort((a, b) => a.slotIndex - b.slotIndex)[0] || null;

    return {
      teacher,
      date: state.ui.simDate,
      dayOfWeek: dow,
      noCurrentSessionNow: true,
      currentSlot: exactSlot,
      upcomingToday
    };
  }

  return {
    teacher,
    date: state.ui.simDate,
    dayOfWeek: scheduledNow.dayOfWeek,
    slotIndex: scheduledNow.slotIndex,
    classCode: scheduledNow.classCode,
    room: scheduledNow.room || teacher.defaultRoom,
    timeSlot: exactSlot,
    isPastSession: false
  };
}

function toggleStudentAbsent(studentId, sessionKey, existingAbsentIds) {
  if (activeDraftKey !== sessionKey || !activeDraftAbsentIds) {
    activeDraftKey = sessionKey;
    activeDraftAbsentIds = new Set(existingAbsentIds);
  }
  if (activeDraftAbsentIds.has(studentId)) {
    activeDraftAbsentIds.delete(studentId);
  } else {
    activeDraftAbsentIds.add(studentId);
  }
  renderApp();
}

function saveTeacherAttendance() {
  const ctx = getActiveTeacherSessionContext();
  if (!ctx || ctx.noCurrentSessionNow) return;

  const realNow = getMoroccanDateTime();
  const sessionKey = `${ctx.date}_${ctx.slotIndex}_${ctx.classCode}`;
  const existing = state.attendanceSessions[sessionKey];
  const classStudents = state.students.filter(s => s.classCode === ctx.classCode);

  const absentSet =
    activeDraftKey === sessionKey && activeDraftAbsentIds
      ? activeDraftAbsentIds
      : new Set(existing ? existing.absentStudentIds : []);

  const absentIds = Array.from(absentSet);
  const totalStudents = classStudents.length;
  const absentCount = absentIds.length;
  const presentCount = totalStudents - absentCount;

  // تحديد ما إذا كان المسك في الوقت أو متأخراً (حصة سابقة في الوراء)
  const isLate = Boolean(
    ctx.isPastSession ||
      ctx.date < state.ui.simDate ||
      (ctx.date === state.ui.simDate &&
        timeToMinutes(state.ui.simTime) > timeToMinutes(ctx.timeSlot.endTime) + 15)
  );

  state.attendanceSessions[sessionKey] = {
    sessionId: sessionKey,
    date: ctx.date,
    dayOfWeek: ctx.dayOfWeek,
    slotIndex: ctx.slotIndex,
    scheduledStart: ctx.timeSlot.startTime,
    scheduledEnd: ctx.timeSlot.endTime,
    classCode: ctx.classCode,
    teacherId: ctx.teacher.teacherId,
    status: existing ? existing.status : isLate ? 'LATE' : 'ON_TIME',
    totalStudents,
    presentCount,
    absentCount,
    absentStudentIds: absentIds,
    submittedAt: existing ? existing.submittedAt : realNow.timeStr,
    lastModifiedAt: existing ? realNow.timeStr : null,
    submittedDate: realNow.dateStr,
    updatedAtTs: Date.now()
  };

  // إذا كانت حصة سابقة من الوراء وتم مسك غيابها الآن، نغلقها فوراً ونعود للحصة الحالية
  if (ctx.isPastSession || state.ui.selectedSessionOverride) {
    state.ui.selectedSessionOverride = null;
    state.ui.showMissedDrawer = false;
  }
  activeDraftKey = null;
  activeDraftAbsentIds = null;

  saveState();
  showToast(
    absentCount === 0
      ? '✅ تم حفظ الغياب بنجاح (الجميع حاضر) وإرساله إلى المدير'
      : `✅ تم حفظ الغياب بنجاح (${absentCount} غائب) وإرساله إلى المدير`
  );
  renderApp();
}

function selectMissedSession(date, dayOfWeek, slotIndex, classCode, room) {
  state.ui.selectedSessionOverride = {
    date,
    dayOfWeek,
    slotIndex,
    classCode,
    room,
    isPastSession: true
  };
  state.ui.showMissedDrawer = false;
  activeDraftKey = null;
  activeDraftAbsentIds = null;
  saveState();
  renderApp();
}

function clearSessionOverride() {
  state.ui.selectedSessionOverride = null;
  activeDraftKey = null;
  activeDraftAbsentIds = null;
  saveState();
  renderApp();
}

// قراءة ملف مسار (ListEleve) متعدد الأوراق واستخراج جميع الأقسام والتلاميذ
function parseMassarListEleveWorkbook(workbook) {
  const importedClasses = [];
  const importedStudents = [];

  workbook.SheetNames.forEach(sheetName => {
    const sheet = workbook.Sheets[sheetName];
    const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
    if (!rows || rows.length < 5) return;

    // البحث عن سطر ترويسة الجدول (ر.ت | الرمز | النسب | الإسم)
    let headerRowIdx = -1;
    let levelName = '';
    let rawClassCode = sheetName;

    for (let r = 0; r < Math.min(rows.length, 20); r++) {
      const rowStr = rows[r].map(c => String(c || '').trim()).join(' ');
      if (rowStr.includes('المستوى') && rows[r][2]) {
        levelName = String(rows[r][2]).trim();
      }
      if (rowStr.includes('القسم') && rows[r][2]) {
        rawClassCode = String(rows[r][2]).trim();
      }
      if (rowStr.includes('النسب') || (rowStr.includes('الرمز') && rowStr.includes('الإسم'))) {
        headerRowIdx = r;
        break;
      }
    }

    if (headerRowIdx === -1) return;

    const classCode = normalizeMassarClassCode(rawClassCode || sheetName);
    const displayName = levelName ? `${levelName} (${rawClassCode})` : `قسم ${classCode}`;

    importedClasses.push({
      classCode,
      massarClassCode: rawClassCode,
      displayName,
      level: classCode.startsWith('TC') ? 'TC' : classCode.startsWith('1BAC') ? '1BAC' : '2BAC'
    });

    let rollCounter = 1;
    for (let r = headerRowIdx + 1; r < rows.length; r++) {
      const row = rows[r];
      if (!row) continue;
      const rollRaw = String(row[0] || '').trim();
      const massarCode = String(row[1] || '').trim();
      const nom = String(row[2] || '').trim();
      const prenom = String(row[3] || '').trim();
      const gender = String(row[4] || '').trim();
      const birthDate = String(row[5] || '').trim();

      if (!nom && !prenom) continue;
      const fullName = `${nom} ${prenom}`.trim();
      const rollNumber = parseInt(rollRaw, 10) || rollCounter;
      rollCounter++;

      importedStudents.push({
        studentId: `${classCode}_${massarCode || rollNumber}`,
        rollNumber,
        massarCode,
        fullName,
        gender,
        birthDate,
        classCode
      });
    }
  });

  return { importedClasses, importedStudents };
}

// استيراد ملف Excel (يتعرف تلقائياً على ملف مسار ListEleve أو ملف الجدول العام لاستعمالات الزمن)
function handleTimetableExcelUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function (e) {
    try {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: 'array' });

      // 1) التحقق أولاً: هل الملف المرفوع هو ملف لوائح التلاميذ والأقسام من مسار (ListEleve)؟
      const massarResult = parseMassarListEleveWorkbook(workbook);
      if (massarResult.importedStudents.length > 0) {
        state.classes = massarResult.importedClasses;
        state.students = massarResult.importedStudents;
        state.ui.selectedStudentClass = state.classes[0]?.classCode || 'TC-SC-F-1';
        saveState();
        showToast(
          `✅ تم استيراد ${massarResult.importedClasses.length} قسماً و ${massarResult.importedStudents.length} تلميذاً من ملف مسار بنجاح!`
        );
        renderApp();
        return;
      }

      // 2) وإلا قراءته كملف الجدول العام لاستعمالات الزمن للمدرسين
      const sheetName = workbook.SheetNames[0];
      const sheet = workbook.Sheets[sheetName];
      const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });

      const importedTeachers = [];
      const importedSlots = [];
      const discoveredClasses = new Map();
      state.classes.forEach(c => discoveredClasses.set(c.classCode, c));

      const usedCodes = new Set([state.settings.principalCode || 'ADMIN888']);
      let teacherSeq = 1;
      rows.forEach(row => {
        const col0 = String(row[0] || '').trim();
        const col1 = String(row[1] || '').trim();
        const col2 = String(row[2] || '').trim();

        if (
          !col0 ||
          col0.includes('الأستاذ') ||
          col0.includes('المديرية') ||
          col0.includes('المؤسسة') ||
          col0.includes('الجدول') ||
          col0.includes('حرر في')
        ) {
          return;
        }

        let hasSessions = false;
        for (let c = 3; c < Math.min(row.length, 52); c++) {
          const cellVal = String(row[c] || '').trim();
          if (cellVal && !/^[1-4]$/.test(cellVal) && !cellVal.includes('صباح') && !cellVal.includes('مساء')) {
            hasSessions = true;
            break;
          }
        }
        if (!hasSessions) return;

        const tId = `T${String(teacherSeq).padStart(2, '0')}`;
        const existingTeacher = state.teachers.find(t => t.excelAlias === col0);
        const loginCode =
          existingTeacher && existingTeacher.loginCode && existingTeacher.loginCode.length === 8
            ? existingTeacher.loginCode
            : generateRandom8CharCode(usedCodes);
        usedCodes.add(loginCode);

        importedTeachers.push({
          teacherId: tId,
          loginCode,
          excelAlias: col0,
          fullName: existingTeacher ? existingTeacher.fullName : col0,
          subject: col1 || 'مادة دراسية',
          defaultRoom: col2 || '-'
        });

        for (let i = 0; i < 48; i++) {
          const rawCell = String(row[3 + i] || '').trim();
          if (!rawCell) continue;
          const lines = rawCell.split(/[\r\n/]+/).map(s => s.trim()).filter(Boolean);
          const classCode = normalizeMassarClassCode(lines[0]);
          const room = (lines[1] || col2 || '').replace(/[()]/g, '');
          const dayOfWeek = Math.floor(i / 8) + 1;
          const slotIndex = (i % 8) + 1;

          importedSlots.push({
            slotId: `${tId}_${dayOfWeek}_${slotIndex}`,
            teacherId: tId,
            classCode,
            dayOfWeek,
            slotIndex,
            room
          });

          if (!discoveredClasses.has(classCode)) {
            discoveredClasses.set(classCode, {
              classCode,
              displayName: `قسم ${classCode}`,
              level: classCode.startsWith('TC') ? 'TC' : classCode.startsWith('1BAC') ? '1BAC' : '2BAC'
            });
          }
        }
        teacherSeq++;
      });

      if (importedTeachers.length > 0) {
        state.teachers = importedTeachers;
        state.timetable = importedSlots;
        state.classes = Array.from(discoveredClasses.values());
        state.ui.currentTeacherId = state.teachers[0].teacherId;
        saveState();
        showToast(`✅ تم استيراد ${importedTeachers.length} أستاذاً مع توليد أرقامهم التعريفية (8 حروف وأرقام) بنجاح!`);
        renderApp();
      } else {
        showToast('⚠️ لم يتم التعرف على بنية الملف المرفوع');
      }
    } catch (err) {
      console.error(err);
      showToast('❌ حدث خطأ أثناء قراءة ملف Excel');
    }
  };
  reader.readAsArrayBuffer(file);
}

// تصدير تقرير الغياب للمدير بصيغة Excel
function exportAttendanceToExcel() {
  if (typeof XLSX === 'undefined') {
    showToast('مكتبة Excel غير محملة');
    return;
  }
  const rows = [
    ['التاريخ', 'الأستاذ', 'المادة', 'القسم', 'توقيت الحصة', 'وقت المسك الفعلي', 'حالة المسك', 'عدد الحاضرين', 'عدد الغائبين', 'أسماء التلاميذ الغائبين']
  ];

  Object.values(state.attendanceSessions).forEach(sess => {
    const teacher = state.teachers.find(t => t.teacherId === sess.teacherId);
    const absentNames = (sess.absentStudentIds || [])
      .map(id => {
        const st = state.students.find(s => s.studentId === id);
        return st ? st.fullName : id;
      })
      .join('، ');

    rows.push([
      sess.date,
      teacher ? teacher.fullName : sess.teacherId,
      teacher ? teacher.subject : '',
      sess.classCode,
      `${sess.scheduledStart} - ${sess.scheduledEnd}`,
      sess.submittedAt,
      sess.status === 'ON_TIME' ? 'تم في الوقت' : 'مسك متأخر',
      sess.presentCount,
      sess.absentCount,
      absentNames || 'الجميع حاضر'
    ]);
  });

  const ws = XLSX.utils.aoa_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'سجل الغياب');
  XLSX.writeFile(wb, `تقرير_مسك_الغياب_${state.ui.simDate}.xlsx`);
  showToast('📥 تم تحميل تقرير الغياب بصيغة Excel');
}

function renderTeacherView() {
  const ctx = getActiveTeacherSessionContext();
  const teacher = ctx.teacher;
  const missedList = getMissedSessionsForTeacher(teacher.teacherId);
  const dow = getDayOfWeek(state.ui.simDate);

  // شريط الحصص السابقة التي في الوراء (فقط الحصص التي مرت ولم يُمسك فيها الغياب بعد)
  const missedSectionHtml = `
    <div class="missed-bar">
      <div style="font-weight:700; color:#92400e; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
        ⏪ حصص سابقة في الوراء (غير ممسوكة): <strong>${missedList.length}</strong>
      </div>
      <div style="display:flex; gap:5px; flex-shrink:0;">
        ${
          state.ui.selectedSessionOverride
            ? `<button class="btn btn-outline" style="padding:3px 8px; font-size:0.74rem;" onclick="clearSessionOverride()">الحصة الحالية ✕</button>`
            : ''
        }
        <button class="missed-bar-btn" onclick="toggleMissedDrawer()">
          ${state.ui.showMissedDrawer ? 'إغلاق ▲' : 'العودة لحصة سابقة ▼'}
        </button>
      </div>
    </div>

    ${
      state.ui.showMissedDrawer
        ? `<div class="card" style="border-color:#fcd34d; background:#fffef7;">
            <div style="font-weight:800; font-size:0.84rem; margin-bottom:4px;">
              ⏪ الحصص السابقة التي مرّ وقتها ولم يُمسك غيابها
            </div>
            <div style="font-size:0.75rem; color:var(--muted); margin-bottom:8px;">
              الحصص التي قمت بمسك غيابها تختفي تلقائياً من هذه اللائحة ولا تظهر لك مجدداً
            </div>
            ${
              missedList.length === 0
                ? `<p style="font-size:0.82rem; color:var(--present-text); font-weight:700;">🎉 جميع حصصك السابقة تم مسك غيابها بالكامل.</p>`
                : `<div style="display:flex; flex-direction:column; gap:6px; max-height:220px; overflow-y:auto;">
                    ${missedList
                      .map(
                        m => `<div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px; background:#fff; border:1px solid var(--border); border-radius:8px; gap:8px;">
                          <div style="min-width:0;">
                            <div style="font-weight:800; font-size:0.84rem; direction:ltr; text-align:right;">${m.classCode}</div>
                            <div style="font-size:0.75rem; color:var(--muted);">${DAYS_AR[m.dayOfWeek]} ${m.date} • ${m.startTime}–${m.endTime}</div>
                          </div>
                          <button class="btn btn-primary" style="padding:4px 10px; font-size:0.76rem;"
                            onclick="selectMissedSession('${m.date}', ${m.dayOfWeek}, ${m.slotIndex}, '${m.classCode}', '${m.room}')">
                            مسك الغياب
                          </button>
                        </div>`
                      )
                      .join('')}
                  </div>`
            }
          </div>`
        : ''
    }
  `;

  // إذا لم تكن للأستاذ حصة جارية في هذه الساعة بالضبط وفق التوقيت المغربي
  if (ctx.noCurrentSessionNow) {
    return `
      <div class="teacher-shell">
        <div class="teacher-banner">
          <div class="teacher-top-row">
            <div style="min-width:0; flex:1;">
              <div style="font-weight:800; font-size:0.95rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                👨‍🏫 ذ. ${teacher.fullName}
              </div>
              <div style="font-size:0.74rem; opacity:0.88;">
                📘 ${teacher.subject} • القاعة: ${teacher.defaultRoom}
              </div>
            </div>
            <span class="badge" style="background:rgba(255,255,255,0.18); color:#fff; font-size:0.74rem;">
              🇲🇦 ${DAYS_AR[dow] || ''} ${state.ui.simDate.slice(5)} • ${state.ui.simTime}
            </span>
          </div>

          <div class="session-pill-box">
            <div style="min-width:0;">
              <div style="font-weight:800; font-size:0.88rem;">
                🕒 لا توجد لديك حصة مبرمجة في هذه الساعة (${state.ui.simTime})
              </div>
              <div style="font-size:0.76rem; opacity:0.92; margin-top:2px;">
                ${
                  ctx.upcomingToday
                    ? `⏭️ حصتك القادمة اليوم: قسم <strong>${ctx.upcomingToday.classCode}</strong> (${ctx.upcomingToday.timeSlot.startTime}–${ctx.upcomingToday.timeSlot.endTime})`
                    : 'لا توجد حصص متبقية لك في هذا اليوم حسب التوقيت الحالي'
                }
              </div>
            </div>
          </div>
        </div>

        ${missedSectionHtml}

        <div class="card" style="text-align:center; padding:22px 14px;">
          <div style="font-size:1.8rem; margin-bottom:6px;">⏰</div>
          <div style="font-weight:800; font-size:0.95rem; color:var(--text); margin-bottom:4px;">
            تظهر هنا تلقائياً فقط الحصة الموافقة للتوقيت المغربي الحالي (${state.ui.simTime})
          </div>
          <div style="font-size:0.8rem; color:var(--muted);">
            إذا كانت لديك حصة سابقة مرّ وقتها ولم تمسك غيابها بعد، يمكنك الضغط على زر <strong>«العودة لحصة سابقة ▼»</strong> أعلاه لإضافة التلاميذ المتغيبين.
          </div>
        </div>
      </div>
    `;
  }

  const sessionKey = `${ctx.date}_${ctx.slotIndex}_${ctx.classCode}`;
  const savedRecord = state.attendanceSessions[sessionKey];
  const classStudents = state.students.filter(s => s.classCode === ctx.classCode);

  const currentAbsentSet =
    activeDraftKey === sessionKey && activeDraftAbsentIds
      ? activeDraftAbsentIds
      : new Set(savedRecord ? savedRecord.absentStudentIds : []);

  const absentCount = currentAbsentSet.size;
  const presentCount = classStudents.length - absentCount;

  return `
    <div class="teacher-shell">
      <!-- بطاقة مدمجة للأستاذ تعرض فقط الحصة الموافقة للتوقيت المغربي الحالي -->
      <div class="teacher-banner">
        <div class="teacher-top-row">
          <div style="min-width:0; flex:1;">
            <div style="font-weight:800; font-size:0.95rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
              👨‍🏫 ذ. ${teacher.fullName}
            </div>
            <div style="font-size:0.74rem; opacity:0.88;">
              📘 ${teacher.subject} • القاعة: ${ctx.room || teacher.defaultRoom}
            </div>
          </div>
          <span class="badge" style="background:rgba(255,255,255,0.18); color:#fff; font-size:0.74rem;">
            🇲🇦 ${DAYS_AR[ctx.dayOfWeek] || ''} ${ctx.date.slice(5)} • ${state.ui.simTime}
          </span>
        </div>

        <div class="session-pill-box">
          <div style="min-width:0;">
            <div style="font-size:0.76rem; opacity:0.92; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
              ${ctx.isPastSession ? `⏪ عودة لحصة سابقة (${DAYS_AR[ctx.dayOfWeek]} ${ctx.date})` : '🟢 الحصة الجارية الآن حسب التوقيت المغربي'}
            </div>
            <div style="font-weight:800; font-size:0.9rem;">
              ⏰ ${ctx.timeSlot.label}: ${ctx.timeSlot.startTime}–${ctx.timeSlot.endTime}
            </div>
          </div>
          <div class="session-class-badge">${ctx.classCode}</div>
        </div>
      </div>

      ${missedSectionHtml}

      <!-- لائحة التلاميذ للحصة الجارية -->
      <div class="card">
        <div class="card-header" style="margin-bottom:8px;">
          <div class="card-title" style="font-size:0.9rem;">
            👥 تلاميذ ${ctx.classCode} (${classStudents.length})
          </div>
          ${
            savedRecord
              ? `<span class="badge ${savedRecord.status === 'ON_TIME' ? 'badge-ontime' : 'badge-late'}">
                  ${savedRecord.status === 'ON_TIME' ? '✅ تم في الوقت' : '🟡 مسك متأخر'} (${savedRecord.submittedAt})
                </span>`
              : `<span class="badge badge-pending">اضغط على الغائب لتحويله للأحمر 🔴</span>`
          }
        </div>

        <div class="student-list">
          ${classStudents
            .map(st => {
              const isAbsent = currentAbsentSet.has(st.studentId);
              return `
                <div class="student-row ${isAbsent ? 'is-absent' : ''}"
                     onclick='toggleStudentAbsent("${st.studentId}", "${sessionKey}", ${JSON.stringify(Array.from(currentAbsentSet))})'>
                  <div class="student-info">
                    <div class="student-num">${String(st.rollNumber).padStart(2, '0')}</div>
                    <div class="student-name">${st.fullName}</div>
                  </div>
                  <div class="status-chip">
                    ${isAbsent ? '🔴 غائب' : '🟢 حاضر'}
                  </div>
                </div>
              `;
            })
            .join('')}
        </div>
      </div>

      <!-- الشريط السفلي الثابت والمدمج للحفظ -->
      <div class="bottom-bar">
        <div class="bottom-bar-inner">
          <div class="counters">
            <div class="counter-pill counter-present" title="الحاضرون">🟢 ${presentCount}</div>
            <div class="counter-pill counter-absent" title="الغائبون">🔴 ${absentCount}</div>
          </div>
          <button class="save-btn ${savedRecord ? 'saved' : ''}" onclick="saveTeacherAttendance()">
            ${
              savedRecord
                ? `✅ تم الحفظ (${savedRecord.submittedAt}) • تحديث`
                : '💾 حفظ وإرسال الغياب'
            }
          </button>
        </div>
      </div>
    </div>
  `;
}

function getAbsentTodayDetailsList() {
  const dow = getDayOfWeek(state.ui.simDate);
  const absentMap = new Map();
  const justifiedMap = state.justifiedAbsences || {};

  // نجمع كل الحصص الممسوكة في تاريخ اليوم المحدد
  Object.values(state.attendanceSessions).forEach(record => {
    if (!record || record.date !== state.ui.simDate) return;
    if (!record.absentStudentIds || record.absentStudentIds.length === 0) return;

    const teacher = state.teachers.find(t => t.teacherId === record.teacherId) || {
      fullName: record.teacherId,
      subject: '-'
    };
    const slot = state.timeSlots.find(s => s.slotIndex === record.slotIndex) || {
      startTime: record.scheduledStart || '08:00',
      endTime: record.scheduledEnd || '09:00',
      label: `حصة ${record.slotIndex}`
    };

    record.absentStudentIds.forEach(rawId => {
      const st = resolveStudentById(rawId, record.classCode);
      const key = st.studentId || rawId;
      if (!absentMap.has(key)) {
        const clsObj = state.classes.find(c => c.classCode === st.classCode);
        absentMap.set(key, {
          student: st,
          classObj: clsObj || { classCode: st.classCode, massarClassCode: st.classCode, displayName: st.classCode },
          sessions: []
        });
      }
      const isJustified = Boolean(justifiedMap[`${record.sessionId}_${rawId}`] || justifiedMap[`${record.sessionId}_${st.studentId}`]);
      absentMap.get(key).sessions.push({
        sessionId: record.sessionId,
        rawStudentId: rawId,
        slotIndex: record.slotIndex,
        timeRange: `${slot.startTime}–${slot.endTime}`,
        slotLabel: slot.label,
        teacherName: teacher.fullName,
        subject: teacher.subject,
        isJustified
      });
    });
  });

  return Array.from(absentMap.values());
}

function toggleAbsentTodayPanel() {
  state.ui.showAbsentTodayPanel = !state.ui.showAbsentTodayPanel;
  saveState();
  renderApp();
}

function openStudentCardFromAbsentList(studentId, classCode) {
  state.ui.principalTab = 'STUDENTS';
  if (classCode && classCode !== '-') {
    state.ui.selectedStudentClass = classCode;
  }
  state.ui.inspectedStudentId = studentId;
  saveState();
  renderApp();
}

function exportAbsentTodayToExcel() {
  if (typeof XLSX === 'undefined') {
    showToast('مكتبة Excel غير متوفرة حالياً');
    return;
  }
  const list = getAbsentTodayDetailsList();
  if (list.length === 0) {
    showToast('⚠️ لا يوجد متعلمون غائبون مسجلون في هذا اليوم');
    return;
  }

  const rows = [
    [
      'الرقم الترتيبي',
      'اسم المتعلم(ة)',
      'رقم مسار',
      'القسم (جدول الحصص)',
      'رمز القسم (مسار)',
      'النوع',
      'تاريخ الازدياد',
      'عدد ساعات الغياب اليوم',
      'تفاصيل الحصص المتغيب فيها اليوم'
    ]
  ];

  list.forEach((item, idx) => {
    const st = item.student;
    const sessText = item.sessions
      .map(s => `${s.timeRange} (${s.subject} - ذ. ${s.teacherName}) [${s.isJustified ? 'مبرر' : 'غير مبرر'}]`)
      .join(' | ');
    rows.push([
      idx + 1,
      st.fullName,
      st.massarCode || '-',
      st.classCode || '-',
      item.classObj?.massarClassCode || st.classCode || '-',
      st.gender || '-',
      st.birthDate || '-',
      item.sessions.length,
      sessText
    ]);
  });

  const ws = XLSX.utils.aoa_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'الغائبون اليوم');
  XLSX.writeFile(wb, `لائحة_الغائبين_اليوم_${state.ui.simDate}.xlsx`);
  showToast('📥 تم تحميل لائحة المتعلمين الغائبين اليوم بصيغة Excel');
}

function renderAbsentTodayPanel(absentTodayList) {
  const dow = getDayOfWeek(state.ui.simDate);
  return `
    <div class="card absent-today-panel">
      <div class="card-header">
        <div>
          <div class="card-title" style="color:var(--absent-text);">
            🔴 لائحة المتعلمين الغائبين اليوم (${DAYS_AR[dow] || ''} ${state.ui.simDate}) — المجموع: ${absentTodayList.length}
          </div>
          <div style="font-size:0.8rem; color:var(--muted);">
            تتضمن اللائحة الاسم الكامل للمتعلم، رقم مسار، القسم، والحصص التي سُجل غيابه فيها اليوم
          </div>
        </div>
        <div style="display:flex; gap:6px; flex-wrap:wrap;">
          ${
            absentTodayList.length > 0
              ? `<button class="btn btn-primary" style="background:var(--absent-text);" onclick="exportAbsentTodayToExcel()">
                  📥 تصدير لائحة الغائبين (Excel)
                </button>`
              : ''
          }
          <button class="btn btn-outline" onclick="toggleAbsentTodayPanel()">إغلاق اللائحة ✕</button>
        </div>
      </div>

      ${
        absentTodayList.length === 0
          ? `<div style="padding:18px; text-align:center; background:#fff; border-radius:10px; border:1px solid var(--border); color:var(--present-text); font-weight:800;">
              🎉 لا يوجد أي متعلم مسجل غائباً في حصص اليوم (${state.ui.simDate}) حتى الآن.
            </div>`
          : `<div class="table-wrap" style="background:#fff; border-radius:10px; border:1px solid var(--border);">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>اسم المتعلم(ة)</th>
                    <th>رقم مسار</th>
                    <th>القسم</th>
                    <th>النوع / تاريخ الازدياد</th>
                    <th>الحصص المتغيب فيها اليوم</th>
                    <th>إجراء</th>
                  </tr>
                </thead>
                <tbody>
                  ${absentTodayList
                    .map((item, idx) => {
                      const st = item.student;
                      const massarCode = st.massarCode || 'غير متوفر';
                      const massarCls = item.classObj?.massarClassCode;
                      return `
                        <tr>
                          <td style="font-weight:800;">${idx + 1}</td>
                          <td style="font-weight:800; font-size:0.9rem; color:var(--text);">
                            ${st.fullName}
                          </td>
                          <td>
                            <div style="display:inline-flex; align-items:center; gap:5px;">
                              <span class="badge" style="background:#0f172a; color:#fff; font-family:monospace; font-size:0.84rem; letter-spacing:1px; padding:4px 10px;">
                                ${massarCode}
                              </span>
                              ${
                                st.massarCode
                                  ? `<button class="btn btn-outline" style="padding:2px 6px; font-size:0.72rem;" onclick="copyText('${st.massarCode}')" title="نسخ رقم مسار">📋</button>`
                                  : ''
                              }
                            </div>
                          </td>
                          <td>
                            <span class="badge" style="background:#e0f2fe; color:#0369a1; font-weight:800; direction:ltr;">
                              ${st.classCode}
                            </span>
                            ${
                              massarCls && massarCls !== st.classCode
                                ? `<div style="font-size:0.72rem; color:var(--muted); margin-top:2px;">مسار: ${massarCls}</div>`
                                : ''
                            }
                          </td>
                          <td style="font-size:0.78rem; color:var(--muted);">
                            ${st.gender || '-'} ${st.birthDate ? `• ${st.birthDate}` : ''}
                          </td>
                          <td>
                            <div style="display:flex; flex-direction:column; gap:4px;">
                              ${item.sessions
                                .map(
                                  s => `<div style="font-size:0.78rem; background:#fef2f2; border:1px solid #fecaca; border-radius:6px; padding:3px 8px; display:flex; align-items:center; justify-content:space-between; gap:6px;">
                                    <span>⏰ <strong>${s.timeRange}</strong> • ${s.subject} (ذ. ${s.teacherName})</span>
                                    <span class="badge ${s.isJustified ? 'badge-ontime' : 'badge-danger'}" style="font-size:0.7rem;">
                                      ${s.isJustified ? '✅ مبرر' : 'غير مبرر'}
                                    </span>
                                  </div>`
                                )
                                .join('')}
                            </div>
                          </td>
                          <td>
                            <button class="btn btn-outline" style="padding:4px 9px; font-size:0.76rem;"
                                    onclick="openStudentCardFromAbsentList('${st.studentId}', '${st.classCode}')">
                              🪪 بطاقة التلميذ
                            </button>
                          </td>
                        </tr>
                      `;
                    })
                    .join('')}
                </tbody>
              </table>
            </div>`
      }
    </div>
  `;
}

function renderPrincipalView() {
  const dow = getDayOfWeek(state.ui.simDate);
  const todayScheduled = state.timetable
    .filter(t => t.dayOfWeek === dow)
    .sort((a, b) => a.slotIndex - b.slotIndex);

  let recordedOnTimeCount = 0;
  let recordedLateCount = 0;
  let pendingCount = 0;

  const sessionRows = todayScheduled.map(sched => {
    const teacher = state.teachers.find(t => t.teacherId === sched.teacherId) || {
      fullName: sched.teacherId,
      subject: '-'
    };
    const slot = state.timeSlots.find(s => s.slotIndex === sched.slotIndex) || {
      startTime: '08:00',
      endTime: '09:00',
      label: `حصة ${sched.slotIndex}`
    };
    const sessionKey = `${state.ui.simDate}_${sched.slotIndex}_${sched.classCode}`;
    const record = state.attendanceSessions[sessionKey];

    if (record) {
      if (record.status === 'ON_TIME') recordedOnTimeCount++;
      else recordedLateCount++;
    } else {
      pendingCount++;
    }

    return {
      sched,
      teacher,
      slot,
      record
    };
  });

  const absentTodayList = getAbsentTodayDetailsList();

  const filteredRows = sessionRows.filter(r => {
    const f = state.ui.principalFilterStatus;
    if (f === 'ALL') return true;
    if (f === 'PENDING') return !r.record;
    if (f === 'ON_TIME') return r.record && r.record.status === 'ON_TIME';
    if (f === 'LATE') return r.record && r.record.status === 'LATE';
    return true;
  });

  return `
    <div>
      <!-- بطاقات الإحصائيات المباشرة للمدير -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">مجموع التلاميذ بالمؤسسة</div>
          <div class="kpi-value" style="color:var(--primary);">${state.students.length}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">عدد الأقسام / الأساتذة</div>
          <div class="kpi-value">${state.classes.length} أقسام • ${state.teachers.length} أستاذاً</div>
        </div>
        <div class="kpi-card kpi-card-clickable ${state.ui.showAbsentTodayPanel ? 'active-card' : ''}"
             onclick="toggleAbsentTodayPanel()"
             title="اضغط لعرض أسماء المتعلمين الغائبين ومعلوماتهم (القسم ورقم مسار)">
          <div class="kpi-label" style="display:flex; justify-content:space-between; align-items:center; gap:4px;">
            <span>التلاميذ المتغيبون اليوم</span>
            <span style="font-size:0.7rem; background:#fee2e2; color:var(--absent-text); padding:1px 7px; border-radius:999px; font-weight:800;">
              ${state.ui.showAbsentTodayPanel ? 'إخفاء ▲' : 'عرض الأسماء ▼'}
            </span>
          </div>
          <div class="kpi-value" style="color:var(--absent-text);">🔴 ${absentTodayList.length}</div>
          <div style="font-size:0.71rem; color:var(--muted); margin-top:2px; font-weight:700;">
            👆 اضغط لعرض الأسماء والقسم ورقم مسار
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">حصص اليوم المسجلة (في الوقت / متأخر)</div>
          <div class="kpi-value" style="color:var(--present-text);">
            ✅ ${recordedOnTimeCount + recordedLateCount} <span style="font-size:0.9rem; color:var(--muted);">من ${todayScheduled.length}</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">حصص اليوم التي لم يتم مسكها</div>
          <div class="kpi-value" style="color:var(--late-text);">⏳ ${pendingCount}</div>
        </div>
      </div>

      ${state.ui.showAbsentTodayPanel ? renderAbsentTodayPanel(absentTodayList) : ''}

      <!-- تبويبات لوحة قيادة المدير -->
      <div class="tabs">
        <button class="tab-btn ${state.ui.principalTab === 'LIVE' ? 'active' : ''}" onclick="setPrincipalTab('LIVE')">
          📊 تتبع مسك الغياب اليومي
        </button>
        <button class="tab-btn ${state.ui.principalTab === 'STUDENTS' ? 'active' : ''}" onclick="setPrincipalTab('STUDENTS')">
          🎓 التتبع الفردي للتلاميذ والإنذارات
        </button>
        <button class="tab-btn ${state.ui.principalTab === 'SCHEDULE' ? 'active' : ''}" onclick="setPrincipalTab('SCHEDULE')">
          ⏰ إعداد مواقيت الحصص المرنة والضوابط
        </button>
        <button class="tab-btn ${state.ui.principalTab === 'EXCEL' ? 'active' : ''}" onclick="setPrincipalTab('EXCEL')">
          📥 استيراد جدول الحصص (Excel) والأساتذة
        </button>
      </div>

      ${state.ui.principalTab === 'LIVE' ? renderPrincipalLiveTab(filteredRows) : ''}
      ${state.ui.principalTab === 'STUDENTS' ? renderPrincipalStudentsTab() : ''}
      ${state.ui.principalTab === 'SCHEDULE' ? renderPrincipalScheduleTab() : ''}
      ${state.ui.principalTab === 'EXCEL' ? renderPrincipalExcelTab() : ''}
    </div>
  `;
}

function renderPrincipalLiveTab(rows) {
  return `
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">📡 المراقبة المباشرة لمسك الغياب — ${DAYS_AR[getDayOfWeek(state.ui.simDate)]} ${state.ui.simDate}</div>
          <div style="font-size:0.84rem; color:var(--muted);">
            يميز النظام بين: الحصص المسجلة في وقتها، المسك المتأخر (بأثر رجعي)، والحصص التي لم تُمسك بعد
          </div>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          <select class="input" onchange="setPrincipalFilter(this.value)">
            <option value="ALL" ${state.ui.principalFilterStatus === 'ALL' ? 'selected' : ''}>جميع الحالات</option>
            <option value="ON_TIME" ${state.ui.principalFilterStatus === 'ON_TIME' ? 'selected' : ''}>🟢 تم في الوقت</option>
            <option value="LATE" ${state.ui.principalFilterStatus === 'LATE' ? 'selected' : ''}>🟡 مسك متأخر</option>
            <option value="PENDING" ${state.ui.principalFilterStatus === 'PENDING' ? 'selected' : ''}>⚪ لم يتم المسك</option>
          </select>
          <button class="btn btn-primary" onclick="exportAttendanceToExcel()">📥 تصدير التقرير (Excel)</button>
        </div>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>الأستاذ</th>
              <th>المادة</th>
              <th>القسم</th>
              <th>توقيت الحصة</th>
              <th>حالة المسك</th>
              <th>وقت التسجيل الفعلي</th>
              <th>حصيلة الغياب والأسماء</th>
            </tr>
          </thead>
          <tbody>
            ${
              rows.length === 0
                ? `<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--muted);">لا توجد حصص مطابقة للفلتر المحدد في هذا اليوم.</td></tr>`
                : rows
                    .map(({ sched, teacher, slot, record }) => {
                      let statusBadge = `<span class="badge badge-pending">⚪ لم يتم المسك</span>`;
                      let timeInfo = '—';
                      let summaryInfo = `<span style="color:var(--muted);">في انتظار مسك الأستاذ</span>`;

                      if (record) {
                        if (record.status === 'ON_TIME') {
                          statusBadge = `<span class="badge badge-ontime">🟢 تم في الوقت</span>`;
                        } else {
                          statusBadge = `<span class="badge badge-late">🟡 مسك متأخر</span>`;
                        }
                        timeInfo = `<strong>${record.submittedAt}</strong> ${
                          record.lastModifiedAt ? `<span style="font-size:0.75rem; color:var(--muted);">(عُدّل ${record.lastModifiedAt})</span>` : ''
                        }`;

                        if (record.absentCount === 0) {
                          summaryInfo = `<span class="badge badge-ontime">🟢 الجميع حاضر (${record.totalStudents}/${record.totalStudents})</span>`;
                        } else {
                          const names = (record.absentStudentIds || [])
                            .map(id => {
                              const st = resolveStudentById(id, sched.classCode);
                              return st ? `${st.fullName} (${st.massarCode || '-'})` : id;
                            })
                            .join('، ');
                          summaryInfo = `
                            <div>
                              <span class="badge badge-danger">🔴 الغائبون: ${record.absentCount}</span>
                              <div style="font-size:0.8rem; color:var(--absent-text); margin-top:4px; font-weight:700;">${names}</div>
                            </div>
                          `;
                        }
                      }

                      return `
                        <tr>
                          <td style="font-weight:800;">${teacher.fullName}</td>
                          <td>${teacher.subject}</td>
                          <td><span class="badge" style="background:#e0f2fe; color:#0369a1;">${sched.classCode}</span></td>
                          <td>${slot.startTime} – ${slot.endTime}</td>
                          <td>${statusBadge}</td>
                          <td>${timeInfo}</td>
                          <td>${summaryInfo}</td>
                        </tr>
                      `;
                    })
                    .join('')
            }
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderPrincipalStudentsTab() {
  const selectedClass = state.ui.selectedStudentClass || state.classes[0]?.classCode;
  const studentsInClass = state.students.filter(s => s.classCode === selectedClass);
  const justifiedMap = state.justifiedAbsences || {};

  // حساب ساعات الغياب (المبررة وغير المبررة) لكل تلميذ عبر جميع السجلات المحفوظة
  const statsByStudent = {};
  Object.values(state.attendanceSessions).forEach(sess => {
    (sess.absentStudentIds || []).forEach(rawId => {
      const resolved = resolveStudentById(rawId, sess.classCode);
      const stId = resolved.studentId || rawId;
      if (!statsByStudent[stId]) {
        statsByStudent[stId] = { total: 0, justified: 0, unjustified: 0, logs: [] };
      }
      const jKey = `${sess.sessionId}_${stId}`;
      const jKeyRaw = `${sess.sessionId}_${rawId}`;
      const isJustified = Boolean(justifiedMap[jKey] || justifiedMap[jKeyRaw]);
      statsByStudent[stId].total += 1;
      if (isJustified) statsByStudent[stId].justified += 1;
      else statsByStudent[stId].unjustified += 1;
      statsByStudent[stId].logs.push({
        sessionId: sess.sessionId,
        date: sess.date,
        time: `${sess.scheduledStart}–${sess.scheduledEnd}`,
        teacherId: sess.teacherId,
        isJustified
      });
    });
  });

  const inspectedStudent = state.ui.inspectedStudentId
    ? resolveStudentById(state.ui.inspectedStudentId, selectedClass)
    : null;
  const inspectedStats = inspectedStudent
    ? statsByStudent[inspectedStudent.studentId] || { total: 0, justified: 0, unjustified: 0, logs: [] }
    : null;

  return `
    ${
      inspectedStudent
        ? `<div class="card" style="border:2px solid var(--primary); background:#f0fdfa;">
            <div class="card-header">
              <div>
                <div class="card-title">🪪 بطاقة تتبع المواظبة الفردية — ${inspectedStudent.fullName}</div>
                <div style="font-size:0.82rem; color:var(--muted); margin-top:4px; display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
                  <span class="badge" style="background:#0f172a; color:#fff; font-family:monospace;">رقم مسار: ${inspectedStudent.massarCode || '-'}</span>
                  <span class="badge" style="background:#e0f2fe; color:#0369a1;">القسم: ${inspectedStudent.classCode}</span>
                  ${inspectedStudent.birthDate ? `<span>🎂 تاريخ الازدياد: ${inspectedStudent.birthDate}</span>` : ''}
                </div>
              </div>
              <button class="btn btn-outline" onclick="inspectStudent(null)">إغلاق البطاقة ✕</button>
            </div>
            <div class="kpi-grid" style="margin-bottom:12px;">
              <div class="kpi-card">
                <div class="kpi-label">مجموع الغيابات</div>
                <div class="kpi-value">${inspectedStats.total} ساعات</div>
              </div>
              <div class="kpi-card">
                <div class="kpi-label">الغيابات المبررة</div>
                <div class="kpi-value" style="color:var(--present-text);">✅ ${inspectedStats.justified} ساعات</div>
              </div>
              <div class="kpi-card">
                <div class="kpi-label">الغيابات غير المبررة</div>
                <div class="kpi-value" style="color:var(--absent-text);">🔴 ${inspectedStats.unjustified} ساعات</div>
              </div>
            </div>
            ${
              inspectedStats.logs.length === 0
                ? `<p style="font-weight:700; color:var(--present-text);">لا يوجد أي غياب مسجل على هذا التلميذ.</p>`
                : `<div class="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>التاريخ</th>
                          <th>الحصة</th>
                          <th>الأستاذ والمادة</th>
                          <th>حالة التبرير</th>
                          <th>إجراء الإدارة</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${inspectedStats.logs
                          .map(lg => {
                            const t = state.teachers.find(x => x.teacherId === lg.teacherId);
                            return `
                              <tr>
                                <td>${lg.date}</td>
                                <td>${lg.time}</td>
                                <td>${t ? `${t.fullName} (${t.subject})` : lg.teacherId}</td>
                                <td>
                                  ${
                                    lg.isJustified
                                      ? `<span class="badge badge-ontime">✅ غياب مبرر</span>`
                                      : `<span class="badge badge-danger">❌ غير مبرر</span>`
                                  }
                                </td>
                                <td>
                                  <button class="btn btn-outline" style="padding:4px 10px; font-size:0.8rem;"
                                          onclick="toggleJustification('${lg.sessionId}', '${inspectedStudent.studentId}')">
                                    ${lg.isJustified ? 'إلغاء التبرير' : '✔️ اعتماد كمبرر'}
                                  </button>
                                </td>
                              </tr>
                            `;
                          })
                          .join('')}
                      </tbody>
                    </table>
                  </div>`
            }
          </div>`
        : ''
    }

    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">🎓 لائحة التلاميذ وتتبع المواظبة والإنذارات</div>
          <div style="font-size:0.84rem; color:var(--muted);">اضغط على «بطاقة التلميذ» لعرض سجل غياباته وتبريرها، أو استورد لائحة القسم من Excel</div>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
          <select class="input" onchange="setSelectedStudentClass(this.value)">
            ${state.classes
              .map(
                c => `<option value="${c.classCode}" ${c.classCode === selectedClass ? 'selected' : ''}>
                  ${c.classCode} — ${c.displayName}
                </option>`
              )
              .join('')}
          </select>
          <label class="btn btn-outline" style="cursor:pointer;">
            📂 استيراد تلاميذ القسم (Excel)
            <input type="file" accept=".xlsx,.xls" style="display:none;" onchange="handleStudentsExcelUpload(event, '${selectedClass}')" />
          </label>
        </div>
      </div>

      <!-- إضافة تلميذ جديد للقسم -->
      <div style="display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap;">
        <input id="new-student-name" type="text" class="input" placeholder="اسم التلميذ الجديد لإضافته إلى ${selectedClass}..." style="flex:1; min-width:220px;" />
        <button class="btn btn-primary" onclick="addStudentToClass('${selectedClass}')">➕ إضافة تلميذ</button>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>الرقم</th>
              <th>اسم التلميذ(ة)</th>
              <th>رقم مسار</th>
              <th>القسم</th>
              <th>مجموع الغياب</th>
              <th>المبرر / غير المبرر</th>
              <th>الحالة والتنبيهات</th>
              <th>البطاقة الفردية</th>
            </tr>
          </thead>
          <tbody>
            ${studentsInClass
              .map(st => {
                const stStats = statsByStudent[st.studentId] || { total: 0, justified: 0, unjustified: 0 };
                let alertBadge = `<span class="badge badge-ontime">🟢 مواظبة عادية</span>`;
                if (stStats.unjustified >= 8) {
                  alertBadge = `<span class="badge badge-danger">🚨 إنذار: ${stStats.unjustified}س غير مبررة</span>`;
                } else if (stStats.unjustified >= 4) {
                  alertBadge = `<span class="badge badge-danger">⚠️ تنبيه: تجاوز 4 ساعات بدون مبرر</span>`;
                } else if (stStats.total >= 1) {
                  alertBadge = `<span class="badge badge-late">مسجل بـ ${stStats.total} ساعة غياب</span>`;
                }
                return `
                  <tr>
                    <td>${String(st.rollNumber).padStart(2, '0')}</td>
                    <td style="font-weight:800;">${st.fullName}</td>
                    <td><span class="badge" style="background:#f1f5f9; color:#0f172a; font-family:monospace; font-weight:800;">${st.massarCode || '-'}</span></td>
                    <td><span class="badge" style="background:#e0f2fe; color:#0369a1; direction:ltr;">${st.classCode}</span></td>
                    <td style="font-weight:800;">${stStats.total} ساعات</td>
                    <td>
                      <span style="color:var(--present-text); font-weight:700;">مبرر: ${stStats.justified}س</span> •
                      <span style="color:var(--absent-text); font-weight:700;">غير مبرر: ${stStats.unjustified}س</span>
                    </td>
                    <td>${alertBadge}</td>
                    <td>
                      <button class="btn btn-outline" style="padding:5px 10px; font-size:0.8rem;"
                              onclick="inspectStudent('${st.studentId}')">
                        🪪 بطاقة التلميذ
                      </button>
                    </td>
                  </tr>
                `;
              })
              .join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderPrincipalScheduleTab() {
  const editedTeacherId = state.ui.editedTimetableTeacherId || state.teachers[0]?.teacherId;
  const teacherSlots = state.timetable
    .filter(t => t.teacherId === editedTeacherId)
    .sort((a, b) => a.dayOfWeek - b.dayOfWeek || a.slotIndex - b.slotIndex);

  return `
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">⚙️ إعدادات مواقيت الحصص المرنة وضوابط المسك المتأخر</div>
          <div style="font-size:0.84rem; color:var(--muted);">
            أي تعديل يجريه المدير هنا ينعكس فوراً لدى جميع الأساتذة دون المساس بجداول الحصص أو السجلات السابقة
          </div>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-outline" onclick="applySchedulePreset('NORMAL')">☀️ التوقيت العادي (08:00)</button>
          <button class="btn btn-outline" onclick="applySchedulePreset('RAMADAN')">🌙 توقيت رمضان المرن (08:40)</button>
        </div>
      </div>

      <div style="margin-bottom:20px; padding:14px; background:#f8fafc; border:1px solid var(--border); border-radius:12px;">
        <div style="font-weight:800; margin-bottom:8px;">⏳ المدة المسموح بها لمسك الغياب المتأخر (للحصص السابقة):</div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          ${[
            { val: 1, label: 'خلال 24 ساعة' },
            { val: 3, label: 'خلال 3 أيام' },
            { val: 7, label: 'خلال 7 أيام (الافتراضي)' },
            { val: -1, label: 'مفتوح دون حد زمني' }
          ]
            .map(
              opt => `
              <button class="btn ${Number(state.settings.lateEntryMaxDays) === opt.val ? 'btn-primary' : 'btn-outline'}"
                      onclick="updateLateEntryMaxDays(${opt.val})">
                ${opt.label}
              </button>
            `
            )
            .join('')}
        </div>
      </div>

      <div class="table-wrap" style="margin-bottom:20px;">
        <table>
          <thead>
            <tr>
              <th>الحصة</th>
              <th>الفترة</th>
              <th>ساعة البداية</th>
              <th>ساعة النهاية</th>
            </tr>
          </thead>
          <tbody>
            ${state.timeSlots
              .map(
                (slot, idx) => `
                <tr>
                  <td style="font-weight:800;">${slot.label}</td>
                  <td>${slot.period === 'MORNING' ? '🌅 الفترة الصباحية' : '🌇 الفترة المسائية'}</td>
                  <td>
                    <input type="time" class="input" value="${slot.startTime}"
                           onchange="updateSlotTime(${idx}, 'startTime', this.value)" />
                  </td>
                  <td>
                    <input type="time" class="input" value="${slot.endTime}"
                           onchange="updateSlotTime(${idx}, 'endTime', this.value)" />
                  </td>
                </tr>
              `
              )
              .join('')}
          </tbody>
        </table>
      </div>

      <!-- تعديل استعمال زمن أستاذ معين من طرف المدير -->
      <div style="border-top:2px solid var(--border); padding-top:16px;">
        <div class="card-header">
          <div>
            <div class="card-title">🗓️ تعديل استعمال زمن أستاذ معين</div>
            <div style="font-size:0.82rem; color:var(--muted);">إضافة أو تعديل أو حذف حصة لأستاذ معين عند حدوث تغيير في الجدول خلال السنة الدراسية</div>
          </div>
          <select class="input" onchange="setEditedTimetableTeacher(this.value)">
            ${state.teachers
              .map(
                t => `<option value="${t.teacherId}" ${t.teacherId === editedTeacherId ? 'selected' : ''}>
                  ${t.fullName} — ${t.subject}
                </option>`
              )
              .join('')}
          </select>
        </div>

        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; background:#f8fafc; padding:12px; border-radius:10px;">
          <select id="new-slot-day" class="input">
            ${[1, 2, 3, 4, 5, 6].map(d => `<option value="${d}">${DAYS_AR[d]}</option>`).join('')}
          </select>
          <select id="new-slot-index" class="input">
            ${state.timeSlots.map(s => `<option value="${s.slotIndex}">${s.label} (${s.startTime}–${s.endTime})</option>`).join('')}
          </select>
          <select id="new-slot-class" class="input">
            ${state.classes.map(c => `<option value="${c.classCode}">${c.classCode}</option>`).join('')}
          </select>
          <input id="new-slot-room" type="text" class="input" placeholder="القاعة (اختياري)" style="width:130px;" />
          <button class="btn btn-primary" onclick="addOrUpdateTeacherSlot('${editedTeacherId}')">➕ حفظ الحصة في جدول الأستاذ</button>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>اليوم</th>
                <th>الحصة والتوقيت</th>
                <th>القسم</th>
                <th>القاعة</th>
                <th>حذف</th>
              </tr>
            </thead>
            <tbody>
              ${teacherSlots
                .map(ts => {
                  const tm = state.timeSlots.find(x => x.slotIndex === ts.slotIndex);
                  return `
                    <tr>
                      <td style="font-weight:700;">${DAYS_AR[ts.dayOfWeek]}</td>
                      <td>${tm ? `${tm.label} (${tm.startTime}–${tm.endTime})` : ts.slotIndex}</td>
                      <td><span class="badge" style="background:#e0f2fe; color:#0369a1;">${ts.classCode}</span></td>
                      <td>${ts.room || '-'}</td>
                      <td>
                        <button class="btn btn-outline" style="padding:3px 10px; color:var(--absent-text);"
                                onclick="deleteTeacherSlot('${ts.slotId}')">🗑️</button>
                      </td>
                    </tr>
                  `;
                })
                .join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

function renderPrincipalExcelTab() {
  return `
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">🔑 إعداد الأرقام التعريفية للأساتذة (8 حروف وأرقام عشوائية)</div>
          <div style="font-size:0.82rem; color:var(--muted);">
            يدخل كل أستاذ إلى التطبيق برقمه التعريفي السري المكون من 8 حروف وأرقام فقط، ولا يظهر له زر المدير نهائياً
          </div>
        </div>
        <div style="display:flex; gap:6px; flex-wrap:wrap;">
          <button class="btn btn-outline" onclick="regenerateAllTeacherCodes()">
            🎲 توليد أرقام عشوائية جديدة للجميع
          </button>
          <button class="btn btn-primary" onclick="exportTeacherCodesToExcel()">
            📥 تحميل لائحة الأرقام التعريفية (Excel)
          </button>
        </div>
      </div>

      <!-- الرمز التعريفي الخاص بالمدير -->
      <div style="background:#f8fafc; border:1px solid var(--border); border-radius:10px; padding:10px 14px; margin-bottom:14px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
        <div style="font-size:0.84rem; font-weight:700;">
          👨‍💼 الرقم التعريفي الخاص بالمدير (للدخول إلى لوحة القيادة من صفحة الدخول):
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
          <input type="text" maxlength="12" class="input" style="font-family:monospace; font-weight:800; letter-spacing:1.5px; width:140px; text-align:center;"
                 value="${state.settings.principalCode || 'ADMIN888'}"
                 onchange="updatePrincipalCode(this.value)" />
          <button class="btn btn-outline" onclick="copyText('${state.settings.principalCode || 'ADMIN888'}')">📋 نسخ</button>
        </div>
      </div>

      <div class="table-wrap" style="margin-bottom:20px;">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>الرقم التعريفي (8 حروف وأرقام)</th>
              <th>إجراء الرمز</th>
              <th>الاسم في ملف Excel</th>
              <th>الاسم الحقيقي للأستاذ (قابل للتعديل)</th>
              <th>المادة الدراسية</th>
              <th>القاعة</th>
            </tr>
          </thead>
          <tbody>
            ${state.teachers
              .map(
                (t, idx) => `
                <tr>
                  <td>${idx + 1}</td>
                  <td>
                    <span class="badge" style="background:#0f172a; color:#fff; font-family:monospace; font-size:0.88rem; letter-spacing:1.5px; padding:5px 12px;">
                      ${t.loginCode}
                    </span>
                  </td>
                  <td>
                    <div style="display:flex; gap:4px;">
                      <button class="btn btn-outline" style="padding:4px 8px; font-size:0.75rem;" onclick="copyText('${t.loginCode}')">📋 نسخ</button>
                      <button class="btn btn-outline" style="padding:4px 8px; font-size:0.75rem;" onclick="regenerateSingleTeacherCode(${idx})">🔄 توليد جديد</button>
                    </div>
                  </td>
                  <td style="color:var(--muted); font-size:0.8rem;">${t.excelAlias}</td>
                  <td>
                    <input type="text" class="input" value="${t.fullName}"
                           onchange="updateTeacherName(${idx}, this.value)" />
                  </td>
                  <td>${t.subject}</td>
                  <td>${t.defaultRoom}</td>
                </tr>
              `
              )
              .join('')}
          </tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">📥 استيراد ملفات المؤسسة (لوائح مسار ListEleve + الجدول العام لاستعمالات الزمن)</div>
          <div style="font-size:0.82rem; color:var(--muted);">
            البيانات المحملة حالياً: <strong>${state.classes.length} قسماً</strong>، <strong>${state.students.length} تلميذاً</strong>، و<strong>${state.teachers.length} أستاذاً</strong>
          </div>
        </div>
      </div>

      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); gap:12px; margin-bottom:16px;">
        <div style="border:2px dashed var(--primary); background:#f0fdfa; padding:14px; border-radius:10px; text-align:center;">
          <div style="font-weight:800; font-size:0.9rem; color:var(--primary-dark); margin-bottom:4px;">
            👨‍🎓 1. استيراد لوائح التلاميذ والأقسام من مسار (ListEleve.xlsx)
          </div>
          <div style="font-size:0.75rem; color:var(--muted); margin-bottom:8px;">
            يقرأ جميع أوراق الأقسام الـ 11 تلقائياً ويربطها بجدول الحصص
          </div>
          <input type="file" accept=".xlsx,.xls" onchange="handleTimetableExcelUpload(event)" class="input" style="width:100%;" />
        </div>

        <div style="border:2px dashed #0284c7; background:#f0f9ff; padding:14px; border-radius:10px; text-align:center;">
          <div style="font-weight:800; font-size:0.9rem; color:#0369a1; margin-bottom:4px;">
            🗓️ 2. استيراد «الجدول العام لاستعمالات الزمن للمدرسين.xlsx»
          </div>
          <div style="font-size:0.75rem; color:var(--muted); margin-bottom:8px;">
            يستخرج الأساتذة والمواد والقاعات والحصص الـ 48 تلقائياً
          </div>
          <input type="file" accept=".xlsx,.xls" onchange="handleTimetableExcelUpload(event)" class="input" style="width:100%;" />
        </div>
      </div>

      <div style="display:flex; flex-wrap:wrap; gap:6px;">
        ${state.classes
          .map(c => {
            const count = state.students.filter(s => s.classCode === c.classCode).length;
            return `<span class="badge" style="background:#e0f2fe; color:#0369a1; padding:5px 10px;">
              ${c.classCode}: <strong>${count} تلميذاً</strong>
            </span>`;
          })
          .join('')}
      </div>
    </div>
  `;
}

// دوال إدارة الأرقام التعريفية العشوائية (8 حروف وأرقام)
function updatePrincipalCode(newVal) {
  const clean = String(newVal || '').trim().toUpperCase();
  if (clean.length < 4) {
    showToast('⚠️ يجب ألا يقل رمز المدير عن 4 حروف وأرقام');
    renderApp();
    return;
  }
  state.settings.principalCode = clean;
  saveState();
  showToast(`✅ تم تحديث الرقم التعريفي للمدير إلى: ${clean}`);
  renderApp();
}

function regenerateSingleTeacherCode(idx) {
  const used = new Set([
    state.settings.principalCode || 'ADMIN888',
    ...state.teachers.map(t => t.loginCode)
  ]);
  const newCode = generateRandom8CharCode(used);
  state.teachers[idx].loginCode = newCode;
  saveState();
  showToast(`🔄 تم توليد رمز جديد للأستاذ: ${newCode}`);
  renderApp();
}

function regenerateAllTeacherCodes() {
  const used = new Set([state.settings.principalCode || 'ADMIN888']);
  state.teachers.forEach(t => {
    t.loginCode = generateRandom8CharCode(used);
  });
  saveState();
  showToast('🎲 تم توليد أرقام تعريفية عشوائية جديدة (8 حروف وأرقام) لجميع الأساتذة');
  renderApp();
}

function copyText(txt) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(txt).then(() => {
      showToast(`📋 تم نسخ الرمز: ${txt}`);
    });
  } else {
    showToast(`الرمز: ${txt}`);
  }
}

function exportTeacherCodesToExcel() {
  if (typeof XLSX === 'undefined') {
    showToast('مكتبة Excel غير محملة');
    return;
  }
  const rows = [
    ['الرقم الترتيبي', 'اسم الأستاذ(ة)', 'المادة الدراسية', 'القاعة', 'الرقم التعريفي للدخول (8 حروف وأرقام)']
  ];
  state.teachers.forEach((t, idx) => {
    rows.push([idx + 1, t.fullName, t.subject, t.defaultRoom, t.loginCode]);
  });
  const ws = XLSX.utils.aoa_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'الأرقام التعريفية للأساتذة');
  XLSX.writeFile(wb, 'لائحة_الأرقام_التعريفية_للأساتذة_أنفك.xlsx');
  showToast('📥 تم تحميل ملف الأرقام التعريفية للأساتذة بصيغة Excel');
}

function toggleMissedDrawer() {
  state.ui.showMissedDrawer = !state.ui.showMissedDrawer;
  saveState();
  renderApp();
}

function setPrincipalTab(tab) {
  state.ui.principalTab = tab;
  saveState();
  renderApp();
}

function setPrincipalFilter(val) {
  state.ui.principalFilterStatus = val;
  saveState();
  renderApp();
}

function setSelectedStudentClass(cls) {
  state.ui.selectedStudentClass = cls;
  saveState();
  renderApp();
}

function updateSimDate(val) {
  state.ui.manualTimeOverride = true;
  state.ui.simDate = val;
  state.ui.selectedSessionOverride = null;
  saveState();
  renderApp();
}

function updateSimTime(val) {
  state.ui.manualTimeOverride = true;
  state.ui.simTime = val;
  state.ui.selectedSessionOverride = null;
  saveState();
  renderApp();
}

function resetToMoroccanLiveTime() {
  state.ui.manualTimeOverride = false;
  syncWithMoroccanClock();
  state.ui.selectedSessionOverride = null;
  saveState();
  showToast('🇲🇦 تم تفعيل التوقيت المغربي الحقيقي المباشر');
  renderApp();
}

function updateLateEntryMaxDays(val) {
  state.settings.lateEntryMaxDays = val;
  saveState();
  showToast('✅ تم تحديث المدة المسموح بها لمسك الغياب المتأخر');
  renderApp();
}

function updateSlotTime(index, field, value) {
  state.timeSlots[index][field] = value;
  saveState();
  showToast('⏰ تم تحديث توقيت الحصة بنجاح');
  renderApp();
}

function applySchedulePreset(mode) {
  if (mode === 'NORMAL') {
    state.timeSlots = JSON.parse(JSON.stringify(DEFAULT_TIME_SLOTS));
  } else if (mode === 'RAMADAN') {
    state.timeSlots = [
      { slotIndex: 1, period: 'MORNING', periodNumber: 1, label: 'صباحية 1', startTime: '08:40', endTime: '09:25' },
      { slotIndex: 2, period: 'MORNING', periodNumber: 2, label: 'صباحية 2', startTime: '09:25', endTime: '10:10' },
      { slotIndex: 3, period: 'MORNING', periodNumber: 3, label: 'صباحية 3', startTime: '10:20', endTime: '11:05' },
      { slotIndex: 4, period: 'MORNING', periodNumber: 4, label: 'صباحية 4', startTime: '11:05', endTime: '11:50' },
      { slotIndex: 5, period: 'AFTERNOON', periodNumber: 1, label: 'مسائية 1', startTime: '12:30', endTime: '13:15' },
      { slotIndex: 6, period: 'AFTERNOON', periodNumber: 2, label: 'مسائية 2', startTime: '13:15', endTime: '14:00' },
      { slotIndex: 7, period: 'AFTERNOON', periodNumber: 3, label: 'مسائية 3', startTime: '14:10', endTime: '14:55' },
      { slotIndex: 8, period: 'AFTERNOON', periodNumber: 4, label: 'مسائية 4', startTime: '14:55', endTime: '15:40' }
    ];
  }
  state.settings.scheduleMode = mode;
  saveState();
  showToast(mode === 'RAMADAN' ? '🌙 تم تفعيل توقيت رمضان المرن' : '☀️ تم تفعيل التوقيت العادي');
  renderApp();
}

function updateTeacherName(idx, val) {
  state.teachers[idx].fullName = val;
  saveState();
  showToast('👨‍🏫 تم حفظ اسم الأستاذ');
}

function inspectStudent(studentId) {
  state.ui.inspectedStudentId = studentId;
  saveState();
  renderApp();
}

function toggleJustification(sessionId, studentId) {
  if (!state.justifiedAbsences) state.justifiedAbsences = {};
  const key = `${sessionId}_${studentId}`;
  state.justifiedAbsences[key] = !state.justifiedAbsences[key];
  saveState();
  showToast(state.justifiedAbsences[key] ? '✅ تم اعتماد الغياب كمبرر' : '⚠️ تم تحويل الغياب إلى غير مبرر');
  renderApp();
}

function addStudentToClass(classCode) {
  const input = document.getElementById('new-student-name');
  const fullName = (input ? input.value : '').trim();
  if (!fullName) {
    showToast('⚠️ يرجى كتابة اسم التلميذ أولاً');
    return;
  }
  const existingInClass = state.students.filter(s => s.classCode === classCode);
  const nextRoll = existingInClass.length + 1;
  state.students.push({
    studentId: `${classCode}_S${Date.now()}`,
    rollNumber: nextRoll,
    fullName,
    classCode
  });
  saveState();
  showToast(`✅ تمت إضافة التلميذ «${fullName}» إلى قسم ${classCode}`);
  renderApp();
}

function handleStudentsExcelUpload(event, targetClassCode) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function (e) {
    try {
      const data = new Uint8Array(e.target.result);
      const wb = XLSX.read(data, { type: 'array' });

      const massarResult = parseMassarListEleveWorkbook(wb);
      if (massarResult.importedStudents.length > 0) {
        state.classes = massarResult.importedClasses;
        state.students = massarResult.importedStudents;
        state.ui.selectedStudentClass = state.classes[0]?.classCode || targetClassCode;
        saveState();
        showToast(
          `✅ تم استيراد جميع الأقسام (${massarResult.importedClasses.length}) وجميع التلاميذ (${massarResult.importedStudents.length}) من ملف مسار بنجاح!`
        );
        renderApp();
        return;
      }

      const sheet = wb.Sheets[wb.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });

      const imported = [];
      rows.forEach(r => {
        const candidates = r.map(c => String(c || '').trim()).filter(Boolean);
        if (candidates.length === 0) return;
        const nameCell = candidates.find(
          c => c.length > 3 && !/^\d+$/.test(c) && !c.includes('الاسم') && !c.includes('التلميذ') && !c.includes('رقم')
        );
        if (nameCell) {
          imported.push({
            studentId: `${targetClassCode}_S${String(imported.length + 1).padStart(2, '0')}_${Date.now()}`,
            rollNumber: imported.length + 1,
            fullName: nameCell,
            classCode: targetClassCode
          });
        }
      });

      if (imported.length > 0) {
        state.students = state.students.filter(s => s.classCode !== targetClassCode).concat(imported);
        saveState();
        showToast(`✅ تم استيراد ${imported.length} تلميذاً لقسم ${targetClassCode}`);
        renderApp();
      } else {
        showToast('⚠️ لم يتم العثور على أسماء تلاميذ في الملف المرفوع');
      }
    } catch (err) {
      console.error(err);
      showToast('❌ تعذر قراءة ملف Excel');
    }
  };
  reader.readAsArrayBuffer(file);
}

function setEditedTimetableTeacher(teacherId) {
  state.ui.editedTimetableTeacherId = teacherId;
  saveState();
  renderApp();
}

function addOrUpdateTeacherSlot(teacherId) {
  const dayOfWeek = Number(document.getElementById('new-slot-day')?.value || 1);
  const slotIndex = Number(document.getElementById('new-slot-index')?.value || 1);
  const classCode = document.getElementById('new-slot-class')?.value || state.classes[0]?.classCode;
  const room = (document.getElementById('new-slot-room')?.value || '').trim();
  const slotId = `${teacherId}_${dayOfWeek}_${slotIndex}`;

  state.timetable = state.timetable.filter(t => t.slotId !== slotId);
  state.timetable.push({
    slotId,
    teacherId,
    classCode,
    dayOfWeek,
    slotIndex,
    room
  });
  saveState();
  showToast('✅ تم حفظ الحصة في جدول الأستاذ بنجاح');
  renderApp();
}

function deleteTeacherSlot(slotId) {
  state.timetable = state.timetable.filter(t => t.slotId !== slotId);
  saveState();
  showToast('🗑️ تم حذف الحصة من جدول الأستاذ');
  renderApp();
}

// دوال تسجيل الدخول والخروج
function logoutSession() {
  state.ui.isLoggedIn = false;
  state.ui.selectedSessionOverride = null;
  activeDraftKey = null;
  activeDraftAbsentIds = null;
  saveState();
  showToast('👋 تم تسجيل الخروج بنجاح');
  renderApp();
}

function loginWithCodeValue(rawCode) {
  const code = String(rawCode || '').trim().toUpperCase();
  if (!code) {
    showToast('⚠️ يرجى إدخال الرقم التعريفي أولاً');
    return;
  }

  const principalCode = (state.settings.principalCode || 'ADMIN888').toUpperCase();
  if (code === principalCode) {
    state.ui.isLoggedIn = true;
    state.ui.role = 'PRINCIPAL';
    saveState();
    showToast('👨‍💼 مرحباً بالسيد المدير في لوحة القيادة');
    renderApp();
    return;
  }

  const foundTeacher = state.teachers.find(t => String(t.loginCode || '').toUpperCase() === code);
  if (foundTeacher) {
    state.ui.isLoggedIn = true;
    state.ui.role = 'TEACHER';
    state.ui.currentTeacherId = foundTeacher.teacherId;
    state.ui.selectedSessionOverride = null;
    activeDraftKey = null;
    activeDraftAbsentIds = null;
    saveState();
    showToast(`👋 مرحباً بك ذ. ${foundTeacher.fullName}`);
    renderApp();
    return;
  }

  showToast('❌ الرقم التعريفي غير صحيح! تأكد من الرمز المكون من 8 حروف وأرقام');
}

function submitLoginPage() {
  const input = document.getElementById('unified-login-input');
  loginWithCodeValue(input ? input.value : '');
}

function toggleDemoCodesOnLogin() {
  state.ui.showDemoCodesOnLogin = !state.ui.showDemoCodesOnLogin;
  saveState();
  renderApp();
}

function renderLoginView() {
  const pCode = state.settings.principalCode || 'ADMIN888';
  return `
    <div class="teacher-shell" style="margin-top:24px;">
      <div class="card" style="text-align:center; padding:26px 18px;">
        <div style="width:64px; height:64px; margin:0 auto 12px; border-radius:16px; background:linear-gradient(135deg, var(--primary), var(--primary-dark)); color:#fff; display:flex; align-items:center; justify-content:center; font-size:2rem; box-shadow:0 6px 16px rgba(15,118,110,0.25);">
          📋
        </div>
        <div style="font-size:1.2rem; font-weight:800; color:var(--text);">تطبيق «مسك الغياب»</div>
        <div style="font-size:0.84rem; font-weight:700; color:var(--primary); margin-bottom:6px;">
          ${state.settings.schoolName}
        </div>
        <div style="font-size:0.8rem; color:var(--muted); margin-bottom:18px;">
          أدخل رقمك التعريفي السري المكون من <strong>8 حروف وأرقام</strong> للدخول مباشرة إلى حسابك
        </div>

        <div style="max-width:300px; margin:0 auto; display:flex; flex-direction:column; gap:10px;">
          <input id="unified-login-input" type="text" maxlength="12" class="input"
                 placeholder="مثال: HWGQ496R"
                 style="text-align:center; font-size:1.15rem; font-weight:800; font-family:monospace; letter-spacing:2px; text-transform:uppercase; padding:11px;"
                 onkeydown="if(event.key==='Enter') submitLoginPage()" />
          <button class="save-btn" style="padding:11px; font-size:0.95rem;" onclick="submitLoginPage()">
            🔐 تسجيل الدخول
          </button>
        </div>

        <div style="margin-top:20px; padding-top:12px; border-top:1px solid var(--border);">
          <button class="btn btn-outline" style="font-size:0.76rem; padding:5px 10px;" onclick="toggleDemoCodesOnLogin()">
            ${state.ui.showDemoCodesOnLogin ? 'إخفاء أرقام التجربة ▲' : '🔍 عرض الأرقام التعريفية للتجربة السريعة ▼'}
          </button>

          ${
            state.ui.showDemoCodesOnLogin
              ? `<div style="margin-top:10px; text-align:right; background:#f8fafc; border:1px solid var(--border); border-radius:10px; padding:10px; max-height:240px; overflow-y:auto;">
                  <div style="margin-bottom:8px; padding-bottom:8px; border-bottom:1px dashed var(--border); display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.8rem; font-weight:800; color:#0f172a;">👨‍💼 حساب السيد المدير:</span>
                    <button class="btn btn-primary" style="padding:3px 10px; font-size:0.76rem; font-family:monospace;" onclick="loginWithCodeValue('${pCode}')">
                      ${pCode} (دخول)
                    </button>
                  </div>
                  <div style="font-size:0.78rem; font-weight:800; color:var(--muted); margin-bottom:6px;">👨‍🏫 حسابات الأساتذة (8 حروف وأرقام):</div>
                  <div style="display:flex; flex-direction:column; gap:5px;">
                    ${state.teachers
                      .map(
                        t => `<div style="display:flex; justify-content:space-between; align-items:center; background:#fff; padding:5px 8px; border-radius:7px; border:1px solid var(--border); font-size:0.76rem;">
                          <span style="font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${t.fullName}</span>
                          <button class="btn btn-outline" style="padding:2px 8px; font-family:monospace; font-weight:800; font-size:0.75rem;" onclick="loginWithCodeValue('${t.loginCode}')">
                            ${t.loginCode}
                          </button>
                        </div>`
                      )
                      .join('')}
                  </div>
                </div>`
              : ''
          }
        </div>
      </div>
    </div>
  `;
}

let deferredInstallPrompt = null;
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  deferredInstallPrompt = e;
  renderApp();
});

async function triggerPwaInstall() {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    renderApp();
  } else {
    showToast('📲 لتثبيت التطبيق على الهاتف: افتح قائمة المتصفح (⋮) واختر «تثبيت التطبيق / الإضافة إلى الشاشة الرئيسية»');
  }
}

function toggleSimDrawer() {
  state.ui.showSimDrawer = !state.ui.showSimDrawer;
  saveState();
  renderApp();
}

function renderApp() {
  const root = document.getElementById('app-root');
  if (!root) return;

  syncWithMoroccanClock();

  if (!state.ui.isLoggedIn) {
    root.innerHTML = `
      <header class="top-bar">
        <div class="top-bar-inner">
          <div class="brand">
            <span>📱 مسك الغياب</span>
            <span class="brand-badge">أنفك</span>
          </div>
          <div class="top-actions">
            <span class="icon-btn" style="cursor:default;">🇲🇦 ${state.ui.simTime}</span>
            <button class="icon-btn" onclick="triggerPwaInstall()">📲 تثبيت التطبيق</button>
          </div>
        </div>
      </header>
      <main class="container">
        ${renderLoginView()}
      </main>
    `;
    return;
  }

  const isTeacher = state.ui.role === 'TEACHER';
  if (isTeacher) {
    // الأستاذ دائماً يعمل بالتوقيت المغربي الحقيقي المباشر
    state.ui.manualTimeOverride = false;
    syncWithMoroccanClock();
  }

  root.innerHTML = `
    <header class="top-bar">
      <div class="top-bar-inner">
        <div class="brand">
          <span>${isTeacher ? '📱 مسك الغياب' : '📊 لوحة قيادة المدير'}</span>
          <span class="brand-badge">أنفك</span>
        </div>

        <div class="top-actions">
          ${
            isTeacher
              ? `<span class="icon-btn" style="cursor:default;" title="التوقيت المغربي المباشر">
                  🇲🇦 ${state.ui.simTime}
                </span>`
              : `<button class="icon-btn" onclick="toggleSimDrawer()" title="التاريخ والتوقيت المغربي">
                  🇲🇦 ${state.ui.simDate.slice(5)} • ${state.ui.simTime}
                </button>`
          }
          <button class="icon-btn" style="background:rgba(239,68,68,0.25); border-color:rgba(239,68,68,0.5);" onclick="logoutSession()" title="تسجيل الخروج">
            🚪 خروج
          </button>
        </div>
      </div>

      ${
        !isTeacher && state.ui.showSimDrawer
          ? `<div class="sim-drawer">
              <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                <span>🇲🇦 تاريخ المعاينة:</span>
                <input type="date" value="${state.ui.simDate}" onchange="updateSimDate(this.value)" />
                <input type="time" value="${state.ui.simTime}" onchange="updateSimTime(this.value)" />
                <button class="btn btn-outline" style="padding:3px 8px; font-size:0.74rem; color:#0f172a;" onclick="resetToMoroccanLiveTime()">
                  🔄 التوقيت المغربي الآني
                </button>
              </div>
              <button class="btn btn-primary" style="padding:4px 10px; font-size:0.76rem; background:#14b8a6;" onclick="triggerPwaInstall()">
                📲 تثبيت على الهاتف
              </button>
            </div>`
          : ''
      }
    </header>

    <main class="container">
      ${isTeacher ? renderTeacherView() : renderPrincipalView()}
    </main>
  `;
}

window.addEventListener('DOMContentLoaded', () => {
  renderApp();
  pullStateFromServer();
  setInterval(pullStateFromServer, 2000);
  setInterval(() => {
    const prevTime = state.ui.simTime;
    syncWithMoroccanClock();
    if (state.ui.simTime !== prevTime) {
      const activeTag = document.activeElement ? document.activeElement.tagName : '';
      if (activeTag !== 'INPUT' && activeTag !== 'SELECT') {
        renderApp();
      }
    }
  }, 15000);
});
