document.addEventListener('DOMContentLoaded', function() {
    const employeeForm = document.querySelector('.employee-form');
    const maNvInput = document.getElementById('id_ma_nv');
    const saveBtn = document.querySelector('.save-btn');
    const cancelBtn = document.querySelector('.cancel-btn');
    const confirmCancelPopup = document.getElementById('confirm-cancel-popup');
    const confirmNoBtn = document.getElementById('confirm-no-btn');
    const confirmYesBtn = document.getElementById('confirm-yes-btn');

    // --- Cancel Button Handler ---
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

    // ...existing code...
    if (maNvInput) {
        // Fetch mã nhân viên tiếp theo khi page load
        fetch('/nhan-vien/api/next-id/', {
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

    // ...existing code...
    const errorPopup = document.getElementById('error-popup');
    const errorPopupTitle = document.getElementById('error-popup-title');
    const errorPopupMsg1 = document.getElementById('error-popup-message1');
    const errorPopupMsg2 = document.getElementById('error-popup-message2');
    const errorPopupExitBtn = document.getElementById('error-popup-exit-btn');
    const errorPopupBackBtn = document.getElementById('error-popup-back-btn');

    function showErrorPopup(title, msg1, msg2) {
        if (errorPopup) {
            errorPopupTitle.textContent = title;
            errorPopupMsg1.textContent = msg1;
            errorPopupMsg2.textContent = msg2;
            errorPopup.style.display = 'flex';
        }
    }

    function hideErrorPopup() {
        if (errorPopup) errorPopup.style.display = 'none';
    }

    // --- Client-side Validation ---
    if (saveBtn) {
        saveBtn.addEventListener('click', function(event) {
            if (!employeeForm.checkValidity()) {
                event.preventDefault();
                showErrorPopup(
                    'THÔNG BÁO LỖI', 
                    'Xin vui lòng nhập đầy đủ thông tin!', 
                    ''
                );
            }
        });
    }

    // --- Server-side Error Handling ---
    const autoShowDuplicate = document.getElementById('auto-show-duplicate-popup');
    if (autoShowDuplicate) {
        showErrorPopup(
            'THÔNG BÁO LỖI', 
            'CCCD hoặc số điện thoại đã tồn tại?', 
            'Xin vui lòng nhập lại thông tin chính xác!'
        );
    }

    const autoShowInvalidInfo = document.getElementById('auto-show-invalid-info-popup');
    if (autoShowInvalidInfo) {
        showErrorPopup(
            'THÔNG BÁO LỖI', 
            'Thông tin không hợp lệ?', 
            'Xin vui lòng nhập lại thông tin chính xác!'
        );
    }

    // --- Popup Button Listeners ---
    if (errorPopupExitBtn) {
        errorPopupExitBtn.addEventListener('click', function() {
            window.location.href = employeeForm.dataset.employeeListUrl;
        });
    }

    if (errorPopupBackBtn) {
        errorPopupBackBtn.addEventListener('click', hideErrorPopup);
    }
    
    if (errorPopup) {
        errorPopup.addEventListener('click', function(event) {
            if (event.target === errorPopup) hideErrorPopup();
        });
    }
});
