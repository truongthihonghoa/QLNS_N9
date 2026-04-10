// Mở modal tính lương
function openSalaryModal() {
    console.log('Hàm openSalaryModal đã được gọi');
    const modal = document.getElementById('salaryModal');
    if (modal) {
        modal.style.display = 'flex';
        console.log('Đã mở Modal');
    } else {
        console.error('Không tìm thấy Modal');
    }
}

// Ẩn modal tính lương
function closeSalaryModal() {
    console.log('Hàm closeSalaryModal đã được gọi');
    const modal = document.getElementById('salaryModal');
    if (modal) {
        modal.style.display = 'none';
        console.log('Đã đóng Modal');
    }
}

// Xử lý khi thay đổi kỳ lương (tháng/năm)
function handlePeriodChange() {
    console.log('Hàm handlePeriodChange đã được gọi');
    showEmployees();
}

// Hiển thị danh sách nhân viên dựa trên kỳ lương và chi nhánh
function showEmployees(e) {
    console.log('Hàm showEmployees đã được gọi');
    if (e) e.preventDefault();

    // Lấy các phần tử dropdown trong modal
    const monthSelect = document.getElementById('salaryMonth') || document.querySelector('select[name="month"]');
    const yearSelect = document.getElementById('salaryYear') || document.querySelector('select[name="year"]');

    const month = monthSelect ? monthSelect.value : '';
    const year = yearSelect ? yearSelect.value : '';

    console.log('Giá trị Tháng:', month);
    console.log('Giá trị Năm:', year);

    const tbody = document.getElementById('employeeTableBody');

    // Lấy chi nhánh đang chọn từ dropdown chính (trên toolbar)
    let mainBranchSelect = document.querySelector('select.branch-dropdown-ge[name="branch"]');

    if (!mainBranchSelect) {
        mainBranchSelect = document.querySelector('select[name="branch"]');
    }

    if (!mainBranchSelect) {
        mainBranchSelect = document.querySelector('#branch');
    }

    let branch = mainBranchSelect ? mainBranchSelect.value : '';

    console.log('Chi nhánh đã chọn:', branch);

    if (!month || !year) {
        alert('Vui lòng chọn cả Tháng và Năm');
        return;
    }

    // Nếu không có chi nhánh được chọn, thử lấy chi nhánh mặc định
    if (!branch) {
        const firstOption = mainBranchSelect ? mainBranchSelect.querySelector('option[value]:not([value=""])') : null;
        if (firstOption) {
            branch = firstOption.value;
            console.log('Sử dụng chi nhánh mặc định:', branch);
        } else {
            alert('Không tìm thấy thông tin chi nhánh. Vui lòng kiểm tra lại.');
            return;
        }
    }

    // URL API lấy danh sách nhân viên
    const periodUrl = '/payroll/period-employees/';

    // Khởi tạo các tham số yêu cầu
    const qs = new URLSearchParams({ branch: branch, month: month, year: year });
    const fullUrl = periodUrl + '?' + qs.toString();

    console.log('Đang gọi URL:', fullUrl);

    // Hiển thị trạng thái đang tải
    tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #666; padding: 20px;">Đang tải dữ liệu nhân viên...</td></tr>';

    fetch(fullUrl, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
        .then(res => {
            if (!res.ok) {
                throw new Error(`Lỗi hệ thống (${res.status}): ${res.statusText}`);
            }
            return res.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            const eligible = Array.isArray(data.eligible_employees) ? data.eligible_employees : [];
            const calculated = Array.isArray(data.calculated_employees) ? data.calculated_employees : [];

            if (!eligible.length && !calculated.length) {
                tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #666; padding: 20px;">Không có nhân viên nào có hợp đồng còn hiệu lực trong kỳ này</td></tr>';
                return;
            }

            // Xây dựng danh sách hiển thị
            let html = '';

            // Nhóm nhân viên đã tính lương (vô hiệu hóa checkbox)
            calculated.forEach(emp => {
                html += `<tr>
                            <td><input type="checkbox" disabled data-ma-nv="${emp.ma_nv}"></td>
                            <td>${emp.ma_nv}</td>
                            <td>${emp.ho_ten} <span style="color: #28a745;">(Đã tính lương)</span></td>
                         </tr>`;
            });

            // Nhóm nhân viên chưa tính lương
            eligible.forEach(emp => {
                html += `<tr>
                            <td><input type="checkbox" name="selected_employees" value="${emp.ma_nv}" data-ma-nv="${emp.ma_nv}"></td>
                            <td>${emp.ma_nv}</td>
                            <td>${emp.ho_ten}</td>
                         </tr>`;
            });

            tbody.innerHTML = html;
            console.log('Đã cập nhật danh sách nhân viên thành công');
        })
        .catch(error => {
            console.error('Lỗi AJAX:', error);
            tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: red; padding: 20px;">Lỗi khi tải dữ liệu: ${error.message}</td></tr>`;
        });
}

// Bắt đầu quy trình tính lương (khi nhấn nút Bắt đầu)
function startSalaryCalculationFlow() {
    console.log('Bắt đầu quy trình tính lương');
    processCalculation();
}

// Xử lý tính lương cho các nhân viên đã chọn
function processCalculation(e) {
    if (e) e.preventDefault();

    const monthSelect = document.getElementById('salaryMonth') || document.querySelector('select[name="month"]');
    const yearSelect = document.getElementById('salaryYear') || document.querySelector('select[name="year"]');

    const month = monthSelect ? monthSelect.value : '';
    const year = yearSelect ? yearSelect.value : '';

    if (!month || !year) {
        alert('Vui lòng chọn kỳ lương (Tháng và Năm)');
        return;
    }

    // Lấy danh sách nhân viên đã được tích chọn
    const checkboxes = document.querySelectorAll('input[name="selected_employees"]:checked');
    if (checkboxes.length === 0) {
        alert('Vui lòng chọn ít nhất một nhân viên để tính lương');
        return;
    }

    const selectedEmployees = [];
    checkboxes.forEach(checkbox => {
        selectedEmployees.push(checkbox.value);
    });

    console.log('Các mã nhân viên đã chọn:', selectedEmployees);

    // Mở modal chi tiết cho nhân viên đầu tiên trong danh sách chọn
    showEmployeeDetail(selectedEmployees[0], month, year);
}

// Hiển thị modal nhập chi tiết lương cho từng nhân viên
function showEmployeeDetail(employeeId, month, year) {
    console.log('Đang hiển thị chi tiết cho mã NV:', employeeId);

    const modal = document.getElementById('salaryDetailModal');
    if (modal) {
        modal.style.display = 'flex';

        // Cập nhật thông tin tiêu đề trong modal chi tiết
        document.getElementById('display-nv-info').textContent = 'Mã nhân viên: ' + employeeId;
        document.getElementById('display-month-info').textContent = 'Kỳ lương: ' + month + '/' + year;

        // Đặt lại (reset) giá trị các ô nhập liệu
        document.getElementById('detail-lcb').value = '';
        document.getElementById('detail-ltg').value = '';
        document.getElementById('detail-thuong').value = '0';
        document.getElementById('detail-phat').value = '0';
        document.getElementById('detail-tong-luong').textContent = '0 VNĐ';

        console.log('Đã mở modal chi tiết lương');
    }
}

// Tự động tính lại tổng lương khi người dùng nhập dữ liệu
function recalculateTotal() {
    const lcb = parseFloat(document.getElementById('detail-lcb').value) || 0;
    const ltg = parseFloat(document.getElementById('detail-ltg').value) || 0;
    const thuong = parseFloat(document.getElementById('detail-thuong').value) || 0;
    const phat = parseFloat(document.getElementById('detail-phat').value) || 0;

    const total = lcb + ltg + thuong - phat;
    document.getElementById('detail-tong-luong').textContent = total.toLocaleString('vi-VN') + ' VNĐ';
}

// Lưu dữ liệu chi tiết lương vào cơ sở dữ liệu
function saveSalaryDetailDb() {
    console.log('Đang thực hiện lưu dữ liệu...');
    // Sau khi xử lý API lưu xong:
    alert('Dữ liệu lương đã được lưu thành công!');
}

// Mở popup xác nhận trước khi hủy bỏ nhập liệu
function openCancelConfirmPopup() {
    const popup = document.getElementById('confirm-cancel-payroll-popup');
    if (popup) {
        popup.style.display = 'flex';
    }
}

// Đóng popup xác nhận hủy
function closeCancelConfirmPopup() {
    const popup = document.getElementById('confirm-cancel-payroll-popup');
    if (popup) {
        popup.style.display = 'none';
    }
}

// Xác nhận hủy bỏ và đóng modal chi tiết
function confirmCancel() {
    console.log('Người dùng đã xác nhận hủy');
    closeCancelConfirmPopup();
    const detailModal = document.getElementById('salaryDetailModal');
    if (detailModal) {
        detailModal.style.display = 'none';
    }
}

// Chọn hoặc bỏ chọn tất cả nhân viên trong danh sách
function toggleSelectAll(source) {
    console.log('Thay đổi trạng thái chọn tất cả:', source.checked);
    const checkboxes = document.querySelectorAll('input[name="selected_employees"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = source.checked;
    });
}

// Mở popup xác nhận xóa bảng lương
function openDeletePayrollPopup(button) {
    console.log('Yêu cầu xóa bảng lương');
    // Logic hiển thị popup xác nhận xóa sẽ được thêm ở đây
}

// Đóng popup xác nhận xóa
function closeDeletePayrollPopup() {
    console.log('Đã đóng popup xóa');
}

// Thực hiện lệnh xóa bảng lương sau khi xác nhận
function confirmDeletePayroll() {
    console.log('Đã xác nhận thực hiện xóa');
}

// Mở modal để chỉnh sửa bảng lương đã tồn tại
function openEditPayrollModal(button) {
    console.log('Đang mở modal chỉnh sửa bảng lương');
}

// Xử lý yêu cầu xuất file (PDF/Excel)
function handleExportApproved() {
    const format = document.getElementById('export-format-select').value;
    console.log('Yêu cầu xuất định dạng:', format);
    alert('Tính năng xuất file định dạng ' + format.toUpperCase() + ' hiện đang được triển khai.');
}