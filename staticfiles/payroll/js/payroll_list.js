/**
 * GÉ CAFE - PAYROLL MANAGEMENT JS
 * Hợp nhất: Xử lý Modal, Tính lương, Lọc trạng thái và Thông báo
 */

// ================================================================
// 1. HELPER FUNCTIONS
// ================================================================
const PayrollHelpers = {
    getDropdownValue: function(id, selector) {
        const element = document.getElementById(id) || document.querySelector(selector);
        return element ? element.value : '';
    },

    getSelectedBranch: function() {
        let branchSelect = document.querySelector('select.branch-dropdown-ge[name="branch"]') ||
                           document.querySelector('select[name="branch"]') ||
                           document.querySelector('#branch');
        return branchSelect ? branchSelect.value : '';
    },

    // Hiển thị thông báo Toast (nếu cần gọi thủ công)
    showToast: function(message) {
        const toast = document.getElementById("toast-notification");
        const toastMsg = document.getElementById("toast-message");
        if (toast && toastMsg) {
            toastMsg.textContent = message;
            toast.classList.add("show");
            setTimeout(() => { toast.classList.remove("show"); }, 3000);
        }
    }
};

// ================================================================
// 2. KHỞI TẠO KHI LOAD TRANG (DOMContentLoaded)
// ================================================================
document.addEventListener('DOMContentLoaded', function() {
    console.log("GÉ CAFE - Payroll List Loaded");

    // --- Xử lý Bộ lọc trạng thái (Tab) ---
    const statusButtons = document.querySelectorAll('.btn-filter');
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            statusButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            const statusKey = this.getAttribute('data-status');
            filterPayrollByStatus(statusKey);
        });
    });

    // Mặc định lọc "Chờ duyệt" khi vừa vào trang
    filterPayrollByStatus('cho-duyet');

    // --- Xử lý Thông báo từ SessionStorage (Sau khi thêm/xóa/sửa thành công) ---
    const isSuccess = sessionStorage.getItem('payroll_success') === 'true';
    const isSaved = sessionStorage.getItem('payroll_saved') === '1';
    const action = sessionStorage.getItem('payroll_action') || 'unknown';

    if (isSuccess || isSaved) {
        let message = sessionStorage.getItem('payroll_success_message') || 'Thao tác thành công!';

        // Xử lý message theo action type
        if (action === 'add') {
            message = 'Thêm bảng lương thành công';
        } else if (action === 'edit') {
            message = 'Cập nhật bảng lương thành công';
        } else if (action === 'delete') {
            message = 'Xóa bảng lương thành công';
        } else if (action === 'approve') {
            message = 'Duyệt bảng lương thành công';
        } else if (action === 'reject') {
            message = 'Từ chối bảng lương thành công';
        }

        // 2. Hiện Toast Notification
        PayrollHelpers.showToast(message);

        // Dọn dẹp để không hiện lại khi F5
        sessionStorage.removeItem('payroll_success');
        sessionStorage.removeItem('payroll_success_message');
        sessionStorage.removeItem('payroll_saved');
        sessionStorage.removeItem('payroll_action');
    }
});

// ================================================================
// 3. LOGIC LỌC BẢNG (FILTER)
// ================================================================
function filterPayrollByStatus(statusKey) {
    const allRows = document.querySelectorAll('.ge-main-table tbody tr');
    const actionCols = document.querySelectorAll('.action-column');

    allRows.forEach(row => {
        const rowStatus = row.getAttribute('data-status');
        if (rowStatus) {
            row.style.display = (rowStatus === statusKey) ? '' : 'none';
        }
    });

    // Chỉ hiện cột Hành động (Sửa/Xóa) khi ở tab "Chờ duyệt"
    actionCols.forEach(col => {
        col.style.display = (statusKey === 'cho-duyet') ? '' : 'none';
    });

    // Hiện cụm nút Xuất báo cáo khi ở tab "Đã duyệt"
    const exportContainer = document.getElementById('export-approved-container');
    if (exportContainer) {
        exportContainer.style.display = (statusKey === 'da-duyet') ? 'block' : 'none';
    }
}

// ================================================================
// 4. QUY TRÌNH TÍNH LƯƠNG (MODAL & AJAX)
// ================================================================

// Mở modal chọn kỳ lương
function openSalaryModal() {
    const modal = document.getElementById('salaryModal');
    if (modal) {
        modal.classList.add('show');
    }
}

// Đóng modal chọn kỳ lương
function closeSalaryModal() {
    const modal = document.getElementById('salaryModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Khi người dùng bấm nút "Hiển thị" sau khi chọn Tháng/Năm
function handlePeriodChange() {
    showEmployees();
}

// Lấy danh sách nhân viên từ Server qua AJAX
function showEmployees(e) {
    if (e) e.preventDefault();

    const month = document.getElementById('salaryMonth').value;
    const year = document.getElementById('salaryYear').value;
    const branch = PayrollHelpers.getSelectedBranch();
    const tbody = document.getElementById('employeeTableBody');

    if (!month || !year) {
        alert('Vui lòng chọn cả Tháng và Năm');
        return;
    }

    if (!branch) {
        alert('Không tìm thấy thông tin chi nhánh!');
        return;
    }

    tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #666; padding: 20px;">Đang tải dữ liệu nhân viên...</td></tr>';

    const fullUrl = `/payroll/period-employees/?branch=${branch}&month=${month}&year=${year}`;

    fetch(fullUrl, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) throw new Error(data.error);

        const eligible = data.eligible_employees || [];
        const calculated = data.calculated_employees || [];

        if (!eligible.length && !calculated.length) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 20px;">Không có nhân viên có hợp đồng hiệu lực trong kỳ này.</td></tr>';
            return;
        }

        let html = '';
        // Nhân viên đã tính lương (Disabled)
        calculated.forEach(emp => {
            html += `<tr>
                <td><input type="checkbox" disabled></td>
                <td>${emp.ma_nv}</td>
                <td>${emp.ho_ten} <span style="color: #28a745;">(Đã tính lương)</span></td>
            </tr>`;
        });

        // Nhân viên chưa tính lương (Cho phép chọn)
        eligible.forEach(emp => {
            html += `<tr>
                <td><input type="checkbox" name="selected_employees" value="${emp.ma_nv}"></td>
                <td>${emp.ma_nv}</td>
                <td>${emp.ho_ten}</td>
            </tr>`;
        });

        tbody.innerHTML = html;
    })
    .catch(error => {
        tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: red; padding: 20px;">Lỗi: ${error.message}</td></tr>`;
    });
}

// Khi nhấn nút "Tính lương" cuối cùng trong modal
function startSalaryCalculationFlow() {
    const month = document.getElementById('salaryMonth').value;
    const year = document.getElementById('salaryYear').value;
    const branch = PayrollHelpers.getSelectedBranch();
    const checkboxes = document.querySelectorAll('input[name="selected_employees"]:checked');

    if (!month || !year) {
        alert('Vui lòng chọn kỳ lương');
        return;
    }

    if (checkboxes.length === 0) {
        alert('Vui lòng chọn ít nhất 1 nhân viên');
        return;
    }

    const employees = Array.from(checkboxes).map(cb => cb.value);

    // Chuyển hướng sang trang chi tiết để nhập số liệu (Django View xử lý)
    const url = `/payroll/add/?branch=${branch}&month=${month}&year=${year}&employees=${employees.join(',')}`;
    window.location.href = url;
}

// ================================================================
// 5. CÁC HÀM TIỆN ÍCH & EVENT KHÁC
// ================================================================

function toggleSelectAll(source) {
    const checkboxes = document.querySelectorAll('input[name="selected_employees"]');
    checkboxes.forEach(cb => cb.checked = source.checked);
}

function handleExportApproved() {
    const format = document.getElementById('export-format-select').value;
    alert('Tính năng xuất file ' + format.toUpperCase() + ' hiện đang được triển khai.');
}

// --- Popup Hủy ---
function openCancelConfirmPopup() {
    const popup = document.getElementById('confirm-cancel-payroll-popup');
    if (popup) popup.style.display = 'flex';
}

function closeCancelConfirmPopup() {
    const popup = document.getElementById('confirm-cancel-payroll-popup');
    if (popup) popup.style.display = 'none';
}

function confirmCancel() {
    closeCancelConfirmPopup();
    const detailModal = document.getElementById('salaryDetailModal');
    if (detailModal) {
        detailModal.classList.remove('show');
        detailModal.style.display = 'none';
    }
}

// --- Xử lý duyệt/từ chối bảng lương ---
function handlePayrollAction(event, form, action) {
    event.preventDefault();

    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Set thông báo thành công
            sessionStorage.setItem('payroll_success', 'true');
            sessionStorage.setItem('payroll_action', action);
            if (action === 'approve') {
                sessionStorage.setItem('payroll_success_message', 'Duyệt bảng lương thành công!');
            } else if (action === 'reject') {
                sessionStorage.setItem('payroll_success_message', 'Từ chối bảng lương thành công!');
            }
            // Reload trang
            window.location.reload();
        } else {
            alert('Thao tác thất bại: ' + (data.message || 'Lỗi không xác định'));
        }
    })
    .catch(error => {
        console.error('Lỗi khi duyệt/từ chối:', error);
        alert('Thao tác thất bại, vui lòng thử lại!');
    });
}

// --- Placeholder cho các nút Sửa/Xóa (Sẽ xử lý ở các view tương ứng) ---
function openEditPayrollModal(button) { console.log('Sửa bảng lương'); }
