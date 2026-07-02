import { api } from "./api.js";

export async function renderStudents() {
  // If your backend expects no school_id query, use: const students = await api.listStudents();
  const students = await api.listStudents();

  const rows = (students || [])
    .map(
      (s) => `
        <tr>
          <td>${s.id ?? "-"}</td>
          <td>${(s.first_name ?? "").trim()} ${(s.last_name ?? "").trim()}</td>
          <td>${s.roll_number ?? "-"}</td>
          <td>${s.class_name ?? "-"}</td>
        </tr>
      `
    )
    .join("");

  return `
    <div class="card p-3 mb-3">
      <h6>Add Student</h6>
      <div class="row g-2">
        <div class="col"><input id="s_first_name" class="form-control" placeholder="First name" /></div>
        <div class="col"><input id="s_last_name" class="form-control" placeholder="Last name" /></div>
        <div class="col"><input id="s_roll" class="form-control" placeholder="Roll no" /></div>
      </div>
      <div class="row g-2 mt-2">
        <div class="col"><input id="s_class" class="form-control" placeholder="Class" /></div>
        <div class="col"><input id="s_section" class="form-control" placeholder="Section" value="A" /></div>
        <div class="col"><input id="s_dob" type="date" class="form-control" /></div>
        <div class="col"><button id="addStudentBtn" class="btn btn-primary w-100">Save</button></div>
      </div>
    </div>

    <div class="card p-3">
      <h6>Students</h6>
      <table class="table table-sm">
        <thead>
          <tr><th>ID</th><th>Name</th><th>Roll</th><th>Class</th></tr>
        </thead>
        <tbody>
          ${
            rows ||
            `<tr><td colspan="4" class="text-muted text-center">No students found</td></tr>`
          }
        </tbody>
      </table>
    </div>
  `;
}
