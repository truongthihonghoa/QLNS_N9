document.addEventListener('DOMContentLoaded', function () {
    const contractForm = document.querySelector('.contract-form');
    const cancelBtn = document.querySelector('.contract-cancel-btn');
    const employeeNameInput = document.getElementById('ten_nv');
    const employeeCodeInput = document.getElementById('ma_nv');
    const employeeOptions = Array.from(document.querySelectorAll('#employee-options option'));
    const contractTypeSelect = document.getElementById('loai_hd');
    const luongCoBanInput = document.getElementById('luong_co_ban');
    const luongTheoGioInput = document.getElementById('luong_theo_gio');
    const mucLuongInput = document.getElementById('muc_luong');
    const soGioLamToiThieuInput = document.getElementById('so_gio_lam_toi_thieu');
    const thuongInput = document.getElementById('thuong');
    const positionSelect = document.getElementById('chuc_vu');
    const branchSelect = document.getElementById('dia_diem_lam_viec');
    const ngayBatDauInput = document.getElementById('ngay_bd');
    const ngayKetThucInput = document.getElementById('ngay_kt');
    
    // Asterisks
    const luongCoBanRequired = document.getElementById('luong-co-ban-required');
    const luongTheoGioRequired = document.getElementById('luong-theo-gio-required');

    const confirmCancelPopup = document.getElementById('confirm-cancel-popup');
    const confirmNoBtn = document.getElementById('confirm-no-btn');
    const confirmYesBtn = document.getElementById('confirm-yes-btn');

    const errorPopup = document.getElementById('error-popup');
    const errorPopupTitle = document.getElementById('error-popup-title');
    const errorPopupMessage1 = document.getElementById('error-popup-message1');
    const errorPopupMessage2 = document.getElementById('error-popup-message2');
    const errorPopupExitBtn = document.getElementById('error-popup-exit-btn');
    const errorPopupBackBtn = document.getElementById('error-popup-back-btn');

    const successPopup = document.getElementById('success-popup');
    const successPopupTitle = document.getElementById('success-popup-title');
    const successPopupMessage = document.getElementById('success-popup-message');
    const successPopupConfirmBtn = document.getElementById('success-popup-confirm-btn');

    function syncEmployeeCode() {
        const selectedOption = employeeOptions.find((option) => option.value === employeeNameInput.value.trim());
        if (selectedOption) {
            employeeCodeInput.value = selectedOption.dataset.code || '';
            
            // Cập nhật Chức vụ (Ghi đè hoặc xóa nếu nhân viên mới không có)
            const pos = selectedOption.dataset.position;
            if (positionSelect) {
                if (pos && pos !== 'None' && pos !== '') {
                    positionSelect.value = pos;
                } else {
                    positionSelect.value = ""; 
                }
            }
            
            // Cập nhật Địa điểm làm việc (Ghi đè hoặc xóa nếu nhân viên mới không có)
            const branch = selectedOption.dataset.branch;
            if (branchSelect) {
                if (branch && branch !== 'None' && branch !== '' && branch !== 'undefined') {
                    branchSelect.value = branch;
                } else {
                    branchSelect.value = "";
                }
            }
        } else {
            // Xóa hết dữ liệu nếu không chọn nhân viên nào
            employeeCodeInput.value = '';
            if (positionSelect) positionSelect.value = "";
            if (branchSelect) branchSelect.value = "";
        }
    }

    function showErrorPopup(message) {
        if (errorPopupTitle) {
            errorPopupTitle.textContent = 'THÔNG BÁO LỖI';
        }
        if (errorPopupMessage1) {
            errorPopupMessage1.textContent = message;
        }
        if (errorPopupMessage2) {
            errorPopupMessage2.textContent = '';
        }
        if (errorPopupExitBtn) {
            errorPopupExitBtn.style.display = 'none';
        }
        if (errorPopupBackBtn) {
            errorPopupBackBtn.textContent = 'Đóng';
        }
        if (errorPopup) {
            errorPopup.style.display = 'flex';
        }
    }

    function hideErrorPopup() {
        if (errorPopup) {
            errorPopup.style.display = 'none';
        }
    }

    function showSuccessPopup(message) {
        const toast = document.getElementById('toast-success');
        const toastMessage = document.getElementById('toast-message');
        if (toast && toastMessage) {
            toastMessage.textContent = message || 'Thêm hợp đồng lao động thành công';
            toast.classList.add('show');
            
            setTimeout(() => {
                window.location.href = contractForm.dataset.contractListUrl;
            }, 2000);
        }
    }

    function validateDates() {
        const bd = ngayBatDauInput.value;
        const kt = ngayKetThucInput.value;
        if (bd && kt && new Date(kt) < new Date(bd)) {
            showErrorPopup('Ngày kết thúc không thể nhỏ hơn ngày bắt đầu. Vui lòng kiểm tra lại!');
            return false;
        }
        return true;
    }

    function formatCurrency(value) {
        if (!value) return "0";
        // Chuyển về số nguyên, xóa mọi ký tự không phải số
        let val = value.toString().replace(/\D/g, "");
        if (val === "") return "0";
        // Thêm dấu chấm phân cách hàng nghìn
        return val.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    function unformatCurrency(value) {
        if (!value) return 0;
        // Xóa mọi ký tự không phải số (bao gồm dấu chấm, phẩy, VND, etc.)
        const cleanValue = value.toString().replace(/\D/g, "");
        return parseInt(cleanValue, 10) || 0;
    }

    function formatInputField(input) {
        let cursorPosition = input.selectionStart;
        let originalLength = input.value.length;
        let formattedValue = formatCurrency(input.value);
        input.value = formattedValue;
        
        // Điều chỉnh con trỏ sau khi format
        let newLength = formattedValue.length;
        cursorPosition = cursorPosition + (newLength - originalLength);
        input.setSelectionStart(cursorPosition);
        input.setSelectionEnd(cursorPosition);
    }

    function getPartTimeHourlyRate() {
        return unformatCurrency(luongTheoGioInput.value);
    }

    function updateMucLuong() {
        if (!contractTypeSelect) return;
        
        const contractType = contractTypeSelect.value.trim().toUpperCase();
        let mucLuong = 0;

        if (contractType === 'FULLTIME') {
            mucLuong = unformatCurrency(luongCoBanInput.value);
        } else if (contractType === 'PARTTIME') {
            const hourlyRate = unformatCurrency(luongTheoGioInput.value);
            const minimumHours = parseFloat(soGioLamToiThieuInput.value) || 0;
            mucLuong = hourlyRate * minimumHours;
        }

        // LUÔN LUÔN cộng thêm thưởng cho cả Full Time và Part Time
        const bonusAmount = unformatCurrency(thuongInput.value);
        mucLuong += bonusAmount;

        const finalValue = mucLuong > 0 ? Math.round(mucLuong) : 0;
        if (mucLuongInput) {
            mucLuongInput.value = formatCurrency(finalValue);
        }
    }

    function applyPartTimeMode() {
        luongTheoGioInput.disabled = false;
        luongTheoGioInput.required = true; // Bắt buộc Lương theo giờ
        if (luongTheoGioRequired) luongTheoGioRequired.classList.remove('is-hidden');
        
        luongCoBanInput.value = "0";
        luongCoBanInput.disabled = true; // Mới: Khóa lương cơ bản nếu là Part Time
        luongCoBanInput.required = false;
        if (luongCoBanRequired) luongCoBanRequired.classList.add('is-hidden');
        
        soGioLamToiThieuInput.value = 80;
        soGioLamToiThieuInput.disabled = false;
        soGioLamToiThieuInput.required = true;
        updateMucLuong();
    }

    function applyFullTimeMode() {
        luongCoBanInput.value = formatCurrency(3480000);
        luongCoBanInput.disabled = false;
        luongCoBanInput.required = true;
        if (luongCoBanRequired) luongCoBanRequired.classList.remove('is-hidden');
        
        luongTheoGioInput.value = "0";
        luongTheoGioInput.disabled = true; // Khóa lương theo giờ nếu là Full Time
        luongTheoGioInput.required = false;
        if (luongTheoGioRequired) luongTheoGioRequired.classList.add('is-hidden');
        
        soGioLamToiThieuInput.value = 174;
        soGioLamToiThieuInput.disabled = false;
        soGioLamToiThieuInput.required = true;
        updateMucLuong();
    }

    function applyContractTypeRules() {
        if (contractTypeSelect.value === 'PARTTIME') {
            applyPartTimeMode();
            return;
        }
        if (contractTypeSelect.value === 'FULLTIME') {
            applyFullTimeMode();
            return;
        }
        luongTheoGioInput.disabled = false;
        soGioLamToiThieuInput.disabled = false;
        mucLuongInput.value = 0;
    }

    function handleLuongTheoGioChange() {
        updateMucLuong();
    }

    async function submitForm(event) {
        event.preventDefault();
        syncEmployeeCode();
        updateMucLuong();

        // Strip dots before sending
        if (!validateDates()) {
            return;
        }

        const formData = new FormData(contractForm);
        const moneyFields = ['muc_luong', 'luong_co_ban', 'luong_theo_gio', 'thuong'];
        moneyFields.forEach(field => {
            if (formData.has(field)) {
                formData.set(field, formData.get(field).replace(/\./g, ""));
            }
        });

        try {
            const response = await fetch(contractForm.action || window.location.href, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': contractForm.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: formData,
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                showErrorPopup(data.message || 'Không thể tạo hợp đồng. Vui lòng thử lại sau.');
                return;
            }

            showSuccessPopup(data.message || 'Thêm hợp đồng lao động thành công');
        } catch (_error) {
            showErrorPopup('Không thể tạo hợp đồng. Vui lòng thử lại sau.');
        }
    }

    if (employeeNameInput) {
        employeeNameInput.addEventListener('input', syncEmployeeCode);
        employeeNameInput.addEventListener('change', syncEmployeeCode);
    }
    if (contractTypeSelect) {
        contractTypeSelect.addEventListener('change', applyContractTypeRules);
    }
    if (luongCoBanInput) {
        luongCoBanInput.addEventListener('input', function() {
            formatInputField(this);
            updateMucLuong();
        });
    }
    if (luongTheoGioInput) {
        luongTheoGioInput.addEventListener('input', function() {
            formatInputField(this);
            updateMucLuong();
        });
        luongTheoGioInput.addEventListener('change', updateMucLuong);
    }
    if (soGioLamToiThieuInput) {
        soGioLamToiThieuInput.addEventListener('input', updateMucLuong);
    }
    if (thuongInput) {
        thuongInput.addEventListener('input', function() {
            formatInputField(this);
            updateMucLuong();
        });
        thuongInput.addEventListener('change', updateMucLuong);
    }
    if (mucLuongInput) {
        mucLuongInput.addEventListener('input', function() {
            formatInputField(this);
        });
    }
    if (contractForm) {
        contractForm.addEventListener('submit', submitForm);
    }
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function () {
            confirmCancelPopup.style.display = 'flex';
        });
    }
    if (confirmNoBtn) {
        confirmNoBtn.addEventListener('click', function () {
            confirmCancelPopup.style.display = 'none';
        });
    }
    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', function () {
            window.location.href = contractForm.dataset.contractListUrl;
        });
    }
    if (confirmCancelPopup) {
        confirmCancelPopup.addEventListener('click', function (event) {
            if (event.target === confirmCancelPopup) {
                confirmCancelPopup.style.display = 'none';
            }
        });
    }
    if (errorPopupBackBtn) {
        errorPopupBackBtn.addEventListener('click', hideErrorPopup);
    }
    if (errorPopup) {
        errorPopup.addEventListener('click', function (event) {
            if (event.target === errorPopup) {
                hideErrorPopup();
            }
        });
    }
    syncEmployeeCode();
    applyContractTypeRules();
    updateMucLuong();
});
