document.addEventListener('DOMContentLoaded', function() {
    console.log('DEBUG: DOM loaded, initializing login.js');

    // --- CSRF Token Helper Function ---
    // Gets the CSRF token from the cookie, which is the most reliable method for AJAX.
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // --- Element Selection ---
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    const forgotPasswordPopup = document.getElementById('forgot-password-popup');
    const closeForgotPasswordBtn = document.getElementById('close-forgot-password-btn');
    const cancelForgotPasswordBtn = document.getElementById('cancel-forgot-password-btn');
    const forgotPasswordForm = document.getElementById('forgot-password-form');

    // --- Popup Functions ---
    function showForgotPasswordPopup() {
        if (forgotPasswordPopup) {
            forgotPasswordPopup.style.display = 'flex';
            forgotPasswordPopup.classList.add('show');
            console.log('DEBUG: Forgot password popup shown');
        } else {
            console.error('ERROR: Forgot password popup element not found!');
        }
    }

    function closeForgotPasswordPopup() {
        if (forgotPasswordPopup) {
            forgotPasswordPopup.style.display = 'none';
            forgotPasswordPopup.classList.remove('show');
            if (forgotPasswordForm) forgotPasswordForm.reset();
            console.log('DEBUG: Forgot password popup closed');
        }
    }

    // --- Event Listeners for Popup ---
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            showForgotPasswordPopup();
        });
    }

    const closeHandler = (e) => {
        e.preventDefault();
        if (typeof showConfirm === 'function') {
            showConfirm('XÁC NHẬN HỦY', 'Bạn có thông tin chưa lưu, xác nhận hủy?', (confirmed) => {
                if (confirmed) {
                    closeForgotPasswordPopup();
                }
            });
        } else {
            if (confirm('Bạn có thông tin chưa lưu, xác nhận hủy?')) {
                closeForgotPasswordPopup();
            }
        }
    };

    if (closeForgotPasswordBtn) closeForgotPasswordBtn.addEventListener('click', closeHandler);
    if (cancelForgotPasswordBtn) cancelForgotPasswordBtn.addEventListener('click', closeHandler);
    
    // --- Form Submission Logic ---
    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default page reload
            console.log('DEBUG: Form submitted via JavaScript. Handling with fetch...');
            handleSavePassword(this);
        });
    }

    function handleSavePassword(form) {
        const showAlert = window.showAlert || alert;

        // Basic frontend validation
        if (!form.reset_username.value.trim()) {
            showAlert('Lỗi', 'Vui lòng nhập tên đăng nhập!');
            return;
        }
        if (form.new_password.value.length < 8 || !/\d/.test(form.new_password.value) || !/[a-zA-Z]/.test(form.new_password.value)) {
            showAlert('Lỗi', 'Mật khẩu phải có ít nhất 8 ký tự, bao gồm cả chữ và số.');
            return;
        }
        if (form.new_password.value !== form.confirm_new_password.value) {
            showAlert('Lỗi', 'Mật khẩu xác nhận không khớp!');
            return;
        }
        
        const formData = new FormData(form);
        const url = form.action;
        const savePasswordBtn = form.querySelector('#save-password-btn');
        const csrftoken = getCookie('csrftoken'); // Get token from cookie

        if (!csrftoken) {
            showAlert('Lỗi nghiêm trọng', 'Không tìm thấy CSRF token. Vui lòng tải lại trang.');
            return;
        }

        if (savePasswordBtn) {
            savePasswordBtn.innerHTML = '<span class="text-wrapper-4-popup">Đang xử lý...</span>';
            savePasswordBtn.disabled = true;
        }

        console.log(`DEBUG: Sending fetch POST to ${url} with CSRF token.`);

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrftoken // Use the token from the cookie
            }
        })
        .then(response => {
            if (!response.ok) {
                // The server responded with an error status (4xx, 5xx)
                console.error(`Server responded with error: ${response.status}`);
                // We attempt to parse the JSON body for an error message, but it might fail
                return response.json().catch(() => {
                    throw new Error(`Lỗi server: ${response.status}`);
                }).then(errData => {
                    throw new Error(errData.message || `Lỗi server: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showAlert('Thành công', 'Đổi mật khẩu thành công. Mật khẩu mới đã được cập nhật.');
                closeForgotPasswordPopup();
            } else {
                showAlert('Lỗi', data.message || 'Có lỗi xảy ra từ phía server!');
            }
        })
        .catch(error => {
            console.error('Fetch Error:', error);
            // This catch block now handles true network errors OR errors thrown from the .then block
            showAlert('Lỗi', error.message || 'Không thể kết nối đến server. Vui lòng kiểm tra console của server Django.');
        })
        .finally(() => {
            if (savePasswordBtn) {
                savePasswordBtn.innerHTML = '<span class="text-wrapper-4-popup">Lưu Mật Khẩu</span>';
                savePasswordBtn.disabled = false;
            }
        });
    }

    // --- Password Toggle Functions ---
    window.togglePasswordVisibility = function() {
        const passwordInput = document.getElementById('password');
        const eyeIcon = document.getElementById('eye-icon');
        if (passwordInput && eyeIcon) {
            passwordInput.type = (passwordInput.type === 'password') ? 'text' : 'password';
            eyeIcon.style.opacity = (passwordInput.type === 'password') ? '1' : '0.5';
        }
    };

    window.toggleNewPasswordVisibility = function() {
        const passwordInput = document.getElementById('new-password');
        const eyeIcon = document.getElementById('new-password-eye');
        if (passwordInput && eyeIcon) {
            passwordInput.type = (passwordInput.type === 'password') ? 'text' : 'password';
            eyeIcon.style.opacity = (passwordInput.type === 'password') ? '1' : '0.5';
        }
    };

    window.toggleConfirmPasswordVisibility = function() {
        const passwordInput = document.getElementById('confirm-new-password');
        const eyeIcon = document.getElementById('confirm-password-eye');
        if (passwordInput && eyeIcon) {
            passwordInput.type = (passwordInput.type === 'password') ? 'text' : 'password';
            eyeIcon.style.opacity = (passwordInput.type === 'password') ? '1' : '0.5';
        }
    };
});
