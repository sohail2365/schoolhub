export function showAlert(message, type = "success") {
    const box = document.getElementById("alerts");
    box.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
  }
  
  export function clearAlerts() {
    const box = document.getElementById("alerts");
    box.innerHTML = "";
  }
  