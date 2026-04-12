document.addEventListener('DOMContentLoaded', function () {
    const viewModal = document.getElementById('view-schedule-modal');
    const sendConfirmModal = document.getElementById('send-confirm-modal');
    const deleteModal = document.getElementById('confirm-delete-popup');
    const selectAllSchedules = document.getElementById('select-all-schedules');
    const rowCheckboxes = document.querySelectorAll('.schedule-row-checkbox');
    const sendNotificationBtn = document.getElementById('send-notification-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');

    // Modal functions
    function showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Load schedule detail via AJAX (Demo - use mock data)
    function loadScheduleDetail(scheduleId) {
        // Mock data for demo
        const mockData = {
            'LL001': {
                'ma_llv': 'LL001',
                'ngay_lam': '25/03/2026',
                'khung_gio': '7:00 - 11:00',
                'trang_thai': 'Chưa Gửi',
                'ngay_tao': '24/03/2026',
                'nhan_vien': [
                    {'ma_nv': 'NV001', 'ten_nv': 'Nguyễn Văn A', 'vi_tri': 'Pha chế'}
                ]
            },
            'LL002': {
                'ma_llv': 'LL002',
                'ngay_lam': '26/03/2026',
                'khung_gio': '13:00 - 17:00',
                'trang_thai': 'Đã Gửi',
                'ngay_tao': '25/03/2026',
                'nhan_vien': [
                    {'ma_nv': 'NV002', 'ten_nv': 'Trần Thị B', 'vi_tri': 'Phục vụ'},
                    {'ma_nv': 'NV003', 'ten_nv': 'Lê Minh C', 'vi_tri': 'Thu ngân'}
                ]
            },
            'LL003': {
                'ma_llv': 'LL003',
                'ngay_lam': '27/03/2026',
                'khung_gio': '18:00 - 22:00',
                'trang_thai': 'Chưa Gửi',
                'ngay_tao': '26/03/2026',
                'nhan_vien': [
                    {'ma_nv': 'NV004', 'ten_nv': 'Phạm Khánh D', 'vi_tri': 'Giữ xe'}
                ]
            }
        };
        
        const data = mockData[scheduleId] || {};
        populateViewModal(data);
        showModal('view-schedule-modal');
    }

    function populateViewModal(data) {
        document.getElementById('view-schedule-date').textContent = data.ngay_lam || '-';
        document.getElementById('view-schedule-shift').textContent = data.khung_gio || '-';
        document.getElementById('view-schedule-created').textContent = data.ngay_tao || '-';
        
        const statusElement = document.getElementById('view-schedule-status');
        if (statusElement) {
            statusElement.textContent = data.trang_thai || '-';
            statusElement.className = 'status-pill ' + (data.trang_thai === 'Đã Gửi' ? 'is-sent' : 'is-draft');
        }

        // Populate employee list
        const employeeList = document.getElementById('view-employee-list');
        employeeList.innerHTML = '';
        
        if (data.nhan_vien && data.nhan_vien.length > 0) {
            data.nhan_vien.forEach(employee => {
                const row = document.createElement('div');
                row.className = 'schedule-employee-item';
                
                const code = document.createElement('span');
                code.textContent = employee.ma_nv || '-';
                
                const name = document.createElement('span');
                name.textContent = employee.ten_nv || '-';
                
                const position = document.createElement('span');
                position.textContent = employee.vi_tri || '-';
                
                row.appendChild(code);
                row.appendChild(name);
                row.appendChild(position);
                
                employeeList.appendChild(row);
            });
        } else {
            const emptyRow = document.createElement('div');
            emptyRow.className = 'schedule-employee-item';
            emptyRow.innerHTML = '<span colspan="3" style="color: #666;">Chưa có nhân viên được phân công</span>';
            employeeList.appendChild(emptyRow);
        }
    }

    // Delete schedule via AJAX (Demo - confirm but don't remove)
    function deleteSchedule(scheduleId) {
        closeModal('confirm-delete-popup');
        
        // Demo: show success message but don't remove row
        showSuccessMessage('Xóa lịch làm việc thành công (Demo UI)');
        
        // KHÔNG xóa khỏi danh sách - giữ nguyên mock data
    }

    // Send notification via AJAX (Demo - show message only)
    function sendNotification() {
        const form = document.getElementById('notification-form');
        const formData = new FormData(form);
        
        // Check if any schedules are selected
        const selectedSchedules = formData.getAll('schedule_ids');
        if (selectedSchedules.length === 0) {
            showErrorMessage('Vui lòng chọn ít nhất một lịch làm việc để gửi thông báo');
            return;
        }

        // Demo: just show success message, don't update status
        closeModal('send-confirm-modal');
        
        // KHÔNG update trạng thái - giữ nguyên mock data
        // Reset select all checkbox
        if (selectAllSchedules) {
            selectAllSchedules.checked = false;
        }
        
        showSuccessMessage('Đã gửi thông báo thành công (Demo UI)');
    }

    // Helper functions
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showSuccessMessage(message) {
        showMessage(message, 'success');
    }

    function showErrorMessage(message) {
        showMessage(message, 'error');
    }

    function showMessage(message, type) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        
        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.style.cssText = 'padding: 10px; margin: 10px 0; border-radius: 5px; z-index: 9999; position: fixed; top: 20px; right: 20px; max-width: 400px;';
        
        if (type === 'error') {
            alertDiv.style.backgroundColor = '#f8d7da';
            alertDiv.style.color = '#721c24';
            alertDiv.style.border = '1px solid #f5c6cb';
        } else {
            alertDiv.style.backgroundColor = '#d4edda';
            alertDiv.style.color = '#155724';
            alertDiv.style.border = '1px solid #c3e6cb';
        }
        
        alertDiv.textContent = message;
        document.body.appendChild(alertDiv);
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            if (alertDiv) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Event listeners
    // Detail buttons
    document.querySelectorAll('.schedule-detail-btn').forEach(button => {
        button.addEventListener('click', function () {
            const scheduleId = this.dataset.scheduleId;
            loadScheduleDetail(scheduleId);
        });
    });

    // Delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function () {
            const scheduleId = this.dataset.deleteId;
            if (confirmDeleteBtn) {
                confirmDeleteBtn.onclick = function() {
                    deleteSchedule(scheduleId);
                };
            }
            showModal('confirm-delete-popup');
        });
    });

    // Send notification button
    if (sendNotificationBtn) {
        sendNotificationBtn.addEventListener('click', function () {
            showModal('send-confirm-modal');
        });
    }

    // Select all checkbox
    if (selectAllSchedules) {
        selectAllSchedules.addEventListener('change', function () {
            const checkboxes = document.querySelectorAll('.schedule-row-checkbox:not(:disabled)');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    // Individual checkboxes
    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            if (!selectAllSchedules) return;

            const enabledCheckboxes = document.querySelectorAll('.schedule-row-checkbox:not(:disabled)');
            const checkedCount = Array.from(enabledCheckboxes).filter(item => item.checked).length;
            
            selectAllSchedules.checked = checkedCount === enabledCheckboxes.length;
            selectAllSchedules.indeterminate = checkedCount > 0 && checkedCount < enabledCheckboxes.length;
        });
    });

    // Close modal when clicking outside
    [viewModal, sendConfirmModal, deleteModal].forEach(modal => {
        if (modal) {
            modal.addEventListener('click', function (event) {
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            });
        }
    });

    // Close modal buttons
    document.querySelectorAll('.schedule-modal-close').forEach(button => {
        button.addEventListener('click', function () {
            const modal = this.closest('.schedule-modal-overlay');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Handle send notification confirmation
    const confirmSendBtn = document.getElementById('confirm-send-btn');
    if (confirmSendBtn) {
        confirmSendBtn.addEventListener('click', sendNotification);
    }

    // Handle cancel buttons
    document.querySelectorAll('.schedule-cancel-btn').forEach(button => {
        button.addEventListener('click', function (e) {
            // Prevent default behavior and navigate properly
            e.preventDefault();
            const href = this.getAttribute('href');
            if (href) {
                window.location.href = href;
            }
        });
    });

    // Handle cancel buttons in modals
    document.querySelectorAll('.modal-cancel-btn').forEach(button => {
        button.addEventListener('click', function () {
            // Close the modal using data-modal attribute
            const modalId = this.getAttribute('data-modal');
            if (modalId) {
                closeModal(modalId);
            }
        });
    });
});
