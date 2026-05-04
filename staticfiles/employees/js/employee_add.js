document.addEventListener('DOMContentLoaded', function() {
    const employeeForm = document.querySelector('.employee-form');
    const maNvInput = document.getElementById('id_ma_nv');
    const saveBtn = document.querySelector('.save-btn');
    const cancelBtn = document.querySelector('.cancel-btn');
    const confirmCancelPopup = document.getElementById('confirm-cancel-popup');
    const confirmNoBtn = document.getElementById('confirm-no-btn');
    const confirmYesBtn = document.getElementById('confirm-yes-btn');
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
                avatarPreview.src = defaultAvatarSrc;
                avatarPreview.classList.add('upload-icon');
                avatarPreview.classList.add('is-empty');
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

    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(event) {
            event.preventDefault();
            if (confirmCancelPopup) {
                confirmCancelPopup.style.display = 'flex';
                return;
            }
            window.location.href = employeeForm.dataset.employeeListUrl;
        });
    }

    if (confirmNoBtn) {
        confirmNoBtn.addEventListener('click', function() {
            confirmCancelPopup.style.display = 'none';
        });
    }

    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', function() {
            window.location.href = employeeForm.dataset.employeeListUrl;
        });
    }

    if (confirmCancelPopup) {
        confirmCancelPopup.addEventListener('click', function(event) {
            if (event.target === confirmCancelPopup) {
                confirmCancelPopup.style.display = 'none';
            }
        });
    }

    if (maNvInput) {
        fetch('/employees/api/next-id/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.next_id) {
                maNvInput.value = data.next_id;
            }
        })
        .catch(error => console.error('Error fetching next employee ID:', error));
    }

    function showErrorPopup(title, msg1, msg2) {
        if (typeof window.showToast === 'function') {
            window.showToast(msg1, 'error');
        } else {
            alert(msg1);
        }
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', function(event) {
            if (!employeeForm.checkValidity()) {
                event.preventDefault();
                showErrorPopup('THÔNG BÁO LỖI', 'Xin vui lòng nhập đầy đủ thông tin!', '');
            }
        });
    }

    const autoShowInvalidInfo = document.getElementById('auto-show-invalid-info-popup');
    if (autoShowInvalidInfo) {
        showErrorPopup('THÔNG BÁO LỖI', 'Thông tin không hợp lệ?', 'Xin vui lòng nhập lại thông tin chính xác!');
    }

    bindAvatarUpload();
});
