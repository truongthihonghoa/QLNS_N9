document.addEventListener('DOMContentLoaded', function () {
    const confirmDeletePopup = document.getElementById('confirm-delete-popup');
    const deletePopupNoBtn = document.getElementById('delete-popup-no-btn');
    const deletePopupYesBtn = document.getElementById('delete-popup-yes-btn');
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const employeeCards = document.querySelectorAll('.employee-card');

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
});
