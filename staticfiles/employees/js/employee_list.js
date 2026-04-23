document.addEventListener('DOMContentLoaded', function () {
    const SUCCESS_TOAST_AUTO_HIDE_MS = 3000;
    const confirmDeletePopup = document.getElementById('confirm-delete-popup');
    const deletePopupNoBtn = document.getElementById('delete-popup-no-btn');
    const deletePopupYesBtn = document.getElementById('delete-popup-yes-btn');
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const employeeCards = document.querySelectorAll('.employee-card-modern-row');
    const successToast = document.getElementById('employee-success-toast');
    const successToastMessage = document.getElementById('employee-success-toast-message');
    let successToastTimer = null;

    function hideConfirmDeletePopup() {
        if (confirmDeletePopup) {
            confirmDeletePopup.style.display = 'none';
        }
    }

    function showConfirmDeletePopup() {
        if (confirmDeletePopup) {
            confirmDeletePopup.style.display = 'flex';
        }
    }

    function showSuccessToast(message) {
        if (!successToast) {
            return;
        }

        if (successToastMessage) {
            successToastMessage.textContent = message;
        }

        successToast.classList.add('is-visible');

        if (successToastTimer) {
            window.clearTimeout(successToastTimer);
        }

        successToastTimer = window.setTimeout(function () {
            hideSuccessToast();
        }, SUCCESS_TOAST_AUTO_HIDE_MS);
    }

    function hideSuccessToast() {
        if (successToast) {
            successToast.classList.remove('is-visible');
        }

        if (successToastTimer) {
            window.clearTimeout(successToastTimer);
            successToastTimer = null;
        }
    }

    employeeCards.forEach(function (card) {
        const detailUrl = card.dataset.detailUrl;
        if (!detailUrl) {
            return;
        }

        card.addEventListener('click', function (event) {
            if (event.target.closest('.card-action')) {
                return;
            }
            window.location.href = detailUrl;
        });

        card.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                window.location.href = detailUrl;
            }
        });
    });

    deleteButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation();
            showConfirmDeletePopup();
        });
    });

    if (deletePopupNoBtn) {
        deletePopupNoBtn.addEventListener('click', hideConfirmDeletePopup);
    }

    if (deletePopupYesBtn) {
        deletePopupYesBtn.addEventListener('click', hideConfirmDeletePopup);
    }

    if (confirmDeletePopup) {
        confirmDeletePopup.addEventListener('click', function (event) {
            if (event.target === confirmDeletePopup) {
                hideConfirmDeletePopup();
            }
        });
    }

    if (successToast && successToast.classList.contains('is-visible') && successToastMessage && successToastMessage.textContent.trim()) {
        showSuccessToast(successToastMessage.textContent.trim());
    }
});
