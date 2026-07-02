// Dashboard API Integration

const API_BASE = (window.location.protocol === "file:" || !window.location.origin || window.location.origin === "null")
    ? "http://127.0.0.1:8000"
    : window.location.origin;

// ============ FILTERS API ============

async function loadFilters() {
    try {
        const response = await fetch(`${API_BASE}/api/filters/classes`, {
            headers: getHeaders()
        });
        const data = await response.json();
        
        // Populate class dropdown
        const classDropdown = document.getElementById('filterClass');
        data.classes.forEach(cls => {
            const option = document.createElement('option');
            option.value = cls;
            option.textContent = cls;
            classDropdown.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading classes:', error);
    }
}

async function applyFilters() {
    const filters = {
        search: document.getElementById('filterName').value,
        class_name: document.getElementById('filterClass').value,
        attendance_status: document.getElementById('filterAttendance').value,
        fee_status: document.getElementById('filterFee').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/filters/students`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(filters)
        });
        
        const students = await response.json();
        updateStudentTable(students);
    } catch (error) {
        console.error('Error filtering:', error);
        alert('❌ Error applying filters');
    }
}

async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/api/filters/analytics`, {
            headers: getHeaders()
        });
        const data = await response.json();
        
        // Update card values
        document.querySelector('[data-card="total-students"] .card-value').textContent = data.total_students;
        document.querySelector('[data-card="avg-attendance"] .card-value').textContent = data.avg_attendance;
        document.querySelector('[data-card="fee-collection"] .card-value').textContent = data.fee_collection;
        document.querySelector('[data-card="class-performance"] .card-value').textContent = data.class_performance;
        document.querySelector('[data-card="pending-fees"] .card-value').textContent = data.pending_fees;
        document.querySelector('[data-card="top-performers"] .card-value').textContent = data.top_performers;
        document.querySelector('[data-card="low-attendance"] .card-value').textContent = data.low_attendance;
        document.querySelector('[data-card="overdue-fees"] .card-value').textContent = data.overdue_fees;
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// ============ SETTINGS API ============

async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/settings/school`, {
            headers: getHeaders()
        });
        const school = await response.json();
        
        // Populate form
        document.getElementById('schoolName').value = school.name;
        document.getElementById('schoolCity').value = school.city;
        document.getElementById('schoolPhone').value = school.phone;
        document.getElementById('schoolEmail').value = school.email;
        document.getElementById('schoolWebsite').value = school.website || '';
        document.getElementById('activeClasses').value = school.active_classes || '';
        document.getElementById('workingDays').value = school.working_days;
        document.getElementById('feeStructure').value = school.fee_structure || '';
        document.getElementById('feeDueDay').value = school.fee_due_day;
        document.getElementById('lateFeePercent').value = school.late_fee_percent;
        document.getElementById('holidays').value = school.holidays || '';
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function saveSettings() {
    const settings = {
        name: document.getElementById('schoolName').value,
        city: document.getElementById('schoolCity').value,
        phone: document.getElementById('schoolPhone').value,
        email: document.getElementById('schoolEmail').value,
        website: document.getElementById('schoolWebsite').value,
        active_classes: document.getElementById('activeClasses').value,
        working_days: parseInt(document.getElementById('workingDays').value),
        fee_structure: document.getElementById('feeStructure').value,
        fee_due_day: parseInt(document.getElementById('feeDueDay').value),
        late_fee_percent: parseInt(document.getElementById('lateFeePercent').value),
        holidays: document.getElementById('holidays').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/settings/school`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            alert('✅ Settings saved successfully!');
            closeModal('settingsModal');
        } else {
            throw new Error('Failed to save');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('❌ Error saving settings');
    }
}

async function checkUserRole() {
    try {
        const response = await fetch(`${API_BASE}/api/settings/user-role`, {
            headers: getHeaders()
        });
        const user = await response.json();
        
        // Store in localStorage
        localStorage.setItem('user_role', user.role);
        localStorage.setItem('user_permissions', JSON.stringify(user.permissions));
        
        // Update UI based on role
        updateUIByRole(user);
    } catch (error) {
        console.error('Error checking role:', error);
    }
}

function updateUIByRole(user) {
    const permissions = user.permissions;
    
    // Hide elements based on permissions
    if (!permissions.includes('settings')) {
        document.querySelector('[onclick="openSettingsModal()"]').style.display = 'none';
    }
    if (!permissions.includes('export')) {
        document.querySelector('[onclick="exportToExcel()"]').style.display = 'none';
    }
    
    // Update user display
    document.getElementById('userName').textContent = user.name;
    document.getElementById('userRole').textContent = user.role.toUpperCase();
}

function getHeaders() {
    return {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
    };
}

// ============ INITIALIZATION ============

window.addEventListener('load', async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }
    
    // Load all data
    await checkUserRole();
    await loadFilters();
    await loadAnalytics();
    await loadSettings();
});