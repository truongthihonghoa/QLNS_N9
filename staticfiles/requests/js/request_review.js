document.addEventListener('DOMContentLoaded', function () {
    const detailModal = document.getElementById('request-detail-modal');
    const detailButtons = document.querySelectorAll('[data-open-modal="request-detail-modal"]');
    const closeButtons = document.querySelectorAll('[data-close-modal="request-detail-modal"]');
    const detailName = document.getElementById('request-detail-name');
    const detailCode = document.getElementById('request-detail-code');
    const detailGrid = document.getElementById('request-detail-grid');

    function renderRows(rows) {
        if (!detailGrid) {
            return;
        }

        detailGrid.innerHTML = '';

        rows.forEach((row) => {
            const rowElement = document.createElement('div');
            rowElement.className = 'request-detail-row';

            const label = document.createElement('div');
            label.className = 'request-detail-label';
            label.textContent = `${row.label}:`;

            const value = document.createElement('div');
            value.className = 'request-detail-value';
            value.textContent = row.value;

            rowElement.append(label, value);
            detailGrid.appendChild(rowElement);
        });
    }

    detailButtons.forEach((button) => {
        button.addEventListener('click', function () {
            if (detailName) {
                detailName.textContent = this.dataset.employeeName || '';
            }
            if (detailCode) {
                detailCode.textContent = `Mã nhân viên - ${this.dataset.employeeCode || ''}`;
            }
            renderRows(this.dataset.rows ? JSON.parse(this.dataset.rows) : []);
            if (detailModal) {
                detailModal.classList.add('is-visible');
            }
        });
    });

    closeButtons.forEach((button) => {
        button.addEventListener('click', function () {
            if (detailModal) {
                detailModal.classList.remove('is-visible');
            }
        });
    });

    if (detailModal) {
        detailModal.addEventListener('click', function (event) {
            if (event.target === detailModal) {
                detailModal.classList.remove('is-visible');
            }
        });
    }
    // Approve/Reject Action Logic
    const approveBtn = document.querySelector('.request-approve-btn');
    const rejectBtn = document.querySelector('.request-reject-btn');

    function showToast(message, type = 'success') {
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
        } else {
            alert(message);
        }
    }

    if (approveBtn) {
        approveBtn.addEventListener('click', function() {
            showToast('Duyệt yêu cầu thành công!');
            if (detailModal) detailModal.classList.remove('is-visible');
        });
    }

    if (rejectBtn) {
        rejectBtn.addEventListener('click', function() {
            showToast('Từ chối yêu cầu thành công!', 'info');
            if (detailModal) detailModal.classList.remove('is-visible');
        });
    }
});
