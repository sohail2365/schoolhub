import { api } from "./api.js";

export async function renderAttendance() {
  return `
    <div class="card p-3">
      <h6>Mark Attendance</h6>
      <div class="row g-2">
        <div class="col"><input id="a_student_id" class="form-control" placeholder="Student ID"></div>
        <div class="col"><input id="a_teacher_id" class="form-control" placeholder="Teacher ID"></div>
        <div class="col"><input id="a_class" class="form-control" placeholder="Class"></div>
        <div class="col"><input id="a_date" type="date" class="form-control"></div>
        <div class="col">
          <select id="a_status" class="form-select">
            <option value="present">Present</option>
            <option value="absent">Absent</option>
            <option value="late">Late</option>
          </select>
        </div>
        <div class="col"><button id="markAttendanceBtn" class="btn btn-primary w-100">Submit</button></div>
      </div>
    </div>
  `;
}
