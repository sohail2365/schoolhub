const API_BASE = (window.location.protocol === "file:" || !window.location.origin || window.location.origin === "null")
    ? "http://127.0.0.1:8000"
    : window.location.origin;

function getToken() {
  return localStorage.getItem("access_token");
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };

  const hasExplicitContentType = Object.keys(headers).some(
    (k) => k.toLowerCase() === "content-type"
  );

  const isFormLike =
    options.body instanceof FormData || options.body instanceof URLSearchParams;

  if (!hasExplicitContentType && options.body != null && !isFormLike) {
    headers["Content-Type"] = "application/json";
  }

  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export const api = {
  login: ({ email, password }) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      headers: { "Content-Type": "application/json" },
    }),

  listStudents: () => request("/students"),
  createStudent: (payload) =>
    request("/students", { method: "POST", body: JSON.stringify(payload) }),
    
  markAttendance: (payload) =>
    request("/attendance", { method: "POST", body: JSON.stringify(payload) }),
  attendanceSummary: (studentId) =>
    request(`/attendance/report/${studentId}`),

  createGrade: (payload) =>
    request("/grades", { method: "POST", body: JSON.stringify(payload) }),
  studentGrades: (studentId) => request(`/grades/student/${studentId}`),

  createFee: (payload) =>
    request("/fees", { method: "POST", body: JSON.stringify(payload) }),
  recordPayment: (feeId, payload) =>
    request(`/fees/${feeId}/payment`, { method: "POST", body: JSON.stringify(payload) }),

  dashboardMetrics: () => request("/dashboard"),
  
  // Additional endpoints from backend
  listAnnouncements: () => request("/announcements"),
  createAnnouncement: (payload) =>
    request("/announcements", { method: "POST", body: JSON.stringify(payload) }),
  deletAnnouncement: (id) =>
    request(`/announcements/${id}`, { method: "DELETE" }),
  
  getSchoolProfile: () => request("/schools/profile"),
  updateSchoolProfile: (payload) =>
    request("/schools/profile", { method: "PUT", body: JSON.stringify(payload) }),
  schoolStats: () => request("/schools/stats"),
  
  getPendingFees: () => request("/fees/pending"),
  feeCollectionReport: () => request("/fees/report"),
  
  getStudentFees: (studentId) => request(`/fees/student/${studentId}`),
  studentAttendance: (studentId) => request(`/attendance/student/${studentId}`),
  attendanceReport: (studentId) => request(`/attendance/report/${studentId}`),
  classAttendanceReport: (className) => request(`/attendance/class/${className}/report`),
  classGrades: (className) => request(`/grades/class/${className}`),
  subjectStats: (subject) => request(`/grades/subject/${subject}/stats`),
  
  reportsAttendanceRange: (startDate, endDate) =>
    request(`/reports/attendance/${startDate}/${endDate}`),
  reportsPerformance: (studentId) =>
    request(`/reports/performance/${studentId}`),
  reportsFeesCollection: () =>
    request("/reports/fees-collection"),
  reportsClassPerformance: (className) =>
    request(`/reports/class/${className}/performance`),
    
  attendanceToday: () => request("/dashboard/attendance-today"),
  recentActivities: () => request("/dashboard/recent-activities"),
};
