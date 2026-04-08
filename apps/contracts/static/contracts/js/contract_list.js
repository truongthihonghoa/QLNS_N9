document.addEventListener('DOMContentLoaded', function () {
    const detailPopup = document.getElementById('contract-detail-popup');
    const detailCloseBtn = document.getElementById('contract-detail-close-btn');
    const detailButtons = document.querySelectorAll('.detail-btn');
    const deletePopup = document.getElementById('confirm-delete-popup');
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const deleteNoBtn = document.getElementById('delete-popup-no-btn');
    const deleteYesBtn = document.getElementById('delete-popup-yes-btn');
    const deleteAlert = document.getElementById('contract-delete-alert');
    const deleteAlertClose = document.getElementById('contract-delete-alert-close');
    const deleteSuccessToast = document.getElementById('contract-delete-success-toast');
    const searchInput = document.getElementById('contract-search-input');
    const searchBtn = document.getElementById('contract-search-btn');
    const searchEmpty = document.getElementById('contract-search-empty');

    function getCookie(name) {
        const cookieValue = document.cookie
            .split(';')
            .map((cookie) => cookie.trim())
            .find((cookie) => cookie.startsWith(`${name}=`));
        return cookieValue ? decodeURIComponent(cookieValue.split('=').slice(1).join('=')) : '';
    }

    function getTableRows() {
        return Array.from(document.querySelectorAll('#contract-table-body tr'));
    }

    function normalizeText(value) {
        return String(value || '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/đ/g, 'd')
            .replace(/Đ/g, 'D')
            .toLowerCase()
            .trim();
    }

    function populateDetailModal(data) {
        const elements = {
            'detail-contract-id': data.ma_hd,
            'detail-contract-number': data.so_hd_hien_thi || data.ma_hd,
            'detail-signed-date': data.ngay_ky || data.ngay_bd,
            'detail-company-representative': data.dai_dien_ben_a || 'Truong Thi Hong Hoa',
            'detail-company-position': data.chuc_vu_ben_a || 'Quan ly GE CAFE - Chi nhanh Le Hong Phong',
            'detail-employee-name': (data.ten_nv || '').toUpperCase(),
            'detail-employee-code': data.ma_nv,
            'detail-birth-date': data.ngay_sinh || '15/05/1998',
            'detail-contract-type': data.loai_hd,
            'detail-start-date': data.ngay_bd,
            'detail-end-date': data.ngay_kt,
            'detail-salary-display': data.luong_hien_thi || data.tong_luong || data.muc_luong,
            'detail-position': data.chuc_vu,
            'detail-trang-thai': data.trang_thai || 'CO HIEU LUC',
            'detail-sign-a': data.dai_dien_ben_a || 'Truong Thi Hong Hoa',
            'detail-sign-b': data.ten_nv
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value || '';
            }
        });
    }

    function openDetailFromButton(button) {
        populateDetailModal({
            ma_hd: button.dataset.contractId,
            so_hd_hien_thi: button.dataset.contractId,
            ngay_ky: button.dataset.startDate,
            ten_nv: button.dataset.employeeName,
            ma_nv: button.dataset.employeeId,
            loai_hd: button.dataset.contractType,
            ngay_bd: button.dataset.startDate,
            ngay_kt: button.dataset.endDate,
            chuc_vu: button.dataset.position,
            luong_hien_thi: button.dataset.salary,
            trang_thai: 'CO HIEU LUC'
        });

        if (detailPopup) {
            detailPopup.style.display = 'flex';
        }
    }

    function updateVisibleIndexes() {
        let visibleIndex = 1;

        getTableRows().forEach((row) => {
            if (row.classList.contains('contract-row-hidden')) {
                return;
            }

            const sttCell = row.querySelector('.contract-stt');
            if (sttCell) {
                sttCell.textContent = visibleIndex;
            }
            visibleIndex += 1;
        });
    }

    function performSearch() {
        const keyword = normalizeText(searchInput ? searchInput.value : '');
        let visibleCount = 0;

        getTableRows().forEach((row) => {
            const cells = Array.from(row.querySelectorAll('td'));
            const searchText = normalizeText(cells
                .slice(1, 5)
                .map((cell) => cell.textContent || '')
                .join(' '));
            const isMatch = !keyword || searchText.includes(keyword);

            row.classList.toggle('contract-row-hidden', !isMatch);
            if (isMatch) {
                visibleCount += 1;
            }
        });

        updateVisibleIndexes();

        if (searchEmpty) {
            searchEmpty.classList.toggle('is-visible', visibleCount === 0);
        }
    }

    function parseDisplayDate(value) {
        const parts = String(value || '').split('/');
        if (parts.length !== 3) {
            return null;
        }

        const [day, month, year] = parts.map((part) => parseInt(part, 10));
        if (!day || !month || !year) {
            return null;
        }

        return new Date(year, month - 1, day);
    }

    function isContractStillActive(endDateText) {
        const endDate = parseDisplayDate(endDateText);
        if (!endDate) {
            return true;
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        endDate.setHours(0, 0, 0, 0);
        return endDate >= today;
    }

    function showDeleteAlert() {
        if (deleteAlert) {
            deleteAlert.classList.add('is-visible');
        }
    }

    function hideDeleteAlert() {
        if (deleteAlert) {
            deleteAlert.classList.remove('is-visible');
        }
    }

    function showDeleteSuccessToast() {
        if (!deleteSuccessToast) {
            return;
        }

        deleteSuccessToast.classList.add('is-visible');
        window.setTimeout(function () {
            deleteSuccessToast.classList.remove('is-visible');
        }, 2200);
    }

    detailButtons.forEach((button) => {
        button.addEventListener('click', function () {
            openDetailFromButton(this);
        });
    });

    if (detailCloseBtn) {
        detailCloseBtn.addEventListener('click', function () {
            detailPopup.style.display = 'none';
        });
    }

    if (detailPopup) {
        detailPopup.addEventListener('click', function (event) {
            if (event.target === detailPopup) {
                detailPopup.style.display = 'none';
            }
        });
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', performSearch);
    }

    if (searchInput) {
        searchInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                performSearch();
            }
        });
    }

    deleteButtons.forEach((button) => {
        button.addEventListener('click', function () {
            if (deletePopup) {
                deletePopup.dataset.deleteId = this.dataset.deleteId || '';
                deletePopup.style.display = 'flex';
            }
        });
    });

    if (deleteNoBtn) {
        deleteNoBtn.addEventListener('click', function () {
            deletePopup.style.display = 'none';
        });
    }

    if (deleteYesBtn) {
        deleteYesBtn.addEventListener('click', async function () {
            deletePopup.style.display = 'none';

            const deleteId = deletePopup.dataset.deleteId || '';
            const targetButton = Array.from(document.querySelectorAll('.delete-btn')).find((button) => (button.dataset.deleteId || '') === deleteId);
            if (!targetButton) return;

            try {
                const response = await fetch(`/contracts/${deleteId}/delete/`, {
                    method: 'DELETE',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });
                const data = await response.json();

                if (!response.ok || !data.success) {
                    if (data.error_code === 'ACTIVE_CONTRACT' || isContractStillActive(targetButton.dataset.endDate || '')) {
                        showDeleteAlert();
                    }
                    return;
                }

                const targetRow = targetButton.closest('tr');
                if (targetRow) {
                    targetRow.remove();
                }
                updateVisibleIndexes();
                if (searchEmpty) {
                    const visibleRows = Array.from(document.querySelectorAll('#contract-table-body tr')).filter((row) => !row.classList.contains('contract-row-hidden'));
                    searchEmpty.classList.toggle('is-visible', visibleRows.length === 0);
                }
                showDeleteSuccessToast();
            } catch (_error) {
                if (isContractStillActive(targetButton.dataset.endDate || '')) {
                    showDeleteAlert();
                }
            }
        });
    }

    if (deleteAlertClose) {
        deleteAlertClose.addEventListener('click', hideDeleteAlert);
    }

    if (deleteAlert) {
        deleteAlert.addEventListener('click', function (event) {
            if (event.target === deleteAlert) {
                hideDeleteAlert();
            }
        });
    }
});
