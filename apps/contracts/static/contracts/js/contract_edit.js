document.addEventListener('DOMContentLoaded', function () {
    const contractForm = document.querySelector('.contract-edit-form');
    const cancelBtn = document.querySelector('.contract-cancel-btn');
    const contractTypeSelect = document.getElementById('loai_hd');
    const luongCoBanInput = document.getElementById('luong_co_ban');
    const luongTheoGioInput = document.getElementById('luong_theo_gio');
    const mucLuongInput = document.getElementById('muc_luong');
    const soGioLamToiThieuInput = document.getElementById('so_gio_lam_toi_thieu');
    const thuongInput = document.getElementById('thuong');

    // Asterisks
    const luongCoBanRequired = document.getElementById('luong-co-ban-required');
    const luongTheoGioRequired = document.getElementById('luong-theo-gio-required');
    const ngayBatDauInput = document.getElementById('ngay_bd');
    const ngayKetThucInput = document.getElementById('ngay_kt');

    const confirmCancelPopup = document.getElementById('confirm-cancel-popup');
    const confirmNoBtn = document.getElementById('confirm-no-btn');
    const confirmYesBtn = document.getElementById('confirm-yes-btn');

    const errorPopup = document.getElementById('error-popup');
    const errorPopupTitle = document.getElementById('error-popup-title');
    const errorPopupMessage1 = document.getElementById('error-popup-message1');
    const errorPopupMessage2 = document.getElementById('error-popup-message2');
    const errorPopupExitBtn = document.getElementById('error-popup-exit-btn');
    const errorPopupBackBtn = document.getElementById('error-popup-back-btn');

    function showErrorPopup(message) {
        if (errorPopupTitle) errorPopupTitle.textContent = 'THÔNG BÁO LỖI';
        if (errorPopupMessage1) errorPopupMessage1.textContent = message;
        if (errorPopupMessage2) errorPopupMessage2.textContent = '';
        if (errorPopupExitBtn) errorPopupExitBtn.style.display = 'none';
        if (errorPopupBackBtn) errorPopupBackBtn.textContent = 'Đóng';
        if (errorPopup) errorPopup.style.display = 'flex';
    }

    function hideErrorPopup() {
        if (errorPopup) errorPopup.style.display = 'none';
    }

    function showSuccessPopup(message) {
        const toast = document.getElementById('toast-success');
        const toastMessage = document.getElementById('toast-message');
        if (toast && toastMessage) {
            toastMessage.textContent = message || 'Cập nhật hợp đồng lao động thành công';
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
        if (!value && value !== 0) return "";
        let val = value.toString().replace(/\D/g, "");
        if (val === "") return "0";
        return val.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    function unformatCurrency(value) {
        if (!value) return 0;
        const cleanValue = value.toString().replace(/\D/g, "");
        return parseInt(cleanValue, 10) || 0;
    }

    function formatInputField(input) {
        let cursorPosition = input.selectionStart;
        let originalLength = input.value.length;
        let formattedValue = formatCurrency(input.value);
        input.value = formattedValue;
        
        let newLength = formattedValue.length;
        cursorPosition = cursorPosition + (newLength - originalLength);
        input.setSelectionStart(cursorPosition);
        input.setSelectionEnd(cursorPosition);
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

        const bonusAmount = unformatCurrency(thuongInput.value);
        mucLuong += bonusAmount;

        const finalValue = mucLuong > 0 ? Math.round(mucLuong) : 0;
        if (mucLuongInput) {
            mucLuongInput.value = formatCurrency(finalValue);
        }
    }

    function applyContractTypeRules() {
        const type = contractTypeSelect.value;
        if (type === 'PARTTIME') {
            luongTheoGioInput.disabled = false;
            luongTheoGioInput.required = true;
            if (luongTheoGioRequired) luongTheoGioRequired.classList.remove('is-hidden');
            
            luongCoBanInput.disabled = true;
            luongCoBanInput.required = false;
            if (luongCoBanRequired) luongCoBanRequired.classList.add('is-hidden');
        } else if (type === 'FULLTIME') {
            luongCoBanInput.disabled = false;
            luongCoBanInput.required = true;
            if (luongCoBanRequired) luongCoBanRequired.classList.remove('is-hidden');
            
            luongTheoGioInput.disabled = true;
            luongTheoGioInput.required = false;
            if (luongTheoGioRequired) luongTheoGioRequired.classList.add('is-hidden');
        }
        updateMucLuong();
    }

    async function submitForm(event) {
        event.preventDefault();
        updateMucLuong();

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
                showErrorPopup(data.message || 'Không thể cập nhật hợp đồng. Vui lòng thử lại sau.');
                return;
            }
            showSuccessPopup(data.message);
        } catch (_error) {
            showErrorPopup('Không thể cập nhật hợp đồng. Vui lòng thử lại sau.');
        }
    }

    // Listeners
    if (contractTypeSelect) contractTypeSelect.addEventListener('change', applyContractTypeRules);
    
    [luongCoBanInput, luongTheoGioInput, thuongInput].forEach(input => {
        if (input) {
            input.addEventListener('input', function() {
                formatInputField(this);
                updateMucLuong();
            });
        }
    });

    if (soGioLamToiThieuInput) soGioLamToiThieuInput.addEventListener('input', updateMucLuong);
    if (contractForm) contractForm.addEventListener('submit', submitForm);
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            if (confirmCancelPopup) confirmCancelPopup.style.display = 'flex';
        });
    }
    
    if (confirmNoBtn) {
        confirmNoBtn.addEventListener('click', function() {
            if (confirmCancelPopup) confirmCancelPopup.style.display = 'none';
        });
    }
    
    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', function() {
            window.location.href = contractForm.dataset.contractListUrl;
        });
    }

    if (confirmCancelPopup) {
        confirmCancelPopup.addEventListener('click', function(event) {
            if (event.target === confirmCancelPopup) {
                confirmCancelPopup.style.display = 'none';
            }
        });
    }

    // Initial values
    [luongCoBanInput, luongTheoGioInput, thuongInput, mucLuongInput].forEach(field => {
        if (field && field.value) {
            field.value = formatCurrency(field.value);
        }
    });

    applyContractTypeRules();
});
