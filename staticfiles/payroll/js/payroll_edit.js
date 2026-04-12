/**
 * GÉ CAFE - PAYROLL LOGIC JS
 */


document.addEventListener('DOMContentLoaded', function() {
    console.log("GÉ CAFE - Payroll System Ready");

    // --- LOGIC TÍNH TOÁN (Dùng cho trang Edit/Add) ---
    const employeeCards = document.querySelectorAll('.payroll-employee-card');
    employeeCards.forEach(card => {
        const bonusInput = card.querySelector('.bonus-input');
        const penaltyInput = card.querySelector('.penalty-input');
        const totalInput = card.querySelector('.total-salary-input');

        const baseSalary = parseFloat(card.dataset.base) || 0;
        const hourlyRate = parseFloat(card.dataset.hourly) || 0;
        const hoursWorked = parseFloat(card.dataset.hours) || 0;

        function calculateTotal() {
            const bonus = parseFloat(bonusInput.value) || 0;
            const penalty = parseFloat(penaltyInput.value) || 0;
            const total = baseSalary + (hourlyRate * hoursWorked) + bonus - penalty;

            // Format hiển thị kiểu 5.000.000 cho đẹp
            totalInput.value = new Intl.NumberFormat('vi-VN').format(total);
        }

        if (bonusInput && penaltyInput) {
            bonusInput.addEventListener('input', calculateTotal);
            penaltyInput.addEventListener('input', calculateTotal);
            calculateTotal(); // Chạy lần đầu
        }
    });

    // --- LOGIC THÔNG BÁO (Toast) ---
    const payrollForm = document.querySelector('form'); // Đảm bảo form có ID này
    if (payrollForm) {
        payrollForm.addEventListener('submit', function(e) {
            sessionStorage.setItem('payroll_success', 'true');
            sessionStorage.setItem('payroll_saved', '1');  // Thêm dòng này
            sessionStorage.setItem('payroll_action', 'edit');
            sessionStorage.setItem('payroll_success_message', 'Cập nhật bảng lương thành công');
        });
    }
});