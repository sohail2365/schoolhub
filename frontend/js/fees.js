export async function renderFees() {
    return `
      <div class="card p-3 mb-3">
        <h6>Create Fee</h6>
        <div class="row g-2">
          <div class="col"><input id="f_student_id" class="form-control" placeholder="Student ID"></div>
          <div class="col"><input id="f_type" class="form-control" placeholder="Fee Type"></div>
          <div class="col"><input id="f_amount" type="number" class="form-control" placeholder="Amount"></div>
          <div class="col"><input id="f_due_date" type="date" class="form-control"></div>
          <div class="col"><button id="createFeeBtn" class="btn btn-primary w-100">Create</button></div>
        </div>
      </div>
      <div class="card p-3">
        <h6>Record Payment</h6>
        <div class="row g-2">
          <div class="col"><input id="p_fee_id" class="form-control" placeholder="Fee ID"></div>
          <div class="col"><input id="p_amount" type="number" class="form-control" placeholder="Amount Paid"></div>
          <div class="col">
            <select id="p_method" class="form-select">
              <option value="cash">Cash</option>
              <option value="bank_transfer">Bank Transfer</option>
              <option value="card">Card</option>
              <option value="mobile_money">Mobile Money</option>
            </select>
          </div>
          <div class="col"><button id="recordPaymentBtn" class="btn btn-success w-100">Pay</button></div>
        </div>
      </div>
    `;
  }
  