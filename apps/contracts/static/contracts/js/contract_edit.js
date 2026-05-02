document.addEventListener('DOMContentLoaded', function () {
    // Chỉ chạy trên trang sửa hợp đồng
    const contractForm = document.querySelector('.contract-edit-form');
    if (!contractForm) {
        return;
    }
    
    const cancelBtn = document.querySelector('.contract-cancel-btn');
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

    function showErrorPopup(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'error');
        } else {
            alert(message);
        }
    }

    function showSuccessPopup(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message || 'Cập nhật hợp đồng thành công', 'success');
            setTimeout(() => {
                window.location.href = contractForm.dataset.contractListUrl;
            }, 2000);
        } else {
            alert(message);
            window.location.href = contractForm.dataset.contractListUrl;
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
        val = parseInt(val, 10).toString();
        return val.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    function unformatCurrency(value) {
        if (!value) return 0;
        const cleanValue = value.toString().replace(/\D/g, "");
        return parseInt(cleanValue, 10) || 0;
    }

    function formatInputField(input) {
        if (!input) return;
        let cursorPosition = input.selectionStart;
        let originalLength = input.value.length;
        let formattedValue = formatCurrency(input.value);
        input.value = formattedValue;
        let newLength = formattedValue.length;
        cursorPosition = cursorPosition + (newLength - originalLength);
        input.setSelectionStart(cursorPosition);
        input.setSelectionEnd(cursorPosition);
    }

    window.updateMucLuong = function() {
        if (!contractTypeSelect) return;
        const contractType = (contractTypeSelect.value || "").trim().toUpperCase();
        let mucLuong = 0;

        if (contractType.includes('FULLTIME')) {
            const baseSalary = unformatCurrency(luongCoBanInput.value);
            mucLuong = baseSalary;
        } else if (contractType.includes('PARTTIME')) {
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
    };

    window.applyContractTypeRules = function() {
        if (!contractTypeSelect) return;
        const currentType = (contractTypeSelect.value || "").trim().toUpperCase();
        if (currentType.includes('PARTTIME')) {
            luongTheoGioInput.disabled = false;
            luongTheoGioInput.required = true;
            if (luongTheoGioRequired) luongTheoGioRequired.classList.remove('is-hidden');
            
            luongCoBanInput.disabled = true;
            luongCoBanInput.required = false;
            if (luongCoBanRequired) luongCoBanRequired.classList.add('is-hidden');
        } else if (currentType.includes('FULLTIME')) {
            luongCoBanInput.disabled = false;
            luongCoBanInput.required = true;
            if (luongCoBanRequired) luongCoBanRequired.classList.remove('is-hidden');
            
            luongTheoGioInput.disabled = true;
            luongTheoGioInput.required = false;
            if (luongTheoGioRequired) luongTheoGioRequired.classList.add('is-hidden');
        }
        window.updateMucLuong();
    };

    async function submitForm(event) {
        event.preventDefault();
        
        if (!validateDates()) {
            return;
        }

        const formData = new FormData(contractForm);
        // Xóa dấu chấm phân cách tiền tệ trước khi gửi
        const moneyFields = ['muc_luong', 'luong_co_ban', 'luong_theo_gio', 'thuong'];
        moneyFields.forEach(field => {
            if (formData.has(field)) {
                formData.set(field, formData.get(field).replace(/\./g, ""));
            }
        });

        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: formData,
            });

            const data = await response.json();
            if (data.success) {
                showSuccessPopup(data.message);
            } else {
                showErrorPopup(data.message || 'Lỗi khi cập nhật hợp đồng');
            }
        } catch (error) {
            console.error('Error:', error);
            showErrorPopup('Có lỗi xảy ra khi kết nối đến máy chủ');
        }
    }

    // Gán sự kiện
    if (contractForm) {
        contractForm.addEventListener('submit', submitForm);
        
        // Theo dõi thay đổi các trường ảnh hưởng đến lương
        const impactIds = ['loai_hd', 'luong_co_ban', 'luong_theo_gio', 'so_gio_lam_toi_thieu', 'thuong'];
        ['input', 'change'].forEach(evt => {
            contractForm.addEventListener(evt, (e) => {
                if (impactIds.includes(e.target.id)) {
                    if (e.target.id === 'loai_hd') applyContractTypeRules();
                    if (['luong_co_ban', 'luong_theo_gio', 'thuong'].includes(e.target.id)) formatInputField(e.target);
                    updateMucLuong();
                }
            });
        });

        // Chặn Enter
        contractForm.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'BUTTON') {
                e.preventDefault();
            }
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => confirmCancelPopup.style.display = 'flex');
    }
    if (confirmNoBtn) {
        confirmNoBtn.addEventListener('click', () => confirmCancelPopup.style.display = 'none');
    }
    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', () => window.location.href = contractForm.dataset.contractListUrl);
    }

    // Format giá trị ban đầu
    [luongCoBanInput, luongTheoGioInput, thuongInput, mucLuongInput].forEach(input => {
        if (input && input.value) input.value = formatCurrency(input.value);
    });
    
    applyContractTypeRules();
});
