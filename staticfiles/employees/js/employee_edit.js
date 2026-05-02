document.addEventListener('DOMContentLoaded', function() {
    const employeeForm = document.querySelector('.employee-form');
    const saveBtn = document.querySelector('.save-btn');
    const cancelBtn = document.querySelector('.cancel-btn');
    const avatarInput = document.getElementById('id_anh_dai_dien');
    const avatarTrigger = document.getElementById('employee-avatar-trigger');
    const avatarPreview = document.getElementById('employee-avatar-preview');
    const defaultAvatarSrc = avatarPreview ? avatarPreview.getAttribute('src') : '';

    function bindAvatarUpload() {
        if (!avatarInput || !avatarTrigger || !avatarPreview) {
            return;
        }

        avatarTrigger.addEventListener('click', function() {
            avatarInput.click();
        });

        avatarInput.addEventListener('change', function(event) {
            const [file] = event.target.files || [];
            if (!file) {
                if (defaultAvatarSrc) {
                    avatarPreview.src = defaultAvatarSrc;
                    avatarPreview.classList.toggle('is-empty', avatarPreview.naturalWidth === 0);
                    avatarPreview.classList.toggle('upload-icon', avatarPreview.naturalWidth === 0);
                }
                return;
            }

            const reader = new FileReader();
            reader.onload = function(loadEvent) {
                avatarPreview.src = loadEvent.target.result;
                avatarPreview.classList.remove('upload-icon');
                avatarPreview.classList.remove('is-empty');
            };
            reader.readAsDataURL(file);
        });
    }

    function showErrorPopup(title, msg1, msg2) {
        if (typeof window.showToast === 'function') {
            window.showToast(msg1, 'error');
        } else {
            alert(msg1);
        }
    }

    const confirmCancelPopup = document.getElementById('confirm-cancel-popup');
    const confirmNoBtn = document.getElementById('confirm-no-btn');
    const confirmYesBtn = document.getElementById('confirm-yes-btn');

    function showConfirmCancelPopup() {
        if (confirmCancelPopup) {
            confirmCancelPopup.style.display = 'flex';
        }
    }

    function hideConfirmCancelPopup() {
        if (confirmCancelPopup) {
            confirmCancelPopup.style.display = 'none';
        }
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', showConfirmCancelPopup);
    }
    if (confirmNoBtn) {
        confirmNoBtn.addEventListener('click', hideConfirmCancelPopup);
    }
    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', () => window.location.href = employeeForm.dataset.returnUrl || employeeForm.dataset.employeeListUrl);
    }
    if (confirmCancelPopup) {
        confirmCancelPopup.addEventListener('click', (event) => {
            if (event.target === confirmCancelPopup) {
                hideConfirmCancelPopup();
            }
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', function(event) {
            if (!employeeForm.checkValidity()) {
                event.preventDefault();
                showErrorPopup('THÔNG BÁO LỖI', 'Xin vui lòng nhập đầy đủ thông tin!', '');
            }
        });
    }

    bindAvatarUpload();
});
