// Additional JavaScript for modal employee toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Override the showEventDetail function to store current event
    const originalShowEventDetail = window.showEventDetail;
    if (typeof originalShowEventDetail === 'function') {
        window.showEventDetail = function(event) {
            // Store current event globally for toggle function access
            window.currentEventDetail = event;
            
            // Call original function
            return originalShowEventDetail(event);
        };
    }
});

// Toggle employee in shift function
window.toggleEmployeeInShift = function(employeeName, isChecked) {
    // Find the current event that opened the modal
    const currentEvent = window.currentEventDetail;
    
    if (!currentEvent) return;
    
    // Get current employees list
    const employees = currentEvent.extendedProps.employees;
    
    if (isChecked) {
        // Add employee back to the shift if not already present
        if (!employees.some(emp => emp.name === employeeName)) {
            // Find the employee from the original data
            const schedulesData = JSON.parse(document.getElementById('schedules-data').textContent);
            const empData = schedulesData.find(item => item.ten_nv === employeeName && 
                item.ngay_lam === currentEvent.extendedProps.ngay_lam && 
                item.khung_gio === currentEvent.extendedProps.ca_lam);
            
            if (empData) {
                employees.push({
                    id: empData.ma_llv,
                    name: empData.ten_nv,
                    chuc_vu: empData.chuc_vu,
                    status: empData.trang_thai
                });
            }
        }
    } else {
        // Remove employee from the shift
        const index = employees.findIndex(emp => emp.name === employeeName);
        if (index > -1) {
            employees.splice(index, 1);
        }
    }
    
    // Update the event title and display
    if (employees.length > 0) {
        currentEvent.setProp('title', employees.map(e => e.name).join(', '));
        currentEvent.setProp('display', 'auto');
    } else {
        // If no employees left, hide the shift or show empty state
        currentEvent.setProp('title', currentEvent.extendedProps.ca_lam);
        // Keep the event visible but empty
    }
    
    // Update the modal employee list visual
    const participantDiv = document.querySelector(`[data-employee-name="${employeeName}"]`);
    if (participantDiv) {
        if (!isChecked) {
            participantDiv.style.opacity = '0.5';
            participantDiv.style.textDecoration = 'line-through';
        } else {
            participantDiv.style.opacity = '1';
            participantDiv.style.textDecoration = 'none';
        }
    }
    
    // Show toast notification
    if (typeof window.showToast === 'function') {
        window.showToast(
            isChecked ? `Đã thêm ${employeeName} vào ca làm việc` : `Đã bỏ ${employeeName} khỏi ca làm việc`,
            'info'
        );
    }
};
