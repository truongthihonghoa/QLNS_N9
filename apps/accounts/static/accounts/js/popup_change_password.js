/**
 * Change Password Popup Handler
 * Handles: Popup open/close, Cancel confirmation, Password change AJAX, Password toggle
 */
document.addEventListener('DOMContentLoaded', function() {
    const popup = document.getElementById('change-password-popup');
    const closeBtn = document.getElementById('close-change-password-btn');
    const cancelBtn = document.getElementById('cancel-change-password-btn');
    const saveBtn = document.getElementById('save-change-password-btn');
    const errorContainer = document.getElementById('change-password-error');

    // Input fields
    const usernameInput = document.getElementById('change-username');
    const oldPasswordInput = document.getElementById('old-password');
    const newPasswordInput = document.getElementById('new-password');
    const confirmPasswordInput = document.getElementById('confirm-password');

    // Static path for eye icons (set via data attribute on body or global var)
    const EYE_OPENED_ICON = '/static/accounts/img/eye_opened.png';
    const EYE_CLOSED_ICON = '/static/accounts/img/eye_closed.png';

    // ========== PASSWORD TOGGLE (Eye Icon) ==========
    document.querySelectorAll('.toggle-password').forEach(icon => {
        icon.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const img = this.querySelector('.eye-icon-img');

            if (input && img) {
                if (input.type === 'password') {
                    input.type = 'text';
                    img.src = EYE_CLOSED_ICON;
                } else {
                    input.type = 'password';
                    img.src = EYE_OPENED_ICON;
                }
            }
        });
    });

    // CSRF token from cookie
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Show popup using style.display
    function showPopup() {
        if (popup) {
            popup.style.display = 'flex';
            clearForm();
        }
    }

    // Hide popup using style.display
    function hidePopup() {
        if (popup) {
            popup.style.display = 'none';
        }
    }

    // Clear form
    function clearForm() {
        if (usernameInput) usernameInput.value = '';
        if (oldPasswordInput) oldPasswordInput.value = '';
        if (newPasswordInput) newPasswordInput.value = '';
        if (confirmPasswordInput) confirmPasswordInput.value = '';
        hideError();
    }

    // Show error message
    function showError(message) {
        if (errorContainer) {
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
        }
    }

    // Hide error message
    function hideError() {
        if (errorContainer) {
            errorContainer.textContent = '';
            errorContainer.style.display = 'none';
        }
    }

    // Handle cancel button - trigger confirm cancel popup
    function handleCancel() {
        const hasData = (usernameInput && usernameInput.value) ||
                       (oldPasswordInput && oldPasswordInput.value) ||
                       (newPasswordInput && newPasswordInput.value) ||
                       (confirmPasswordInput && confirmPasswordInput.value);

        if (hasData) {
            // Show confirm cancel popup
            const confirmPopup = document.getElementById('confirm-cancel-popup');
            if (confirmPopup) {
                confirmPopup.style.display = 'flex';

                // Handle confirm cancel
                const yesBtn = document.getElementById('confirm-yes-btn');
                const noBtn = document.getElementById('confirm-no-btn');

                if (yesBtn) {
                    // Remove old handlers to avoid duplicates
                    yesBtn.replaceWith(yesBtn.cloneNode(true));
                    const newYesBtn = document.getElementById('confirm-yes-btn');
                    newYesBtn.addEventListener('click', function() {
                        hidePopup();
                        confirmPopup.style.display = 'none';
                        clearForm();
                    });
                }

                if (noBtn) {
                    // Remove old handlers to avoid duplicates
                    noBtn.replaceWith(noBtn.cloneNode(true));
                    const newNoBtn = document.getElementById('confirm-no-btn');
                    newNoBtn.addEventListener('click', function() {
                        confirmPopup.style.display = 'none';
                    });
                }
            }
        } else {
            hidePopup();
        }
    }

    // Handle save password
    function handleSave() {
        hideError();

        const data = {
            username: usernameInput ? usernameInput.value.trim() : '',
            old_password: oldPasswordInput ? oldPasswordInput.value : '',
            new_password: newPasswordInput ? newPasswordInput.value : '',
            confirm_password: confirmPasswordInput ? confirmPasswordInput.value : ''
        };

        fetch('/accounts/change-password/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            },
            body: new URLSearchParams(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Hide change password popup first
                hidePopup();
                clearForm();

                // Use global notification popup for SUCCESS
                if (window.showNotification) {
                    window.showNotification(data.message || 'Đổi mật khẩu thành công', 'success');
                }
            } else {
                // Use global notification popup for ERROR
                if (window.showNotification) {
                    window.showNotification(data.message || 'Hệ thống lỗi, không thể thay đổi mật khẩu', 'error');
                } else {
                    showError(data.message || 'Hệ thống lỗi, không thể thay đổi mật khẩu');
                }
            }
        })
        .catch(error => {
            // Use global notification popup for ERROR
            if (window.showNotification) {
                window.showNotification('Hệ thống lỗi, không thể thay đổi mật khẩu', 'error');
            } else {
                showError('Hệ thống lỗi, không thể thay đổi mật khẩu');
            }
        });
    }

    // Event listeners - ONLY for cancel and close buttons (NOT overlay)
    if (closeBtn) {
        closeBtn.addEventListener('click', handleCancel);
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', handleCancel);
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', handleSave);
    }

    // Make showPopup globally accessible
    window.showChangePasswordPopup = showPopup;
});