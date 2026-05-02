document.addEventListener('DOMContentLoaded', function () {
    // Only run on edit pages (not add pages)
    if (!document.querySelector('.contract-edit-form')) {
        return;
    }
    
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


    function showErrorPopup(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'error');
        } else {
            alert(message);
        }
    }

    function showSuccessPopup(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message || 'Cập nhật hợp đồng lao động thành công', 'success');
        } else {
            alert(message);
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

    document.addEventListener('DOMContentLoaded', function () {
    // Only run on edit pages (not add pages)
    if (!document.querySelector('.contract-edit-form')) {
        return;
    }

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


    function showErrorPopup(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'error');
        } else {
            alert(message);
        }
    }

    function showSuccessPopup(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message || 'Cập nhật hợp đồng lao động thành công', 'success');
        } else {
            alert(message);
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

        // Loại bỏ số 0 ở đầu (ví dụ "02" thành "2")
        val = parseInt(val, 10).toString();

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

    // Đưa các hàm quan trọng ra toàn cục để có thể gọi trực tiếp từ HTML nếu cần
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
        const type = (contractTypeSelect.value || "").trim().toUpperCase();
        if (type.includes('PARTTIME')) {
            luongTheoGioInput.disabled = false;
            luongTheoGioInput.required = true;
            if (luongTheoGioRequired) luongTheoGioRequired.classList.remove('is-hidden');

            luongCoBanInput.disabled = true;
            luongCoBanInput.required = false;
            if (luongCoBanRequired) luongCoBanRequired.classList.add('is-hidden');
        } else if (type.includes('FULLTIME')) {
            luongCoBanInput.disabled = false;
            luongCoBanInput.required = true;
            if (luongCoBanRequired) luongCoBanRequired.classList.remove('is-hidden');

            luongTheoGioInput.disabled = true;
            luongTheoGioInput.required = false;
            if (luongTheoGioRequired) luongTheoGioRequired.classList.add('is-hidden');
        }
        window.updateMucLuong();
    };


    function submitForm(event) {
        updateMucLuong();

        if (!validateDates()) {
            event.preventDefault();
            return false;
        }

        // Format money fields before normal form submission
        const moneyFields = ['muc_luong', 'luong_co_ban', 'luong_theo_gio', 'thuong'];
        moneyFields.forEach(field => {
            const input = document.getElementById(field);
            if (input) {
                input.value = input.value.replace(/\./g, "");
            }
        });

        // Allow normal form submission
        // Don't prevent default - let the form submit normally
        return true;
    }

    // Listeners
    if (contractForm) {
        // GIÁM SÁT TOÀN DIỆN: Bắt mọi sự kiện nhập liệu trên toàn bộ form
        const impactIds = ['loai_hd', 'luong_co_ban', 'luong_theo_gio', 'so_gio_lam_toi_thieu', 'thuong'];

        ['input', 'keyup', 'change', 'paste'].forEach(evtType => {
            contractForm.addEventListener(evtType, function(e) {
                const target = e.target;
                if (!target) return;

                // 1. Kiểm tra xem ô vừa tác động có ảnh hưởng đến lương không
                if (impactIds.includes(target.id) || impactIds.includes(target.name)) {

                    // 2. Nếu đổi loại hợp đồng, áp dụng quy tắc khóa/mở trường trước
                    if (target.id === 'loai_hd') {
                        applyContractTypeRules();
                    }

                    // 3. Định dạng dấu chấm tiền tệ (chỉ cho các trường tiền)
                    const moneyIds = ['luong_co_ban', 'luong_theo_gio', 'thuong'];
                    if (moneyIds.includes(target.id)) {
                        formatInputField(target);
                    }

                    // 4. Cập nhật Mức lương NGAY LẬP TỨC
                    updateMucLuong();
                }
            });
        });
    }
    if (contractForm) {
        // Remove any existing submit listeners to avoid conflicts
        contractForm.removeEventListener('submit', submitForm);
        contractForm.addEventListener('submit', submitForm);

        // Chặn phím Enter tự động gửi form khi đang nhập liệu
        contractForm.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.keyCode === 13) {
                const target = e.target;
                // Nếu không phải đang đứng ở nút bấm hoặc textarea thì chặn Enter
                if (target.tagName !== 'BUTTON' && target.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    return false;
                }
            }
        });
    }

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

    // Đưa các hàm quan trọng ra toàn cục để có thể gọi trực tiếp từ HTML nếu cần
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
        const type = (contractTypeSelect.value || "").trim().toUpperCase();
        if (type.includes('PARTTIME')) {
            luongTheoGioInput.disabled = false;
            luongTheoGioInput.required = true;
            if (luongTheoGioRequired) luongTheoGioRequired.classList.remove('is-hidden');
            
            luongCoBanInput.disabled = true;
            luongCoBanInput.required = false;
            if (luongCoBanRequired) luongCoBanRequired.classList.add('is-hidden');
        } else if (type.includes('FULLTIME')) {
            luongCoBanInput.disabled = false;
            luongCoBanInput.required = true;
            if (luongCoBanRequired) luongCoBanRequired.classList.remove('is-hidden');
            
            luongTheoGioInput.disabled = true;
            luongTheoGioInput.required = false;
            if (luongTheoGioRequired) luongTheoGioRequired.classList.add('is-hidden');
        }
        window.updateMucLuong();
    };


    function submitForm(event) {
        updateMucLuong();

        if (!validateDates()) {
            event.preventDefault();
            return false;
        }

        // Format money fields before normal form submission
        const moneyFields = ['muc_luong', 'luong_co_ban', 'luong_theo_gio', 'thuong'];
        moneyFields.forEach(field => {
            const input = document.getElementById(field);
            if (input) {
                input.value = input.value.replace(/\./g, "");
            }
        });

        // Allow normal form submission
        // Don't prevent default - let the form submit normally
        return true;
    }

    // Listeners
    if (contractForm) {
        // GIÁM SÁT TOÀN DIỆN: Bắt mọi sự kiện nhập liệu trên toàn bộ form
        const impactIds = ['loai_hd', 'luong_co_ban', 'luong_theo_gio', 'so_gio_lam_toi_thieu', 'thuong'];
        
        ['input', 'keyup', 'change', 'paste'].forEach(evtType => {
            contractForm.addEventListener(evtType, function(e) {
                const target = e.target;
                if (!target) return;

                // 1. Kiểm tra xem ô vừa tác động có ảnh hưởng đến lương không
                if (impactIds.includes(target.id) || impactIds.includes(target.name)) {
                    
                    // 2. Nếu đổi loại hợp đồng, áp dụng quy tắc khóa/mở trường trước
                    if (target.id === 'loai_hd') {
                        applyContractTypeRules();
                    }
                    
                    // 3. Định dạng dấu chấm tiền tệ (chỉ cho các trường tiền)
                    const moneyIds = ['luong_co_ban', 'luong_theo_gio', 'thuong'];
                    if (moneyIds.includes(target.id)) {
                        formatInputField(target);
                    }
                    
                    // 4. Cập nhật Mức lương NGAY LẬP TỨC
                    updateMucLuong();
                }
            });
        });
    }
    if (contractForm) {
        // Remove any existing submit listeners to avoid conflicts
        contractForm.removeEventListener('submit', submitForm);
        contractForm.addEventListener('submit', submitForm);

        // Chặn phím Enter tự động gửi form khi đang nhập liệu
        contractForm.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.keyCode === 13) {
                const target = e.target;
                // Nếu không phải đang đứng ở nút bấm hoặc textarea thì chặn Enter
                if (target.tagName !== 'BUTTON' && target.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    return false;
                }
            }
        });
    }
    
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
