export async function renderGrades() {
    return `
      <div class="card p-3">
        <h6>Add Grade</h6>
        <div class="row g-2">
          <div class="col"><input id="g_student_id" class="form-control" placeholder="Student ID"></div>
          <div class="col"><input id="g_subject" class="form-control" placeholder="Subject"></div>
          <div class="col"><input id="g_exam" class="form-control" placeholder="Exam name"></div>
        </div>
        <div class="row g-2 mt-2">
          <div class="col"><input id="g_marks" type="number" class="form-control" placeholder="Marks"></div>
          <div class="col"><input id="g_total" type="number" class="form-control" placeholder="Total"></div>
          <div class="col"><input id="g_date" type="date" class="form-control"></div>
          <div class="col"><button id="addGradeBtn" class="btn btn-primary w-100">Save</button></div>
        </div>
      </div>
    `;
  }
  