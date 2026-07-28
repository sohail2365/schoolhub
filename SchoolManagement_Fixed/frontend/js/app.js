import { api } from "./api.js";
import { showAlert, clearAlerts } from "./utils.js";
import { renderDashboard } from "./dashboard.js";
import { renderStudents } from "./students.js";
import { renderAttendance } from "./attendance.js";
import { renderGrades } from "./grades.js";
import { renderFees } from "./fees.js";

const authSection = document.getElementById("authSection");
const appSection = document.getElementById("appSection");
const tabContent = document.getElementById("tabContent");

let globalEventsBound = false;

function isAuthed() {
  return !!localStorage.getItem("access_token");
}

function bindGlobalEvents() {
  if (globalEventsBound) return;
  globalEventsBound = true;

  document.getElementById("loginBtn").onclick = async () => {
    clearAlerts();
    try {
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value.trim();

      if (!email || !password) {
        showAlert("Email and password are required", "danger");
        return;
      }

      const res = await api.login({ email, password });
      localStorage.setItem("access_token", res.token);
      showAlert("Login successful");
      await init();
    } catch (e) {
      showAlert(e.message || "Login failed", "danger");
    }
  };

  document.getElementById("logoutBtn").onclick = async () => {
    localStorage.removeItem("access_token");
    showAlert("Logged out");
    await init();
  };

  document.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.onclick = async () => {
      document.querySelectorAll("[data-tab]").forEach((x) => x.classList.remove("active"));
      btn.classList.add("active");
      await loadTab(btn.dataset.tab);
    };
  });
}

async function loadTab(tab) {
  clearAlerts();
  try {
    if (tab === "dashboard") tabContent.innerHTML = await renderDashboard();
    if (tab === "students") tabContent.innerHTML = await renderStudents();
    if (tab === "attendance") tabContent.innerHTML = await renderAttendance();
    if (tab === "grades") tabContent.innerHTML = await renderGrades();
    if (tab === "fees") tabContent.innerHTML = await renderFees();

    bindTabActions();
  } catch (e) {
    showAlert(e.message || "Failed to load tab", "danger");
  }
}

function bindTabActions() {
  const addStudentBtn = document.getElementById("addStudentBtn");
  if (addStudentBtn) {
    addStudentBtn.onclick = async () => {
      try {
        const firstName = document.getElementById("s_first_name").value.trim();
        const lastName = document.getElementById("s_last_name").value.trim();
        
        // FIX: Gender must be "male", "female", or "other" (not "Not Specified")
        const payload = {
          name: `${firstName} ${lastName}`.trim(),
          roll_number: document.getElementById("s_roll").value.trim(),
          class_name: document.getElementById("s_class").value.trim(),
          date_of_birth: document.getElementById("s_dob").value,
          gender: "other", // FIX: Changed from "Not Specified" to "other"
          father_name: "N/A",
          mother_name: "N/A",
          email: `student_${Date.now()}@gmail.com`,
          phone: "0000000000",
          address: "N/A",
        };
    
        console.log("STUDENT_PAYLOAD_EMAIL:", payload.email);
        await api.createStudent(payload);
        showAlert("Student added");
        await loadTab("students");
      } catch (e) {
        showAlert(e.message || "Failed to add student", "danger");
      }
    };
    
  }

  const markAttendanceBtn = document.getElementById("markAttendanceBtn");
  if (markAttendanceBtn) {
    markAttendanceBtn.onclick = async () => {
      try {
        // FIX: Corrected API call with proper endpoint and payload structure
        await api.markAttendance({
          student_id: Number(document.getElementById("a_student_id").value),
          date: document.getElementById("a_date").value,
          is_present: document.getElementById("a_status").value === "present",
          remarks: document.getElementById("a_remarks")?.value || "",
        });
        showAlert("Attendance submitted");
      } catch (e) {
        showAlert(e.message || "Failed to mark attendance", "danger");
      }
    };
  }

  const addGradeBtn = document.getElementById("addGradeBtn");
  if (addGradeBtn) {
    addGradeBtn.onclick = async () => {
      try {
        // FIX: Corrected payload structure for grades API
        await api.createGrade({
          student_id: Number(document.getElementById("g_student_id").value),
          subject: document.getElementById("g_subject").value.trim(),
          marks_obtained: Number(document.getElementById("g_marks").value),
          total_marks: Number(document.getElementById("g_total").value) || 100,
          exam_date: document.getElementById("g_date").value,
          teacher_id: null, // Will be set by backend
        });
        showAlert("Grade added");
      } catch (e) {
        showAlert(e.message || "Failed to add grade", "danger");
      }
    };
  }

  const createFeeBtn = document.getElementById("createFeeBtn");
  if (createFeeBtn) {
    createFeeBtn.onclick = async () => {
      try {
        // FIX: Corrected payload structure for fees API
        await api.createFee({
          student_id: Number(document.getElementById("f_student_id").value),
          fee_name: document.getElementById("f_type").value.trim(),
          amount: Number(document.getElementById("f_amount").value),
          due_date: document.getElementById("f_due_date").value,
          month: document.getElementById("f_month")?.value || "January",
        });
        showAlert("Fee created");
      } catch (e) {
        showAlert(e.message || "Failed to create fee", "danger");
      }
    };
  }

  const recordPaymentBtn = document.getElementById("recordPaymentBtn");
  if (recordPaymentBtn) {
    recordPaymentBtn.onclick = async () => {
      try {
        // FIX: Corrected API call with fee_id as parameter
        const feeId = Number(document.getElementById("p_fee_id").value);
        await api.recordPayment(feeId, {
          amount_paid: Number(document.getElementById("p_amount").value),
          payment_date: document.getElementById("p_date")?.value || new Date().toISOString().split('T')[0],
          payment_method: document.getElementById("p_method").value || "cash",
          receipt_number: document.getElementById("p_receipt")?.value || null,
        });
        showAlert("Payment recorded");
        await loadTab("fees");
      } catch (e) {
        showAlert(e.message || "Failed to record payment", "danger");
      }
    };
  }
}

async function init() {
  bindGlobalEvents();

  if (isAuthed()) {
    authSection.classList.add("d-none");
    appSection.classList.remove("d-none");

    const activeTab = document.querySelector("[data-tab].active")?.dataset.tab || "dashboard";
    await loadTab(activeTab);
  } else {
    authSection.classList.remove("d-none");
    appSection.classList.add("d-none");
    tabContent.innerHTML = "";
  }
}

init();
