document.addEventListener('DOMContentLoaded', function () {
    // Only run on add pages (not edit pages)
    if (document.querySelector('.contract-edit-form')) {
        return;
    }
    
    const contractForm = document.querySelector('.contract-form');
    const cancelBtn = document.querySelector('.contract-cancel-btn');
    const employeeNameInput = document.getElementById('ten_nv');
    const employeeCodeInput = document.getElementById('ma_nv');
    const employeeDropdown = document.getElementById('employee-dropdown');
    const employeeOptions = Array.from(document.querySelectorAll('.employee-option'));
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

    // Mapping từ Tiếng Việt sang Mã (Key) để tránh bị reset trường Chức vụ
    const positionMap = {
        'Quản lý': 'QUAN_LY',
        'Phục vụ': 'PHUC_VU',
        'Pha chế': 'PHA_CHE',
        'Giữ xe': 'GIU_XE',
        'Thu ngân': 'THU_NGAN'
    };


    // Autocomplete functionality
    function filterEmployees(searchTerm) {
        const filtered = employeeOptions.filter(option => {
            const name = option.dataset.name.toLowerCase();
            return name.includes(searchTerm.toLowerCase());
        });
        
        employeeDropdown.innerHTML = '';
        
        if (filtered.length === 0) {
            employeeDropdown.style.display = 'none';
            return;
        }
        
        filtered.forEach(option => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'employee-option';
            optionDiv.dataset.name = option.dataset.name;
            optionDiv.dataset.code = option.dataset.code;
            optionDiv.dataset.position = option.dataset.position;
            optionDiv.dataset.branch = option.dataset.branch;
            optionDiv.textContent = option.dataset.name;
            employeeDropdown.appendChild(optionDiv);
        });
        
        employeeDropdown.style.display = 'block';
    }
    
    function selectEmployee(employeeElement) {
        const name = employeeElement.dataset.name;
        const code = employeeElement.dataset.code;
        const position = employeeElement.dataset.position;
        const branch = employeeElement.dataset.branch;
        
        employeeNameInput.value = name;
        employeeCodeInput.value = code;
        
        // Tự động điền chức vụ và chi nhánh
        if (positionSelect && position && position !== 'None' && position !== '') {
            const mappedValue = positionMap[position] || position;
            positionSelect.value = mappedValue;
        }
        
        if (branchSelect && branch && branch !== 'None' && branch !== '' && branch !== 'undefined') {
            branchSelect.value = branch;
        }
        
        employeeDropdown.style.display = 'none';
    }
    
    function syncEmployeeCode(skipAutofill = false) {
        const selectedOption = employeeOptions.find((option) => option.dataset.name === employeeNameInput.value.trim());
        if (selectedOption) {
            employeeCodeInput.value = selectedOption.dataset.code || '';
            
            // Nếu không phải đang trong quá trình nộp form, mới thực hiện tự động điền
            if (!skipAutofill) {
                const pos = selectedOption.dataset.position;
                if (positionSelect) {
                    if (pos && pos !== 'None' && pos !== '') {
                        // Dùng positionMap để lấy mã đúng (QUAN_LY, PHUC_VU...)
                        const mappedValue = positionMap[pos] || pos;
                        positionSelect.value = mappedValue;
                    }
                }
                
                const branch = selectedOption.dataset.branch;
                if (branchSelect) {
                    if (branch && branch !== 'None' && branch !== '' && branch !== 'undefined') {
                        branchSelect.value = branch;
                    }
                }
            }
        } else {
            employeeCodeInput.value = '';
            if (!skipAutofill) {
                if (positionSelect) positionSelect.value = "";
                if (branchSelect) branchSelect.value = "";
            }
        }
    }

    function showErrorPopup(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'error');
        } else {
            alert(message);
        }
    }

    function showSuccessPopup(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message || 'Thêm hợp đồng lao động thành công', 'success');
            
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
        if (!value) return "0";
        // Chuyển về số nguyên, xóa mọi ký tự không phải số
        let val = value.toString().replace(/\D/g, "");
        if (val === "") return "0";
        
        // Loại bỏ số 0 ở đầu (ví dụ "02" thành "2")
        val = parseInt(val, 10).toString();
        
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

        // LUÔN LUÔN cộng thêm thưởng cho cả Full Time và Part Time
        const bonusAmount = unformatCurrency(thuongInput.value);
        mucLuong += bonusAmount;

        const finalValue = mucLuong > 0 ? Math.round(mucLuong) : 0;
        if (mucLuongInput) {
            // Cập nhật giá trị hiển thị
            mucLuongInput.value = formatCurrency(finalValue);
        }
    };

    function applyPartTimeMode() {
        luongTheoGioInput.disabled = false;
        luongTheoGioInput.required = true;
        if (luongTheoGioRequired) luongTheoGioRequired.classList.remove('is-hidden');
        
        // Chỉ đặt mặc định 30.000 nếu đang trống hoặc bằng 0
        const currentHourly = unformatCurrency(luongTheoGioInput.value);
        if (currentHourly === 0) {
            luongTheoGioInput.value = formatCurrency(30000);
        }
        
        luongCoBanInput.value = "0";
        luongCoBanInput.disabled = true;
        luongCoBanInput.required = false;
        if (luongCoBanRequired) luongCoBanRequired.classList.add('is-hidden');
        
        // Chỉ đặt mặc định 80 giờ nếu đang trống hoặc bằng 0
        const currentHours = parseFloat(soGioLamToiThieuInput.value) || 0;
        if (currentHours === 0) {
            soGioLamToiThieuInput.value = 80;
        }
        
        soGioLamToiThieuInput.disabled = false;
        soGioLamToiThieuInput.required = true;
        window.updateMucLuong();
    }

    function applyFullTimeMode() {
        // Chỉ đặt mặc định 3.480.000 nếu đang trống hoặc bằng 0
        const currentBase = unformatCurrency(luongCoBanInput.value);
        if (currentBase === 0) {
            luongCoBanInput.value = formatCurrency(3480000);
        }
        
        luongCoBanInput.disabled = false;
        luongCoBanInput.required = true;
        if (luongCoBanRequired) luongCoBanRequired.classList.remove('is-hidden');
        
        luongTheoGioInput.value = "0";
        luongTheoGioInput.disabled = true;
        luongTheoGioInput.required = false;
        if (luongTheoGioRequired) luongTheoGioRequired.classList.add('is-hidden');
        
        // Chỉ đặt mặc định 174 giờ nếu đang trống hoặc bằng 0
        const currentHours = parseFloat(soGioLamToiThieuInput.value) || 0;
        if (currentHours === 0) {
            soGioLamToiThieuInput.value = 174;
        }
        
        soGioLamToiThieuInput.disabled = false;
        soGioLamToiThieuInput.required = true;
        window.updateMucLuong();
    }

    window.applyContractTypeRules = function() {
        const currentType = (contractTypeSelect.value || "").trim().toUpperCase();
        if (currentType.includes('PARTTIME')) {
            applyPartTimeMode();
            return;
        }
        if (currentType.includes('FULLTIME')) {
            applyFullTimeMode();
            return;
        }
        
        // Mặc định cho các loại khác
        luongTheoGioInput.disabled = false;
        soGioLamToiThieuInput.disabled = false;
        window.updateMucLuong();
    };
    function handleLuongTheoGioChange() {
        updateMucLuong();
    }

    async function submitForm(event) {
        event.preventDefault();
        // Chỉ đồng bộ mã, không tự động điền lại các trường khác để tránh mất dữ liệu đã chọn
        syncEmployeeCode(true);
        updateMucLuong();

        // Validation các trường bắt buộc
        const requiredFields = [
            { id: 'ten_nv', name: 'Tên nhân viên' },
            { id: 'loai_hd', name: 'Loại hợp đồng' },
            { id: 'ngay_bd', name: 'Ngày bắt đầu' },
            { id: 'ngay_kt', name: 'Ngày kết thúc' },
            { id: 'so_gio_lam_toi_thieu', name: 'Số giờ làm tối thiểu' },
            { id: 'chuc_vu', name: 'Chức vụ' },
            { id: 'dia_diem_lam_viec', name: 'Địa điểm làm việc' }
        ];

        // Kiểm tra các trường bắt buộc
        for (const field of requiredFields) {
            const element = document.getElementById(field.id);
            if (!element || !element.value.trim()) {
                showErrorPopup(`Trường ${field.name} là bắt buộc và không được để trống.`);
                element?.focus();
                return;
            }
        }

        // Kiểm tra lương cơ bản hoặc lương theo giờ tùy theo loại hợp đồng
        const loaiHd = document.getElementById('loai_hd').value;
        if (loaiHd === 'FULLTIME') {
            const luongCoBan = document.getElementById('luong_co_ban');
            if (!luongCoBan.value.trim()) {
                showErrorPopup('Lương cơ bản là bắt buộc đối với hợp đồng Full Time.');
                luongCoBan.focus();
                return;
            }
        } else if (loaiHd === 'PARTTIME') {
            const luongTheoGio = document.getElementById('luong_theo_gio');
            if (!luongTheoGio.value.trim()) {
                showErrorPopup('Lương theo giờ là bắt buộc đối với hợp đồng Part Time.');
                luongTheoGio.focus();
                return;
            }
        }

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
        employeeNameInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.trim();
            if (searchTerm.length > 0) {
                filterEmployees(searchTerm);
            } else {
                employeeDropdown.style.display = 'none';
            }
        });
        
        employeeNameInput.addEventListener('change', syncEmployeeCode);
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.employee-autocomplete')) {
                employeeDropdown.style.display = 'none';
            }
        });
    }
    
    // Handle dropdown option clicks
    employeeDropdown.addEventListener('click', function(e) {
        if (e.target.classList.contains('employee-option')) {
            selectEmployee(e.target);
        }
    });
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

    if (mucLuongInput) {
        mucLuongInput.addEventListener('input', function() {
            formatInputField(this);
        });
    }
    if (contractForm) {
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
