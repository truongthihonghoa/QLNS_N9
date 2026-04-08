/* Biến toàn cục để quản lý danh sách nhân viên đang được tính lương */
let selectedEmployees = [];
let currentProcessingIndex = 0;
let editingRow = null; // Biến lưu trữ hàng đang được chỉnh sửa

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

/**
 * Logic Lọc bảng lương theo Tab
 */
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.btn-filter');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            const filterText = this.innerText.trim();
            let statusKey = 'cho-duyet';
            if (filterText === 'Đã duyệt') statusKey = 'da-duyet';
            if (filterText === 'Đã từ chối') statusKey = 'da-tu-choi';

            applyFilter(statusKey);
        });
    });

    // Mặc định lọc "Chờ duyệt" khi tải trang
    applyFilter('cho-duyet');
});

// --- LOGIC XÓA BẢNG LƯƠNG ---
let currentDeleteUrl = ''; // Lưu URL xóa hiện tại

function openDeletePayrollPopup(btnOrPayrollId) {
    let payrollId = '';
    let empName = '';
    let deleteUrl = '';
    let status = '';

    if (typeof btnOrPayrollId === 'string') {
        payrollId = btnOrPayrollId;
        const row = document.querySelector(`tr[data-ma-luong="${payrollId}"]`);
        empName = row ? (row.cells[2]?.innerText || '') : '';
        deleteUrl = `/payroll/delete/${payrollId}/`;
        status = row ? row.getAttribute('data-status') : '';
    } else if (btnOrPayrollId && btnOrPayrollId.dataset) {
        payrollId = btnOrPayrollId.dataset.payrollId || '';
        empName = btnOrPayrollId.dataset.empName || '';
        deleteUrl = btnOrPayrollId.dataset.deleteUrl || '';
        const row = document.querySelector(`tr[data-ma-luong="${payrollId}"]`);
        status = row ? row.getAttribute('data-status') : '';
    }

    // ✅ CHECK ĐIỀU KIỆN: Chỉ cho phép xóa khi trạng thái là "cho-duyet"
    if (status !== 'cho-duyet') {
        showPayrollToast('❌ Chỉ được xóa bảng lương ở trạng thái "Đang chờ duyệt"!');
        return;
    }

    if (!deleteUrl || !payrollId) {
        return;
    }

    const popup = document.getElementById('confirm-delete-payroll-popup');
    const infoDisplay = document.getElementById('delete-payroll-info');
    const cancelBtn = document.getElementById('delete-payroll-cancel-btn');
    const confirmBtn = document.getElementById('delete-payroll-confirm-btn');

    if (!popup || !infoDisplay || !cancelBtn || !confirmBtn) {
        return;
    }

    infoDisplay.textContent = empName ? `${payrollId} - ${empName}` : payrollId;
    currentDeleteUrl = deleteUrl; // Lưu URL để dùng khi xác nhận

    popup.style.display = 'flex';
    popup.setAttribute('aria-hidden', 'false');

    cancelBtn.onclick = function () {
        closeDeletePayrollPopup();
    };

    confirmBtn.onclick = function () {
        confirmDeletePayroll(payrollId);
    };

    popup.onclick = function (e) {
        if (e.target === popup) {
            closeDeletePayrollPopup();
        }
    };
}

function closeDeletePayrollPopup() {
    const popup = document.getElementById('confirm-delete-payroll-popup');
    if (popup) {
        popup.style.display = 'none';
        popup.setAttribute('aria-hidden', 'true');
    }
    currentDeleteUrl = '';
}

function confirmDeletePayroll(payrollId) {
    if (!currentDeleteUrl) {
        showPayrollToast('Không có URL xóa bảng lương');
        return;
    }

    const csrfToken = getCookie('csrftoken');
    fetch(currentDeleteUrl, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken || '',
        },
    })
    .then(res => {
        if (res.redirected) {
            window.location.href = res.url;
            return;
        }
        return res.ok ? res.json() : Promise.reject(new Error('Delete failed'));
    })
    .then((data) => {
        // Xóa hàng từ bảng
        const row = document.querySelector(`tr[data-ma-luong="${payrollId}"]`);
        if (row) {
            row.remove();
            // Cập nhật lại số thứ tự
            const tbody = document.querySelector('.ge-main-table tbody');
            Array.from(tbody.rows).forEach((r, index) => {
                if (r.cells.length > 1) r.cells[0].innerText = index + 1;
            });
        }
        showPayrollToast('Xóa bảng lương thành công');
        closeDeletePayrollPopup();
    })
    .catch(() => {
        showPayrollToast('Không thể xóa bảng lương');
    });
}

// --- LOGIC XÁC NHẬN HỦY ---
function openCancelConfirmPopup() {
    const popup = document.getElementById('confirm-cancel-payroll-popup');
    if (popup) popup.style.display = 'flex';
}

function closeCancelConfirmPopup() {
    const popup = document.getElementById('confirm-cancel-payroll-popup');
    if (popup) popup.style.display = 'none';
}

function confirmCancel() {
    closeCancelConfirmPopup(); // Đóng popup xác nhận
    closeDetailModal();        // Đóng modal tính lương chính
}


/**
 * Mở Modal Chỉnh sửa và đổ dữ liệu từ hàng vào Form
 */
function openEditPayrollModal(btn) {
    const row = btn.closest('tr');

    // ✅ CHECK ĐIỀU KIỆN: Chỉ cho phép chỉnh sửa khi trạng thái là "cho-duyet"
    const status = row.getAttribute('data-status');
    if (status !== 'cho-duyet') {
        showPayrollToast('❌ Chỉ được chỉnh sửa bảng lương ở trạng thái "Đang chờ duyệt"!');
        return;
    }

    editingRow = row; // Lưu lại hàng đang chọn để sửa
    const maNV = row.getAttribute('data-ma-nv') || "";

    // Lấy dữ liệu từ các ô (Cell) của hàng
    const maLuong = row.cells[1].innerText;
    const tenNV = row.cells[2].innerText;
    const kyLuong = row.cells[3].innerText;
    const lcb = row.cells[4].innerText;
    const ltg = row.cells[5].innerText;
    const sgl = row.cells[6].innerText;
    const thuong = row.cells[7].innerText;
    const phat = row.cells[8].innerText;

    // Đổ dữ liệu vào Modal chi tiết
    document.getElementById('display-ma-luong').innerText = `Mã lương: ${maLuong}`;
    document.getElementById('display-nv-info').innerText = `Mã NV: ${maNV} - ${tenNV}`;
    document.getElementById('display-month-info').innerText = `Tháng: ${kyLuong}`;

    // Làm sạch dữ liệu tiền tệ: "1.234.567" -> "1234567"
    const cleanMoney = (str) => (str || '').replace(/[^0-9.-]/g, '');
    const cleanNumber = (str) => (str || '').replace(/[^0-9.]/g, '');

    document.getElementById('detail-lcb').value = cleanMoney(lcb);
    document.getElementById('detail-ltg').value = cleanMoney(ltg);
    document.getElementById('detail-sgl').value = cleanNumber(sgl);
    document.getElementById('detail-thuong').value = cleanMoney(thuong);
    document.getElementById('detail-phat').value = cleanMoney(phat);

    // Đổi tiêu đề Modal để người dùng biết là đang sửa
    document.querySelector('#salaryDetailModal .detail-title').innerText = "Chỉnh sửa lương";
    recalculateTotal();

    document.getElementById('salaryDetailModal').style.display = 'flex';
}

function applyFilter(statusKey) {
    const rows = document.querySelectorAll('.ge-main-table tbody tr');
    const actionHeader = document.querySelector('.ge-main-table thead th:last-child');

    // Xác định xem có nên ẩn cột hành động hay không (Ẩn ở tab Đã duyệt và Đã từ chối)
    const shouldHideAction = (statusKey === 'da-duyet' || statusKey === 'da-tu-choi');

    // Ẩn/Hiện tiêu đề cột "Hành động"
    if (actionHeader) {
        actionHeader.style.display = shouldHideAction ? 'none' : '';
    }

    // Ẩn/Hiện khu vực nút Xuất (Chỉ hiện khi statusKey là 'da-duyet')
    const exportContainer = document.getElementById('export-approved-container');
    if (exportContainer) {
        exportContainer.style.display = (statusKey === 'da-duyet') ? 'flex' : 'none';
    }

    rows.forEach(row => {
        if (row.cells.length === 1) return; // Bỏ qua dòng "Không có dữ liệu"
        const isMatch = row.getAttribute('data-status') === statusKey;
        row.style.display = isMatch ? '' : 'none';

        // Ẩn/Hiện ô nội dung hành động tương ứng trong hàng
        const actionCell = row.cells[row.cells.length - 1];
        if (actionCell) {
            actionCell.style.display = shouldHideAction ? 'none' : '';
        }
    });
}

/**
 * Xử lý hành động xuất file
 */
function handleExportApproved() {
    const format = document.getElementById('export-format-select').value;
    showPayrollToast(`Xuất bảng lương thành công ${format.toUpperCase()}`);
}

// Status updates are handled via server-side form POST now (no JS).

/**
 * Điều khiển đóng/mở Modal chính
 */
function openSalaryModal() {
    const modal = document.getElementById('salaryModal');
    if (modal) modal.style.display = 'flex';
}

function closeSalaryModal() {
    document.getElementById('salaryModal').style.display = 'none';
}

/**
 * Xử lý khi chọn tháng ở Modal 1
 */
function handlePeriodChange() {
    const month = document.getElementById('salaryMonth').value;
    const year = document.getElementById('salaryYear').value;
    const btnConfirm = document.getElementById('btnConfirmCalculate');
    const warning = document.getElementById('processedWarning');

    if (month && year) {
        btnConfirm.disabled = false;
        if (warning) {
            warning.style.display = 'none';
            warning.textContent = '⚠️ Kỳ lương này đã được tính.';
        }

        const tbody = document.getElementById('employeeTableBody');
        const branchSelect = document.querySelector('select.branch-dropdown-ge[name="branch"]');
        const branch = branchSelect ? branchSelect.value : '';

        const periodUrlEl = document.getElementById('payroll-period-employees-url');
        let periodUrl = '';
        if (periodUrlEl) {
            try {
                periodUrl = JSON.parse(periodUrlEl.textContent || '""');
            } catch (e) {
                periodUrl = '';
            }
        }

        if (!tbody || !periodUrl || !branch) {
            btnConfirm.disabled = true;
            return;
        }

        // Load eligible employees from server (exclude already-calculated employees for this period)
        const qs = new URLSearchParams({ branch: branch, month: month, year: year });

        fetch(`${periodUrl}?${qs.toString()}`, { method: 'GET' })
            .then(res => res.ok ? res.json() : Promise.reject())
            .then(data => {
                const eligible = Array.isArray(data.eligible_employees) ? data.eligible_employees : [];
                const calculated = Array.isArray(data.calculated_employees) ? data.calculated_employees : [];

                if (warning) {
                    if (calculated.length > 0) {
                        const names = calculated.map(e => e.ho_ten).join(', ');
                        warning.style.display = 'block';
                        warning.textContent = `⚠️ Kỳ lương này đã được tính cho: ${names}`;
                    } else {
                        warning.style.display = 'none';
                    }
                }

                if (!eligible.length) {
                    btnConfirm.disabled = true;
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="3" style="text-align: center; color: #666; padding: 20px;">
                                Không còn nhân viên nào chưa được tính lương cho kỳ này
                            </td>
                        </tr>
                    `;
                    return;
                }

                tbody.innerHTML = eligible.map(emp => `
                    <tr>
                        <td><input type="checkbox" data-ma-nv="${emp.ma_nv}"></td>
                        <td>${emp.ma_nv}</td>
                        <td>${emp.ho_ten}</td>
                    </tr>
                `).join('');
            })
            .catch(() => {
                // Fallback: show employees from embedded branch list if endpoint fails
                const jsonEl = document.getElementById('branch-employees');
                let employees = [];
                if (jsonEl) {
                    try {
                        employees = JSON.parse(jsonEl.textContent || '[]');
                    } catch (e) {
                        employees = [];
                    }
                }

                if (!employees.length) {
                    btnConfirm.disabled = true;
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="3" style="text-align: center; color: #666; padding: 20px;">
                                Không có nhân viên thuộc chi nhánh đang chọn
                            </td>
                        </tr>
                    `;
                    return;
                }

                tbody.innerHTML = employees.map(emp => `
                    <tr>
                        <td><input type="checkbox" data-ma-nv="${emp.ma_nv}"></td>
                        <td>${emp.ma_nv}</td>
                        <td>${emp.ho_ten}</td>
                    </tr>
                `).join('');
            });
    } else {
        btnConfirm.disabled = true;
        const tbody = document.getElementById('employeeTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="3" style="text-align: center; color: #666; padding: 20px;">
                        Vui lòng chọn kỳ lương để hiển thị danh sách
                    </td>
                </tr>
            `;
        }
        if (warning) {
            warning.style.display = 'none';
        }
    }
}

function toggleSelectAll(source) {
    const checkboxes = document.querySelectorAll('#employeeTableBody input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = source.checked);
}

/**
 * Lưu thông tin lương chi tiết và cập nhật bảng danh sách
 */
function saveSalaryDetail() {
    // 1. Lấy dữ liệu từ Form (sử dụng các ID đã định nghĩa trong HTML)
    const maLuong = document.getElementById('display-ma-luong').innerText.replace('Mã lương: ', '').trim();
    const nvInfo = document.getElementById('display-nv-info').innerText;
    const kyLuong = document.getElementById('display-month-info').innerText.replace('Tháng: ', '').trim();
    const infoParts = nvInfo.split(' - ');

    // Tách Mã NV và Tên NV an toàn (Tránh crash nếu không có dấu " - ")
    const maNV = infoParts[0].replace('Mã NV: ', '').replace('Nhân viên: ', '').trim();
    const hoTen = infoParts.length > 1 ? infoParts[1].trim() : infoParts[0].replace('Nhân viên: ', '').trim();

    const lcb = document.getElementById('detail-lcb').value || "0";
    const ltg = document.getElementById('detail-ltg').value || "0";
    const sgl = document.getElementById('detail-sgl').value;
    const scl = document.getElementById('detail-scl') ? document.getElementById('detail-scl').value : "0";
    const thuong = document.getElementById('detail-thuong').value || "0";
    const phat = document.getElementById('detail-phat').value || "0";
    const tongLuong = document.getElementById('detail-tong-luong').innerText;

    // Extract month/year from "MM/YYYY"
    let month = "";
    let year = "";
    if (kyLuong.includes('/')) {
        const parts = kyLuong.split('/');
        month = (parts[0] || '').trim();
        year = (parts[1] || '').trim();
    }

    // Selected branch from top dropdown (used to persist Luong.chi_nhanh)
    const branchSelect = document.querySelector('select.branch-dropdown-ge[name="branch"]');
    const selectedBranch = branchSelect ? branchSelect.value : "";

    // Save to DB first
    const saveUrlEl = document.getElementById('payroll-save-url');
    let saveUrl = "";
    if (saveUrlEl) {
        try { saveUrl = JSON.parse(saveUrlEl.textContent || '""'); } catch (e) { saveUrl = ""; }
    }
    if (!saveUrl) {
        showPayrollToast("Không thể lưu bảng lương vào CSDL");
        return;
    }

    const formData = new FormData();
    // On update, maLuong is the primary key. For new rows, server will generate one.
    if (editingRow) {
        formData.append('ma_luong', maLuong);
    }
    formData.append('ma_nv', maNV);
    formData.append('branch', selectedBranch);
    formData.append('month', month);
    formData.append('year', year);
    formData.append('luong_co_ban', lcb);
    formData.append('luong_theo_gio', ltg);
    formData.append('so_gio_lam', sgl);
    formData.append('so_ca_lam', scl);
    formData.append('thuong', thuong);
    formData.append('phat', phat);
    formData.append('tong_luong', tongLuong);

    const csrfToken = getCookie('csrftoken');
    fetch(saveUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        },
    })
    .then(res => res.ok ? res.json() : Promise.reject())
    .then(saved => {
        // Update UI based on saved payload (DB truth)
        const savedMaLuong = saved.ma_luong;
        const savedKyLuong = saved.ky_luong;
        const savedLcb = saved.luong_co_ban;
        const savedLtg = saved.luong_theo_gio;
        const savedSgl = String(saved.so_gio_lam ?? sgl);
        const savedThuong = saved.thuong;
        const savedPhat = saved.phat;
        const savedTong = saved.tong_luong;

        if (editingRow) {
            editingRow.cells[1].innerText = savedMaLuong;
            editingRow.cells[3].innerText = savedKyLuong;
            editingRow.cells[4].innerText = savedLcb;
            editingRow.cells[5].innerText = savedLtg;
            editingRow.cells[6].innerText = savedSgl;
            editingRow.cells[7].innerText = savedThuong;
            editingRow.cells[8].innerText = savedPhat;
            editingRow.cells[9].innerHTML = `<strong>${savedTong}</strong>`;

            showPayrollToast("Cập nhật bảng lương thành công");
            closeDetailModal();

            editingRow = null;
            return;
        }

        // Insert new row into UI so user can continue multi-employee flow without reload.
        const tbody = document.querySelector('.ge-main-table tbody');
        if (tbody.rows.length === 1 && tbody.rows[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        const statusActionHtml = `
            <div class="status-badge cho-duyet">
                <form method="post" action="/payroll/status/${savedMaLuong}/" style="display:inline;">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken') || ''}">
                    <input type="hidden" name="status" value="da_duyet">
                    <input type="hidden" name="next" value="${window.location.pathname + window.location.search}">
                    <button class="btn-action-ge btn-approve-ge" type="submit" title="Duyệt"><i class="fas fa-check"></i></button>
                </form>
                <form method="post" action="/payroll/status/${savedMaLuong}/" style="display:inline;">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken') || ''}">
                    <input type="hidden" name="status" value="da_tu_choi">
                    <input type="hidden" name="next" value="${window.location.pathname + window.location.search}">
                    <button class="btn-action-ge btn-reject-ge" type="submit" title="Từ chối"><i class="fas fa-times"></i></button>
                </form>
            </div>
        `;

        const deleteFormHtml = `
            <form method="post" action="/payroll/delete/${savedMaLuong}/" style="display:inline;" onsubmit="return confirm('Bạn có chắc muốn xóa bảng lương ${savedMaLuong}?');">
                <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken') || ''}">
                <input type="hidden" name="next" value="${window.location.pathname + window.location.search}">
                <button type="submit" class="btn-action-ge btn-delete-ge" title="Xóa"><i class="fas fa-trash-alt"></i></button>
            </form>
        `;

        const newRow = document.createElement('tr');
        newRow.className = 'new-row-highlight';
        newRow.setAttribute('data-ma-luong', savedMaLuong);
        newRow.setAttribute('data-ma-nv', maNV);
        newRow.setAttribute('data-status', 'cho-duyet');

        newRow.innerHTML = `
            <td>1</td>
            <td>${savedMaLuong}</td>
            <td>${hoTen}</td>
            <td>${savedKyLuong}</td>
            <td>${savedLcb}</td>
            <td>${savedLtg}</td>
            <td>${savedSgl}</td>
            <td>${savedThuong}</td>
            <td>${savedPhat}</td>
            <td><strong>${savedTong}</strong></td>
            <td>${statusActionHtml}</td>
            <td>
                <div class="action-buttons">
                    <button type="button" class="btn-action-ge btn-edit-ge" title="Sửa" onclick="openEditPayrollModal(this)"><i class="fas fa-pen"></i></button>
                    ${deleteFormHtml}
                </div>
            </td>
        `;

        tbody.insertBefore(newRow, tbody.firstChild);
        Array.from(tbody.rows).forEach((row, index) => {
            if (row.cells.length > 1) row.cells[0].innerText = index + 1;
        });

        // Continue workflow
        currentProcessingIndex++;
        if (currentProcessingIndex < selectedEmployees.length) {
            showEmployeeDetail(currentProcessingIndex);
        } else {
            closeDetailModal();
            showPayrollToast("Thêm bảng lương thành công");
        }
    })
    .catch(() => {
        showPayrollToast("Không thể lưu bảng lương vào CSDL");
    });

    return;

    // UI updates are handled after successful DB save above.
}

// DB-backed save for salary detail modal (used by the UI button).
function saveSalaryDetailDb() {
    const maLuongRaw = (document.getElementById('display-ma-luong')?.innerText || '').trim();
    const nvInfoRaw = (document.getElementById('display-nv-info')?.innerText || '').trim();
    const monthInfoRaw = (document.getElementById('display-month-info')?.innerText || '').trim();

    const maLuong = (maLuongRaw.includes(':') ? maLuongRaw.split(':').slice(1).join(':') : maLuongRaw).trim();
    const kyLuong = (monthInfoRaw.includes(':') ? monthInfoRaw.split(':').slice(1).join(':') : monthInfoRaw).trim();

    let maNV = '';
    let hoTen = '';
    if (nvInfoRaw.includes(':')) {
        const afterColon = nvInfoRaw.split(':').slice(1).join(':').trim();
        const parts = afterColon.split(' - ');
        maNV = (parts[0] || '').trim();
        hoTen = (parts.slice(1).join(' - ') || '').trim();
    } else {
        const parts = nvInfoRaw.split(' - ');
        maNV = (parts[0] || '').trim();
        hoTen = (parts.slice(1).join(' - ') || '').trim();
    }

    let month = '';
    let year = '';
    if (kyLuong.includes('/')) {
        const parts = kyLuong.split('/');
        month = (parts[0] || '').trim();
        year = (parts[1] || '').trim();
    }

    // Lấy giá trị từ input fields
    const lcb = document.getElementById('detail-lcb')?.value || '0';
    const ltg = document.getElementById('detail-ltg')?.value || '0';
    const sgl = document.getElementById('detail-sgl')?.value || '0';
    const scl = document.getElementById('detail-scl')?.value || '0';
    const thuong = document.getElementById('detail-thuong')?.value || '0';
    const phat = document.getElementById('detail-phat')?.value || '0';

    // Tính tổng lương từ các giá trị (dọn sạch số)
    const parseMoney = (id) => {
    const val = document.getElementById(id).value || '0';return parseInt(val.replace(/\./g, '').replace(/[^0-9-]/g, '')) || 0;};
    const parseSgl = (str) => parseFloat((str || '0').replace(/[^0-9.-]/g, '')) || 0;
    const totalCalc = (parseMoney(ltg) * parseSgl(sgl)) + parseMoney(lcb) + parseMoney(thuong) - parseMoney(phat);

    const branchSelect = document.querySelector('select.branch-dropdown-ge[name="branch"]');
    const selectedBranch = branchSelect ? branchSelect.value : '';

    const saveUrlEl = document.getElementById('payroll-save-url');
    let saveUrl = '';
    if (saveUrlEl) {
        try { saveUrl = JSON.parse(saveUrlEl.textContent || '""'); } catch (e) { saveUrl = ''; }
    }
    if (!saveUrl) {
        showPayrollToast('Không thể lưu bảng lương vào CSDL');
        return;
    }

    const formData = new FormData();
    if (editingRow) {
        formData.append('ma_luong', maLuong);
    }
    formData.append('ma_nv', maNV);
    formData.append('branch', selectedBranch);
    formData.append('month', month);
    formData.append('year', year);
    formData.append('luong_co_ban', lcb);
    formData.append('luong_theo_gio', ltg);
    formData.append('so_gio_lam', sgl);
    formData.append('so_ca_lam', scl);
    formData.append('thuong', thuong);
    formData.append('phat', phat);
    formData.append('tong_luong', totalCalc.toString());

    const csrfToken = getCookie('csrftoken');
    fetch(saveUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        },
    })
        .then(async (res) => {
            if (!res.ok) {
                let msg = 'Không thể lưu bảng lương vào CSDL';
                try {
                    const err = await res.json();
                    if (err && err.error) {
                        if (err.error === 'not_editable') {
                            msg = 'Bảng lương này không ở trạng thái chờ duyệt, không thể sửa!';
                        } else {
                            msg = msg + ` (${err.error})`;
                        }
                    }
                } catch (e) {}
                throw new Error(msg);
            }
            return res.json();
        })
        .then((saved) => {
            const savedMaLuong = saved.ma_luong;
            const savedKyLuong = saved.ky_luong;
            const savedLcb = saved.luong_co_ban;
            const savedLtg = saved.luong_theo_gio;
            const savedSgl = String(saved.so_gio_lam ?? sgl);
            const savedThuong = saved.thuong;
            const savedPhat = saved.phat;
            const savedTong = saved.tong_luong;

            if (editingRow) {
                editingRow.cells[1].innerText = savedMaLuong;
                editingRow.cells[3].innerText = savedKyLuong;
                editingRow.cells[4].innerText = savedLcb;
                editingRow.cells[5].innerText = savedLtg;
                editingRow.cells[6].innerText = savedSgl;
                editingRow.cells[7].innerText = savedThuong;
                editingRow.cells[8].innerText = savedPhat;
                editingRow.cells[9].innerHTML = `<strong>${savedTong}</strong>`;

                showPayrollToast('Cập nhật bảng lương thành công');
                closeDetailModal();
                editingRow = null;
                return;
            }

            // Insert new row into UI so user can continue multi-employee flow without reload.
            const tbody = document.querySelector('.ge-main-table tbody');
            if (tbody.rows.length === 1 && tbody.rows[0].cells.length === 1) {
                tbody.innerHTML = '';
            }

            const csrf = getCookie('csrftoken') || '';
            const statusActionHtml = `
                <div class="status-badge cho-duyet">
                    <form method="post" action="/payroll/status/${savedMaLuong}/" style="display:inline;">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
                        <input type="hidden" name="status" value="da_duyet">
                        <input type="hidden" name="next" value="${window.location.pathname + window.location.search}">
                        <button class="btn-action-ge btn-approve-ge" type="submit" title="Duyệt"><i class="fas fa-check"></i></button>
                    </form>
                    <form method="post" action="/payroll/status/${savedMaLuong}/" style="display:inline;">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
                        <input type="hidden" name="status" value="da_tu_choi">
                        <input type="hidden" name="next" value="${window.location.pathname + window.location.search}">
                        <button class="btn-action-ge btn-reject-ge" type="submit" title="Từ chối"><i class="fas fa-times"></i></button>
                    </form>
                </div>
            `;

            const deleteBtnHtml = `
                <button
                    type="button"
                    class="btn-action-ge btn-delete-ge"
                    title="Xóa"
                    data-payroll-id="${savedMaLuong}"
                    data-emp-name="${hoTen}"
                    data-delete-url="/payroll/delete/${savedMaLuong}/"
                    onclick="openDeletePayrollPopup(this)"
                ><i class="fas fa-trash-alt"></i></button>
            `;

            const newRow = document.createElement('tr');
            newRow.className = 'new-row-highlight';
            newRow.setAttribute('data-ma-luong', savedMaLuong);
            newRow.setAttribute('data-ma-nv', maNV);
            newRow.setAttribute('data-status', 'cho-duyet');

            newRow.innerHTML = `
                <td>1</td>
                <td>${savedMaLuong}</td>
                <td>${hoTen}</td>
                <td>${savedKyLuong}</td>
                <td>${savedLcb}</td>
                <td>${savedLtg}</td>
                <td>${savedSgl}</td>
                <td>${savedThuong}</td>
                <td>${savedPhat}</td>
                <td><strong>${savedTong}</strong></td>
                <td>${statusActionHtml}</td>
                <td>
                    <div class="action-buttons">
                        <button type="button" class="btn-action-ge btn-edit-ge" title="Sửa" onclick="openEditPayrollModal(this)"><i class="fas fa-pen"></i></button>
                        ${deleteBtnHtml}
                    </div>
                </td>
            `;

            tbody.insertBefore(newRow, tbody.firstChild);
            Array.from(tbody.rows).forEach((row, index) => {
                if (row.cells.length > 1) row.cells[0].innerText = index + 1;
            });

            currentProcessingIndex++;
            if (currentProcessingIndex < selectedEmployees.length) {
                showEmployeeDetail(currentProcessingIndex);
            } else {
                closeDetailModal();
                showPayrollToast('Thêm bảng lương thành công');
            }
        })
        .catch((err) => {
            showPayrollToast(err && err.message ? err.message : 'Không thể lưu bảng lương vào CSDL');
        });
}

/**
 * Chuyển từ Modal 1 sang Modal Chi tiết
 */
function processCalculation() {
    const month = document.getElementById('salaryMonth').value;
    const year = document.getElementById('salaryYear').value;
    if (!month || !year) return;

    // 1. Lấy tất cả các checkbox được chọn
    const checkedBoxes = document.querySelectorAll('#employeeTableBody input[type="checkbox"]:checked');

    if (checkedBoxes.length === 0) {
        alert("Vui lòng chọn ít nhất một nhân viên để tính lương.");
        return;
    }

    // 2. Lưu danh sách nhân viên đã chọn vào biến toàn cục
    selectedEmployees = Array.from(checkedBoxes).map(cb => {
        const row = cb.closest('tr');
        return {
            id: row.cells[1].innerText,
            name: row.cells[2].innerText
        };
    });

    // 3. Bắt đầu xử lý từ nhân viên đầu tiên
    currentProcessingIndex = 0;
    closeSalaryModal();
    showEmployeeDetail(currentProcessingIndex);
}

/**
 * Hàm bổ trợ để hiển thị thông tin nhân viên cụ thể lên Modal chi tiết
 */
function showEmployeeDetail(index) {
    const emp = selectedEmployees[index];
    const month = document.getElementById('salaryMonth').value;
    const year = document.getElementById('salaryYear').value;

    // 1. Tạo mã lương định dạng ML0001 dựa trên số lượng hàng hiện có trong bảng + index xử lý
    const currentCount = document.querySelectorAll('.ge-main-table tbody tr').length + 1 + index;
    const maLuong = `ML${currentCount.toString().padStart(4, '0')}`;

    const displayMonth = `${month}/${year}`;

    // 3. Đổ dữ liệu vào modal chi tiết
    document.getElementById('display-ma-luong').innerText = `Mã lương: ${maLuong}`;
    document.getElementById('display-nv-info').innerText = `Mã NV: ${emp.id} - ${emp.name}`;
    document.getElementById('display-month-info').innerText = `Tháng: ${displayMonth}`;

    // Reset before loading calc info
    document.getElementById('detail-lcb').value = "0";
    document.getElementById('detail-ltg').value = "0";
    document.getElementById('detail-sgl').value = "0";
    document.getElementById('detail-scl').value = "0";

    // Reset các ô nhập liệu thưởng/phạt
    document.getElementById('detail-thuong').value = "0";
    document.getElementById('detail-phat').value = "0";

    // Mở modal chi tiết (show quickly), then fill from contract + attendance
    document.getElementById('salaryDetailModal').style.display = 'flex';

    loadCalcInfoForEmployee(emp.id, month, year);
}

async function loadCalcInfoForEmployee(maNv, month, year) {
    const urlEl = document.getElementById('payroll-calc-info-url');
    if (!urlEl) {
        recalculateTotal();
        return;
    }

    let baseUrl = '';
    try {
        baseUrl = JSON.parse(urlEl.textContent || '""');
    } catch (e) {
        baseUrl = '';
    }

    if (!baseUrl) {
        recalculateTotal();
        return;
    }

    const qs = new URLSearchParams({ ma_nv: maNv, month: month, year: year });

    try {
        const res = await fetch(`${baseUrl}?${qs.toString()}`, { method: 'GET' });
        if (!res.ok) {
            showPayrollToast('Không lấy được dữ liệu hợp đồng/chấm công để tính lương');
            recalculateTotal();
            return;
        }

        const data = await res.json();
        const fmt = (n) => (Number(n || 0)).toLocaleString('vi-VN');

        document.getElementById('detail-lcb').value = fmt(data.luong_co_ban);
        document.getElementById('detail-ltg').value = fmt(data.luong_theo_gio);
        document.getElementById('detail-sgl').value = String(data.so_gio_lam ?? 0);
        document.getElementById('detail-scl').value = String(data.so_ca_lam ?? 0);

        recalculateTotal();
    } catch (e) {
        showPayrollToast('Không lấy được dữ liệu hợp đồng/chấm công để tính lương');
        recalculateTotal();
    }
}

/**
 * Hiển thị thông báo Toast
 */
function showPayrollToast(message) {
    const toast = document.getElementById('toast-notification');
    const toastContent = toast ? toast.querySelector('.toast-content') : null;

    if (toast) {
        toastContent.innerText = message;

        // Reset trạng thái và hiển thị trượt từ phải vào
        toast.classList.remove('show', 'fade-out');
        void toast.offsetWidth; // Force reflow để trigger animation
        toast.classList.add('show');

        // Sau 3 giây thì mờ dần và ẩn đi
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 600); // Đợi hiệu ứng mờ kết thúc rồi mới ẩn hẳn
        }, 3000);
    }
}

function recalculateTotal() {
    // Hàm parse tiền tệ chuẩn (lọc sạch dấu chấm, chữ VNĐ, ký tự lạ)
    const parseMoney = (id) => {
        const val = document.getElementById(id).value || '0';
        return Number(val.replace(/[^0-9-]/g, '')) || 0;
    };

    const parseNumber = (id) => {
        const val = document.getElementById(id).value || '0';
        return Number(val.replace(/[^0-9.-]/g, '')) || 0;
    };

    const lcb = parseMoney('detail-lcb');     // lương cơ bản
    const ltg = parseMoney('detail-ltg');     // lương theo giờ
    const sgl = parseNumber('detail-sgl');    // số giờ làm
    const thuong = parseMoney('detail-thuong');
    const phat = parseMoney('detail-phat');

    // 👉 FIX: đảm bảo không bị NaN
    const total = (ltg * sgl) + lcb + thuong - phat;

    // 👉 FIX: format chuẩn tiền VN
    const formatted = total.toLocaleString('vi-VN');

    document.getElementById('detail-tong-luong').innerText = formatted + " VNĐ";
}
function closeDetailModal() {
    // Reset lại trạng thái khi đóng modal
    editingRow = null;
    document.querySelector('#salaryDetailModal .detail-title').innerText = "Tính lương";
    document.getElementById('salaryDetailModal').style.display = 'none';
}
