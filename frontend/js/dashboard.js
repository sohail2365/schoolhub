import { api } from "./api.js";

export async function renderDashboard() {
  const year = new Date().getFullYear();
  const metrics = await api.dashboardMetrics(1, year);

  const totalStudents = metrics?.total_students ?? metrics?.students_count ?? 0;
  const attendanceRate = metrics?.attendance_rate ?? metrics?.attendance_percentage ?? 0;
  const feesDue = metrics?.fees_due ?? metrics?.total_fees_due ?? 0;

  return `
    <div class="row g-3">
      <div class="col-md-4">
        <div class="card card-metric p-3">
          <h6>Total Students</h6>
          <h3>${totalStudents}</h3>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card card-metric p-3">
          <h6>Attendance Rate</h6>
          <h3>${Number(attendanceRate).toFixed(1)}%</h3>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card card-metric p-3">
          <h6>Fees Due</h6>
          <h3>${feesDue}</h3>
        </div>
      </div>
    </div>
  `;
}
