document.addEventListener('DOMContentLoaded', function() {
    // --- Login Button ---
    const loginBtn = document.getElementById('login-btn');
    if(loginBtn) {
        loginBtn.addEventListener('click', function() {
            window.location.href = this.dataset.dashboardUrl;
        });
    }

    // --- Forgot Password Popup ---
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    const forgotPasswordPopup = document.getElementById('forgot-password-popup');
    const closeForgotPasswordBtn = document.getElementById('close-forgot-password-btn');
    const cancelForgotPasswordBtn = document.getElementById('cancel-forgot-password-btn');
    const savePasswordBtn = document.getElementById('save-password-btn');

    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (forgotPasswordPopup) forgotPasswordPopup.style.display = 'flex';
        });
    }

    const closeForgotPasswordPopup = () => {
        if (forgotPasswordPopup) forgotPasswordPopup.style.display = 'none';
    };

    // --- Confirm Cancel Popup ---
    const confirmCancelPopup = document.getElementById('confirm-cancel-popup');
    const confirmNoBtn = document.getElementById('confirm-no-btn');
    const confirmYesBtn = document.getElementById('confirm-yes-btn');
    
    const showConfirmCancelPopup = () => {
        if (confirmCancelPopup) confirmCancelPopup.style.display = 'flex';
    };
    const closeConfirmCancelPopup = () => {
        if (confirmCancelPopup) confirmCancelPopup.style.display = 'none';
    };

    if (closeForgotPasswordBtn) closeForgotPasswordBtn.addEventListener('click', showConfirmCancelPopup);
    if (cancelForgotPasswordBtn) cancelForgotPasswordBtn.addEventListener('click', showConfirmCancelPopup);
    if (forgotPasswordPopup) {
        forgotPasswordPopup.addEventListener('click', (e) => {
            if (e.target === forgotPasswordPopup) showConfirmCancelPopup();
        });
    }

    if (confirmNoBtn) confirmNoBtn.addEventListener('click', closeConfirmCancelPopup);
    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', () => {
            closeConfirmCancelPopup();
            closeForgotPasswordPopup();
        });
    }

    // --- Generic Success Popup ---
    const successPopup = document.getElementById('success-popup');
    const successPopupTitle = document.getElementById('success-popup-title');
    const successPopupMessage = document.getElementById('success-popup-message');
    const successPopupConfirmBtn = document.getElementById('success-popup-confirm-btn');

    function showSuccessPopup(title, message) {
        closeForgotPasswordPopup();
        if (successPopup) {
            successPopupTitle.textContent = title;
            successPopupMessage.textContent = message;
            successPopup.style.display = 'flex';
        }
    }

    function hideSuccessPopup() {
        if (successPopup) successPopup.style.display = 'none';
    }

    if (successPopupConfirmBtn) {
        successPopupConfirmBtn.addEventListener('click', hideSuccessPopup);
    }

    // --- Trigger Success Notification ---
    if (savePasswordBtn) {
        savePasswordBtn.addEventListener('click', () => {
            showSuccessPopup('Đổi mật khẩu thành công', 'Mật khẩu mới đã được cập nhật.');
        });
    }
});
