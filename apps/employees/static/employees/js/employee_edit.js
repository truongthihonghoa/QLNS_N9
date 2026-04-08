document.addEventListener('DOMContentLoaded', function() {
    const employeeForm = document.querySelector('.employee-form');
    const saveBtn = document.querySelector('.save-btn');
    const cancelBtn = document.querySelector('.cancel-btn');

    // --- Generic Error Popup ---
    const errorPopup = document.getElementById('error-popup');
    const errorPopupExitBtn = document.getElementById('error-popup-exit-btn');
    const errorPopupBackBtn = document.getElementById('error-popup-back-btn');

    function showErrorPopup(title, msg1, msg2) {
        if (errorPopup) {
            document.getElementById('error-popup-title').textContent = title;
            document.getElementById('error-popup-message1').textContent = msg1;
            document.getElementById('error-popup-message2').textContent = msg2;
            errorPopup.style.display = 'flex';
        }
    }
    function hideErrorPopup() {
        if (errorPopup) errorPopup.style.display = 'none';
    }

    if (errorPopupExitBtn) errorPopupExitBtn.addEventListener('click', () => window.location.href = employeeForm.dataset.returnUrl || employeeForm.dataset.employeeListUrl);
    if (errorPopupBackBtn) errorPopupBackBtn.addEventListener('click', hideErrorPopup);
    if (errorPopup) errorPopup.addEventListener('click', (e) => { if (e.target === errorPopup) hideErrorPopup(); });

    // --- Confirm Cancel Popup ---
    const confirmCancelPopup = document.getElementById('confirm-cancel-popup');
    const confirmNoBtn = document.getElementById('confirm-no-btn');
    const confirmYesBtn = document.getElementById('confirm-yes-btn');

    function showConfirmCancelPopup() {
        if (confirmCancelPopup) confirmCancelPopup.style.display = 'flex';
    }
    function hideConfirmCancelPopup() {
        if (confirmCancelPopup) confirmCancelPopup.style.display = 'none';
    }

    if (cancelBtn) cancelBtn.addEventListener('click', showConfirmCancelPopup);
    if (confirmNoBtn) confirmNoBtn.addEventListener('click', hideConfirmCancelPopup);
    if (confirmYesBtn) confirmYesBtn.addEventListener('click', () => window.location.href = employeeForm.dataset.returnUrl || employeeForm.dataset.employeeListUrl);
    if (confirmCancelPopup) confirmCancelPopup.addEventListener('click', (e) => { if (e.target === confirmCancelPopup) hideConfirmCancelPopup(); });

    // --- Form Submission ---
    if (saveBtn) {
        saveBtn.addEventListener('click', function(event) {
            if (!employeeForm.checkValidity()) {
                event.preventDefault();
                showErrorPopup('THÔNG BÁO LỖI', 'Xin vui lòng nhập đầy đủ thông tin!', '');
            }
        });
    }
});
