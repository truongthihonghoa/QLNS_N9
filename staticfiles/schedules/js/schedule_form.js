document.addEventListener('DOMContentLoaded', function () {
    // Handle cancel buttons in create/edit forms
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

    // Handle form submissions (Demo - add to mock data)
    const forms = document.querySelectorAll('.schedule-form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            // Prevent actual form submission
            e.preventDefault();

            // Get form data
            const formData = new FormData(form);
            const ngayLam = formData.get('ngay_lam');
            const khungGio = formData.get('khung_gio');

            // Validate
            if (!ngayLam || !khungGio) {
                alert('Vui lòng điền đầy đủ thông tin');
                return;
            }

            // Show success message
            alert('Tạo lịch làm việc thành công (Demo UI)');

            // Navigate back to list after 1 second
            setTimeout(() => {
                window.location.href = '/schedules/';
            }, 1000);
        });
    });

    // Handle employee selection
    const selectAllCheckbox = document.querySelector('input[name="select_all_employees"]');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function () {
            const employeeCheckboxes = document.querySelectorAll('input[name="selected_employees"]');
            employeeCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    // Update position requirements when employees are selected
    document.querySelectorAll('input[name="selected_employees"]').forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const ma_nv = this.value;
            const positionSelect = document.querySelector(`select[name="position_${ma_nv}"]`);

            if (this.checked && positionSelect) {
                positionSelect.setAttribute('required', 'required');
            } else if (positionSelect) {
                positionSelect.removeAttribute('required');
                positionSelect.value = '';
            }
        });
    });
});
