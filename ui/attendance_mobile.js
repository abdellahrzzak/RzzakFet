
function getRecordDisplayTime(rec) {
  if (!rec) return '';
  const s = rec.submittedAt || rec.submittedTime;
  if (s && s !== 'undefined' && s !== 'null') return s;
  const ts = rec.updatedAt || rec.updatedAtTs;
  if (ts) {
    try {
      const d = new Date(Number(ts));
      if (!isNaN(d.getTime())) {
        const hh = String(d.getHours()).padStart(2, '0');
        const mm = String(d.getMinutes()).padStart(2, '0');
        return `${hh}:${mm}`;
      }
    } catch (e) {}
  }
  return '';
}

// Strict Chronological Sorting for Exams
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

    return (a.class_name || a.classCode || '').localeCompare(b.class_name || b.classCode || '');
  });
}
window.sortExamsChronologically = sortExamsChronologically;

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



const TIMETABLE_TO_MASSAR_CLASS = Object.entries(MASSAR_TO_TIMETABLE_CLASS).reduce((acc, [m, t]) => {

  acc[t] = m;

  return acc;

}, {});



function matchClassCode(code1, code2) {

  if (!code1 || !code2) return false;

  const c1 = String(code1).trim().toUpperCase();

  const c2 = String(code2).trim().toUpperCase();

  if (c1 === c2) return true;

  if (MASSAR_TO_TIMETABLE_CLASS[c1] === c2 || TIMETABLE_TO_MASSAR_CLASS[c1] === c2) return true;

  if (MASSAR_TO_TIMETABLE_CLASS[c2] === c1 || TIMETABLE_TO_MASSAR_CLASS[c2] === c1) return true;

  return false;

}



function getStudentsForClass(classCode) {

  if (!classCode) return [];

  return (state.students || []).filter(s => matchClassCode(s.classCode, classCode));

}



function getDateForDayOfWeek(targetDow, baseDateStr) {

  const [y, m, d] = (baseDateStr || state.ui.simDate).split('-').map(Number);

  const dt = new Date(y, m - 1, d);

  const curDow = dt.getDay();

  const curOffset = curDow === 0 ? 6 : (curDow - 1);

  const targetOffset = Number(targetDow) === 0 ? 6 : (Number(targetDow) - 1);

  const diff = targetOffset - curOffset;

  const targetDt = new Date(dt);

  targetDt.setDate(dt.getDate() + diff);

  const yyyy = targetDt.getFullYear();

  const mm = String(targetDt.getMonth() + 1).padStart(2, '0');

  const dd = String(targetDt.getDate()).padStart(2, '0');

  return `${yyyy}-${mm}-${dd}`;

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

function getTimeSlot(slotIndex) {

  const idx = Number(slotIndex);

  const found = (state.timeSlots || []).find(s => Number(s.slotIndex ?? s.index) === idx);

  const st = found ? (found.startTime || found.start) : null;

  const en = found ? (found.endTime || found.end) : null;



  const FALLBACK_SLOTS = {

    1: { startTime: '08:00', endTime: '09:00', label: '08:00 - 09:00' },

    2: { startTime: '09:00', endTime: '10:00', label: '09:00 - 10:00' },

    3: { startTime: '10:00', endTime: '11:00', label: '10:00 - 11:00' },

    4: { startTime: '11:00', endTime: '12:00', label: '11:00 - 12:00' },

    5: { startTime: '14:00', endTime: '15:00', label: '14:00 - 15:00' },

    6: { startTime: '15:00', endTime: '16:00', label: '15:00 - 16:00' },

    7: { startTime: '16:00', endTime: '17:00', label: '16:00 - 17:00' },

    8: { startTime: '17:00', endTime: '18:00', label: '17:00 - 18:00' }

  };

  const def = FALLBACK_SLOTS[idx] || { startTime: '08:00', endTime: '09:00', label: `حصة ${idx}` };



  return {

    slotIndex: idx,

    index: idx,

    period: idx <= 4 ? 'MORNING' : 'AFTERNOON',

    periodNumber: idx <= 4 ? idx : idx - 4,

    startTime: st || def.startTime,

    endTime: en || def.endTime,

    start: st || def.startTime,

    end: en || def.endTime,

    label: (found && found.label) ? found.label : `${st || def.startTime}–${en || def.endTime}`

  };

}



function isSessionInFuture(dateStr, slotIndex) {

  const simDate = state.ui.simDate;

  if (dateStr > simDate) return true; // يوم لاحق في المستقبل

  if (dateStr === simDate) {

    const timeSlot = getTimeSlot(slotIndex);

    const nowMins = timeToMinutes(state.ui.simTime);

    const startMins = timeToMinutes(timeSlot.startTime);

    if (nowMins < startMins) return true; // حصة اليوم لم يحن وقتها بعد

  }

  return false;

}



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

  const schoolData = window.INITIAL_SCHOOL_DATA || window.ANFG_SCHOOL_DATA || {

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

      if ((!parsed.timetable || parsed.timetable.length === 0) && schoolData.timetable && schoolData.timetable.length > 0) {

        parsed.timetable = schoolData.timetable;

      }

      if (schoolData.teachers && schoolData.teachers.length > 0) {

        const sMap = new Map(schoolData.teachers.map(t => [t.teacherId, t]));

        if (!parsed.teachers || parsed.teachers.length === 0) {

          parsed.teachers = schoolData.teachers;

        } else {

          const existingIds = new Set();

          parsed.teachers = parsed.teachers.map(t => {

            existingIds.add(t.teacherId);

            const sT = sMap.get(t.teacherId);

            return sT ? { ...t, loginCode: sT.loginCode || t.loginCode, fullName: sT.fullName || t.fullName, subject: sT.subject || t.subject, defaultRoom: sT.defaultRoom || t.defaultRoom } : t;

          });

          schoolData.teachers.forEach(st => {

            if (!existingIds.has(st.teacherId)) {

              parsed.teachers.push(st);

            }

          });

        }

      }

      if ((!parsed.classes || parsed.classes.length === 0) && schoolData.classes && schoolData.classes.length > 0) {

        parsed.classes = schoolData.classes;

      }

      if ((!parsed.students || parsed.students.length === 0) && schoolData.students && schoolData.students.length > 0) {

        parsed.students = schoolData.students;

      }

      if (!parsed.examsPlanning) {

        parsed.examsPlanning = sortExamsChronologically(schoolData.examsPlanning || []);

      }

      if (!parsed.ministerialCalendar) {

        parsed.ministerialCalendar = schoolData.ministerialCalendar || {};

      }

      if (!parsed.ui.teacherTab) {

        parsed.ui.teacherTab = 'ATTENDANCE';

      }



      if (parsed.ui) {

        parsed.ui.manualTimeOverride = false;

        if (!parsed.entryPasses) parsed.entryPasses = {};

        if (!parsed.dismissalReports) parsed.dismissalReports = {};

        parsed.ui.simDate = moroccanNow.dateStr;

        parsed.ui.simTime = moroccanNow.timeStr;

        parsed.ui.selectedSessionOverride = null;

      }

      if (parsed && parsed.examsPlanning) { parsed.examsPlanning = sortExamsChronologically(parsed.examsPlanning); }
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

    entryPasses: {},

    dismissalReports: {},

    examsPlanning: schoolData.examsPlanning || [],

    ministerialCalendar: schoolData.ministerialCalendar || {},

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



// ==========================================

// Cloud Firestore 24/7 Synchronization

// ==========================================

// Multi-Institution Dynamic Resolution

const _urlParams = new URLSearchParams(window.location.search);

const _schoolParam = _urlParams.get('school') || _urlParams.get('s');

if (_schoolParam) {

  try { localStorage.setItem('rzzak_school_id', _schoolParam.trim()); } catch(_) {}

}

const _savedSchool = (function() {

  try { return localStorage.getItem('rzzak_school_id'); } catch(_) { return null; }

})();



const _bundledSchool = (window.INITIAL_SCHOOL_DATA && (window.INITIAL_SCHOOL_DATA.schoolDocId || (window.INITIAL_SCHOOL_DATA.settings && (window.INITIAL_SCHOOL_DATA.settings.gresa || window.INITIAL_SCHOOL_DATA.settings.schoolId)))) || 'H12657';



const CLOUD_CONFIG = {

  projectId: 'rzzakfet-app',

  apiKey: 'AIzaSyDRAO-ae9rMBFf722p-Jei1UnbtCQ4i0qQ',

  schoolDocId: _schoolParam || _savedSchool || _bundledSchool || 'default_school'

};

const CLOUD_BASE_URL = `https://firestore.googleapis.com/v1/projects/${CLOUD_CONFIG.projectId}/databases/(default)/documents`;



function toFirestoreValue(val) {

  if (val === null || val === undefined) return { nullValue: null };

  if (typeof val === 'boolean') return { booleanValue: val };

  if (typeof val === 'number') {

    if (Number.isInteger(val)) return { integerValue: String(val) };

    return { doubleValue: val };

  }

  if (typeof val === 'string') return { stringValue: val };

  if (Array.isArray(val)) {

    return { arrayValue: { values: val.map(toFirestoreValue) } };

  }

  if (typeof val === 'object') {

    const fields = {};

    for (const [k, v] of Object.entries(val)) {

      if (v !== undefined) fields[k] = toFirestoreValue(v);

    }

    return { mapValue: { fields } };

  }

  return { stringValue: String(val) };

}



function fromFirestoreValue(val) {

  if (!val || typeof val !== 'object') return null;

  if ('stringValue' in val) return val.stringValue;

  if ('integerValue' in val) return parseInt(val.integerValue, 10);

  if ('doubleValue' in val) return parseFloat(val.doubleValue);

  if ('booleanValue' in val) return val.booleanValue;

  if ('nullValue' in val) return null;

  if ('timestampValue' in val) return val.timestampValue;

  if ('arrayValue' in val) {

    return (val.arrayValue.values || []).map(fromFirestoreValue);

  }

  if ('mapValue' in val) {

    const obj = {};

    const fields = val.mapValue.fields || {};

    for (const [k, v] of Object.entries(fields)) {

      obj[k] = fromFirestoreValue(v);

    }

    return obj;

  }

  return null;

}



function parseFirestoreDoc(doc) {

  if (!doc || !doc.fields) return null;

  const obj = {};

  for (const [k, v] of Object.entries(doc.fields)) {

    obj[k] = fromFirestoreValue(v);

  }

  return obj;

}



async function syncSessionToCloud(sessionId, sessionData) {

  if (!sessionId || !sessionData) return;

  try {

    const safeId = sessionId.replace(/\//g, '_');

    const url = `${CLOUD_BASE_URL}/attendance_schools/${CLOUD_CONFIG.schoolDocId}/sessions/${safeId}?key=${CLOUD_CONFIG.apiKey}`;

    const cleanSess = {

      date: String(sessionData.date || ''),

      slotIndex: Number(sessionData.slotIndex || 1),

      classCode: String(sessionData.classCode || ''),

      className: String(sessionData.className || ''),

      teacherId: String(sessionData.teacherId || ''),

      teacherName: String(sessionData.teacherName || ''),

      subject: String(sessionData.subject || ''),

      absentStudentIds: Array.isArray(sessionData.absentStudentIds) ? sessionData.absentStudentIds.map(String) : [],

      lateStudentIds: Array.isArray(sessionData.lateStudentIds) ? sessionData.lateStudentIds.map(String) : [],

      attendanceMap: sessionData.attendanceMap || {},

      sessionId: sessionId,

      status: String(sessionData.status || 'COMPLETED'),

      totalStudents: Number(sessionData.totalStudents || 0),

      presentCount: Number(sessionData.presentCount || 0),

      absentCount: Number(sessionData.absentCount || 0),

      dayOfWeek: sessionData.dayOfWeek !== undefined ? Number(sessionData.dayOfWeek) : 1,

      scheduledStart: String(sessionData.scheduledStart || ''),

      scheduledEnd: String(sessionData.scheduledEnd || ''),

      updatedAt: Date.now()

    };

    const fields = {};

    for (const [k, v] of Object.entries(cleanSess)) {

      fields[k] = toFirestoreValue(v);

    }

    await fetch(url, {

      method: 'PATCH',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify({ fields })

    });

    if (CLOUD_CONFIG.schoolDocId !== 'default_school') {

      try {

        const defUrl = `${CLOUD_BASE_URL}/attendance_schools/default_school/sessions/${safeId}?key=${CLOUD_CONFIG.apiKey}`;

        await fetch(defUrl, {

          method: 'PATCH',

          headers: { 'Content-Type': 'application/json' },

          body: JSON.stringify({ fields })

        });

      } catch(_) {}

    }

  } catch (err) {

    console.warn('[syncSessionToCloud error]:', err);

  }

}



async function syncReportToCloud(reportObj) {

  if (!reportObj || !reportObj.reportId) return;

  try {

    const repId = reportObj.reportId;

    const url = `${CLOUD_BASE_URL}/attendance_schools/${CLOUD_CONFIG.schoolDocId}/reports/${repId}?key=${CLOUD_CONFIG.apiKey}`;

    const cleanRep = {

      reportId: repId,

      studentName: String(reportObj.studentName || ''),

      date: String(reportObj.date || ''),

      reasonType: String(reportObj.reasonType || 'عرقلة السير العادي'),

      status: String(reportObj.status || 'PENDING_ADMIN'),

      customReason: String(reportObj.customReason || ''),

      studentId: String(reportObj.studentId || ''),

      massarCode: String(reportObj.massarCode || ''),

      classCode: String(reportObj.classCode || ''),

      teacherId: String(reportObj.teacherId || ''),

      teacherName: String(reportObj.teacherName || ''),

      subject: String(reportObj.subject || ''),

      time: String(reportObj.time || '08:00'),

      createdAt: reportObj.createdAt || Date.now()

    };

    const fields = {};

    for (const [k, v] of Object.entries(cleanRep)) {

      fields[k] = toFirestoreValue(v);

    }

    await fetch(url, {

      method: 'PATCH',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify({ fields })

    });

    if (CLOUD_CONFIG.schoolDocId !== 'default_school') {

      try {

        const defUrl = `${CLOUD_BASE_URL}/attendance_schools/default_school/reports/${repId}?key=${CLOUD_CONFIG.apiKey}`;

        await fetch(defUrl, {

          method: 'PATCH',

          headers: { 'Content-Type': 'application/json' },

          body: JSON.stringify({ fields })

        });

      } catch(_) {}

    }

  } catch (err) {

    console.warn('[syncReportToCloud error]:', err);

  }

}




async function syncExamToCloud(examObj) {
  if (Date.now() < cloudBackoffUntil) return false;
  if (!examObj || !examObj.id) return false;
  try {
    const cleanExam = {
      id: String(examObj.id),
      academic_year: String(examObj.academic_year || '2026/2027'),
      semester: Number(examObj.semester || 1),
      class_name: String(examObj.class_name || examObj.class_code || ''),
      class_code: String(examObj.class_code || examObj.class_name || ''),
      subject_name: String(examObj.subject_name || examObj.subject || ''),
      subject: String(examObj.subject || examObj.subject_name || ''),
      teacher_name: String(examObj.teacher_name || ''),
      teacher_id: String(examObj.teacher_id || ''),
      exam_number: Number(examObj.exam_number || examObj.exam_num || 1),
      exam_date: String(examObj.exam_date || ''),
      exam_time_str: String(examObj.exam_time_str || ''),
      correction_date: String(examObj.correction_date || ''),
      submission_deadline: String(examObj.submission_deadline || ''),
      room_name: String(examObj.room_name || ''),
      slot_index: Number(examObj.slot_index || 1),
      day_of_week: Number(examObj.day_of_week || 1),
      is_compensatory: Boolean(examObj.is_compensatory),
      status: String(examObj.status || 'SCHEDULED'),
      source: String(examObj.source || 'MOBILE_TEACHER'),
      notes: String(examObj.notes || ''),
      updated_at: String(examObj.updated_at || new Date().toISOString())
    };
    const fields = {};
    for (const [k, v] of Object.entries(cleanExam)) {
      fields[k] = toFirestoreValue(v);
    }
    const examId = cleanExam.id;
    const url = `${CLOUD_BASE_URL}/attendance_schools/${CLOUD_CONFIG.schoolDocId}/exams/${encodeURIComponent(examId)}?key=${CLOUD_CONFIG.apiKey}`;
    const res = await fetch(url, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields })
    });
    if (res.status === 429) {
      cloudBackoffUntil = Date.now() + 60000;
      return false;
    }
    if (CLOUD_CONFIG.schoolDocId !== 'default_school') {
      try {
        const defUrl = `${CLOUD_BASE_URL}/attendance_schools/default_school/exams/${encodeURIComponent(examId)}?key=${CLOUD_CONFIG.apiKey}`;
        fetch(defUrl, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fields })
        }).catch(() => {});
      } catch (_) {}
    }
    return res.ok;
  } catch (err) {
    console.warn('[syncExamToCloud error]:', err);
    return false;
  }
}

async function deleteExamFromCloud(examId) {
  if (!examId) return;
  try {
    const url = `${CLOUD_BASE_URL}/attendance_schools/${CLOUD_CONFIG.schoolDocId}/exams/${encodeURIComponent(examId)}?key=${CLOUD_CONFIG.apiKey}`;
    fetch(url, { method: 'DELETE' }).catch(() => {});
    if (CLOUD_CONFIG.schoolDocId !== 'default_school') {
      const defUrl = `${CLOUD_BASE_URL}/attendance_schools/default_school/exams/${encodeURIComponent(examId)}?key=${CLOUD_CONFIG.apiKey}`;
      fetch(defUrl, { method: 'DELETE' }).catch(() => {});
    }
  } catch (_) {}
}

async function syncAllPendingToCloud() {

  const sessions = state.attendanceSessions || {};

  for (const [sId, sess] of Object.entries(sessions)) {

    if (!sess._cloudSynced) {

      await syncSessionToCloud(sId, sess);

      sess._cloudSynced = true;

    }

  }

  const reports = state.dismissalReports || {};
  for (const [rId, rep] of Object.entries(reports)) {
    if (!rep._cloudSynced) {
      await syncReportToCloud(rep);
      rep._cloudSynced = true;
    }
  }

  const exams = state.examsPlanning || [];
  for (const ex of exams) {
    if (!ex._cloudSynced) {
      const ok = await syncExamToCloud(ex);
      if (ok) ex._cloudSynced = true;
    }
  }

}



let cloudBackoffUntil = 0;



async function pullFromCloudFirestore() {

  if (Date.now() < cloudBackoffUntil) return;

  try {

    // 1. School data

    const schoolRes = await fetch(`${CLOUD_BASE_URL}/attendance_schools/${CLOUD_CONFIG.schoolDocId}?key=${CLOUD_CONFIG.apiKey}`, { cache: 'no-store' });

    if (schoolRes.status === 429) {

      cloudBackoffUntil = Date.now() + 60000;

      return;

    }

    if (schoolRes.ok) {

      const doc = await schoolRes.json();

      const schoolData = parseFirestoreDoc(doc);

      if (schoolData) {

        const isResetSignal = (schoolData.resetToken && (!state.resetToken || schoolData.resetToken > state.resetToken)) ||

                              (Array.isArray(schoolData.students) && schoolData.students.length === 0 &&

                               Array.isArray(schoolData.timetable) && schoolData.timetable.length === 0);

        if (isResetSignal) {

          applyServerSharedData(schoolData, true);

          return;

        }

        applyServerSharedData(schoolData, true);

      }

    }



    // 2. Sessions

    const sessRes = await fetch(`${CLOUD_BASE_URL}/attendance_schools/${CLOUD_CONFIG.schoolDocId}/sessions?key=${CLOUD_CONFIG.apiKey}&pageSize=300`, { cache: 'no-store' });

    if (sessRes.status === 429) {

      cloudBackoffUntil = Date.now() + 60000;

      return;

    }

    if (sessRes.ok) {

      const sessJson = await sessRes.json();

      const docs = sessJson.documents || [];

      if (!state.attendanceSessions) state.attendanceSessions = {};

      let hasNew = false;

      docs.forEach(d => {

        const parsed = parseFirestoreDoc(d);

        if (parsed && parsed.sessionId) {

          const cur = state.attendanceSessions[parsed.sessionId];

          if (!cur || (parsed.updatedAt && parsed.updatedAt >= (cur.updatedAt || 0))) {

            parsed._cloudSynced = true;

            state.attendanceSessions[parsed.sessionId] = parsed;

            hasNew = true;

          }

        }

      });

      if (hasNew) {

        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));

        renderApp();

      }

    }



    // 3. Reports

    const repRes = await fetch(`${CLOUD_BASE_URL}/attendance_schools/${CLOUD_CONFIG.schoolDocId}/reports?key=${CLOUD_CONFIG.apiKey}&pageSize=300`, { cache: 'no-store' });

    if (repRes.status === 429) {

      cloudBackoffUntil = Date.now() + 60000;

      return;

    }

    if (repRes.ok) {

      const repJson = await repRes.json();

      const docs = repJson.documents || [];

      if (!state.dismissalReports) state.dismissalReports = {};

      let hasNewRep = false;

      docs.forEach(d => {

        const parsed = parseFirestoreDoc(d);

        if (parsed && parsed.reportId) {

          const cur = state.dismissalReports[parsed.reportId];

          if (!cur || JSON.stringify(cur) !== JSON.stringify(parsed)) {

            parsed._cloudSynced = true;

            state.dismissalReports[parsed.reportId] = parsed;

            hasNewRep = true;

          }

        }

      });

      if (hasNewRep) {

        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));

        renderApp();

      }

    }

    // 4. Exams Planning
    const examRes = await fetch(`${CLOUD_BASE_URL}/attendance_schools/${CLOUD_CONFIG.schoolDocId}/exams?key=${CLOUD_CONFIG.apiKey}&pageSize=300`, { cache: 'no-store' });
    if (examRes.ok) {
      const examJson = await examRes.json();
      const docs = examJson.documents || [];
      if (!state.examsPlanning) state.examsPlanning = [];
      let hasNewExam = false;
      docs.forEach(d => {
        const parsed = parseFirestoreDoc(d);
        if (parsed && (parsed.id || parsed.class_name)) {
          const exId = parsed.id || d.name.split('/').pop();
          parsed.id = exId;
          parsed._cloudSynced = true;
          const curIdx = state.examsPlanning.findIndex(e => e.id === exId);
          if (curIdx === -1) {
            state.examsPlanning.push(parsed);
            hasNewExam = true;
          } else {
            const cur = state.examsPlanning[curIdx];
            if (JSON.stringify(cur) !== JSON.stringify(parsed)) {
              state.examsPlanning[curIdx] = parsed;
              hasNewExam = true;
            }
          }
        }
      });
      if (hasNewExam) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        renderApp();
      }
    }


  } catch (err) {

    // Silent on offline/network failure

  }

}



function saveState(isConfigUpdate = false) {

  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));

  pushStateToServer(isConfigUpdate);

}



async function pushStateToServer(isConfigUpdate = false) {

  // Push to local server if available

  try {

    const payload = {

      attendanceSessions: state.attendanceSessions || {},

      justifiedAbsences: state.justifiedAbsences || {},

      dismissalReports: state.dismissalReports || {},

      examsPlanning: state.examsPlanning || [],

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

    // Local server offline; continue to Cloud Firestore

  }



  // Push directly to 24/7 Cloud Firestore

  try {

    await syncAllPendingToCloud();

  } catch (e) {

    // Offline queue

  }

}



function applyServerSharedData(serverData, shouldRender = true) {

  if (!serverData || typeof serverData !== 'object') return;

  let changed = false;



  const isResetSignal = (serverData.resetToken && (!state.resetToken || serverData.resetToken > state.resetToken)) ||

                        (serverData.isReset === true) ||

                        (Array.isArray(serverData.students) && serverData.students.length === 0 &&

                         Array.isArray(serverData.timetable) && serverData.timetable.length === 0 &&

                         (!serverData.attendanceSessions || Object.keys(serverData.attendanceSessions).length === 0));



  if (isResetSignal) {

    console.log('[RESET] Factory reset signal applied to mobile database.');

    state.resetToken = serverData.resetToken || Date.now();

    state.students = Array.isArray(serverData.students) ? serverData.students : [];

    state.classes = Array.isArray(serverData.classes) ? serverData.classes : [];

    state.teachers = Array.isArray(serverData.teachers) ? serverData.teachers : [];

    state.timetable = Array.isArray(serverData.timetable) ? serverData.timetable : [];

    state.attendanceSessions = {};

    state.dismissalReports = {};

    state.entryPasses = {};

    state.justifiedAbsences = {};

    if (serverData.settings) state.settings = serverData.settings;

    if (serverData.timeSlots) state.timeSlots = serverData.timeSlots;

    if (serverData.updatedAt) lastServerSyncAt = serverData.updatedAt;

    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));

    if (shouldRender) renderApp();

    return true;

  }



  if (serverData.entryPasses && typeof serverData.entryPasses === 'object') {

    if (!state.entryPasses) state.entryPasses = {};

    for (const [k, p] of Object.entries(serverData.entryPasses)) {

      const curP = state.entryPasses[k];

      if (!curP || JSON.stringify(curP) !== JSON.stringify(p)) {

        state.entryPasses[k] = p;

        changed = true;

      }

    }

  }



  if (serverData.dismissalReports && typeof serverData.dismissalReports === 'object') {

    if (!state.dismissalReports) state.dismissalReports = {};

    for (const [k, rep] of Object.entries(serverData.dismissalReports)) {

      const curRep = state.dismissalReports[k];

      if (!curRep || JSON.stringify(curRep) !== JSON.stringify(rep)) {

        state.dismissalReports[k] = rep;

        changed = true;

      }

    }

  }



  if (Array.isArray(serverData.examsPlanning)) {

    state.examsPlanning = serverData.examsPlanning;

    changed = true;

  }

  if (serverData.ministerialCalendar && typeof serverData.ministerialCalendar === 'object') {

    state.ministerialCalendar = serverData.ministerialCalendar;

    changed = true;

  }



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

  if (Array.isArray(serverData.classes) && serverData.classes.length > 0 && (!state.classes || state.classes.length === 0 || JSON.stringify(state.classes) !== JSON.stringify(serverData.classes))) {

    state.classes = serverData.classes;

    changed = true;

  }

  if (Array.isArray(serverData.students) && serverData.students.length > 0 && (!state.students || state.students.length === 0 || JSON.stringify(state.students) !== JSON.stringify(serverData.students))) {

    state.students = serverData.students;

    changed = true;

  }

  if (Array.isArray(serverData.timetable) && serverData.timetable.length > 0 && (!state.timetable || state.timetable.length === 0 || JSON.stringify(state.timetable) !== JSON.stringify(serverData.timetable))) {

    state.timetable = serverData.timetable;

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

  let pulledFromLocal = false;

  // Sync fresh exams planning data if available

  fetch('/api/exams_planning/data?t=' + Date.now(), { cache: 'no-store' })

    .then(r => r.ok ? r.json() : null)

    .then(ex => {

      if (ex && Array.isArray(ex.exams)) {

        state.examsPlanning = ex.exams;

        if (ex.settings && ex.settings.ministerial_calendar) {

          state.ministerialCalendar = ex.settings.ministerial_calendar;

        }

        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));

      }

    }).catch(() => {});

  try {

    const res = await fetch('/api/sync?t=' + Date.now(), { cache: 'no-store' });

    if (res.ok) {

      const serverData = await res.json();

      const isResetSignal = (serverData.resetToken && (!state.resetToken || serverData.resetToken > state.resetToken)) ||

                            (serverData.isReset === true) ||

                            (Array.isArray(serverData.students) && serverData.students.length === 0 &&

                             Array.isArray(serverData.timetable) && serverData.timetable.length === 0 &&

                             (!serverData.attendanceSessions || Object.keys(serverData.attendanceSessions).length === 0));

      if (isResetSignal) {

        applyServerSharedData(serverData, true);

        return true;

      }

      const localKeys = Object.keys(state.attendanceSessions || {});

      const serverSessions = serverData.attendanceSessions || {};

      const hasUnsyncedLocal = localKeys.some(k => !serverSessions[k]);

      if (hasUnsyncedLocal) {

        await pushStateToServer(false);

      }

      applyServerSharedData(serverData, true);

      pulledFromLocal = true;

    }

  } catch (e) {

    pulledFromLocal = false;

  }



  // If local server is not accessible or if running on Firebase Hosting, pull directly from Cloud Firestore

  if (!pulledFromLocal || location.hostname.includes('web.app') || location.hostname.includes('firebaseapp.com')) {

    await pullFromCloudFirestore();

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

  for (let idx = 1; idx <= 8; idx++) {

    const s = getTimeSlot(idx);

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
  const [cy, cm, cd] = state.ui.simDate.split('-').map(Number);
  const currentDt = new Date(cy, cm - 1, cd);
  const nowMs = new Date(state.ui.simDate + "T" + state.ui.simTime + ":00").getTime();
  const missed = [];

  // فحص آخر يومين فقط لتغطية الـ 24 ساعة بدقة واستبعاد ما زاد عن 24 ساعة نهائياً
  for (let offset = 0; offset <= 2; offset++) {
    const d = new Date(currentDt);
    d.setDate(d.getDate() - offset);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const dateStr = [yyyy, mm, dd].join('-');
    const dow = d.getDay();
    if (dow === 0) continue; // الأحد عطلة

    const teacherSlots = state.timetable
      .filter(t => t.teacherId === teacherId && t.dayOfWeek === dow)
      .sort((a, b) => b.slotIndex - a.slotIndex);

    teacherSlots.forEach(ts => {
      const timeSlot = getTimeSlot(ts.slotIndex);
      if (!timeSlot || !timeSlot.endTime) return;

      const sessionEndMs = new Date(dateStr + 'T' + timeSlot.endTime + ':00').getTime();
      const diffHours = (nowMs - sessionEndMs) / (1000 * 3600);

      // 1. إذا كانت الحصة في المستقبل اليوم: لا تعتبر فائتة
      if (diffHours < 0) return;

      // 2. إذا مر عليها أكثر من 24 ساعة: لا تظهر للأستاذ مطلقاً حسب رغبة المؤسسة
      if (diffHours > 24) return;

      const sessionId = dateStr + '_' + ts.slotIndex + '_' + ts.classCode;
      if (!state.attendanceSessions[sessionId]) {
        missed.push({
          date: dateStr,
          dayOfWeek: dow,
          slotIndex: ts.slotIndex,
          classCode: ts.classCode,
          room: ts.room,
          startTime: timeSlot.startTime,
          endTime: timeSlot.endTime,
          label: timeSlot.label,
          diffHours: Math.round(diffHours)
        });
      }
    });
  }

  return missed;
}



// الحالة المؤقتة للغائبين والمتأخرين في الشاشة الحالية للأستاذ

let activeDraftAbsentIds = null;

let activeDraftLateIds = null;

let activeDraftKey = null;



function selectTeacherSession(date, dayOfWeek, slotIndex, classCode, room) {

  // منع مسك الغياب للحصص القادمة التي لم يحن وقتها بعد

  if (isSessionInFuture(date || state.ui.simDate, slotIndex)) {

    showToast('⚠️ لا يمكن مسك الغياب إلا في الساعة الفعلية التي يتواجد بها الأستاذ بالقسم!');

    return;

  }



  state.ui.selectedSessionOverride = {

    date: date || state.ui.simDate,

    dayOfWeek: Number(dayOfWeek),

    slotIndex: Number(slotIndex),

    classCode: String(classCode),

    room: room || ''

  };

  activeDraftKey = null;

  activeDraftAbsentIds = null;

  activeDraftLateIds = null;

  state.ui.showMissedDrawer = false;

  saveState();

  renderApp();

  setTimeout(() => {

    const el = document.getElementById('teacher-active-session-card');

    if (el) el.scrollIntoView({ behavior: 'smooth' });

  }, 80);

}



function clearTeacherSessionOverride() {

  state.ui.selectedSessionOverride = null;

  activeDraftKey = null;

  activeDraftAbsentIds = null;

  activeDraftLateIds = null;

  saveState();

  renderApp();

}



function toggleTeacherWeeklyTimetable() {

  state.ui.showWeeklyTimetable = !state.ui.showWeeklyTimetable;

  saveState();

  renderApp();

}



function getActiveTeacherSessionContext() {

  syncWithMoroccanClock();

  const teacher = (state.teachers || []).find(t => t.teacherId === state.ui.currentTeacherId) || (state.teachers && state.teachers[0]) || { teacherId: 'T01', fullName: 'أستاذ', subject: '', defaultRoom: '' };

  const ov = state.ui.selectedSessionOverride;



  if (ov) {

    const timeSlot = getTimeSlot(ov.slotIndex);

    return {

      teacher,

      date: ov.date,

      dayOfWeek: Number(ov.dayOfWeek),

      slotIndex: Number(ov.slotIndex),

      classCode: ov.classCode,

      room: ov.room || teacher.defaultRoom,

      timeSlot,

      isOverride: true,

      isPastSession: Boolean(ov.isPastSession)

    };

  }



  const dow = getDayOfWeek(state.ui.simDate);

  const exactSlot = getExactSlotForTime(state.ui.simTime);



  const scheduledNow = exactSlot

    ? (state.timetable || []).find(

        t => t.teacherId === teacher.teacherId && Number(t.dayOfWeek) === Number(dow) && Number(t.slotIndex) === Number(exactSlot.slotIndex)

      )

    : null;



  if (!scheduledNow) {

    const nowMins = timeToMinutes(state.ui.simTime);

    const upcomingToday = (state.timetable || [])

      .filter(t => t.teacherId === teacher.teacherId && Number(t.dayOfWeek) === Number(dow))

      .map(t => ({

        ...t,

        timeSlot: getTimeSlot(t.slotIndex)

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

    dayOfWeek: Number(scheduledNow.dayOfWeek),

    slotIndex: Number(scheduledNow.slotIndex),

    classCode: scheduledNow.classCode,

    room: scheduledNow.room || teacher.defaultRoom,

    timeSlot: exactSlot,

    isCurrentNow: true

  };

}



function toggleStudentAbsent(studentId, sessionKey, existingAbsentIds, existingLateIds) {

  const existing = state.attendanceSessions[sessionKey];

  if (activeDraftKey !== sessionKey || !activeDraftAbsentIds || !activeDraftLateIds) {

    activeDraftKey = sessionKey;

    activeDraftAbsentIds = new Set(existingAbsentIds || (existing ? existing.absentStudentIds : []));

    activeDraftLateIds = new Set(existingLateIds || (existing ? (existing.lateStudentIds || []) : []));

  }

  if (activeDraftAbsentIds.has(studentId)) {

    activeDraftAbsentIds.delete(studentId);

  } else {

    activeDraftAbsentIds.add(studentId);

    activeDraftLateIds.delete(studentId);

  }

  renderApp();

}



function toggleStudentLate(studentId, sessionKey, existingAbsentIds, existingLateIds) {

  const existing = state.attendanceSessions[sessionKey];

  if (activeDraftKey !== sessionKey || !activeDraftAbsentIds || !activeDraftLateIds) {

    activeDraftKey = sessionKey;

    activeDraftAbsentIds = new Set(existingAbsentIds || (existing ? existing.absentStudentIds : []));

    activeDraftLateIds = new Set(existingLateIds || (existing ? (existing.lateStudentIds || []) : []));

  }

  if (activeDraftLateIds.has(studentId)) {

    activeDraftLateIds.delete(studentId);

  } else {

    activeDraftLateIds.add(studentId);

    activeDraftAbsentIds.delete(studentId);

  }

  renderApp();

}



function saveTeacherAttendance() {

  const ctx = getActiveTeacherSessionContext();

  if (!ctx || ctx.noCurrentSessionNow) return;



  const realNow = getMoroccanDateTime();

  const sessionKey = `${ctx.date}_${ctx.slotIndex}_${ctx.classCode}`;

  const existing = state.attendanceSessions[sessionKey];

  const classStudents = getStudentsForClass(ctx.classCode);



  const absentSet =

    activeDraftKey === sessionKey && activeDraftAbsentIds

      ? activeDraftAbsentIds

      : new Set(existing ? existing.absentStudentIds : []);



  const lateSet =

    activeDraftKey === sessionKey && activeDraftLateIds

      ? activeDraftLateIds

      : new Set(existing ? (existing.lateStudentIds || []) : []);



  const absentIds = Array.from(absentSet);

  const lateIds = Array.from(lateSet);

  const totalStudents = classStudents.length;

  const absentCount = absentIds.length;

  const lateCount = lateIds.length;

  const presentCount = Math.max(0, totalStudents - absentCount);



  // Generate per-student attendanceMap: 'A' (Absent), 'L' (Late), 'P' (Present)

  const attMap = {};

  classStudents.forEach(s => {

    if (absentSet.has(s.studentId)) attMap[s.studentId] = 'A';

    else if (lateSet.has(s.studentId)) attMap[s.studentId] = 'L';

    else attMap[s.studentId] = 'P';

  });



  // تحديد ما إذا كان المسك في الوقت أو متأخراً (حصة سابقة في الوراء)

  const isLateSession = Boolean(

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

    className: ctx.classCode,

    teacherId: ctx.teacher.teacherId,

    teacherName: ctx.teacher.fullName || '',

    subject: ctx.teacher.subject || '',

    status: existing ? existing.status : isLateSession ? 'LATE' : 'ON_TIME',

    totalStudents,

    presentCount,

    absentCount,

    lateCount,

    absentStudentIds: absentIds,

    lateStudentIds: lateIds,

    attendanceMap: attMap,

    submittedAt: (existing && existing.submittedAt) ? existing.submittedAt : (realNow.timeStr || new Date().toLocaleTimeString('ar-MA', {hour:'2-digit', minute:'2-digit'})),

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

  activeDraftLateIds = null;



  saveState();

  let msg = `✅ تم حفظ الغياب بنجاح وإرساله للإدارة`;

  if (absentCount === 0 && lateCount === 0) {

    msg = `✅ تم حفظ الغياب بنجاح (الجميع حاضر 🟢)`;

  } else {

    msg = `✅ تم حفظ الحصة (${absentCount} غائب 🔴 • ${lateCount} متأخر 🟡)`;

  }

  showToast(msg);

  renderApp();

}



function selectMissedSession(date, dayOfWeek, slotIndex, classCode, room) {
  const timeSlot = getTimeSlot(slotIndex);
  if (timeSlot && timeSlot.endTime) {
    const nowMs = new Date(state.ui.simDate + "T" + state.ui.simTime + ":00").getTime();
    const sessionEndMs = new Date(date + 'T' + timeSlot.endTime + ':00').getTime();
    const diffHours = (nowMs - sessionEndMs) / (1000 * 3600);
    if (diffHours > 24) {
      showToast('⚠️ لقد مر أكثر من 24 ساعة على موعد هذه الحصة، ولم يعد بالإمكان مسكها من طرف الأستاذ.');
      return;
    }
  }

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

  activeDraftLateIds = null;

  saveState();

  renderApp();

}



function clearSessionOverride() {

  state.ui.selectedSessionOverride = null;

  activeDraftKey = null;

  activeDraftAbsentIds = null;

  activeDraftLateIds = null;

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





// استخراج التلاميذ المحالين على الإدارة (الذين لديهم تقرير إحالة رسمي أو إذن دخول معتمد)

function getReferredStudentsForClass(classCode, currentSlotIndex, dateStr) {

  if (!classCode) return { referred: [], permitted: [] };



  const classStudents = getStudentsForClass(classCode);

  const studentsMap = {};

  classStudents.forEach(s => { 

    if (s.studentId) studentsMap[s.studentId] = s;

    if (s.massarCode) studentsMap[s.massarCode] = s;

  });



  const passesMap = state.entryPasses || {};

  const dismissalReports = state.dismissalReports || {};

  const referredSet = new Map();

  const permittedSet = new Map();



  // 1. أولاً: التحقق من أوراق السماح بالدخول المسلمة من الإدارة

  Object.values(passesMap).forEach(pass => {

    if (!pass || pass.status === 'REVOKED') return;

    const st = (pass.studentId && studentsMap[pass.studentId]) ||

               (pass.massarCode && studentsMap[pass.massarCode]) ||

               (pass.studentName && classStudents.find(s => s.fullName === pass.studentName));

    if (!st) return;



    const isValidDate = (pass.validForDate === dateStr || pass.issuedDate === dateStr || !pass.validForDate || pass.absentDate <= dateStr);

    if (isValidDate) {

      const cleanKey = st.massarCode || st.studentId;

      permittedSet.set(cleanKey, {

        student: st,

        pass: pass

      });

    }

  });



  // 2. ثانياً: التلاميذ المحالون فعلياً على الإدارة (تقارير إحالة صادرة عن الإدارة أو الأساتذة ولم تُسوَّ بعد)

  Object.values(dismissalReports).forEach(rep => {

    if (!rep || rep.resolved || rep.status === 'RESOLVED') return;

    const st = (rep.studentId && studentsMap[rep.studentId]) ||

               (rep.massarCode && studentsMap[rep.massarCode]) ||

               (rep.studentName && classStudents.find(s => s.fullName === rep.studentName)) ||

               (matchClassCode(rep.classCode, classCode) ? (studentsMap[rep.studentId] || studentsMap[rep.massarCode]) : null);

    if (!st) return;



    const cleanKey = st.massarCode || st.studentId || rep.studentId;

    if (permittedSet.has(cleanKey)) return;



    const slotObj = (state.timeSlots || []).find(ts => ts.slotIndex === rep.slotIndex);

    const slotLabel = slotObj ? `${slotObj.label} (${slotObj.startTime}–${slotObj.endTime})` : (rep.time ? `الساعة ${rep.time}` : '');



    referredSet.set(cleanKey, {

      student: st,

      report: rep,

      slotLabel: slotLabel,

      reason: rep.reasonType || rep.customReason || 'إحالة على الإدارة',

      teacherName: rep.teacherName || '',

      date: rep.date

    });

  });



  return {

    referred: Array.from(referredSet.values()),

    permitted: Array.from(permittedSet.values())

  };

}





function clearSessionOverride() {

  clearTeacherSessionOverride();

}



function renderTeacherView() {

  const ctx = getActiveTeacherSessionContext();

  const teacher = ctx.teacher;

  const dow = getDayOfWeek(state.ui.simDate);

  const nowMins = timeToMinutes(state.ui.simTime);



  const teacherAllSlots = (state.timetable || []).filter(t => t.teacherId === teacher.teacherId);

  const todaySlots = (state.timetable || [])

    .filter(t => t.teacherId === teacher.teacherId && Number(t.dayOfWeek) === Number(dow))

    .sort((a, b) => Number(a.slotIndex) - Number(b.slotIndex));

  const missedList = getMissedSessionsForTeacher(teacher.teacherId);



  const teacherTabSwitcherHtml = `

    <div style="display:flex; gap:6px; margin: 10px 0 12px; background: #e2e8f0; padding:4px; border-radius:12px; border:1px solid #cbd5e1;">

      <button type="button" onclick="setTeacherActiveTab('ATTENDANCE')" style="flex:1; padding:8px 10px; border-radius:9px; border:none; font-weight:800; font-size:0.82rem; cursor:pointer; transition:all 0.2s; display:flex; align-items:center; justify-content:center; gap:5px; ${state.ui.teacherTab !== 'EXAMS' ? 'background:#0f766e; color:#fff; box-shadow:0 2px 4px rgba(15,118,110,0.3);' : 'background:transparent; color:#475569;'}">

        <span>📝</span>

        <span>مسك الغياب اليومي</span>

      </button>

      <button type="button" onclick="setTeacherActiveTab('EXAMS')" style="flex:1; padding:8px 10px; border-radius:9px; border:none; font-weight:800; font-size:0.82rem; cursor:pointer; transition:all 0.2s; display:flex; align-items:center; justify-content:center; gap:5px; ${state.ui.teacherTab === 'EXAMS' ? 'background:#d97706; color:#fff; box-shadow:0 2px 4px rgba(217,119,6,0.3);' : 'background:transparent; color:#475569;'}">

        <span>📅</span>

        <span>برمجة الفروض المحروسة</span>

        ${

          (state.examsPlanning || []).filter(e => (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || e.teacher_id === teacher.teacherId).length > 0

            ? `<span style="background:${state.ui.teacherTab === 'EXAMS' ? '#fff' : '#d97706'}; color:${state.ui.teacherTab === 'EXAMS' ? '#d97706' : '#fff'}; font-size:0.68rem; padding:1px 6px; border-radius:99px; font-weight:900;">${(state.examsPlanning || []).filter(e => (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || e.teacher_id === teacher.teacherId).length}</span>`

            : ''

        }

      </button>

    </div>

  `;



  if (state.ui.teacherTab === 'EXAMS') {

    return `

      <div class="teacher-shell">

        <div class="teacher-banner">

          <div class="teacher-top-row">

            <div style="min-width:0; flex:1;">

              <div style="font-weight:800; font-size:0.95rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">

                👨‍🏫 ذ. ${teacher.fullName}

              </div>

              <div style="font-size:0.74rem; opacity:0.88;">

                📘 ${teacher.subject} • القاعة: ${teacher.defaultRoom || 'عامة'}

              </div>

            </div>

            <span class="badge" style="background:rgba(255,255,255,0.18); color:#fff; font-size:0.74rem;">

              🇲🇦 ${DAYS_AR[dow] || ''} ${state.ui.simDate.slice(5)} • ${state.ui.simTime}

            </span>

          </div>

        </div>



        ${teacherTabSwitcherHtml}



        ${renderTeacherExamsSection(teacher)}

      </div>

    `;

  }



  // شريط الحصص السابقة التي في الوراء (غير الممسوكة وفق مهلة المدير)

  const missedSectionHtml = `

    <div class="missed-bar">

      <div style="font-weight:700; color:#92400e; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">

        ⏪ حصص سابقة (غير ممسوكة): <strong>${missedList.length}</strong>

      </div>

      <div style="display:flex; gap:5px; flex-shrink:0;">

        ${

          state.ui.selectedSessionOverride

            ? `<button class="btn btn-outline" style="padding:3px 8px; font-size:0.74rem;" onclick="clearSessionOverride()">إلغاء التحديد ✕</button>`

            : ''

        }

        <button class="missed-bar-btn" onclick="toggleMissedDrawer()">

          ${state.ui.showMissedDrawer ? 'إغلاق ▲' : 'عرض السابقة ▼'}

        </button>

      </div>

    </div>



    ${

      state.ui.showMissedDrawer

        ? `<div class="card" style="border-color:#fcd34d; background:#fffef7; margin-bottom:12px;">

            <div style="font-weight:800; font-size:0.84rem; margin-bottom:4px;">

              ⏪ الحصص السابقة التي مرّ وقتها ولم يُمسك غيابها

            </div>

            <div style="font-size:0.75rem; color:var(--muted); margin-bottom:8px;">

              الحصص التي قمت بمسك غيابها تختفي تلقائياً من هذه اللائحة

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

                            <div style="font-size:0.75rem; color:var(--muted);">${DAYS_AR[m.dayOfWeek]} ${m.date} • (${m.startTime}–${m.endTime})</div>

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



  // قسم جدول حصص اليوم للأستاذ: تعرض أوقات الحصص الفعلية بدقة وتفعل فقط الحصة الحالية

  const todayClassesHtml = `

    <div class="card" style="margin-bottom:12px; border: 1.5px solid #0284c7; background: #f0f9ff;">

      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; border-bottom:1px solid #bae6fd; padding-bottom:6px;">

        <div style="font-weight:900; font-size:0.92rem; color:#0369a1; display:flex; align-items:center; gap:6px;">

          <span>📆</span>

          <span>جدول حصصك اليوم (${DAYS_AR[dow]}):</span>

        </div>

        <span class="badge" style="background:#0284c7; color:#fff; font-weight:800; font-size:0.75rem;">

          ${todaySlots.length} حصص مبرمجة

        </span>

      </div>



      ${

        todaySlots.length === 0

          ? `<div style="text-align:center; padding:14px; font-size:0.84rem; color:#0369a1; font-weight:700;">

              🌴 لا توجد لديك حصص مبرمجة في هذا اليوم (${DAYS_AR[dow] || 'اليوم'}).

            </div>`

          : `<div style="display:flex; flex-direction:column; gap:8px;">

              ${todaySlots.map(ts => {

                const timeSlot = getTimeSlot(ts.slotIndex);

                const sessionKey = `${state.ui.simDate}_${ts.slotIndex}_${ts.classCode}`;

                const sessRec = state.attendanceSessions[sessionKey];

                const isSelected = state.ui.selectedSessionOverride &&

                                   state.ui.selectedSessionOverride.date === state.ui.simDate &&

                                   Number(state.ui.selectedSessionOverride.slotIndex) === Number(ts.slotIndex) &&

                                   state.ui.selectedSessionOverride.classCode === ts.classCode;

                const startMins = timeToMinutes(timeSlot.startTime);

                const endMins = timeToMinutes(timeSlot.endTime);

                const isLiveNow = (nowMins >= startMins && nowMins < endMins);

                const isUpcoming = (nowMins < startMins);

                const isPast = (nowMins >= endMins);



                let statusBadge = '';

                let actionBtn = '';



                if (sessRec) {

                  // الحصة تم مسك غيابها بالفعل

                  statusBadge = `<span class="badge" style="background:#16a34a; color:#fff; font-size:0.72rem;">✅ تم المسك (${sessRec.absentCount || 0} غائب • ${sessRec.lateCount || 0} متأخر)</span>`;

                  if (isSelected) {

                    actionBtn = `<button class="btn btn-outline" style="padding:4px 8px; font-size:0.74rem; background:#e0f2fe; color:#0369a1; border-color:#0284c7;" onclick="clearSessionOverride()">المعروضة حالياً ✓</button>`;

                  } else {

                    actionBtn = `<button class="btn btn-outline" style="padding:4px 10px; font-size:0.75rem; border-color:#0284c7; color:#0369a1; font-weight:700;" onclick="selectTeacherSession('${state.ui.simDate}', ${dow}, ${ts.slotIndex}, '${ts.classCode}', '${ts.room || ''}')">✏️ مراجعة / تعديل</button>`;

                  }

                } else if (isLiveNow) {

                  // الحصة جارية الآن وفق التوقيت الفعلي: مفعلة لمسك الغياب فوراً

                  statusBadge = `<span class="badge" style="background:#0f766e; color:#fff; font-size:0.72rem; animation: pulse 2s infinite;">🟢 جارية الآن</span>`;

                  if (isSelected || (!state.ui.selectedSessionOverride && !ctx.noCurrentSessionNow && Number(ctx.slotIndex) === Number(ts.slotIndex))) {

                    actionBtn = `<button class="btn btn-outline" style="padding:4px 8px; font-size:0.74rem; background:#dcfce7; color:#15803d; border-color:#16a34a; font-weight:800;" onclick="clearSessionOverride()">الجارية حالياً ✓</button>`;

                  } else {

                    actionBtn = `<button class="btn btn-primary" style="padding:5px 12px; font-size:0.78rem; background:#0f766e; font-weight:800;" onclick="selectTeacherSession('${state.ui.simDate}', ${dow}, ${ts.slotIndex}, '${ts.classCode}', '${ts.room || ''}')">📝 مسك الغياب الآن 🟢</button>`;

                  }

                } else if (isUpcoming) {

                  // حصة قادمة لم يحن وقتها بعد: غير مفعلة إطلاقاً وفق التوجيه الصارم للمستخدم

                  statusBadge = `<span class="badge" style="background:#f1f5f9; color:#64748b; font-size:0.72rem;">⏳ لم يحن وقتها بعد</span>`;

                  actionBtn = `<button class="btn" disabled style="padding:4px 10px; font-size:0.74rem; background:#f8fafc; color:#94a3b8; border:1px solid #cbd5e1; cursor:not-allowed; opacity:0.65;" title="لا يمكن مسك الغياب إلا في الساعة الفعلية للحصة">🔒 غير مفعلة (تبدأ ${timeSlot.startTime})</button>`;

                } else {

                  // حصة سابقة مرت اليوم ولم يُمسك غيابها بعد: متاحة للمسك المتأخر

                  statusBadge = `<span class="badge" style="background:#fef3c7; color:#92400e; font-size:0.72rem; border:1px solid #fcd34d;">⚠️ مر وقتها (غير ممسوكة)</span>`;

                  if (isSelected) {

                    actionBtn = `<button class="btn btn-outline" style="padding:4px 8px; font-size:0.74rem; background:#fef3c7; color:#92400e; border-color:#f59e0b;" onclick="clearSessionOverride()">المعروضة حالياً ✓</button>`;

                  } else {

                    actionBtn = `<button class="btn btn-primary" style="padding:4px 10px; font-size:0.75rem; background:#d97706; font-weight:800;" onclick="selectTeacherSession('${state.ui.simDate}', ${dow}, ${ts.slotIndex}, '${ts.classCode}', '${ts.room || ''}')">⏪ مسك متأخر</button>`;

                  }

                }



                return `

                  <div style="display:flex; justify-content:space-between; align-items:center; padding:9px 11px; background:#ffffff; border:1px solid ${isLiveNow ? '#0f766e' : isSelected ? '#0284c7' : '#e0f2fe'}; border-radius:9px; gap:8px; box-shadow: ${isLiveNow ? '0 0 0 2px #5eead4' : isSelected ? '0 0 0 2px #38bdf8' : 'none'};">

                    <div style="min-width:0; flex:1;">

                      <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">

                        <span style="font-weight:900; font-size:0.92rem; color:#0f172a; direction:ltr; text-align:right;">${ts.classCode}</span>

                        ${statusBadge}

                      </div>

                      <div style="font-size:0.75rem; color:#64748b; margin-top:3px;">

                        ⏰ (${timeSlot.startTime}–${timeSlot.endTime}) • القاعة: ${ts.room || teacher.defaultRoom || '—'}

                      </div>

                    </div>

                    <div style="flex-shrink:0;">

                      ${actionBtn}

                    </div>

                  </div>

                `;

              }).join('')}

            </div>`

      }

    </div>

  `;



  // إذا لم يكن للأستاذ أي حصص في قاعدة البيانات

  if (teacherAllSlots.length === 0) {

    return `

      <div class="teacher-shell">

        <div class="teacher-banner">

          <div class="teacher-top-row">

            <div style="min-width:0; flex:1;">

              <div style="font-weight:800; font-size:0.95rem;">👨‍🏫 ذ. ${teacher.fullName}</div>

              <div style="font-size:0.74rem; opacity:0.88;">📘 ${teacher.subject} • القاعة: ${teacher.defaultRoom}</div>

            </div>

            <span class="badge" style="background:rgba(255,255,255,0.18); color:#fff; font-size:0.74rem;">

              🇲🇦 ${DAYS_AR[dow] || ''} ${state.ui.simDate.slice(5)} • ${state.ui.simTime}

            </span>

          </div>

        </div>



        <div class="card" style="border: 2px solid #f59e0b; background: #fffbeb; text-align: center; padding: 20px 14px; margin-bottom: 12px;">

          <div style="font-size: 2rem; margin-bottom: 6px;">⚠️</div>

          <div style="font-weight: 800; font-size: 0.95rem; color: #92400e; margin-bottom: 6px;">

            لم يتم العثور على حصص مبرمجة في ذاكرة الهاتف لهذا الأستاذ

          </div>

          <div style="font-size: 0.8rem; color: #78350f; line-height: 1.5; margin-bottom: 12px;">

            يرجى التأكد من قيام المدير بتوليد الجدول ومزامنته، أو الضغط على الزر أدناه لسحب جدول الحصص الآن:

          </div>

          <button class="btn btn-primary" onclick="pullFromCloudFirestore().then(() => { showToast('تم تحديث البيانات من السحابة'); renderApp(); })" style="padding: 8px 16px; font-size: 0.84rem; background:#d97706;">

            🔄 سحب جدول الحصص والبيانات الآن من السحابة

          </button>

        </div>

      </div>

    `;

  }



  // إذا لم تكن هناك حصة جارية ولا توجد حصة مختارة override:

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

                🕒 لا توجد لديك حصة جارية في هذه الدقيقة بالضبط (${state.ui.simTime})

              </div>

              <div style="font-size:0.76rem; opacity:0.92; margin-top:2px;">

                ${

                  ctx.upcomingToday

                    ? `⏭️ حصتك القادمة اليوم: قسم <strong>${ctx.upcomingToday.classCode}</strong> (${ctx.upcomingToday.timeSlot.startTime}–${ctx.upcomingToday.timeSlot.endTime})`

                    : 'لا توجد حصص متبقية لك في هذا اليوم حسب التوقيت الحالي.'

                }

              </div>

            </div>

          </div>

        </div>



        ${teacherTabSwitcherHtml}

        ${missedSectionHtml}

        ${todayClassesHtml}

      </div>

    `;

  }



  // إذا كانت هناك حصة نشطة (إما جارية الآن وفق التوقيت أو حصة سابقة مختارة بالضغط عليها)

  const sessionKey = `${ctx.date}_${ctx.slotIndex}_${ctx.classCode}`;

  const savedRecord = state.attendanceSessions[sessionKey];

  const classStudents = getStudentsForClass(ctx.classCode);

  const refData = getReferredStudentsForClass(ctx.classCode, ctx.slotIndex, ctx.date);



  let referredSectionHtml = '';

  if (refData.referred.length > 0) {

    referredSectionHtml += `

      <div class="card" style="border: 2px solid #ef4444; background: #fff5f5; margin-bottom: 12px; border-radius: 12px; padding: 12px; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.12);">

        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">

          <div style="font-weight:900; font-size:0.92rem; color:#991b1b; display:flex; align-items:center; gap:6px;">

            <span style="font-size:1.1rem;">🚨</span>

            <span>التلاميذ المحالون على الإدارة (ملزمون بورقة السماح بالدخول):</span>

          </div>

          <span class="badge" style="background:#dc2626; color:#fff; font-weight:800; font-size:0.75rem;">

            ${refData.referred.length} محال(ة)

          </span>

        </div>

        <div style="font-size:0.76rem; color:#7f1d1d; line-height:1.4; margin-bottom: 8px;">

          ⚠️ <strong>تنبيه للأستاذ:</strong> هؤلاء التلاميذ صدر في حقهم تقرير إحالة على الإدارة، <strong>يمنعون من الدخول إلى الفصل</strong> إلا بعد الإدلاء بورقة السماح بالدخول المسلمة من الحراسة العامة.

        </div>

        <div style="display:flex; flex-direction:column; gap:6px;">

          ${refData.referred.map(r => `

            <div style="display:flex; justify-content:space-between; align-items:center; background:#ffffff; border:1px solid #fca5a5; padding:8px 10px; border-radius:8px;">

              <div>

                <div style="font-weight:800; font-size:0.86rem; color:#1e293b;">

                  👤 ${r.student.fullName} <span style="font-family:monospace; font-size:0.75rem; color:#64748b;">(${r.student.massarCode})</span>

                </div>

                <div style="font-size:0.72rem; color:#dc2626; font-weight:700; margin-top:2px;">

                  🔴 سبب الإحالة: ${r.reason || 'إحالة على الإدارة'} ${r.slotLabel ? `• ${r.slotLabel}` : ''}

                </div>

              </div>

              <span class="badge" style="background:#fee2e2; color:#991b1b; border:1px solid #f87171; font-size:0.7rem; font-weight:800; flex-shrink:0;">

                إحالة على الإدارة 🛑

              </span>

            </div>

          `).join('')}

        </div>

      </div>

    `;

  }



  if (refData.permitted.length > 0) {

    referredSectionHtml += `

      <div class="card" style="border: 1.5px solid #16a34a; background: #f0fdf4; margin-bottom: 12px; border-radius: 12px; padding: 10px 12px; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.08);">

        <div style="font-weight:800; font-size:0.85rem; color:#166534; display:flex; align-items:center; gap:6px; margin-bottom:6px;">

          <span>✅</span>

          <span>تلاميذ أدلوا بورقة السماح بالدخول من الإدارة (مصرح لهم بالدخول):</span>

        </div>

        <div style="display:flex; flex-direction:column; gap:4px;">

          ${refData.permitted.map(p => `

            <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.78rem; background:#ffffff; border:1px solid #bbf7d0; padding:6px 10px; border-radius:6px;">

              <span style="font-weight:700; color:#1e293b;">👤 ${p.student.fullName} (${p.student.massarCode})</span>

              <span style="font-size:0.72rem; color:#15803d; font-weight:800; font-family:monospace;">

                ✓ إذن رقم ${p.pass.passId} (الساعة ${p.pass.issuedAt || p.pass.issuedTime || ''})

              </span>

            </div>

          `).join('')}

        </div>

      </div>

    `;

  }



  const currentAbsentSet =

    activeDraftKey === sessionKey && activeDraftAbsentIds

      ? activeDraftAbsentIds

      : new Set(savedRecord ? savedRecord.absentStudentIds : []);



  const currentLateSet =

    activeDraftKey === sessionKey && activeDraftLateIds

      ? activeDraftLateIds

      : new Set(savedRecord ? (savedRecord.lateStudentIds || []) : []);



  const absentCount = currentAbsentSet.size;

  const lateCount = currentLateSet.size;

  const presentCount = Math.max(0, classStudents.length - absentCount);



  return `

    <div class="teacher-shell">

      ${teacherTabSwitcherHtml}

      <div class="teacher-banner" id="teacher-active-session-card">

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

          <div style="min-width:0; flex:1;">

            <div style="font-size:0.76rem; opacity:0.92; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">

              ${ctx.isOverride ? `📌 حصة مختارة (${DAYS_AR[ctx.dayOfWeek]} ${ctx.date})` : '🟢 الحصة الجارية الآن حسب التوقيت المغربي'}

            </div>

            <div style="font-weight:800; font-size:0.9rem;">

              ⏰ ${ctx.timeSlot.startTime}–${ctx.timeSlot.endTime}

            </div>

          </div>

          <div style="display:flex; align-items:center; gap:6px;">

            <div class="session-class-badge">${ctx.classCode}</div>

            ${

              ctx.isOverride

                ? `<button class="btn btn-outline" style="padding:2px 8px; font-size:0.72rem; color:#fff; border-color:rgba(255,255,255,0.6);" onclick="clearSessionOverride()">✕ إلغاء التحديد</button>`

                : ''

            }

          </div>

        </div>

      </div>



      ${missedSectionHtml}

      ${referredSectionHtml}



      <!-- لائحة التلاميذ للحصة -->

      <div class="card">

        <div class="card-header" style="margin-bottom:8px;">

          <div class="card-title" style="font-size:0.9rem;">

            👥 تلاميذ قسم ${ctx.classCode} (${classStudents.length} تلميذ)

          </div>

          ${

            savedRecord
              ? (() => {
                  const rTime = getRecordDisplayTime(savedRecord);
                  return `<span class="badge ${savedRecord.status === 'ON_TIME' ? 'badge-ontime' : 'badge-late'}">
                    ${savedRecord.status === 'ON_TIME' ? '✅ تم في الوقت' : '🟡 مسك متأخر'}${rTime ? ` (${rTime})` : ''}
                  </span>`;
                })()

              : `<span class="badge badge-pending">حدد الغائبين 🔴 والمتأخرين 🟡</span>`

          }

        </div>



        <div class="student-list">

          ${

            classStudents.length === 0

              ? `<div style="text-align:center; padding:18px; color:var(--muted); font-size:0.84rem; font-weight:700;">

                  لم يتم العثور على تلاميذ لهذا القسم (${ctx.classCode})

                </div>`

              : classStudents

                  .map(st => {

                    const isAbsent = currentAbsentSet.has(st.studentId);

                    const isLate = currentLateSet.has(st.studentId);

                    const isReferred = refData.referred.some(r => r.student.studentId === st.studentId || r.student.massarCode === st.massarCode);

                    const isPermitted = refData.permitted.some(p => p.student.studentId === st.studentId || p.student.massarCode === st.massarCode);

                    const todayReport = Object.values(state.dismissalReports || {}).find(r =>

                      (r.studentId === st.studentId || r.massarCode === st.massarCode) &&

                      r.date === state.ui.simDate &&

                      Number(r.slotIndex) === Number(ctx.slotIndex)

                    );

                    const safeName = (st.fullName || '').replace(/"/g, '&quot;').replace(/'/g, "\'");

                    return `

                      <div class="student-row ${isAbsent ? 'is-absent' : isLate ? 'is-late' : ''}"

                           onclick='toggleStudentAbsent("${st.studentId}", "${sessionKey}", ${JSON.stringify(Array.from(currentAbsentSet))}, ${JSON.stringify(Array.from(currentLateSet))})'>

                        <div class="student-info">

                          <div class="student-num">${String(st.rollNumber).padStart(2, '0')}</div>

                          <div class="student-name">

                            ${st.fullName}

                            ${isReferred ? '<span style="font-size:0.68rem; background:#fee2e2; color:#991b1b; padding:1px 6px; border-radius:4px; font-weight:800; border:1px solid #f87171; margin-right:6px;">ملزم بإذن الدخول 🛑</span>' : ''}

                            ${isPermitted ? '<span style="font-size:0.68rem; background:#dcfce7; color:#15803d; padding:1px 6px; border-radius:4px; font-weight:800; border:1px solid #86efac; margin-right:6px;">مسموح بالدخول ✓</span>' : ''}

                            ${todayReport ? `<span class="chip-dismissed" title="${todayReport.reasonType}">⚠️ أُخرج (${todayReport.time})</span>` : ''}

                          </div>

                        </div>

                        <div style="display:flex; align-items:center; gap:5px; flex-shrink:0;">

                          <button type="button" class="btn-report-incident"

                                  title="كتابة تقرير إخراج التلميذ(ة) من الفصل"

                                  onclick='event.stopPropagation(); openDismissalReportModal("${st.studentId}", "${safeName}", "${st.massarCode || ''}", "${ctx.classCode}", ${ctx.slotIndex})'>

                            ${todayReport ? '✏️ التقرير' : '📝 تقرير'}

                          </button>

                          <button type="button" class="btn-status-toggle btn-toggle-late ${isLate ? 'active-late' : ''}"

                                  title="تسجيل التلميذ متأخر عن الحصة"

                                  onclick='event.stopPropagation(); toggleStudentLate("${st.studentId}", "${sessionKey}", ${JSON.stringify(Array.from(currentAbsentSet))}, ${JSON.stringify(Array.from(currentLateSet))})'>

                            ${isLate ? '🟡 متأخر' : 'تأخر'}

                          </button>

                          <div class="status-chip">

                            ${isAbsent ? '🔴 غائب' : isLate ? '🟡 متأخر' : '🟢 حاضر'}

                          </div>

                        </div>

                      </div>

                    `;

                  })

                  .join('')

          }

        </div>

      </div>



      <!-- جدول حصص اليوم يظهر أيضاً أسفل لائحة التلاميذ لتسهيل المتابعة -->

      ${todayClassesHtml}



      <!-- الشريط السفلي الثابت والمدمج للحفظ -->

      <div class="bottom-bar">

        <div class="bottom-bar-inner">

          <div class="counters">

            <div class="counter-pill counter-present" title="الحاضرون">🟢 ${presentCount}</div>

            <div class="counter-pill counter-late" title="المتأخرون">🟡 ${lateCount}</div>

            <div class="counter-pill counter-absent" title="الغائبون">🔴 ${absentCount}</div>

          </div>

          <button class="save-btn ${savedRecord ? 'saved' : ''}" onclick="saveTeacherAttendance()">

            ${

              savedRecord
                ? (() => {
                    const rTime = getRecordDisplayTime(savedRecord);
                    return `✅ تم الحفظ${rTime ? ` (${rTime})` : ''} • تحديث`;
                  })()

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



function normalizeLoginCode(raw) {

  if (!raw) return '';

  const arabicDigits = ['٠','١','٢','٣','٤','٥','٦','٧','٨','٩'];

  let s = String(raw);

  for (let i = 0; i < 10; i++) {

    s = s.replaceAll(arabicDigits[i], String(i));

  }

  return s.replace(/[\s\-_#\u200B-\u200D\uFEFF]/g, '').trim().toUpperCase();

}



function loginWithCodeValue(rawCode) {

  const code = normalizeLoginCode(rawCode);

  if (!code) {

    showToast('⚠️ يرجى إدخال الرقم التعريفي أولاً');

    return;

  }



  const principalCode = normalizeLoginCode(state.settings.principalCode || 'ADMIN888');

  if (code === principalCode) {

    state.ui.isLoggedIn = true;

    state.ui.role = 'PRINCIPAL';

    saveState();

    showToast('👨‍💼 مرحباً بالسيد المدير في لوحة القيادة');

    renderApp();

    return;

  }



  // 1. Search in active state teachers

  let foundTeacher = (state.teachers || []).find(t => normalizeLoginCode(t.loginCode) === code);



  // 2. Fallback: search directly in bundled initial school data

  const initialData = window.INITIAL_SCHOOL_DATA || window.ANFG_SCHOOL_DATA;

  if (!foundTeacher && initialData && Array.isArray(initialData.teachers)) {

    foundTeacher = initialData.teachers.find(t => normalizeLoginCode(t.loginCode) === code);

    if (foundTeacher) {

      state.teachers = initialData.teachers;

    }

  }



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



function isStandaloneMode() {
  try {
    const isMedia = Boolean(window.matchMedia && (
      window.matchMedia('(display-mode: standalone)').matches ||
      window.matchMedia('(display-mode: fullscreen)').matches ||
      window.matchMedia('(display-mode: minimal-ui)').matches
    ));
    const isNav = Boolean(window.navigator && window.navigator.standalone === true);
    const isRef = Boolean(document.referrer && typeof document.referrer === 'string' && document.referrer.includes('android-app://'));
    const isSearch = Boolean(window.location && typeof window.location.search === 'string' && window.location.search.includes('standalone=true'));
    return Boolean(isMedia || isNav || isRef || isSearch);
  } catch (e) {
    return false;
  }
}



function allowWebAccessTemporarily() {

  sessionStorage.setItem('rzzakfet_allow_web', '1');

  renderApp();

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

    try {

      const choice = await deferredInstallPrompt.userChoice;

      if (choice && choice.outcome === 'accepted') {

        showToast('🎉 تم تثبيت تطبيق rzzakfet بنجاح على هاتفك!');

        allowWebAccessTemporarily();

      }

    } catch (err) {}

    deferredInstallPrompt = null;

  } else {

    const guide = document.getElementById('pwa-install-manual-guide');

    if (guide) {

      guide.style.display = 'block';

      guide.scrollIntoView({ behavior: 'smooth' });

    }

    showToast('📲 افتح خيارات المتصفح (⋮) واختر «تثبيت التطبيق / Ajouter à l\'écran d\'accueil»');

  }

}



function renderInstallPromptGate() {

  return `

    <div class="teacher-shell" style="margin-top:20px;">

      <div class="card" style="text-align:center; padding:28px 18px; border-radius:24px; box-shadow:0 10px 30px rgba(15,118,110,0.12); border:1px solid rgba(15,118,110,0.2);">

        <div style="width:76px; height:76px; margin:0 auto 14px; border-radius:22px; background:#0f766e; display:flex; align-items:center; justify-content:center; box-shadow:0 8px 24px rgba(15,118,110,0.35);">

          <img src="/icon-192.png" alt="rzzakfet" style="width:60px; height:60px; border-radius:16px; object-fit:contain;" />

        </div>

        <div style="font-size:1.35rem; font-weight:800; color:#0f172a; margin-bottom:2px;">تطبيق «rzzakfet»</div>

        <div style="font-size:0.86rem; font-weight:700; color:#0f766e; margin-bottom:12px;">منظومة مسك وتتبع غياب التلاميذ</div>

        

        <p style="font-size:0.84rem; color:#475569; line-height:1.6; margin-bottom:22px; text-align:justify;">

          لتشغيل المنظومة كتطبيق أندرويد متكامل وسريع <strong>بدون ظهور شريط المتصفح أو الروابط (URL)</strong>، يرجى تثبيت التطبيق على الشاشة الرئيسية لهاتفك، ليظهر كأيقونة مستقلة باسم <strong>rzzakfet</strong>.

        </p>



        <div style="display:flex; flex-direction:column; gap:11px; max-width:320px; margin:0 auto;">

          <button class="save-btn" style="padding:13px; font-size:1rem; border-radius:14px; display:flex; align-items:center; justify-content:center; gap:8px;" onclick="triggerPwaInstall()">

            <span>📲</span>

            <span>تثبيت التطبيق على الهاتف (rzzakfet)</span>

          </button>

          

          <button class="btn btn-outline" style="padding:10px; font-size:0.84rem; border-radius:12px; color:#475569;" onclick="allowWebAccessTemporarily()">

            🌐 المتابعة عبر المتصفح للدخول

          </button>

        </div>



        <div id="pwa-install-manual-guide" style="display:none; margin-top:16px; text-align:right; background:#f0fdfa; border:1px solid #99f6e4; border-radius:14px; padding:14px; font-size:0.8rem; color:#115e59; line-height:1.7;">

          <div style="font-weight:800; font-size:0.85rem; margin-bottom:6px; color:#0f766e;">✨ خطوات التثبيت السريعة في المتصفح:</div>

          <div>1️⃣ اضغط على زر الخيارات (<strong>⋮</strong>) في أعلى أو أسفل شاشة المتصفح.</div>

          <div>2️⃣ اختر <strong>«تثبيت التطبيق»</strong> أو <strong>«إضافة إلى الشاشة الرئيسية»</strong> (Ajouter à l'écran d'accueil).</div>

          <div>3️⃣ ستجد أيقونة التطبيق فوراً باسم <strong>rzzakfet</strong> على شاشة هاتفك مثل باقي تطبيقات أندرويد.</div>

        </div>

      </div>

    </div>

  `;

}



function renderLoginView() {

  return `

    <div class="teacher-shell" style="margin-top:20px;">

      <div class="card" style="text-align:center; padding:28px 18px; border-radius:20px; box-shadow:0 8px 24px rgba(0,0,0,0.06);">
        ${!isStandaloneMode() ? `
          <div style="background:#f0fdfa; border:1px solid #99f6e4; border-radius:12px; padding:9px 12px; margin-bottom:16px; display:flex; align-items:center; justify-content:space-between; gap:6px;">
            <div style="text-align:right; min-width:0; flex:1;">
              <div style="font-size:0.78rem; font-weight:800; color:#0f766e;">📲 تشغيل التطبيق كـ PWA مستقل</div>
              <div style="font-size:0.68rem; color:#64748b;">تثبيته يتيح العمل بشاشة كاملة وبدون روابط</div>
            </div>
            <button class="btn btn-outline" style="padding:4px 10px; font-size:0.74rem; border-color:#0f766e; color:#0f766e; font-weight:800; border-radius:8px;" onclick="triggerPwaInstall()">تثبيت</button>
          </div>
        ` : ''}

        <div style="width:70px; height:70px; margin:0 auto 12px; border-radius:18px; background:linear-gradient(135deg, var(--primary), var(--primary-dark)); color:#fff; display:flex; align-items:center; justify-content:center; box-shadow:0 6px 16px rgba(15,118,110,0.25);">

          <img src="/icon-192.png" alt="rzzakfet" style="width:52px; height:52px; border-radius:12px; object-fit:contain;" />

        </div>

        <div style="font-size:1.25rem; font-weight:800; color:var(--text); margin-bottom:2px;">تطبيق «مسك الغياب»</div>

        <div style="font-size:0.86rem; font-weight:700; color:var(--primary); margin-bottom:6px;">

          ${state.settings.schoolName || 'المؤسسة التعليمية'}

        </div>

        <div style="font-size:0.8rem; color:var(--muted); margin-bottom:20px; line-height:1.5;">

          أدخل رقمك التعريفي السري المكون من <strong>8 حروف وأرقام</strong> للدخول المباشر إلى حسابك

        </div>



        <div style="max-width:320px; margin:0 auto; display:flex; flex-direction:column; gap:12px;">

          <input id="unified-login-input" type="text" maxlength="12" class="input"

                 placeholder="مثال: HWGQ496R"

                 autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false"

                 style="text-align:center; font-size:1.25rem; font-weight:800; font-family:monospace; letter-spacing:3px; text-transform:uppercase; padding:12px; border:2px solid var(--border); border-radius:12px;"

                 onkeydown="if(event.key==='Enter') submitLoginPage()" />

          <button class="save-btn" style="padding:12px; font-size:1rem; border-radius:12px; display:flex; align-items:center; justify-content:center; gap:8px;" onclick="submitLoginPage()">

            <span>🔐</span>

            <span>تسجيل الدخول</span>

          </button>

        </div>

      </div>

    </div>

  `;

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

    // Render login view directly with friendly install banner if in browser
    const mainViewHtml = renderLoginView();



    root.innerHTML = `

      <header class="top-bar">

        <div class="top-bar-inner">

          <div class="brand">

            <img src="/icon-192.png" alt="rzzakfet" style="width:24px; height:24px; border-radius:6px; object-fit:contain;" />

            <span>rzzakfet</span>

            <span class="brand-badge">${state.settings.schoolName ? state.settings.schoolName.slice(0, 15) : 'أنفك'}</span>

          </div>

          <div class="top-actions">

            <span class="icon-btn" style="cursor:default;">🇲🇦 ${state.ui.simTime}</span>

            ${!isStandaloneMode() ? '<button class="icon-btn" onclick="triggerPwaInstall()" style="font-weight:700;">📲 تثبيت التطبيق</button>' : ''}

          </div>

        </div>

      </header>

      <main class="container">

        ${mainViewHtml}

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



// ================= MOBILE DISMISSAL REPORT MODAL =================

let activeDismissalTarget = null;



window.renderApp = renderApp;

function openDismissalReportModal(studentId, studentName, massarCode, classCode, slotIndex) {

  const ctx = getActiveTeacherSessionContext();

  const teacher = ctx.teacher;

  activeDismissalTarget = {

    studentId,

    studentName,

    massarCode,

    classCode,

    slotIndex,

    teacherId: teacher.teacherId,

    teacherName: teacher.fullName,

    subject: ctx.subject || teacher.subject || ''

  };



  // Check if report already exists

  const existing = Object.values(state.dismissalReports || {}).find(r =>

    (r.studentId === studentId || r.massarCode === massarCode) &&

    r.date === state.ui.simDate &&

    Number(r.slotIndex) === Number(slotIndex)

  );



  const defaultTime = existing ? existing.time : (state.ui.simTime || new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }));

  const existingReasonType = existing ? existing.reasonType : 'عدم الاستماع لتنبيهات الأستاذ وتكرار الفوضى';

  const existingCustomReason = existing ? (existing.customReason || '') : '';



  const modalHtml = `

    <div id="mobile-dismissal-modal" class="mobile-modal-overlay" onclick="if(event.target===this) closeDismissalReportModal()">

      <div class="mobile-modal-card">

        <div class="mobile-modal-header">

          <div class="mobile-modal-title">

            <span>⚠️</span>

            <span>تقرير إخراج تلميذ من الحصة الدراسية</span>

          </div>

          <button type="button" class="mobile-modal-close" onclick="closeDismissalReportModal()">✕</button>

        </div>



        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:10px; margin-bottom:12px; font-size:0.8rem; line-height:1.5;">

          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">

            <span>التلميذ(ة): <strong style="color:#0369a1;">${studentName}</strong></span>

            <span>القسم: <strong style="font-family:monospace;">${classCode}</strong></span>

          </div>

          <div style="display:flex; justify-content:space-between; color:#64748b; font-size:0.75rem;">

            <span>مسار: <strong style="font-family:monospace;">${massarCode || '-'}</strong></span>

            <span>الحصة: <strong>حصة ${slotIndex}</strong></span>

          </div>

        </div>



        <div style="margin-bottom:12px;">

          <label style="display:block; font-weight:800; font-size:0.8rem; color:#334155; margin-bottom:4px;">

            ⏱️ ساعة الإخراج بالضبط من الفصل:

          </label>

          <input type="time" id="dism-time" value="${defaultTime}" style="width:100%; box-sizing:border-box; padding:7px 10px; border:1.5px solid #cbd5e1; border-radius:8px; font-weight:800; font-family:monospace; font-size:0.9rem;" />

        </div>



        <div style="margin-bottom:12px;">

          <label style="display:block; font-weight:800; font-size:0.8rem; color:#334155; margin-bottom:6px;">

            📌 نوع المخالفة المرتكبة (اختر من القائمة):

          </label>

          

          <label class="violation-option">

            <input type="radio" name="dism-reason-type" value="عدم الاستماع لتنبيهات الأستاذ وتكرار الفوضى" ${existingReasonType === 'عدم الاستماع لتنبيهات الأستاذ وتكرار الفوضى' ? 'checked' : ''} />

            <span>عدم الاستماع لتنبيهات الأستاذ وتكرار الفوضى</span>

          </label>

          <label class="violation-option">

            <input type="radio" name="dism-reason-type" value="عرقلة السير العادي للدراسة والتشويش على الزملاء" ${existingReasonType === 'عرقلة السير العادي للدراسة والتشويش على الزملاء' ? 'checked' : ''} />

            <span>عرقلة السير العادي للدراسة والتشويش على الزملاء</span>

          </label>

          <label class="violation-option">

            <input type="radio" name="dism-reason-type" value="السلوك غير اللائق / عدم احترام الأستاذ أو التلاميذ" ${existingReasonType === 'السلوك غير اللائق / عدم احترام الأستاذ أو التلاميذ' ? 'checked' : ''} />

            <span>السلوك غير اللائق / عدم احترام الأستاذ أو التلاميذ</span>

          </label>

          <label class="violation-option">

            <input type="radio" name="dism-reason-type" value="رفض العمل أو الامتناع عن إحضار الأدوات واللوازم" ${existingReasonType === 'رفض العمل أو الامتناع عن إحضار الأدوات واللوازم' ? 'checked' : ''} />

            <span>رفض العمل أو الامتناع عن إحضار الأدوات واللوازم</span>

          </label>

          <label class="violation-option">

            <input type="radio" name="dism-reason-type" value="مغادرة المقعد أو الفصل الدراسي بدون إذن" ${existingReasonType === 'مغادرة المقعد أو الفصل الدراسي بدون إذن' ? 'checked' : ''} />

            <span>مغادرة المقعد أو الفصل الدراسي بدون إذن</span>

          </label>

          <label class="violation-option">

            <input type="radio" name="dism-reason-type" value="مخالفة أخرى (تحديد السبب أسفله)" ${existingReasonType.includes('أخرى') ? 'checked' : ''} />

            <span>مخالفة أخرى (تحديد السبب أسفله)</span>

          </label>

        </div>



        <div style="margin-bottom:14px;">

          <label style="display:block; font-weight:800; font-size:0.8rem; color:#334155; margin-bottom:4px;">

            📝 بيان الوقائع وتفاصيل سبب الإخراج:

          </label>

          <textarea id="dism-custom-reason" rows="3" placeholder="اكتب هنا توضيحاً مختصراً لسبب إخراج التلميذ وإحالته على إدارة المؤسسة والحراسة العامة..." style="width:100%; box-sizing:border-box; border:1.5px solid #cbd5e1; border-radius:8px; padding:8px 10px; font-family:inherit; font-size:0.82rem; line-height:1.4;">${existingCustomReason}</textarea>

        </div>



        <div style="display:flex; align-items:center; justify-content:flex-end; gap:8px; border-top:1px solid #e2e8f0; padding-top:10px;">

          <button type="button" class="btn btn-outline" style="padding:7px 14px; font-size:0.8rem;" onclick="closeDismissalReportModal()">إلغاء</button>

          <button type="button" class="btn btn-primary" style="background:#dc2626; color:#fff; padding:7px 16px; font-size:0.82rem; font-weight:800; display:flex; align-items:center; gap:5px;" onclick="submitDismissalReport()">

            <span>📤</span>

            <span>إرسال التقرير للإدارة</span>

          </button>

        </div>

      </div>

    </div>

  `;



  const old = document.getElementById('mobile-dismissal-modal');

  if (old) old.remove();



  document.body.insertAdjacentHTML('beforeend', modalHtml);
  updateCompExamClassDropdown();

}



function closeDismissalReportModal() {

  const el = document.getElementById('mobile-dismissal-modal');

  if (el) el.remove();

  activeDismissalTarget = null;

}



async function submitDismissalReport() {

  if (!activeDismissalTarget) return;



  const timeInput = document.getElementById('dism-time');

  const customReasonInput = document.getElementById('dism-custom-reason');

  const checkedRadio = document.querySelector('input[name="dism-reason-type"]:checked');



  const dismissalTime = timeInput ? timeInput.value : (state.ui.simTime || '09:00');

  const reasonType = checkedRadio ? checkedRadio.value : 'عرقلة السير العادي للدراسة والتشويش على الزملاء';

  const customReason = customReasonInput ? customReasonInput.value.trim() : '';



  const repId = `DISM-${state.ui.simDate.replace(/-/g, '')}-${Date.now().toString(16).slice(-4).toUpperCase()}`;



  const reportObj = {

    reportId: repId,

    studentId: activeDismissalTarget.studentId,

    studentName: activeDismissalTarget.studentName,

    massarCode: activeDismissalTarget.massarCode,

    classCode: activeDismissalTarget.classCode,

    teacherId: activeDismissalTarget.teacherId,

    teacherName: activeDismissalTarget.teacherName,

    subject: activeDismissalTarget.subject,

    date: state.ui.simDate,

    time: dismissalTime,

    slotIndex: activeDismissalTarget.slotIndex,

    reasonType: reasonType,

    customReason: customReason,

    status: 'PENDING_ADMIN',

    createdAt: Date.now()

  };



  if (!state.dismissalReports) state.dismissalReports = {};

  state.dismissalReports[repId] = reportObj;



  saveState();

  closeDismissalReportModal();

  renderApp();

  showToast('تم إرسال تقرير إخراج التلميذ(ة) للإدارة بنجاح! ✓');



  try {

    await fetch('/api/attendance/dismissal_report', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(reportObj)

    });

  } catch (err) {

    console.warn('[dismissal report POST error]:', err);

  }

}





// =========================================================================

// TEACHER CONTINUOUS ASSESSMENT & EXAM SCHEDULING (برمجة وتتبع الفروض المحروسة)

// =========================================================================



window.mobileTeacherSem = 1;

window.mobileTeacherWeekOffset = 0;

window.mobileExamSelectedDate = null;



function setTeacherActiveTab(tab) {

  if (!state.ui) state.ui = {};

  state.ui.teacherTab = tab;

  saveState();

  renderApp();

}

window.setTeacherActiveTab = setTeacherActiveTab;



function setMobileTeacherSemester(sem) {

  window.mobileTeacherSem = Number(sem);

  renderApp();

}

window.setMobileTeacherSemester = setMobileTeacherSemester;



function setMobileTeacherWeekOffset(offset) {
  window.mobileTeacherWeekOffset = Number(offset);
  renderApp();
}
window.setMobileTeacherWeekOffset = setMobileTeacherWeekOffset;

function changeMobileExamWeek(delta) {

  window.mobileTeacherWeekOffset = (window.mobileTeacherWeekOffset || 0) + delta;

  window.mobileExamSelectedDate = null; // reset to Monday of new week

  renderApp();

}

window.changeMobileExamWeek = changeMobileExamWeek;



function selectMobileExamDate(dateStr) {

  window.mobileExamSelectedDate = dateStr;

  renderApp();

}

window.selectMobileExamDate = selectMobileExamDate;



function getTeacherWorkloadInfo(teacher) {

  const teacherSlots = (state.timetable || []).filter(t => t.teacherId === teacher.teacherId);

  const teacherClasses = Array.from(new Set(teacherSlots.map(t => t.classCode))).filter(Boolean).sort();

  const classCount = teacherClasses.length;

  let recDays = 12;

  let loadLabel = 'متوسط';

  let recCorrDays = 6;

  if (classCount <= 2) {

    recDays = 9;

    loadLabel = 'خفيف';

    recCorrDays = 4;

  } else if (classCount >= 5) {

    recDays = 15;

    loadLabel = 'مرتفع';

    recCorrDays = 8;

  }

  return { teacherSlots, teacherClasses, classCount, recDays, loadLabel, recCorrDays };

}



function getMoroccanWeekDates(baseDateStr, weekOffset = 0) {

  const refDate = baseDateStr ? new Date(baseDateStr) : new Date();

  if (isNaN(refDate.getTime())) refDate.setTime(Date.now());



  // In JS: 0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat

  const day = refDate.getDay();

  const diffToMon = (day === 0 ? -6 : 1) - day;

  const monday = new Date(refDate);

  monday.setDate(monday.getDate() + diffToMon + (weekOffset * 7));



  const todayStr = state.ui?.simDate || new Date().toISOString().slice(0, 10);

  const week = [];

  const monthNames = ['', 'يناير', 'فبراير', 'مارس', 'أبريل', 'ماي', 'يونيو', 'يوليوز', 'غشت', 'شتنبر', 'أكتوبر', 'نونبر', 'دجنبر'];



  for (let i = 0; i < 6; i++) {

    const cur = new Date(monday);

    cur.setDate(monday.getDate() + i);

    const yyyy = cur.getFullYear();

    const mm = String(cur.getMonth() + 1).padStart(2, '0');

    const dd = String(cur.getDate()).padStart(2, '0');

    const dateStr = `${yyyy}-${mm}-${dd}`;

    week.push({

      dayOfWeek: i + 1,

      dayName: DAYS_AR[i + 1] || '',

      dayNum: cur.getDate(),

      monthNum: cur.getMonth() + 1,

      monthName: monthNames[cur.getMonth() + 1] || '',

      dateStr: dateStr,

      isToday: dateStr === todayStr,

      isPast: dateStr < todayStr

    });

  }

  return week;

}



// ========================================================
// TEACHER EXAMS PLANNING - MOROCCAN WEEKLY TIMETABLE GRID
// ========================================================

window.mobileActiveExamNum = window.mobileActiveExamNum || 1;
window.mobileTeacherSem = window.mobileTeacherSem || 1;
window.mobileTeacherWeekOffset = window.mobileTeacherWeekOffset || 0;

function setMobileActiveExamNum(num) {
  window.mobileActiveExamNum = Number(num);
  renderApp();
}
window.setMobileActiveExamNum = setMobileActiveExamNum;

function setMobileTeacherSemester(sem) {
  window.mobileTeacherSem = Number(sem);
  renderApp();
}
window.setMobileTeacherSemester = setMobileTeacherSemester;

function setMobileTeacherWeekOffset(offset) {
  window.mobileTeacherWeekOffset = Number(offset);
  renderApp();
}
window.setMobileTeacherWeekOffset = setMobileTeacherWeekOffset;

function changeMobileExamWeek(delta) {
  window.mobileTeacherWeekOffset = (window.mobileTeacherWeekOffset || 0) + Number(delta);
  renderApp();
}
window.changeMobileExamWeek = changeMobileExamWeek;

function renderTeacherExamsSection(teacher) {
  const semActive = Number(window.mobileTeacherSem || 1);
  const activeExamNum = Number(window.mobileActiveExamNum || 1);

  const defaultMinCal = {
    "1": {
      exam_1: { name: "الفرض 1", start_date: "2026-11-02", end_date: "2026-11-14", submission_deadline: "2026-11-28" },
      exam_2: { name: "الفرض 2", start_date: "2026-12-07", end_date: "2026-12-19", submission_deadline: "2027-01-02" },
      exam_3: { name: "الفرض 3", start_date: "2027-01-04", end_date: "2027-01-16", submission_deadline: "2027-01-23" },
      exam_4: { name: "الفرض 4", start_date: "2027-01-11", end_date: "2027-01-16", submission_deadline: "2027-01-23" },
      final_exam_deadline: "2027-01-16",
      final_submission_deadline: "2027-01-23"
    },
    "2": {
      exam_1: { name: "الفرض 1", start_date: "2027-03-01", end_date: "2027-03-13", submission_deadline: "2027-03-27" },
      exam_2: { name: "الفرض 2", start_date: "2027-04-12", end_date: "2027-04-24", submission_deadline: "2027-05-08" },
      exam_3: { name: "الفرض 3", start_date: "2027-05-24", end_date: "2027-06-05", submission_deadline: "2027-06-12" },
      exam_4: { name: "الفرض 4", start_date: "2027-05-31", end_date: "2027-06-05", submission_deadline: "2027-06-12" },
      final_exam_deadline: "2027-06-05",
      final_submission_deadline: "2027-06-12"
    }
  };
  const semKey = String(semActive);
  const minCal = (state.ministerialCalendar && state.ministerialCalendar[semKey]) || defaultMinCal[semKey] || defaultMinCal["1"];
  const { teacherSlots, teacherClasses, classCount, recDays, loadLabel } = getTeacherWorkloadInfo(teacher);

  const weekDays = getMoroccanWeekDates(state.ui?.simDate, window.mobileTeacherWeekOffset || 0);

  // All slots for this teacher
  const allTeacherSlots = (state.timetable || []).filter(t => t.teacherId === teacher.teacherId);

  // Filter weekDays to ONLY days this teacher has sessions (e.g. Ali Azri: Mon, Tue, Wed, Thu)
  const activeWeekDays = weekDays.filter(wd => allTeacherSlots.some(s => Number(s.dayOfWeek) === Number(wd.dayOfWeek)));
  const displayDays = activeWeekDays.length > 0 ? activeWeekDays : weekDays;

  // Teacher scheduled exams for this semester
  const myExams = (state.examsPlanning || []).filter(e => {
    const matchTeacher = (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) ||
                         (e.teacher_id && e.teacher_id === teacher.teacherId);
    const matchSem = Number(e.semester) === Number(semActive);
    return matchTeacher && matchSem;
  });

  // Scheduled exams for activeExamNum specifically
  const myActiveExams = myExams.filter(e => Number(e.exam_number || e.exam_num) === activeExamNum);

  // Map of classes that already have activeExamNum scheduled
  const classesWithActiveExam = new Map();
  myActiveExams.forEach(e => {
    const cls = e.class_name || e.class_code;
    if (cls) classesWithActiveExam.set(cls, e);
  });

  const scheduledCountForActiveExam = classesWithActiveExam.size;
  const totalClassesCount = teacherClasses.length || 1;

  // Horizontal Exam Selector Buttons (Image 3 Style: [الفرض 1] [الفرض 2] [الفرض 3] [الفرض 4])
  const examButtonsHtml = [1, 2, 3, 4].map(num => {
    const isAct = num === activeExamNum;
    const countForNum = myExams.filter(e => Number(e.exam_number || e.exam_num) === num).length;
    return `
      <button type="button" onclick="setMobileActiveExamNum(${num})"
              style="flex:1; padding:9px 6px; border-radius:10px; font-weight:900; font-size:0.86rem; border:none; cursor:pointer; transition:all 0.2s; display:flex; align-items:center; justify-content:center; gap:5px; ${
                isAct
                  ? 'background:#2563eb; color:#ffffff; box-shadow:0 3px 8px rgba(37,99,235,0.35); transform:scale(1.02);'
                  : 'background:#f1f5f9; color:#475569; hover:background:#e2e8f0;'
              }">
        <span>الفرض ${num}</span>
        ${countForNum > 0 ? `<span style="background:${isAct ? '#ffffff' : '#2563eb'}; color:${isAct ? '#2563eb' : '#ffffff'}; font-size:0.68rem; padding:1px 6px; border-radius:99px; font-weight:900;">${countForNum}</span>` : ''}
      </button>
    `;
  }).join('');

  const curWeekOffset = Number(window.mobileTeacherWeekOffset || 0);

  // Weekly Grid Table Columns: Compact & Proportionate for Mobile View
  const numCols = Math.max(displayDays.length, 1);
  const gridColumnsHtml = displayDays.map(wd => {
    // Sessions of this teacher on this day, ordered by slotIndex
    const daySessions = allTeacherSlots
      .filter(s => Number(s.dayOfWeek) === Number(wd.dayOfWeek))
      .sort((a, b) => Number(a.slotIndex) - Number(b.slotIndex));

    const sessionsHtml = daySessions.map(s => {
      const ts = getTimeSlot(s.slotIndex);
      const timeLabel = `${ts.startTime} - ${ts.endTime}`;
      const roomLabel = s.room || teacher.defaultRoom || 'ق 01';
      const cCode = s.classCode;

      // 1. Is this session the scheduled exam for activeExamNum strictly on this date?
      const scheduledInThis = myActiveExams.find(e =>
        (e.class_name === cCode || e.class_code === cCode) &&
        (e.exam_date === wd.dateStr)
      );

      // 2. Is activeExamNum already scheduled for this class in ANOTHER session?
      const scheduledInOther = !scheduledInThis && classesWithActiveExam.has(cCode);
      const otherExam = scheduledInOther ? classesWithActiveExam.get(cCode) : null;
      const otherDayName = otherExam ? (DAYS_AR[otherExam.day_of_week] || otherExam.exam_date) : '';
      const otherTime = otherExam ? (otherExam.exam_time_str || '') : '';

      if (scheduledInThis) {
        // GREEN / PROGRAMMED IN THIS SESSION (Compact Chip)
        const corrD = scheduledInThis.correction_date ? scheduledInThis.correction_date.slice(5) : '-';
        const subD = (scheduledInThis.submission_deadline || scheduledInThis.submission_date || '-').slice(5);
        return `
          <div onclick="openQuickScheduleExamModal('${wd.dateStr}', ${s.dayOfWeek}, ${s.slotIndex}, '${cCode}', '${roomLabel}', '${scheduledInThis.id}')"
               style="cursor:pointer; background:#ecfdf5; border:1.5px solid #10b981; border-radius:7px; padding:4px 2px; margin-bottom:4px; text-align:center; box-shadow:0 1px 3px rgba(16,185,129,0.15); transition:all 0.15s;"
               title="انقر لتعديل تاريخ التصحيح والتسليم أو إلغاء هذا الفرض">
            <div style="font-weight:900; font-size:0.72rem; color:#047857; line-height:1.1;">${cCode}</div>
            <div style="font-size:0.54rem; color:#065f46; font-weight:700; margin-top:1px;">${timeLabel}</div>
            <div style="display:inline-block; margin-top:2px; padding:1px 4px; border-radius:4px; background:#10b981; color:#fff; font-size:0.55rem; font-weight:900;">
              ✓ مبرمج
            </div>
            <div style="font-size:0.50rem; color:#374151; margin-top:1px; line-height:1.1;">
              تسليم: <strong>${subD}</strong>
            </div>
          </div>
        `;
      } else if (scheduledInOther) {
        // LOCKED / MUTED (Already scheduled on another date/session) - Click opens modal to view/reschedule/cancel
        const otherDateShort = otherExam && otherExam.exam_date ? otherExam.exam_date.slice(5) : '';
        const otherDow = otherExam ? (otherExam.day_of_week || 1) : 1;
        const otherSlot = otherExam ? (otherExam.slot_index || 1) : 1;
        const otherRoom = otherExam ? (otherExam.room_name || 'ق 01') : 'ق 01';
        const otherId = otherExam ? otherExam.id : '';
        return `
          <div onclick="openQuickScheduleExamModal('${otherExam ? otherExam.exam_date : wd.dateStr}', ${otherDow}, ${otherSlot}, '${cCode}', '${otherRoom}', '${otherId}')"
               style="background:#f8fafc; border:1px dashed #94a3b8; border-radius:7px; padding:4px 2px; margin-bottom:4px; text-align:center; cursor:pointer; opacity:0.85; transition:all 0.15s;"
               title="قسم ${cCode}: تمت برمجة الفرض ${activeExamNum} له مسبقاً بتاريخ ${otherExam ? otherExam.exam_date : ''} (${otherDayName}). انقر للتعديل أو النقل أو الإلغاء.">
            <div style="font-weight:800; font-size:0.70rem; color:#475569; line-height:1.1;">${cCode}</div>
            <div style="font-size:0.54rem; color:#94a3b8; margin-top:1px;">${timeLabel}</div>
            <div style="display:inline-block; margin-top:2px; padding:1px 4px; border-radius:4px; background:#e2e8f0; color:#334155; font-size:0.52rem; font-weight:900;">
              🔒 مبرمج
            </div>
            <div style="font-size:0.48rem; color:#0f766e; font-weight:800; margin-top:1px;">
              ${otherDateShort}
            </div>
          </div>
        `;
      } else {
        // FREE AND AVAILABLE TO SCHEDULE (Compact Box)
        return `
          <div onclick="openQuickScheduleExamModal('${wd.dateStr}', ${s.dayOfWeek}, ${s.slotIndex}, '${cCode}', '${roomLabel}')"
               style="cursor:pointer; background:#ffffff; border:1px solid #cbd5e1; border-radius:7px; padding:4px 2px; margin-bottom:4px; text-align:center; box-shadow:0 1px 2px rgba(0,0,0,0.03); transition:all 0.15s;"
               title="انقر لبرمجة الفرض ${activeExamNum} لهذا القسم">
            <div style="font-weight:900; font-size:0.72rem; color:#0f172a; line-height:1.1;">${cCode}</div>
            <div style="font-size:0.54rem; color:#64748b; font-weight:600; margin-top:1px;">${timeLabel}</div>
            <div style="margin-top:2px; display:inline-flex; align-items:center; gap:2px; padding:1px 4px; border-radius:4px; background:#eff6ff; color:#2563eb; font-size:0.54rem; font-weight:900; border:1px solid #bfdbfe;">
              <span>+</span> <span>برمجة</span>
            </div>
          </div>
        `;
      }
    }).join('');

    return `
      <div style="min-width:0; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:4px 2px; display:flex; flex-direction:column;">
        <div style="text-align:center; padding-bottom:3px; margin-bottom:4px; border-bottom:1.5px solid #e2e8f0;">
          <div style="font-weight:900; font-size:0.76rem; color:#0f172a;">${wd.dayName}</div>
          <div style="font-size:0.62rem; font-weight:800; color:#2563eb;">${wd.dayNum} ${wd.monthName}</div>
        </div>
        <div style="display:flex; flex-direction:column;">
          ${sessionsHtml || '<div style="text-align:center; color:#94a3b8; font-size:0.60rem; padding:8px 0;">فارغ</div>'}
        </div>
      </div>
    `;
  }).join('');

  return `
    <div style="display:flex; flex-direction:column; gap:8px;">

      <!-- Top Header Card: Teacher Name, Semester Switcher & Print Button -->
      <div class="card" style="padding:10px 12px; margin-bottom:0; background:#ffffff; border:1px solid #cbd5e1; border-radius:14px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
          <div>
            <div style="font-weight:900; font-size:1.05rem; color:#0f172a; display:flex; align-items:center; gap:5px;">
              <span>👨‍🏫</span>
              <span>الأستاذ: ${teacher.fullName}</span>
            </div>
            <div style="font-size:0.72rem; color:#64748b; margin-top:1px;">
              المادة: <strong>${teacher.subject || 'عامة'}</strong> • عدد الأقسام: <strong>${classCount}</strong>
            </div>
          </div>

          <div style="display:flex; align-items:center; gap:6px;">
            <!-- Semester Switcher -->
            <div style="display:flex; gap:2px; background:#f1f5f9; padding:2px; border-radius:7px; border:1px solid #e2e8f0;">
              <button type="button" onclick="setMobileTeacherSemester(1)" style="padding:3px 8px; font-size:0.72rem; font-weight:800; border-radius:5px; border:none; cursor:pointer; ${semActive === 1 ? 'background:#0f766e; color:#fff;' : 'background:transparent; color:#64748b;'}">
                الدورة 1
              </button>
              <button type="button" onclick="setMobileTeacherSemester(2)" style="padding:3px 8px; font-size:0.72rem; font-weight:800; border-radius:5px; border:none; cursor:pointer; ${semActive === 2 ? 'background:#0f766e; color:#fff;' : 'background:transparent; color:#64748b;'}">
                الدورة 2
              </button>
            </div>

            <!-- Print Card Button -->
            <button type="button" onclick="printTeacherExamsSheet()" class="btn" style="padding:5px 10px; background:linear-gradient(135deg, #0f766e, #0d9488); color:#fff; font-weight:900; font-size:0.74rem; border-radius:7px; border:none; cursor:pointer; display:flex; align-items:center; gap:4px; box-shadow:0 2px 5px rgba(15,118,110,0.2);">
              <span>🖨️</span>
              <span>طباعة بطاقة الفروض</span>
            </button>

            <!-- Bulk Delete / Cancel Exams Button -->
            ${myExams.length > 0 ? `
              <button type="button" onclick="openTeacherBulkDeleteModal()" class="btn" style="padding:5px 9px; background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; font-weight:900; font-size:0.73rem; border-radius:7px; cursor:pointer; display:flex; align-items:center; gap:4px; box-shadow:0 1px 3px rgba(185,28,28,0.1);" title="إلغاء ومسح فروض محددة أو جميع الفروض">
                <span>🗑️</span>
                <span>إلغاء / مسح الفروض</span>
              </button>
            ` : ''}
          </div>
        </div>

        <!-- Horizontal Exam Selection Buttons (Image 3 Style) -->
        <div style="margin-top:8px; display:flex; gap:5px; background:#f8fafc; padding:3px; border-radius:10px; border:1px solid #e2e8f0;">
          ${examButtonsHtml}
        </div>

        <!-- Progress and Legal Reminder + One-Click Cancel for Active Exam -->
        <div style="margin-top:8px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; font-size:0.72rem; color:#475569; background:#eff6ff; padding:5px 8px; border-radius:7px; border:1px solid #bfdbfe;">
          <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
            <span>📌 برمجة <strong>الفرض ${activeExamNum}</strong>: تم إنجاز <strong>${scheduledCountForActiveExam} من ${totalClassesCount}</strong> أقسام.</span>
            ${scheduledCountForActiveExam > 0 ? `
              <button type="button" onclick="confirmCancelActiveExamForAllClasses(${activeExamNum})"
                      style="padding:2px 8px; background:#fee2e2; border:1px solid #f87171; color:#b91c1c; border-radius:6px; font-weight:900; font-size:0.68rem; cursor:pointer; display:inline-flex; align-items:center; gap:3px;"
                      title="إلغاء برمجة الفرض ${activeExamNum} لجميع أقسامك بضغطة واحدة">
                <span>🗑️</span>
                <span>إلغاء الفرض ${activeExamNum} (كل الأقسام)</span>
              </button>
            ` : ''}
          </div>
          <span style="font-weight:800; color:#1e40af;">المهلة: ≤ 15 يوماً للتسليم ✓</span>
        </div>
      </div>

      <!-- Week Selector & Quick Jump Pills for Future Weeks (Requested by User) -->
      <div class="card" style="padding:8px 10px; margin-bottom:0; background:#ffffff; border:1px solid #cbd5e1; border-radius:12px;">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
          <button type="button" onclick="changeMobileExamWeek(-1)" class="btn btn-outline" style="padding:4px 8px; font-size:0.72rem; border-color:#cbd5e1; font-weight:800; border-radius:6px;" title="الأسبوع السابق">
            ◀ سابق
          </button>
          
          <div style="text-align:center; min-width:0; flex:1;">
            <div style="font-weight:900; font-size:0.80rem; color:#0f172a; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
              📅 أسبوع الفرض: <span style="color:#2563eb;">${weekDays[0].dayNum} ${weekDays[0].monthName} — ${weekDays[5].dayNum} ${weekDays[5].monthName}</span>
            </div>
            <div style="font-size:0.65rem; color:${curWeekOffset === 0 ? '#10b981' : '#2563eb'}; font-weight:800; margin-top:1px;">
              ${curWeekOffset === 0 ? '🟢 الأسبوع الحالي' : curWeekOffset > 0 ? `⏭️ بعد ${curWeekOffset} أسبوع (${curWeekOffset * 7} يوماً)` : `⏮️ قبل ${Math.abs(curWeekOffset)} أسبوع`}
            </div>
          </div>

          <button type="button" onclick="changeMobileExamWeek(1)" class="btn btn-outline" style="padding:4px 8px; font-size:0.72rem; border-color:#cbd5e1; font-weight:800; border-radius:6px;" title="الأسبوع التالي">
            تالٍ ▶
          </button>
        </div>

        <!-- Quick Jump Pills for Future Weeks: Current, +1, +2, +3, +4 -->
        <div style="display:flex; gap:3px; margin-top:6px; padding-top:6px; border-top:1px dashed #e2e8f0;">
          ${[0, 1, 2, 3, 4].map(off => {
            const isSel = curWeekOffset === off;
            const label = off === 0 ? 'الحالي' : off === 1 ? '+1 أسبوع' : off === 2 ? '+أسبوعين' : `+${off} أسابيع`;
            return `
              <button type="button" onclick="setMobileTeacherWeekOffset(${off})"
                      style="flex:1; padding:3px 2px; border-radius:5px; font-weight:800; font-size:0.65rem; border:1px solid ${isSel ? '#2563eb' : '#cbd5e1'}; background:${isSel ? '#eff6ff' : '#f8fafc'}; color:${isSel ? '#1d4ed8' : '#475569'}; cursor:pointer; text-align:center;">
                ${label}
              </button>
            `;
          }).join('')}
        </div>
      </div>

      <!-- Weekly Timetable Grid: 100% Responsive Grid across Phone Screen with Compact Class Boxes -->
      <div style="display:grid; grid-template-columns: repeat(${numCols}, minmax(0, 1fr)); gap: 3px; width: 100%; box-sizing: border-box;">
        ${gridColumnsHtml}
      </div>

      <!-- Extra Actions: Compensatory + Confirm & Print to Administration -->
      <div style="display:flex; flex-direction:column; gap:6px; margin-top:4px;">
        <button type="button" class="btn" onclick="openCompensatoryExamModal()" style="width:100%; padding:10px 14px; background:linear-gradient(135deg, #7c3aed, #6d28d9); color:#fff; font-weight:800; font-size:0.82rem; border-radius:10px; border:none; display:flex; align-items:center; justify-content:center; gap:6px; cursor:pointer; box-shadow:0 2px 6px rgba(109,40,217,0.25);">
          <span>⚡</span>
          <span>برمجة حصة تعويضية خارج الجدول (مع فحص شغور القاعات)</span>
        </button>

        <button type="button" class="btn" onclick="confirmAndPrintTeacherExams()" style="width:100%; padding:11px 14px; background:linear-gradient(135deg, #0f766e, #0d9488); color:#fff; font-weight:900; font-size:0.86rem; border-radius:10px; border:none; display:flex; align-items:center; justify-content:center; gap:8px; cursor:pointer; box-shadow:0 3px 8px rgba(15,118,110,0.3);">
          <span>🚀 🖨️</span>
          <span>تأكيد البرمجة والطباعة (إرسال إلى إدارة المؤسسة)</span>
        </button>
      </div>

    </div>
  `;
}
window.renderTeacherExamsSection = renderTeacherExamsSection;

// ========================================================
// OFFICIAL MINISTERIAL EXAM PLANNING PRINT SHEET
// ========================================================

function printTeacherExamsSheet(teacherOpt) {
  const ctx = typeof getActiveTeacherSessionContext === 'function' ? getActiveTeacherSessionContext() : null;
  const teacher = teacherOpt || (ctx ? ctx.teacher : null) || (state.ui && (state.ui.user || state.ui.activeTeacher)) || (state.teachers && state.teachers[0]);
  if (!teacher) {
    showToast('⚠️ يرجى تسجيل الدخول أولاً');
    return;
  }

  const semActive = Number(window.mobileTeacherSem || 1);
  const myExams = (state.examsPlanning || []).filter(e => {
    const matchT = (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || (e.teacher_id === teacher.teacherId);
    return matchT && Number(e.semester) === semActive;
  });

  const sorted = sortExamsChronologically(myExams);
  const schoolName = state.settings?.schoolName || 'الثانوية التأهيلية أنفك';
  const gresa = state.settings?.gresa || state.settings?.schoolId || 'H12657';
  const province = state.settings?.province || 'سيدي إفني';
  const academy = state.settings?.academy || 'كلميم - واد نون';

  let rowsHtml = '';
  if (sorted.length === 0) {
    rowsHtml = `<tr><td colspan="9" style="text-align:center; padding:25px; color:#64748b; font-weight:700;">لا توجد فروض مبرمجة حالياً للدورة ${semActive === 1 ? 'الأولى' : 'الثانية'}. انقر على الحصص في الجدول لبرمجة الفروض.</td></tr>`;
  } else {
    sorted.forEach((e, idx) => {
      const eDate = e.exam_date || '-';
      const subDate = e.submission_deadline || e.submission_date || '-';
      let diffDays = '-';
      let complianceBadge = '';
      if (eDate !== '-' && subDate !== '-') {
        const d1 = new Date(eDate);
        const d2 = new Date(subDate);
        const diff = Math.round((d2 - d1) / (1000 * 3600 * 24));
        diffDays = `${diff} يوماً`;
      }

      rowsHtml += `
        <tr style="border-bottom:1px solid #cbd5e1; text-align:center;">
          <td style="padding:6px 2px; font-weight:700;">${idx + 1}</td>
          <td style="padding:6px 2px; font-weight:900; color:#0f766e; white-space:nowrap;">الفرض ${e.exam_number || e.exam_num || 1}</td>
          <td style="padding:6px 2px; font-weight:900; white-space:nowrap;">${e.class_name || e.class_code}</td>
          <td style="padding:6px 3px; font-size:0.84rem; text-align:center; vertical-align:middle;">
            <div style="font-weight:900; font-size:0.88rem; color:#0f172a; direction:ltr; white-space:nowrap;">${e.exam_date}</div>
            <div style="font-size:0.75rem; color:#475569; font-weight:700; white-space:nowrap; margin-top:2px;">
              ${DAYS_AR[e.day_of_week] || ''} • <span style="direction:ltr; display:inline-block;">${e.exam_time_str || '-'}</span>
            </div>
          </td>
          <td style="padding:6px 2px; font-weight:700; white-space:nowrap;">${e.room_name || e.room || 'ق 01'}</td>
          <td style="padding:6px 2px; font-weight:700; white-space:nowrap;">${e.correction_date || '-'}</td>
          <td style="padding:6px 2px; font-weight:700; color:#0f766e; white-space:nowrap;">${subDate}</td>
          <td style="padding:6px 2px; font-size:0.78rem; font-weight:700; white-space:nowrap;">${diffDays}</td>
          <td style="padding:6px 2px; font-size:0.76rem; color:#64748b; white-space:nowrap;">${e.is_compensatory ? 'تعويضية' : 'رسمية'}</td>
        </tr>
      `;
    });
  }

  const printDoc = `
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
      <meta charset="UTF-8">
      <title>بطاقة برمجة وتتبع فروض المراقبة المستمرة — ${teacher.fullName}</title>
      <style>
        body { font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; margin:0; padding:20px; color:#0f172a; direction:rtl; }
        .page { max-width:850px; margin:0 auto; padding:25px; border:1px solid #cbd5e1; border-radius:12px; background:#fff; }
        .header { display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #0f766e; padding-bottom:12px; margin-bottom:15px; }
        .inst-title { text-align:right; font-size:0.85rem; line-height:1.4; color:#334155; }
        .doc-title { text-align:center; flex:1; }
        .doc-title h1 { margin:0; font-size:1.25rem; color:#0f766e; }
        .doc-title p { margin:4px 0 0; font-size:0.8rem; color:#64748b; }
        .meta-bar { display:flex; justify-content:space-between; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 14px; margin-bottom:15px; font-size:0.88rem; }
        table { width:100%; border-collapse:collapse; margin-bottom:20px; font-size:0.85rem; }
        th { background:#0f766e; color:#fff; padding:8px 4px; border:1px solid #0f766e; font-size:0.82rem; }
        td { border:1px solid #cbd5e1; }
        .signatures { display:flex; justify-content:space-between; margin-top:35px; padding-top:10px; font-size:0.9rem; font-weight:700; }
        .sig-box { width:30%; text-align:center; }
        .sig-line { margin-top:50px; border-top:1px dashed #94a3b8; }
        @media print {
          body { padding:0; background:#fff; }
          .page { border:none; padding:0; box-shadow:none; }
          .no-print { display:none !important; }
        }
      </style>
    </head>
    <body>
      <div class="no-print" style="max-width:850px; margin:0 auto 15px; display:flex; justify-content:space-between; align-items:center;">
        <button onclick="window.print()" style="padding:10px 22px; background:#0f766e; color:#fff; font-weight:800; border:none; border-radius:8px; cursor:pointer; font-size:0.92rem; box-shadow:0 3px 8px rgba(15,118,110,0.3);">🖨️ طباعة البطاقة (A4)</button>
        <button onclick="window.close()" style="padding:8px 16px; background:#f1f5f9; color:#475569; font-weight:700; border:1px solid #cbd5e1; border-radius:8px; cursor:pointer;">إغلاق النافذة</button>
      </div>

      <div class="page">
        <div class="header">
          <div class="inst-title">
            <strong>المملكة المغربية</strong><br/>
            وزارة التربية الوطنية والتعليم الأولي والرياضة<br/>
            ${academy} • ${province}<br/>
            <strong>${schoolName}</strong> (رمز: ${gresa})
          </div>
          <div class="doc-title">
            <h1>بطاقة برمجة وتتبع فروض المراقبة المستمرة</h1>
            <p>وفق المذكرات الوزارية المنظمة للتقويم التربوي • الموسم الدراسي 2026/2027</p>
          </div>
          <div style="text-align:left; font-size:0.8rem; color:#64748b;">
            تاريخ الاعتماد والطباعة:<br/><strong>${new Date().toISOString().slice(0, 10)}</strong>
          </div>
        </div>

        <div class="meta-bar">
          <div>الأستاذ(ة): <strong>${teacher.fullName}</strong></div>
          <div>المادة: <strong>${teacher.subject || 'عامة'}</strong></div>
          <div>الدورة: <strong>الدورة ${semActive === 1 ? 'الأولى' : 'الثانية'}</strong></div>
          <div>إجمالي الفروض المبرمجة: <strong>${sorted.length} فرض</strong></div>
        </div>

        <table style="width:100%; border-collapse:collapse; margin-bottom:20px; font-size:0.84rem; table-layout:fixed;">
          <thead>
            <tr>
              <th style="width:32px; padding:7px 2px;">ر.ت</th>
              <th style="width:68px; padding:7px 2px; white-space:nowrap;">الفرض</th>
              <th style="width:78px; padding:7px 2px; white-space:nowrap;">القسم</th>
              <th style="width:205px; padding:7px 4px; white-space:nowrap;">تاريخ وتوقيت الإجراء</th>
              <th style="width:46px; padding:7px 2px; white-space:nowrap;">القاعة</th>
              <th style="width:88px; padding:7px 2px; white-space:nowrap;">تاريخ التصحيح</th>
              <th style="width:88px; padding:7px 2px; white-space:nowrap;">تاريخ تسليم النقط</th>
              <th style="width:58px; padding:7px 2px; white-space:nowrap;">المدة</th>
              <th style="width:68px; padding:7px 2px; white-space:nowrap;">ملاحظات</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>

        

        <div class="signatures">
          <div class="sig-box">
            <div>توقيع وتأشيرة الأستاذ(ة):</div>
            <div class="sig-line"></div>
          </div>
          <div class="sig-box">
            <div>تأشيرة الحراسة العامة للخارجية:</div>
            <div class="sig-line"></div>
          </div>
          <div class="sig-box">
            <div>خاتم وتأشيرة رئيس المؤسسة:</div>
            <div class="sig-line"></div>
          </div>
        </div>
      </div>

      <script>
        window.addEventListener('load', () => {
          setTimeout(() => { window.print(); }, 400);
        });
      </script>
    </body>
    </html>
  `;

  const printWindow = window.open('', '_blank', 'width=900,height=750');
  if (printWindow) {
    printWindow.document.open();
    printWindow.document.write(printDoc);
    printWindow.document.close();
  } else {
    // If popups blocked, render clean print modal in current window
    let pModal = document.getElementById('mobile-print-exams-modal');
    if (!pModal) {
      pModal = document.createElement('div');
      pModal.id = 'mobile-print-exams-modal';
      document.body.appendChild(pModal);
    }
    pModal.innerHTML = `
      <div style="position:fixed; inset:0; z-index:99999; background:rgba(15,23,42,0.8); backdrop-filter:blur(4px); overflow-y:auto; padding:20px;">
        <div style="max-width:850px; margin:0 auto; background:#fff; border-radius:16px; padding:20px; box-shadow:0 20px 40px rgba(0,0,0,0.3);">
          <div style="display:flex; justify-content:space-between; margin-bottom:15px;" class="no-print">
            <button onclick="window.print()" class="btn" style="background:#0f766e; color:#fff; padding:8px 18px; font-weight:800; border-radius:8px;">🖨️ طباعة الآن (Print / PDF)</button>
            <button onclick="document.getElementById('mobile-print-exams-modal').remove()" class="btn btn-outline" style="padding:6px 14px; font-weight:700;">إغلاق</button>
          </div>
          <div id="print-sheet-content">
            ${printDoc.includes('<div class="page">') ? printDoc.split('<div class="page">')[1].split(/<\/div>\s*<script>/)[0] : printDoc}
          </div>
        </div>
      </div>
    `;
  }
}
window.printTeacherExamsSheet = printTeacherExamsSheet;


function openQuickScheduleExamModal(dateStr, dow, slotIdx, classCode, roomName, existingExamId = null) {

  const ctx = getActiveTeacherSessionContext();

  const teacher = ctx.teacher;

  const { classCount, recDays, recCorrDays } = getTeacherWorkloadInfo(teacher);



  let existing = null;

  if (existingExamId) {

    existing = (state.examsPlanning || []).find(e => e.id === existingExamId);

  }



  const ts = getTimeSlot(slotIdx);

  const timeStr = `${ts.startTime} - ${ts.endTime}`;

  const semKey = String(window.mobileTeacherSem || 1);
  const scheduledForClass = (state.examsPlanning || []).filter(e => {
    if (existing && e.id === existing.id) return false;
    const matchT = (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || (e.teacher_id === teacher.teacherId);
    return matchT && String(e.semester) === semKey && e.class_name === classCode;
  });
  const scheduledNums = new Set(scheduledForClass.map(e => Number(e.exam_number)));

  let examNum = existing ? Number(existing.exam_number || existing.exam_num || 1) : Number(window.mobileActiveExamNum || 1);
  if (!existing && scheduledNums.has(examNum)) {
    for (let n = 1; n <= 4; n++) {
      if (!scheduledNums.has(n)) {
        examNum = n;
        break;
      }
    }
  }



  // Auto calculate dates

  const eDate = new Date(dateStr);

  const corrDate = new Date(eDate);

  corrDate.setDate(corrDate.getDate() + recCorrDays);



  const subDate = new Date(eDate);

  subDate.setDate(subDate.getDate() + recDays);

  const minCal = (state.ministerialCalendar && state.ministerialCalendar[semKey]) || {};

  if (minCal.final_submission_deadline) {

    const maxSub = new Date(minCal.final_submission_deadline);

    if (!isNaN(maxSub.getTime()) && subDate > maxSub) {

      subDate.setTime(maxSub.getTime());

    }

  }



  const subStr = existing ? existing.submission_deadline : subDate.toISOString().slice(0, 10);
  const corrStr = existing ? existing.correction_date : corrDate.toISOString().slice(0, 10);

  // Build list of all official sessions for this teacher and this class across weeks 0 to 4
  const teacherClassSlots = (state.timetable || []).filter(t =>
    (t.teacherId === teacher.teacherId || (t.teacherName && t.teacherName.trim() === teacher.fullName.trim())) &&
    (t.classCode === classCode)
  );

  const sessionOptionsList = [];
  for (let w = 0; w <= 4; w++) {
    const wDays = getMoroccanWeekDates(state.ui?.simDate, w);
    const wLabel = w === 0 ? 'الأسبوع الحالي' : w === 1 ? 'الأسبوع القادم (+1)' : `بعد ${w} أسابيع (+${w})`;
    for (const sl of teacherClassSlots) {
      const mDay = wDays.find(d => Number(d.dayOfWeek) === Number(sl.dayOfWeek));
      if (mDay) {
        const slTs = getTimeSlot(sl.slotIndex);
        const slTime = `${slTs.startTime} - ${slTs.endTime}`;
        const slRoom = sl.room || teacher.defaultRoom || 'ق 01';
        const isSel = (mDay.dateStr === dateStr && Number(sl.slotIndex) === Number(slotIdx));
        const valObj = JSON.stringify({
          date: mDay.dateStr,
          dow: sl.dayOfWeek,
          slot: sl.slotIndex,
          time: slTime,
          room: slRoom,
          weekOffset: w
        }).replace(/"/g, '&quot;');
        sessionOptionsList.push(`<option value="${valObj}" ${isSel ? 'selected' : ''}>📅 ${wLabel} — ${mDay.dayName} ${mDay.dateStr} (${slTime}) [قاعة ${slRoom}]</option>`);
      }
    }
  }

  // Fallback if class not in timetable
  if (sessionOptionsList.length === 0) {
    const valObj = JSON.stringify({
      date: dateStr,
      dow: dow,
      slot: slotIdx,
      time: timeStr,
      room: roomName,
      weekOffset: 0
    }).replace(/"/g, '&quot;');
    sessionOptionsList.push(`<option value="${valObj}" selected>📅 ${DAYS_AR[dow]} ${dateStr} (${timeStr}) [قاعة ${roomName}]</option>`);
  }

  // Remove old modal if any
  const oldModal = document.getElementById('mobile-schedule-exam-modal');
  if (oldModal) oldModal.remove();

  const modalHtml = `
    <div id="mobile-schedule-exam-modal" class="mobile-modal-overlay" onclick="if(event.target===this) closeMobileScheduleExamModal()">
      <div class="mobile-modal-card" style="max-width:440px;">
        
        <div class="mobile-modal-header">
          <div class="mobile-modal-title" style="color:#0f766e;">
            <span>📅</span>
            <span>${existing ? 'تعديل موعد الفرض المحروس' : 'برمجة الفرض المحروس'}</span>
          </div>
          <button type="button" class="mobile-modal-close" onclick="closeMobileScheduleExamModal()">✕</button>
        </div>

        <form onsubmit="submitQuickExamSchedule(event)" style="display:flex; flex-direction:column; gap:11px;">
          
          <input type="hidden" id="quick-exam-id" value="${existing ? existing.id : ''}">
          <input type="hidden" id="quick-exam-date" value="${dateStr}">
          <input type="hidden" id="quick-exam-dow" value="${dow}">
          <input type="hidden" id="quick-exam-slot" value="${slotIdx}">
          <input type="hidden" id="quick-exam-class" value="${classCode}">
          <input type="hidden" id="quick-exam-room" value="${roomName}">
          <input type="hidden" id="quick-exam-time" value="${timeStr}">

          <!-- Class Title Banner -->
          <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:8px 12px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:900; font-size:1.05rem; color:#0f172a; direction:ltr;">${classCode}</div>
              <div style="font-size:0.72rem; color:#64748b;">الأستاذ: <strong>${teacher.fullName}</strong></div>
            </div>
            <div style="background:#f0fdfa; border:1px solid #99f6e4; color:#0f766e; padding:3px 8px; border-radius:7px; font-size:0.74rem; font-weight:800;">
              ${teacher.subject || 'المادة'}
            </div>
          </div>

          <!-- Session / Date Picker Dropdown across weeks 0 to 4 -->
          <div>
            <label style="display:block; font-size:0.76rem; font-weight:800; color:#1e293b; margin-bottom:4px;">
              🔄 اختيار / تعديل موعد وتاريخ الفرض (حصص القسم):
            </label>
            <select id="quick-exam-session-select" class="form-select" onchange="onQuickSessionSelectChanged(this.value)"
                    style="width:100%; padding:8px 10px; border-radius:8px; border:1.5px solid #0f766e; font-size:0.78rem; font-weight:800; background:#f0fdfa; color:#0f766e; box-sizing:border-box;">
              ${sessionOptionsList.join('')}
            </select>
            <div style="font-size:0.68rem; color:#64748b; margin-top:2px;">
              💡 يمكنك تقديم أو تأخير الفرض باختيار أي حصة رسمية للقسم خلال الأسابيع القادمة.
            </div>
          </div>



          <!-- Select Exam Number (1 to 4) -->

          <div>

            <label style="display:block; font-size:0.8rem; font-weight:800; color:#334155; margin-bottom:6px;">

              اختر رقم الفرض المحروس (1 إلى 4):

            </label>

            <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:6px;">

              ${[1, 2, 3, 4].map(num => {
                const isAlready = scheduledNums.has(num);
                const isChecked = (examNum === num);
                if (isAlready) {
                  return `
                    <div style="text-align:center; padding:6px 2px; border-radius:8px; border:1px solid #e2e8f0; background:#f8fafc; opacity:0.6;" title="مبرمج مسبقاً لهذا القسم">
                      <div style="font-size:0.7rem; font-weight:700; color:#94a3b8; text-decoration:line-through;">الفرض ${num}</div>
                      <div style="font-size:0.6rem; color:#dc2626; font-weight:800;">✓ مبرمج</div>
                    </div>
                  `;
                }
                return `
                  <label style="cursor:pointer; text-align:center; padding:8px 4px; border-radius:8px; border:1.5px solid ${isChecked ? '#0f766e' : '#cbd5e1'}; background:${isChecked ? '#f0fdfa' : '#fff'};">
                    <input type="radio" name="quick_exam_num" value="${num}" ${isChecked ? 'checked' : ''} style="display:none;" onchange="document.querySelectorAll('input[name=quick_exam_num]').forEach(r => r.parentElement.style.borderColor = r.checked ? '#0f766e' : '#cbd5e1'); document.querySelectorAll('input[name=quick_exam_num]').forEach(r => r.parentElement.style.background = r.checked ? '#f0fdfa' : '#fff');">
                    <div style="font-size:0.74rem; font-weight:900; color:${isChecked ? '#0f766e' : '#334155'};">
                      الفرض ${num}
                    </div>
                  </label>
                `;
              }).join('')}

            </div>

          </div>



          <!-- Calculated Deadlines (15-day rule) -->

          <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:10px;">

            <div style="font-weight:800; font-size:0.76rem; color:#166534; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">

              <span>⚖️ آجال التصحيح والتسليم المحتسبة:</span>

              <span style="background:#166534; color:#fff; font-size:0.68rem; padding:1px 6px; border-radius:99px; font-weight:800;">

                مهلة ${recDays} يوماً (≤ 15)

              </span>

            </div>



            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">

              <div>

                <label style="display:block; font-size:0.72rem; color:#475569; margin-bottom:2px; font-weight:700;">تاريخ التصحيح:</label>

                <input type="date" id="quick-corr-date" value="${corrStr}" required style="width:100%; padding:6px 8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.78rem; font-weight:800; background:#fff;">

              </div>

              <div>

                <label style="display:block; font-size:0.72rem; color:#166534; margin-bottom:2px; font-weight:800;">تسليم النقط للإدارة:</label>

                <input type="date" id="quick-sub-date" value="${subStr}" required style="width:100%; padding:6px 8px; border-radius:6px; border:1px solid #16a34a; font-size:0.78rem; font-weight:900; color:#166534; background:#fff;">

              </div>

            </div>

          </div>



          <!-- Submit & Delete Buttons -->
          <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px; flex-wrap:wrap;">
            <div>
              ${existing ? `
                <button type="button" class="btn" onclick="deleteQuickExam('${existing.id}')"
                        style="padding:7px 12px; font-size:0.78rem; font-weight:800; background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; border-radius:8px; cursor:pointer; display:flex; align-items:center; gap:4px;">
                  <span>🗑️</span>
                  <span>إلغاء هذا الفرض</span>
                </button>
              ` : ''}
            </div>
            <div style="display:flex; gap:6px;">
              <button type="button" class="btn btn-outline" onclick="closeMobileScheduleExamModal()" style="padding:7px 12px; font-size:0.8rem;">
                إغلاق
              </button>
              <button type="submit" class="btn btn-primary" style="padding:7px 16px; font-size:0.82rem; font-weight:900; background:#0f766e; color:#fff; border-radius:8px; border:none; cursor:pointer;">
                💾 ${existing ? 'حفظ التعديل' : 'تأكيد وحفظ البرمجة'}
              </button>
            </div>
          </div>



        </form>



      </div>

    </div>

  `;



  document.body.insertAdjacentHTML('beforeend', modalHtml);
  updateCompExamClassDropdown();

}

window.openQuickScheduleExamModal = openQuickScheduleExamModal;




async function deleteQuickExam(examId) {
  if (!examId) return;
  const ok = confirm('هل أنت متأكد من رغبتك في إلغاء برمجة هذا الفرض؟\n\nسيتم حذفه وإتاحته للبرمجة في موعد آخر.');
  if (!ok) return;

  if (!state.examsPlanning) state.examsPlanning = [];
  state.examsPlanning = state.examsPlanning.filter(e => e.id !== examId);
  saveState();

  deleteExamFromCloud(examId);

  try {
    fetch('/api/exams_planning/delete_exam', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: examId })
    }).catch(() => {});
  } catch (e) {}

  closeMobileScheduleExamModal();
  renderApp();
  showToast('✓ تم إلغاء برمجة الفرض بنجاح');
}
window.deleteQuickExam = deleteQuickExam;

async function confirmAndPrintTeacherExams(teacherOpt) {
  const ctx = typeof getActiveTeacherSessionContext === 'function' ? getActiveTeacherSessionContext() : null;
  const teacher = teacherOpt || (ctx ? ctx.teacher : null) || (state.ui && (state.ui.user || state.ui.activeTeacher)) || (state.teachers && state.teachers[0]);
  if (!teacher) {
    showToast('⚠️ يرجى تسجيل الدخول كأستاذ أولاً');
    return;
  }

  showToast('🚀 جارٍ تأكيد البرمجة وإرسالها إلى إدارة المؤسسة...');

  const myExams = (state.examsPlanning || []).filter(e => {
    return (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || (e.teacher_id === teacher.teacherId);
  });

  // Sync to Cloud Firestore
  for (const ex of myExams) {
    await syncExamToCloud(ex);
    ex._cloudSynced = true;
  }
  saveState();

  // Also push to desktop local server if accessible
  try {
    fetch('/api/exams_planning/save_exam', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ exams: myExams, teacher_name: teacher.fullName })
    }).catch(() => {});
  } catch (e) {}

  showToast('✓ تم تأكيد وحفظ البرمجة وإرسالها للإدارة بنجاح!');
  printTeacherExamsSheet(teacher);
}
window.confirmAndPrintTeacherExams = confirmAndPrintTeacherExams;

function onQuickSessionSelectChanged(valStr) {
  try {
    const data = JSON.parse(valStr);
    const dateEl = document.getElementById('quick-exam-date');
    const dowEl = document.getElementById('quick-exam-dow');
    const slotEl = document.getElementById('quick-exam-slot');
    const timeEl = document.getElementById('quick-exam-time');
    const roomEl = document.getElementById('quick-exam-room');

    if (dateEl) dateEl.value = data.date;
    if (dowEl) dowEl.value = data.dow;
    if (slotEl) slotEl.value = data.slot;
    if (timeEl) timeEl.value = data.time;
    if (roomEl) roomEl.value = data.room;

    // Recalculate correction and submission dates
    const d = new Date(data.date);
    const corrDate = new Date(d); corrDate.setDate(d.getDate() + 7);
    const subDate = new Date(d); subDate.setDate(d.getDate() + 14);

    const corrEl = document.getElementById('quick-corr-date');
    const subEl = document.getElementById('quick-sub-date');
    if (corrEl) corrEl.value = corrDate.toISOString().slice(0, 10);
    if (subEl) subEl.value = subDate.toISOString().slice(0, 10);
  } catch (e) {
    console.warn('[onQuickSessionSelectChanged error]:', e);
  }
}
window.onQuickSessionSelectChanged = onQuickSessionSelectChanged;

function closeMobileScheduleExamModal() {

  const m = document.getElementById('mobile-schedule-exam-modal');

  if (m) m.remove();

}

window.closeMobileScheduleExamModal = closeMobileScheduleExamModal;



async function submitQuickExamSchedule(event) {

  if (event) event.preventDefault();



  const ctx = getActiveTeacherSessionContext();

  const teacher = ctx.teacher;

  const examId = document.getElementById('quick-exam-id')?.value;

  const dateStr = document.getElementById('quick-exam-date')?.value;

  const dow = parseInt(document.getElementById('quick-exam-dow')?.value || '1', 10);

  const slotIdx = parseInt(document.getElementById('quick-exam-slot')?.value || '1', 10);

  const classCode = document.getElementById('quick-exam-class')?.value;

  const roomName = document.getElementById('quick-exam-room')?.value;

  const timeStr = document.getElementById('quick-exam-time')?.value;



  const examNumRadio = document.querySelector('input[name=quick_exam_num]:checked');

  const examNum = examNumRadio ? parseInt(examNumRadio.value, 10) : 1;



  const corrDate = document.getElementById('quick-corr-date')?.value;

  const subDate = document.getElementById('quick-sub-date')?.value;



  // 15 days rule check

  const d1 = new Date(dateStr);

  const d2 = new Date(subDate);

  const diffDays = Math.round((d2 - d1) / (1000 * 3600 * 24));

  if (diffDays > 15) {

    const ok = confirm(`تنبيه: المهلة الفاصلة (${diffDays} يوماً) تتجاوز الحد الأقصى للمذكرة الوزارية (15 يوماً).\n\nهل ترغب مع ذلك في تثبيت هذا الموعد؟`);

    if (!ok) return;

  }



  const examObj = {

    id: examId || ('EXAM_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7)),

    semester: Number(window.mobileTeacherSem || 1),

    class_name: classCode,

    subject_name: teacher.subject || '',

    teacher_name: teacher.fullName,

    teacher_id: teacher.teacherId,

    exam_number: examNum,

    exam_date: dateStr,

    correction_date: corrDate,

    submission_deadline: subDate,

    slot_index: slotIdx,

    day_of_week: dow,

    exam_time_str: timeStr,

    room_name: roomName,

    is_compensatory: false,

    status: 'SCHEDULED',

    academic_year: '2026/2027',

    source: 'MOBILE_TEACHER',

    updated_at: new Date().toISOString()

  };



  if (!state.examsPlanning) state.examsPlanning = [];

  const existingIdx = state.examsPlanning.findIndex(e => e.id === examObj.id);

  if (existingIdx !== -1) {

    state.examsPlanning[existingIdx] = examObj;

  } else {

    state.examsPlanning.push(examObj);

  }



  saveState();
  syncExamToCloud(examObj);

  closeMobileScheduleExamModal();

  renderApp();

  showToast(`✓ تم تثبيت موعد الفرض ${examNum} لقسم ${classCode} وإرساله`);



  try {

    fetch('/api/exams_planning/save_exam', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(examObj)

    }).catch(() => {});

  } catch (e) {}

}

window.submitQuickExamSchedule = submitQuickExamSchedule;



// =========================================================================

// COMPENSATORY EXAM MODAL (WITH TWO-CONDITION AVAILABILITY CHECK)

// =========================================================================



function updateCompExamClassDropdown() {
  const ctx = getActiveTeacherSessionContext();
  const teacher = ctx.teacher;
  const { teacherClasses } = getTeacherWorkloadInfo(teacher);
  const examNum = parseInt(document.getElementById('comp-exam-num')?.value || '1', 10);
  const sem = Number(window.mobileTeacherSem || 1);
  const classSelect = document.getElementById('comp-exam-class');
  const submitBtn = document.getElementById('btn-comp-submit');
  if (!classSelect) return;

  const scheduledExams = (state.examsPlanning || []).filter(e => {
    const matchT = (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || (e.teacher_id === teacher.teacherId);
    return matchT && Number(e.semester) === sem && Number(e.exam_number) === examNum;
  });
  const scheduledClassNames = new Set(scheduledExams.map(e => e.class_name));
  const availableClasses = teacherClasses.filter(c => !scheduledClassNames.has(c));

  if (availableClasses.length > 0) {
    classSelect.innerHTML = availableClasses.map(c => `<option value="${c}">${c}</option>`).join('');
    classSelect.disabled = false;
    if (submitBtn) submitBtn.disabled = false;
  } else {
    classSelect.innerHTML = `<option value="" disabled selected>⚠️ جميع أقسامك (${teacherClasses.length}) مبرمج لها الفرض ${examNum} بالفعل</option>`;
    classSelect.disabled = true;
    if (submitBtn) submitBtn.disabled = true;
  }
}
window.updateCompExamClassDropdown = updateCompExamClassDropdown;

function openCompensatoryExamModal() {

  const ctx = getActiveTeacherSessionContext();

  const teacher = ctx.teacher;

  const { teacherClasses, recDays, recCorrDays } = getTeacherWorkloadInfo(teacher);



  const defaultDate = window.mobileExamSelectedDate || state.ui?.simDate || new Date().toISOString().slice(0, 10);

  const defaultClass = teacherClasses[0] || (state.classes[0]?.classCode || 'TC-SC-F-1');



  // Rooms list: classrooms, labs, pitch

  const allRooms = ['ق 1', 'ق 2', 'ق 3', 'ق 4', 'ق 5', 'ق 6', 'ق 7', 'مختبر ف ك 1', 'م ع ح 1', 'ملعب  1'];



  // Remove old modal

  const old = document.getElementById('mobile-schedule-exam-modal');

  if (old) old.remove();



  const modalHtml = `

    <div id="mobile-schedule-exam-modal" class="mobile-modal-overlay" onclick="if(event.target===this) closeMobileScheduleExamModal()">

      <div class="mobile-modal-card" style="max-width:440px; border-top: 4px solid #7c3aed;">

        

        <div class="mobile-modal-header">

          <div class="mobile-modal-title" style="color:#7c3aed;">

            <span>⚡</span>

            <span>برمجة حصة تعويضية خارج جدول الحصص</span>

          </div>

          <button type="button" class="mobile-modal-close" onclick="closeMobileScheduleExamModal()">✕</button>

        </div>



        <form onsubmit="submitCompensatoryExamSchedule(event)" style="display:flex; flex-direction:column; gap:10px;">

          

          <div style="font-size:0.75rem; color:#6b21a8; background:#faf5ff; border:1px solid #e9d5ff; border-radius:8px; padding:8px 10px; line-height:1.4;">

            💡 تتيح لك هذه الواجهة تمرير فرض لقسم في حصة خارج جدولك المعتاد، بشرط <strong>شغور القسم</strong> و<strong>شغور القاعة/الملعب</strong>.

          </div>



          <!-- Class & Exam # -->

          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">

            <div>

              <label style="display:block; font-size:0.76rem; font-weight:800; color:#334155; margin-bottom:3px;">القسم المستهدف:</label>

              <select id="comp-exam-class" onchange="runCompensatoryAvailabilityCheck()" required style="width:100%; padding:7px 8px; border-radius:8px; border:1px solid #cbd5e1; font-weight:800; font-size:0.8rem; background:#fff;">

                ${teacherClasses.map(c => `<option value="${c}">${c}</option>`).join('')}

              </select>

            </div>

            <div>

              <label style="display:block; font-size:0.76rem; font-weight:800; color:#334155; margin-bottom:3px;">رقم الفرض (1 إلى 4):</label>

              <select id="comp-exam-num" required style="width:100%; padding:7px 8px; border-radius:8px; border:1px solid #cbd5e1; font-weight:800; font-size:0.8rem; background:#fff;">

                <option value="1">الفرض الأول (1)</option>

                <option value="2">الفرض الثاني (2)</option>

                <option value="3">الفرض الثالث (3)</option>

                <option value="4">الفرض الرابع (4)</option>

              </select>

            </div>

          </div>



          <!-- Date & Day -->

          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">

            <div>

              <label style="display:block; font-size:0.76rem; font-weight:800; color:#334155; margin-bottom:3px;">تاريخ إجراء الفرض:</label>

              <input type="date" id="comp-exam-date" value="${defaultDate}" onchange="runCompensatoryAvailabilityCheck()" required style="width:100%; padding:6px 8px; border-radius:8px; border:1px solid #cbd5e1; font-weight:800; font-size:0.8rem; background:#fff;">

            </div>

            <div>

              <label style="display:block; font-size:0.76rem; font-weight:800; color:#334155; margin-bottom:3px;">فترة الحصة:</label>

              <select id="comp-exam-slot" onchange="runCompensatoryAvailabilityCheck()" required style="width:100%; padding:7px 8px; border-radius:8px; border:1px solid #cbd5e1; font-weight:800; font-size:0.76rem; background:#fff;">

                <optgroup label="الفترة الصباحية">

                  <option value="1">ح 1 (08:00 - 09:00)</option>

                  <option value="2">ح 2 (09:00 - 10:00)</option>

                  <option value="3">ح 3 (10:00 - 11:00)</option>

                  <option value="4">ح 4 (11:00 - 12:00)</option>

                </optgroup>

                <optgroup label="الفترة المسائية">

                  <option value="5">ح 1 (14:00 - 15:00)</option>

                  <option value="6">ح 2 (15:00 - 16:00)</option>

                  <option value="7" selected>ح 3 (16:00 - 17:00)</option>

                  <option value="8">ح 4 (17:00 - 18:00)</option>

                </optgroup>

              </select>

            </div>

          </div>



          <!-- Room / Pitch Selection -->

          <div>

            <label style="display:block; font-size:0.76rem; font-weight:800; color:#334155; margin-bottom:3px;">

              القاعة أو الفضاء / الملعب الرياضي:

            </label>

            <select id="comp-exam-room" onchange="runCompensatoryAvailabilityCheck()" required style="width:100%; padding:7px 8px; border-radius:8px; border:1px solid #cbd5e1; font-weight:800; font-size:0.82rem; background:#fff;">

              ${allRooms.map(r => `<option value="${r}">${r.includes('ملعب') ? '🏟️ ' + r : r.includes('مختبر') ? '🔬 ' + r : '🏛️ ' + r}</option>`).join('')}

            </select>

          </div>



          <!-- Live Availability Status Pill -->

          <div id="comp-avail-status" style="padding:9px 12px; border-radius:8px; font-size:0.75rem; font-weight:800; transition:all 0.2s; background:#f1f5f9; color:#475569; border:1px solid #cbd5e1;">

            ⏳ جاري التحقق من شغور القسم وشغور القاعة/الملعب...

          </div>



          <!-- Calculated Deadlines -->

          <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:8px 10px; display:grid; grid-template-columns: 1fr 1fr; gap:6px;">

            <div>

              <label style="display:block; font-size:0.7rem; color:#475569; margin-bottom:1px; font-weight:700;">تاريخ التصحيح:</label>

              <input type="date" id="comp-corr-date" required style="width:100%; padding:5px 6px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.75rem; font-weight:800;">

            </div>

            <div>

              <label style="display:block; font-size:0.7rem; color:#166534; margin-bottom:1px; font-weight:800;">تسليم النقط للإدارة:</label>

              <input type="date" id="comp-sub-date" required style="width:100%; padding:5px 6px; border-radius:6px; border:1px solid #16a34a; font-size:0.75rem; font-weight:900; color:#166534;">

            </div>

          </div>



          <!-- Buttons -->

          <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:4px;">

            <button type="button" class="btn btn-outline" onclick="closeMobileScheduleExamModal()" style="padding:7px 14px; font-size:0.8rem;">

              إلغاء

            </button>

            <button type="submit" id="btn-comp-submit" class="btn btn-primary" style="padding:7px 18px; font-size:0.82rem; font-weight:900; background:#7c3aed;">

              ⚡ تأكيد وحجز الحصة التعويضية

            </button>

          </div>



        </form>



      </div>

    </div>

  `;



  document.body.insertAdjacentHTML('beforeend', modalHtml);
  updateCompExamClassDropdown();

  runCompensatoryAvailabilityCheck();

}

window.openCompensatoryExamModal = openCompensatoryExamModal;



async function runCompensatoryAvailabilityCheck() {
  const cls = document.getElementById('comp-exam-class')?.value;
  const dVal = document.getElementById('comp-exam-date')?.value;
  const sIdx = parseInt(document.getElementById('comp-exam-slot')?.value || '1', 10);
  const statusEl = document.getElementById('comp-avail-status');
  const submitBtn = document.getElementById('btn-comp-submit');

  if (!cls || !dVal || !statusEl) return;

  const ctx = getActiveTeacherSessionContext();
  const teacher = ctx.teacher;
  const { recDays, recCorrDays } = getTeacherWorkloadInfo(teacher);

  // Auto calculate dates
  const eDate = new Date(dVal);
  const corrDate = new Date(eDate);
  corrDate.setDate(corrDate.getDate() + recCorrDays);

  const subDate = new Date(eDate);
  subDate.setDate(subDate.getDate() + recDays);

  const semKey = String(window.mobileTeacherSem || 1);
  const minCal = (state.ministerialCalendar && state.ministerialCalendar[semKey]) || {};
  if (minCal.final_submission_deadline) {
    const maxSub = new Date(minCal.final_submission_deadline);
    if (!isNaN(maxSub.getTime()) && subDate > maxSub) {
      subDate.setTime(maxSub.getTime());
    }
  }

  const corrEl = document.getElementById('comp-corr-date');
  const subEl = document.getElementById('comp-sub-date');
  if (corrEl) corrEl.value = corrDate.toISOString().slice(0, 10);
  if (subEl) subEl.value = subDate.toISOString().slice(0, 10);

  // Determine day of week (1=Mon ... 6=Sat)
  const dow = getDayOfWeek(dVal);

  // 1. Calculate vacant rooms for this specific (dow, sIdx) directly from the General Timetable
  const allKnownRooms = (state.rooms && state.rooms.length > 0)
    ? state.rooms.map(r => typeof r === 'string' ? r : (r.name || r.roomName || 'ق 1'))
    : ['ق 1', 'ق 2', 'ق 3', 'ق 4', 'ق 5', 'ق 6', 'ق 7', 'مختبر ف ك 1', 'م ع ح 1', 'ملعب  1'];

  // Map occupied rooms in the general timetable
  const occupiedByTimetable = new Map();
  (state.timetable || []).forEach(t => {
    if (Number(t.dayOfWeek) === Number(dow) && Number(t.slotIndex) === Number(sIdx)) {
      if (t.room) occupiedByTimetable.set(t.room.trim(), t.classCode || t.subject || 'حصة رسمية');
    }
  });

  // Also check other scheduled exams on this date and slot
  (state.examsPlanning || []).forEach(ex => {
    if (ex.exam_date === dVal && Number(ex.slot_index) === Number(sIdx)) {
      if (ex.room_name) occupiedByTimetable.set(ex.room_name.trim(), `فرض مبرمج (${ex.class_name || ex.class_code})`);
    }
  });

  // Check if target class is occupied in the general timetable
  const targetClassBusy = (state.timetable || []).find(t =>
    Number(t.dayOfWeek) === Number(dow) && Number(t.slotIndex) === Number(sIdx) && t.classCode === cls
  );
  const targetClassExamBusy = (state.examsPlanning || []).find(ex =>
    ex.exam_date === dVal && Number(ex.slot_index) === Number(sIdx) && (ex.class_name === cls || ex.class_code === cls)
  );

  // Dynamically populate and group rooms by vacancy
  const roomSelect = document.getElementById('comp-exam-room');
  if (roomSelect) {
    const prevRoom = roomSelect.value ? roomSelect.value.trim() : '';
    let freeOptions = '';
    let busyOptions = '';
    let freeCount = 0;

    allKnownRooms.forEach(r => {
      const rTrim = r.trim();
      const isBusy = occupiedByTimetable.has(rTrim);
      const busyReason = occupiedByTimetable.get(rTrim);
      const icon = rTrim.includes('ملعب') ? '🏟️' : rTrim.includes('مختبر') ? '🔬' : '🏛️';
      if (!isBusy) {
        freeCount++;
        const sel = (rTrim === prevRoom) ? 'selected' : '';
        freeOptions += `<option value="${rTrim}" ${sel}>✅ ${icon} ${rTrim} (شاغرة ومتاحة)</option>`;
      } else {
        busyOptions += `<option value="${rTrim}" disabled style="color:#94a3b8;">⛔ ${icon} ${rTrim} (مشغولة: ${busyReason})</option>`;
      }
    });

    roomSelect.innerHTML = `
      <optgroup label="✅ القاعات الشاغرة (${freeCount} فضاءات مفرغة في الجدول العام)">
        ${freeOptions || '<option value="" disabled>لا توجد قاعات شاغرة في هذه الحصة</option>'}
      </optgroup>
      ${busyOptions ? `<optgroup label="⛔ قاعات مشغولة بحصص أخرى">${busyOptions}</optgroup>` : ''}
    `;

    // Auto-select first free room if current is busy or unselected
    if (occupiedByTimetable.has(prevRoom) || !prevRoom) {
      const firstFree = allKnownRooms.find(r => !occupiedByTimetable.has(r.trim()));
      if (firstFree) roomSelect.value = firstFree.trim();
    }
  }

  const chosenRoom = document.getElementById('comp-exam-room')?.value;

  // Validate Class Availability
  if (targetClassBusy || targetClassExamBusy) {
    const reason = targetClassBusy ? `حصة عادية مع ${targetClassBusy.teacherName || 'أستاذ آخر'}` : 'فرض مبرمج مسبقاً';
    statusEl.style.background = '#fef2f2';
    statusEl.style.color = '#991b1b';
    statusEl.style.borderColor = '#fca5a5';
    statusEl.innerHTML = `🔴 <strong>تعذر الحجز:</strong> قسم <strong>${cls}</strong> غير شاغر في هذا التوقيت (${reason})!`;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.style.opacity = '0.5'; }
    return;
  }

  // Validate Room Availability
  if (chosenRoom && occupiedByTimetable.has(chosenRoom.trim())) {
    statusEl.style.background = '#fef2f2';
    statusEl.style.color = '#991b1b';
    statusEl.style.borderColor = '#fca5a5';
    statusEl.innerHTML = `🔴 <strong>القاعة مشغولة:</strong> القاعة ${chosenRoom} محجوزة (${occupiedByTimetable.get(chosenRoom.trim())}). يرجى اختيار قاعة شاغرة من القائمة أعلاه.`;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.style.opacity = '0.5'; }
    return;
  }

  if (!chosenRoom) {
    statusEl.style.background = '#fffbeb';
    statusEl.style.color = '#b45309';
    statusEl.style.borderColor = '#fcd34d';
    statusEl.innerHTML = `⚠️ <strong>تنبيه:</strong> لا توجد قاعات شاغرة متبقية في هذا التوقيت بالجدول العام!`;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.style.opacity = '0.5'; }
    return;
  }

  // All checks pass!
  statusEl.style.background = '#ecfdf5';
  statusEl.style.color = '#065f46';
  statusEl.style.borderColor = '#6ee7b7';
  statusEl.innerHTML = `🟢 <strong>متاح للحجز:</strong> قسم <strong>${cls}</strong> شاغر والقاعة <strong>${chosenRoom}</strong> شاغرة ومستغلة من الجدول العام!`;
  if (submitBtn) { submitBtn.disabled = false; submitBtn.style.opacity = '1'; }
}

window.runCompensatoryAvailabilityCheck = runCompensatoryAvailabilityCheck;



async function submitCompensatoryExamSchedule(event) {

  if (event) event.preventDefault();



  const ctx = getActiveTeacherSessionContext();

  const teacher = ctx.teacher;

  const cls = document.getElementById('comp-exam-class')?.value;

  const num = parseInt(document.getElementById('comp-exam-num')?.value || '1', 10);

  const dVal = document.getElementById('comp-exam-date')?.value;

  const sIdx = parseInt(document.getElementById('comp-exam-slot')?.value || '7', 10);

  const rm = document.getElementById('comp-exam-room')?.value;

  const corr = document.getElementById('comp-corr-date')?.value;

  const sub = document.getElementById('comp-sub-date')?.value;



  const dow = getDayOfWeek(dVal);

  const ts = getTimeSlot(sIdx);

  const timeStr = `${ts.startTime} - ${ts.endTime}`;



  const examObj = {

    id: 'COMP_EXAM_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7),

    semester: Number(window.mobileTeacherSem || 1),

    class_name: cls,

    subject_name: teacher.subject || '',

    teacher_name: teacher.fullName,

    teacher_id: teacher.teacherId,

    exam_number: num,

    exam_date: dVal,

    correction_date: corr,

    submission_deadline: sub,

    slot_index: sIdx,

    day_of_week: dow,

    exam_time_str: timeStr,

    room_name: rm,

    is_compensatory: true,

    compensatory_reason: 'حصة تعويضية مبرمجة بناءً على شغور القسم والقاعة/الملعب',

    status: 'SCHEDULED',

    academic_year: '2026/2027',

    source: 'MOBILE_TEACHER_COMPENSATORY',

    updated_at: new Date().toISOString()

  };



  if (!state.examsPlanning) state.examsPlanning = [];

  state.examsPlanning.push(examObj);



  saveState();

  closeMobileScheduleExamModal();

  renderApp();

  showToast(`⚡ تم حجز وتثبيت الحصة التعويضية للفرض ${num} بقسم ${cls}!`);



  try {

    fetch('/api/exams_planning/save_exam', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(examObj)

    }).catch(() => {});

  } catch (e) {}

}

window.submitCompensatoryExamSchedule = submitCompensatoryExamSchedule;



async function confirmDeleteMobileExam(examId) {

  const ok = confirm('هل أنت متأكد من رغبتك في إلغاء موعد هذا الفرض؟');

  if (!ok) return;



  if (state.examsPlanning) {

    state.examsPlanning = state.examsPlanning.filter(e => e.id !== examId);

  }

  saveState();

  renderApp();

  showToast('تم إلغاء موعد الفرض بنجاح.');



  try {

    fetch('/api/exams_planning/delete_exam', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify({ id: examId })

    }).catch(() => {});

  } catch (e) {}

}

window.confirmDeleteMobileExam = confirmDeleteMobileExam;





window.addEventListener('DOMContentLoaded', () => {

  renderApp();

  pullStateFromServer();

  window.addEventListener('focus', () => { pullStateFromServer(); });

  document.addEventListener('visibilitychange', () => {

    if (!document.hidden) pullStateFromServer();

  });

  setInterval(() => {

    if (!document.hidden) {

      pullStateFromServer();

    }

  }, 25000);

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



// =========================================================================
// TEACHER BULK & SELECTIVE EXAM CANCELLATION CONTROLLER
// =========================================================================

function openTeacherBulkDeleteModal() {
  const ctx = typeof getActiveTeacherSessionContext === 'function' ? getActiveTeacherSessionContext() : null;
  const teacher = (ctx ? ctx.teacher : null) || (state.ui && (state.ui.user || state.ui.activeTeacher)) || (state.teachers && state.teachers[0]);
  if (!teacher) return;
  const semActive = Number(window.mobileTeacherSem || 1);

  const myExams = (state.examsPlanning || []).filter(e => {
    const matchT = (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || (e.teacher_id === teacher.teacherId);
    return matchT && Number(e.semester) === semActive;
  });

  if (myExams.length === 0) {
    if (typeof showToast === 'function') showToast('لا توجد فروض مبرمجة حالياً لإلغائها.');
    else alert('لا توجد فروض مبرمجة حالياً لإلغائها.');
    return;
  }

  // Count exams per exam number
  const counts = { 1: 0, 2: 0, 3: 0, 4: 0 };
  myExams.forEach(e => {
    const num = Number(e.exam_number || e.exam_num || 1);
    if (counts[num] !== undefined) counts[num]++;
  });

  const oldModal = document.getElementById('modal-teacher-bulk-delete');
  if (oldModal) oldModal.remove();

  const numCheckboxesHtml = [1, 2, 3, 4].map(num => {
    const c = counts[num];
    const isDisabled = c === 0;
    return `
      <label style="display:flex; align-items:center; justify-content:space-between; padding:9px 12px; background:${isDisabled ? '#f8fafc' : '#ffffff'}; border:1px solid ${isDisabled ? '#e2e8f0' : '#cbd5e1'}; border-radius:8px; cursor:${isDisabled ? 'not-allowed' : 'pointer'}; opacity:${isDisabled ? '0.6' : '1'};">
        <div style="display:flex; align-items:center; gap:8px;">
          <input type="checkbox" name="teacher_del_exam_num" value="${num}" ${isDisabled ? 'disabled' : 'checked'}
                 style="width:17px; height:17px; accent-color:#dc2626; cursor:pointer;" onchange="updateTeacherDeleteSummary()">
          <span style="font-weight:800; font-size:0.86rem; color:#0f172a;">الفرض ${num}</span>
        </div>
        <span style="font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:99px; ${c > 0 ? 'background:#fee2e2; color:#b91c1c;' : 'background:#f1f5f9; color:#94a3b8;'}">
          ${c > 0 ? `${c} أقسام مبرمجة` : 'غير مبرمج'}
        </span>
      </label>
    `;
  }).join('');

  const modalHtml = `
    <div id="modal-teacher-bulk-delete" class="mobile-modal-overlay" onclick="if(event.target===this) closeTeacherBulkDeleteModal()">
      <div class="mobile-modal-card" style="max-width:440px;">
        <div class="mobile-modal-header" style="border-bottom:1px solid #fee2e2; padding-bottom:8px;">
          <div class="mobile-modal-title" style="color:#b91c1c; display:flex; align-items:center; gap:6px;">
            <span>🗑️</span>
            <span>إلغاء ومسح الفروض المبرمجة</span>
          </div>
          <button type="button" class="mobile-modal-close" onclick="closeTeacherBulkDeleteModal()">✕</button>
        </div>

        <div style="padding:10px 0; display:flex; flex-direction:column; gap:12px;">
          <div style="font-size:0.78rem; color:#475569; background:#fff1f2; padding:8px 10px; border-radius:8px; border:1px solid #fecdd3; line-height:1.4;">
            الأستاذ(ة): <strong>${teacher.fullName}</strong> • <strong>الدورة ${semActive === 1 ? 'الأولى' : 'الثانية'}</strong><br/>
            إجمالي الفروض المبرمجة حالياً: <strong style="color:#b91c1c;">${myExams.length} فرض</strong>
          </div>

          <!-- Selection Scope -->
          <div>
            <div style="font-weight:900; font-size:0.82rem; color:#0f172a; margin-bottom:6px;">
              اختر نطاق الإلغاء:
            </div>
            
            <div style="display:flex; flex-direction:column; gap:6px;">
              <label style="display:flex; align-items:center; gap:8px; padding:8px 10px; background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; cursor:pointer;">
                <input type="radio" name="teacher_del_scope" value="numbers" checked onchange="onTeacherDelScopeToggle('numbers')" style="width:16px; height:16px; accent-color:#dc2626;">
                <span style="font-weight:800; font-size:0.82rem; color:#0f172a;">إلغاء فروض محددة بالأرقام (الفرض 1، 2، 3، أو 4)</span>
              </label>

              <label style="display:flex; align-items:center; gap:8px; padding:8px 10px; background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; cursor:pointer;">
                <input type="radio" name="teacher_del_scope" value="all" onchange="onTeacherDelScopeToggle('all')" style="width:16px; height:16px; accent-color:#dc2626;">
                <span style="font-weight:800; font-size:0.82rem; color:#b91c1c;">إلغاء جميع فروضي بالكامل لهذه الدورة (${myExams.length} فرض)</span>
              </label>
            </div>
          </div>

          <!-- Exam Numbers Selection Block -->
          <div id="teacher-del-numbers-block" style="display:flex; flex-direction:column; gap:6px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-size:0.76rem; font-weight:800; color:#475569;">حدد الفروض المراد إلغاؤها:</span>
              <button type="button" onclick="toggleAllTeacherDelCheckboxes()" style="padding:2px 7px; font-size:0.72rem; font-weight:800; background:#f1f5f9; border:1px solid #cbd5e1; border-radius:5px; cursor:pointer; color:#334155;">
                تحديد الكل / إلغاء
              </button>
            </div>
            <div style="display:flex; flex-direction:column; gap:5px;">
              ${numCheckboxesHtml}
            </div>
          </div>

          <!-- Summary & Confirmation message -->
          <div id="teacher-del-summary-text" style="font-size:0.74rem; color:#991b1b; font-weight:700; text-align:center; min-height:18px;"></div>

          <!-- Buttons -->
          <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:6px; border-top:1px solid #e2e8f0; padding-top:10px;">
            <button type="button" onclick="closeTeacherBulkDeleteModal()" style="padding:8px 16px; background:#f1f5f9; border:1px solid #cbd5e1; border-radius:8px; font-size:0.80rem; font-weight:800; color:#475569; cursor:pointer;">
              تراجع
            </button>
            <button type="button" onclick="executeTeacherBulkDeleteExams()" style="padding:8px 18px; background:linear-gradient(135deg, #dc2626, #b91c1c); border:none; border-radius:8px; font-size:0.82rem; font-weight:900; color:#ffffff; cursor:pointer; box-shadow:0 2px 6px rgba(220,38,38,0.3); display:flex; align-items:center; gap:5px;">
              <span>🗑️</span>
              <span>تأكيد وحذف الفروض</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHtml);
  updateTeacherDeleteSummary();
}
window.openTeacherBulkDeleteModal = openTeacherBulkDeleteModal;

function closeTeacherBulkDeleteModal() {
  const m = document.getElementById('modal-teacher-bulk-delete');
  if (m) m.remove();
}
window.closeTeacherBulkDeleteModal = closeTeacherBulkDeleteModal;

function onTeacherDelScopeToggle(scope) {
  const blk = document.getElementById('teacher-del-numbers-block');
  if (blk) {
    if (scope === 'all') {
      blk.style.opacity = '0.4';
      blk.style.pointerEvents = 'none';
    } else {
      blk.style.opacity = '1';
      blk.style.pointerEvents = 'auto';
    }
  }
  updateTeacherDeleteSummary();
}
window.onTeacherDelScopeToggle = onTeacherDelScopeToggle;

function toggleAllTeacherDelCheckboxes() {
  const boxes = document.querySelectorAll('input[name="teacher_del_exam_num"]:not(:disabled)');
  const allChecked = Array.from(boxes).every(b => b.checked);
  boxes.forEach(b => { b.checked = !allChecked; });
  updateTeacherDeleteSummary();
}
window.toggleAllTeacherDelCheckboxes = toggleAllTeacherDelCheckboxes;

function updateTeacherDeleteSummary() {
  const summaryEl = document.getElementById('teacher-del-summary-text');
  if (!summaryEl) return;
  const scope = document.querySelector('input[name="teacher_del_scope"]:checked')?.value || 'numbers';
  if (scope === 'all') {
    summaryEl.textContent = '⚠️ سيتم حذف وإلغاء كافة فروض الأستاذ المبرمجة بالكامل لهذه الدورة.';
  } else {
    const checked = Array.from(document.querySelectorAll('input[name="teacher_del_exam_num"]:checked')).map(b => b.value);
    if (checked.length === 0) {
      summaryEl.textContent = 'يرجى تحديد رقم فرض واحد على الأقل للإلغاء.';
    } else {
      summaryEl.textContent = `سيتم إلغاء وبرمجة الفروض: ${checked.map(n => 'الفرض ' + n).join(' و ')}`;
    }
  }
}
window.updateTeacherDeleteSummary = updateTeacherDeleteSummary;

async function executeTeacherBulkDeleteExams() {
  const ctx = typeof getActiveTeacherSessionContext === 'function' ? getActiveTeacherSessionContext() : null;
  const teacher = (ctx ? ctx.teacher : null) || (state.ui && (state.ui.user || state.ui.activeTeacher)) || (state.teachers && state.teachers[0]);
  if (!teacher) return;
  const semActive = Number(window.mobileTeacherSem || 1);

  const scope = document.querySelector('input[name="teacher_del_scope"]:checked')?.value || 'numbers';
  let targetExams = [];
  let confirmPrompt = '';
  let apiPayload = { teacher_name: teacher.fullName, semester: semActive };

  if (scope === 'all') {
    targetExams = (state.examsPlanning || []).filter(e => {
      const matchT = (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || (e.teacher_id === teacher.teacherId);
      return matchT && Number(e.semester) === semActive;
    });
    if (targetExams.length === 0) {
      alert('لا توجد فروض مبرمجة حالياً لحذفها.');
      return;
    }
    confirmPrompt = `⚠️ تحذير: هل أنت متأكد من رغبتك في إلغاء وحذف جميع فروضك المبرمجة بالكامل لهذه الدورة (${targetExams.length} فرض)؟\n\nسيتم حذفها وإتاحة الأقسام لإعادة البرمجة.`;
    apiPayload.type = 'teacher';
  } else {
    const checkedNums = Array.from(document.querySelectorAll('input[name="teacher_del_exam_num"]:checked')).map(b => Number(b.value));
    if (checkedNums.length === 0) {
      alert('يرجى تحديد رقم فرض واحد على الأقل (مثلاً: الفرض 4 أو الفرض 1).');
      return;
    }
    targetExams = (state.examsPlanning || []).filter(e => {
      const matchT = (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || (e.teacher_id === teacher.teacherId);
      const matchSem = Number(e.semester) === semActive;
      const num = Number(e.exam_number || e.exam_num || 1);
      return matchT && matchSem && checkedNums.includes(num);
    });
    if (targetExams.length === 0) {
      alert('لا توجد أي فروض مبرمجة مطابقة للأرقام المحددة.');
      return;
    }
    const labels = checkedNums.map(n => `الفرض ${n}`).join(' و ');
    confirmPrompt = `هل أنت متأكد من رغبتك في إلغاء (${labels}) لجميع أقسامك (${targetExams.length} فرض)؟\n\nسيتم حذفها وإتاحة الحصص للبرمجة من جديد.`;
    apiPayload.type = 'exam_numbers';
    apiPayload.exam_numbers = checkedNums;
  }

  if (!confirm(confirmPrompt)) return;

  // 1. Delete from Firestore
  for (const ex of targetExams) {
    deleteExamFromCloud(ex.id);
  }

  // 2. Post bulk delete to server
  try {
    fetch('/api/exams_planning/delete_exams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(apiPayload)
    }).catch(() => {});
  } catch (e) {}

  // 3. Remove from local state
  const targetIds = new Set(targetExams.map(e => e.id));
  state.examsPlanning = (state.examsPlanning || []).filter(e => !targetIds.has(e.id));
  saveState();

  closeTeacherBulkDeleteModal();
  renderApp();

  if (typeof showToast === 'function') {
    showToast(`✓ تم بنجاح إلغاء وحذف ${targetExams.length} فرض مبرمج`, 'success');
  }
}
window.executeTeacherBulkDeleteExams = executeTeacherBulkDeleteExams;

async function confirmCancelActiveExamForAllClasses(examNum) {
  const ctx = typeof getActiveTeacherSessionContext === 'function' ? getActiveTeacherSessionContext() : null;
  const teacher = (ctx ? ctx.teacher : null) || (state.ui && (state.ui.user || state.ui.activeTeacher)) || (state.teachers && state.teachers[0]);
  if (!teacher) return;
  const semActive = Number(window.mobileTeacherSem || 1);

  const targetExams = (state.examsPlanning || []).filter(e => {
    const matchT = (e.teacher_name && e.teacher_name.trim() === teacher.fullName.trim()) || (e.teacher_id === teacher.teacherId);
    return matchT && Number(e.semester) === semActive && Number(e.exam_number || e.exam_num || 1) === Number(examNum);
  });

  if (targetExams.length === 0) {
    if (typeof showToast === 'function') showToast(`لا توجد أي فروض مبرمجة للفرض ${examNum}.`);
    return;
  }

  const ok = confirm(`هل أنت متأكد من رغبتك في إلغاء وحذف برمجة (الفرض ${examNum}) لجميع أقسامك (${targetExams.length} قسم/حصة)؟\n\nسيتم حذفها وإتاحة الحصص للبرمجة من جديد.`);
  if (!ok) return;

  for (const ex of targetExams) {
    deleteExamFromCloud(ex.id);
  }

  try {
    fetch('/api/exams_planning/delete_exams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'exam_numbers',
        exam_numbers: [Number(examNum)],
        teacher_name: teacher.fullName,
        semester: semActive
      })
    }).catch(() => {});
  } catch (e) {}

  const targetIds = new Set(targetExams.map(e => e.id));
  state.examsPlanning = (state.examsPlanning || []).filter(e => !targetIds.has(e.id));
  saveState();

  renderApp();
  if (typeof showToast === 'function') {
    showToast(`✓ تم بنجاح إلغاء الفرض ${examNum} لجميع الأقسام (${targetExams.length} فرض)`, 'success');
  }
}
window.confirmCancelActiveExamForAllClasses = confirmCancelActiveExamForAllClasses;
