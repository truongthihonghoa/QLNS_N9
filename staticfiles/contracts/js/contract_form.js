document.addEventListener('DOMContentLoaded', function () {
    const contractForm = document.querySelector('.contract-form');
    const cancelBtn = document.querySelector('.contract-cancel-btn');
    const employeeNameInput = document.getElementById('ten_nv');
    const employeeCodeInput = document.getElementById('ma_nv');
    const employeeOptions = Array.from(document.querySelectorAll('#employee-options option'));
    const contractTypeSelect = document.getElementById('loai_hd');
    const luongCoBanInput = document.getElementById('luong_co_ban');
    const luongTheoGioSelect = document.getElementById('luong_theo_gio');
    const luongTheoGioKhacWrapper = document.getElementById('luong-theo-gio-khac-wrapper');
    const luongTheoGioKhacInput = document.getElementById('luong_theo_gio_khac');
    const mucLuongInput = document.getElementById('muc_luong');
    const soGioLamToiThieuInput = document.getElementById('so_gio_lam_toi_thieu');

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
        employeeCodeInput.value = selectedOption ? selectedOption.dataset.code || '' : '';
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
        if (successPopupTitle) {
            successPopupTitle.textContent = 'Thêm hợp đồng lao động thành công';
        }
        if (successPopup) {
            successPopup.style.display = 'flex';
        }
        window.setTimeout(function () {
            window.location.href = contractForm.dataset.contractListUrl;
        }, 1200);
    }

    function showLuongTheoGioKhac() {
        luongTheoGioKhacWrapper.classList.add('is-visible');
        luongTheoGioKhacInput.disabled = false;
    }

    function hideLuongTheoGioKhac() {
        luongTheoGioKhacWrapper.classList.remove('is-visible');
        luongTheoGioKhacInput.value = '';
        luongTheoGioKhacInput.disabled = true;
    }

    function getPartTimeHourlyRate() {
        if (luongTheoGioSelect.value === 'khac') {
            return parseFloat(luongTheoGioKhacInput.value) || 0;
        }
        return parseFloat(luongTheoGioSelect.value) || 0;
    }

    function updateMucLuong() {
        const contractType = contractTypeSelect.value;
        let mucLuong = 0;

        if (contractType === 'FULL_TIME') {
            mucLuong = parseFloat(luongCoBanInput.value) || 0;
        } else if (contractType === 'PART_TIME') {
            const hourlyRate = getPartTimeHourlyRate();
            const minimumHours = parseFloat(soGioLamToiThieuInput.value) || 0;
            mucLuong = hourlyRate * minimumHours;
        }

        mucLuongInput.value = mucLuong > 0 ? Math.round(mucLuong) : 0;
    }

    function applyPartTimeMode() {
        luongTheoGioSelect.disabled = false;
        luongCoBanInput.value = 0;
        mucLuongInput.readOnly = true;
        soGioLamToiThieuInput.value = 80;
        soGioLamToiThieuInput.disabled = false;
        if (luongTheoGioSelect.value === 'khac') {
            showLuongTheoGioKhac();
        } else {
            hideLuongTheoGioKhac();
        }
        updateMucLuong();
    }

    function applyFullTimeMode() {
        luongCoBanInput.value = 3480000;
        luongTheoGioSelect.value = '0';
        luongTheoGioSelect.disabled = true;
        hideLuongTheoGioKhac();
        soGioLamToiThieuInput.value = 174;
        soGioLamToiThieuInput.disabled = false;
        mucLuongInput.readOnly = true;
        updateMucLuong();
    }

    function applyContractTypeRules() {
        if (contractTypeSelect.value === 'PART_TIME') {
            applyPartTimeMode();
            return;
        }
        if (contractTypeSelect.value === 'FULL_TIME') {
            applyFullTimeMode();
            return;
        }
        luongTheoGioSelect.disabled = false;
        soGioLamToiThieuInput.disabled = false;
        hideLuongTheoGioKhac();
        mucLuongInput.value = 0;
    }

    function handleLuongTheoGioChange() {
        if (contractTypeSelect.value !== 'PART_TIME') {
            hideLuongTheoGioKhac();
            updateMucLuong();
            return;
        }
        if (luongTheoGioSelect.value === 'khac') {
            showLuongTheoGioKhac();
        } else {
            hideLuongTheoGioKhac();
        }
        updateMucLuong();
    }

    async function submitForm(event) {
        event.preventDefault();
        syncEmployeeCode();
        updateMucLuong();

        try {
            const response = await fetch(contractForm.action || window.location.href, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': contractForm.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: new FormData(contractForm),
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
        luongCoBanInput.addEventListener('input', updateMucLuong);
    }
    if (luongTheoGioSelect) {
        luongTheoGioSelect.addEventListener('change', handleLuongTheoGioChange);
    }
    if (luongTheoGioKhacInput) {
        luongTheoGioKhacInput.addEventListener('input', updateMucLuong);
    }
    if (soGioLamToiThieuInput) {
        soGioLamToiThieuInput.addEventListener('input', updateMucLuong);
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
    hideLuongTheoGioKhac();
    syncEmployeeCode();
    applyContractTypeRules();
    updateMucLuong();
});
