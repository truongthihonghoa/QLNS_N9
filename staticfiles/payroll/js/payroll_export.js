document.addEventListener('DOMContentLoaded', function () {
    const selectAll = document.getElementById('export-select-all');
    const rows = document.querySelectorAll('.export-row-checkbox');
    const confirmPopup = document.getElementById('confirm-delete-popup');
    const actionButtons = [
        document.getElementById('approve-payroll-btn'),
        document.getElementById('export-payroll-btn'),
        document.getElementById('print-payroll-btn'),
    ];

    if (selectAll) {
        selectAll.addEventListener('change', function () {
            rows.forEach((row) => {
                row.checked = selectAll.checked;
            });
        });
    }

    rows.forEach((row) => {
        row.addEventListener('change', function () {
            if (!selectAll) {
                return;
            }
            const checkedCount = Array.from(rows).filter((item) => item.checked).length;
            selectAll.checked = checkedCount === rows.length;
            selectAll.indeterminate = checkedCount > 0 && checkedCount < rows.length;
        });
    });

    actionButtons.forEach((button) => {
        if (!button) {
            return;
        }
        button.addEventListener('click', function () {
            if (confirmPopup) {
                confirmPopup.style.display = 'flex';
            }
        });
    });

    const deleteNoBtn = document.getElementById('delete-popup-no-btn');
    const deleteYesBtn = document.getElementById('delete-popup-yes-btn');
    if (deleteNoBtn) {
        deleteNoBtn.addEventListener('click', function () {
            if (confirmPopup) {
                confirmPopup.style.display = 'none';
            }
        });
    }
    if (deleteYesBtn) {
        deleteYesBtn.addEventListener('click', function () {
            if (confirmPopup) {
                confirmPopup.style.display = 'none';
            }
        });
    }
});
