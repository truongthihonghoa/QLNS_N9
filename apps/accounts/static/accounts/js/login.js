                  /**
 * Login Page JavaScript
 * Handles: Password toggle, Forgot Password popup, Success notifications
 */
document.addEventListener('DOMContentLoaded', function() {
    // --- Password Toggle (Eye Icon) ---
    const eyeIcon = document.getElementById('eye-icon');
    const passwordInput = document.querySelector('input[type="password"][name="password"]');

    if (eyeIcon && passwordInput) {
        eyeIcon.addEventListener('click', function() {
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                this.src = this.src.replace('eye_opened', 'eye_closed');
            } else {
                passwordInput.type = 'password';
                this.src = this.src.replace('eye_closed', 'eye_opened');
            }
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

    // Only show confirm popup when clicking cancel or X button (NOT on overlay click)
    if (closeForgotPasswordBtn) {
        closeForgotPasswordBtn.addEventListener('click', showConfirmCancelPopup);
    }
    if (cancelForgotPasswordBtn) {
        cancelForgotPasswordBtn.addEventListener('click', showConfirmCancelPopup);
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
            if (successPopupTitle) successPopupTitle.textContent = title;
            if (successPopupMessage) successPopupMessage.textContent = message;
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