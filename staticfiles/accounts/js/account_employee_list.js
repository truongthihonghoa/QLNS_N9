document.addEventListener('DOMContentLoaded', function () {
    const modalOverlays = document.querySelectorAll('.account-modal-overlay');
    const openButtons = document.querySelectorAll('[data-open-modal]');
    const closeButtons = document.querySelectorAll('[data-close-modal]');
    const cancelButtons = document.querySelectorAll('.js-open-cancel');
    const editButtons = document.querySelectorAll('.js-edit-account');
    const deactivateButtons = document.querySelectorAll('.js-deactivate-account');
    const addSaveButton = document.getElementById('add-account-save-btn');
    const editSaveButton = document.getElementById('edit-account-save-btn');
    const searchInput = document.getElementById('account-search-input');
    const searchButton = document.getElementById('account-search-btn');

    const cancelPopup = document.getElementById('confirm-cancel-popup');
    const deactivatePopup = document.getElementById('confirm-delete-popup');
    const successPopup = document.getElementById('success-popup');
    const errorPopup = document.getElementById('error-popup');

    const addUsername = document.getElementById('add-username');
    const addPassword = document.getElementById('add-password');
    const addRole = document.getElementById('add-role');
    const editUsername = document.getElementById('edit-username');
    const editRole = document.getElementById('edit-role');

    function openModal(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('is-visible');
        }
    }

    function closeModal(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.remove('is-visible');
        }
    }

    function closeAllModals() {
        modalOverlays.forEach((modal) => modal.classList.remove('is-visible'));
    }

    function showSuccess(message) {
        const title = document.getElementById('success-popup-title');
        const content = document.getElementById('success-popup-message');
        if (title) {
            title.textContent = 'THÔNG BÁO THÀNH CÔNG';
        }
        if (content) {
            content.textContent = message;
        }
        if (successPopup) {
            successPopup.style.display = 'flex';
        }
    }

    function showError(message1, message2) {
        const title = document.getElementById('error-popup-title');
        const line1 = document.getElementById('error-popup-message1');
        const line2 = document.getElementById('error-popup-message2');
        if (title) {
            title.textContent = 'THÔNG BÁO LỖI';
        }
        if (line1) {
            line1.textContent = message1;
        }
        if (line2) {
            line2.textContent = message2;
        }
        if (errorPopup) {
            errorPopup.style.display = 'flex';
        }
    }

    openButtons.forEach((button) => {
        button.addEventListener('click', function () {
            const targetModal = this.dataset.openModal;
            if (targetModal) {
                openModal(targetModal);
            }
        });
    });

    closeButtons.forEach((button) => {
        button.addEventListener('click', function () {
            const targetModal = this.dataset.closeModal;
            if (targetModal) {
                closeModal(targetModal);
            }
        });
    });

    modalOverlays.forEach((overlay) => {
        overlay.addEventListener('click', function (event) {
            if (event.target === overlay) {
                overlay.classList.remove('is-visible');
            }
        });
    });

    editButtons.forEach((button) => {
        button.addEventListener('click', function () {
            if (editUsername) {
                editUsername.value = this.dataset.username || '';
            }
            if (editRole) {
                editRole.value = this.dataset.role || 'Nhân viên';
            }
            openModal('edit-account-modal');
        });
    });

    cancelButtons.forEach((button) => {
        button.addEventListener('click', function () {
            if (!cancelPopup) {
                return;
            }
            cancelPopup.dataset.targetModal = this.dataset.closeModal || '';
            cancelPopup.style.display = 'flex';
        });
    });

    deactivateButtons.forEach((button) => {
        button.addEventListener('click', function () {
            if (!deactivatePopup) {
                return;
            }
            deactivatePopup.dataset.fullName = this.dataset.fullName || '';
            deactivatePopup.style.display = 'flex';
        });
    });

    if (addSaveButton) {
        addSaveButton.addEventListener('click', function () {
            if (!addUsername.value.trim() || !addPassword.value.trim() || !addRole.value) {
                showError('Dữ liệu chưa hợp lệ.', 'Vui lòng nhập đầy đủ thông tin bắt buộc.');
                return;
            }
            closeModal('add-account-modal');
            showSuccess('Thêm tài khoản thành công.');
        });
    }

    if (editSaveButton) {
        editSaveButton.addEventListener('click', function () {
            if (!editUsername.value.trim() || !editRole.value) {
                showError('Dữ liệu chưa hợp lệ.', 'Vui lòng kiểm tra lại thông tin chỉnh sửa.');
                return;
            }
            closeModal('edit-account-modal');
            showSuccess('Cập nhật tài khoản thành công.');
        });
    }

    const successCloseButton = document.getElementById('success-popup-confirm-btn');
    if (successCloseButton) {
        successCloseButton.addEventListener('click', function () {
            if (successPopup) {
                successPopup.style.display = 'none';
            }
        });
    }

    const errorExitButton = document.getElementById('error-popup-exit-btn');
    const errorBackButton = document.getElementById('error-popup-back-btn');
    if (errorExitButton) {
        errorExitButton.addEventListener('click', function () {
            if (errorPopup) {
                errorPopup.style.display = 'none';
            }
        });
    }
    if (errorBackButton) {
        errorBackButton.addEventListener('click', function () {
            if (errorPopup) {
                errorPopup.style.display = 'none';
            }
        });
    }

    const cancelNoButton = document.getElementById('confirm-no-btn');
    const cancelYesButton = document.getElementById('confirm-yes-btn');
    if (cancelNoButton) {
        cancelNoButton.addEventListener('click', function () {
            if (cancelPopup) {
                cancelPopup.style.display = 'none';
            }
        });
    }
    if (cancelYesButton) {
        cancelYesButton.addEventListener('click', function () {
            const target = cancelPopup ? cancelPopup.dataset.targetModal : '';
            if (cancelPopup) {
                cancelPopup.style.display = 'none';
            }
            if (target) {
                closeModal(target);
            }
        });
    }

    const deactivateNoButton = document.getElementById('delete-popup-no-btn');
    const deactivateYesButton = document.getElementById('delete-popup-yes-btn');
    if (deactivateNoButton) {
        deactivateNoButton.addEventListener('click', function () {
            if (deactivatePopup) {
                deactivatePopup.style.display = 'none';
            }
        });
    }
    if (deactivateYesButton) {
        deactivateYesButton.addEventListener('click', function () {
            const fullName = deactivatePopup ? deactivatePopup.dataset.fullName : '';
            if (deactivatePopup) {
                deactivatePopup.style.display = 'none';
            }
            showSuccess(`Đã cập nhật trạng thái ngừng hoạt động cho ${fullName}.`);
        });
    }

    function filterRows() {
        const keyword = (searchInput ? searchInput.value : '').trim().toLowerCase();
        const rows = document.querySelectorAll('#account-table-body tr');
        rows.forEach((row) => {
            const fullName = row.children[1] ? row.children[1].textContent.toLowerCase() : '';
            row.style.display = !keyword || fullName.includes(keyword) ? '' : 'none';
        });
    }

    if (searchButton) {
        searchButton.addEventListener('click', filterRows);
    }
    if (searchInput) {
        searchInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                filterRows();
            }
        });
    }

    closeAllModals();
});
