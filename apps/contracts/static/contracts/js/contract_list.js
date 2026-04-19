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
    const branchFilter = document.getElementById('branch-filter-select');

    if (branchFilter) {
        branchFilter.addEventListener('change', function() {
            const url = new URL(window.location.href);
            if (this.value) {
                url.searchParams.set('branch', this.value);
            } else {
                url.searchParams.delete('branch');
            }
            // Giữ lại tham số tìm kiếm nếu có
            window.location.href = url.toString();
        });
    }

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

    function formatNumber(num) {
        if (!num) return '0';
        return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
    }

    function populateDetailModal(data) {
        const elements = {
            'detail-contract-id': data.ma_hd,
            'detail-contract-no-display': data.ma_hd,
            'detail-employee-code-display': data.ma_nv,

            // Bên A
            'detail-nguoi-dai-dien': data.nguoi_dai_dien || '',
            'detail-chuc-vu-dai-dien': data.chuc_vu_dai_dien || 'Quản lý Chi nhánh',
            'detail-phone-ben-a': data.sdt_dai_dien || '',
            'detail-sig-name-a': data.nguoi_dai_dien || '',

            // Bên B
            'detail-ten-nv': data.ten_nv || '',
            'detail-ma-nv': data.ma_nv || '',
            'detail-cccd': data.cccd || '',
            'detail-ngay-sinh': data.ngay_sinh || '',
            'detail-phone-ben-b': data.sdt_nv || '',
            'detail-dia-chi': data.dia_chi || '',
            'detail-sig-name-b': data.ten_nv || '',

            // Điều khoản
            'detail-loai-hd': data.loai_hd || '',
            'detail-ngay-bd': data.ngay_bd || '',
            'detail-ngay-kt': data.ngay_kt || '',
            'detail-chuc-vu-nv': data.chuc_vu || '',
            'detail-dia-diem-lv': data.dia_diem_lv || '',
            'detail-so-gio-lam': data.so_gio_lam || '0',
            'detail-luong-co-ban': formatNumber(data.muc_luong || data.luong_co_ban),
            'detail-luong-theo-gio': formatNumber(data.luong_theo_gio),

            // Xử lý ghi chú: Nếu trống thì ghi "Không"
            'detail-ghi-chu': (data.ghi_chu && data.ghi_chu.trim() !== '' && data.ghi_chu !== 'Không có ghi chú.') ? data.ghi_chu : 'Không'
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    async function openDetailFromButton(button) {
        const contractId = button.dataset.contractId;

        try {
            const response = await fetch(`/contracts/${contractId}/detail/`);
            if (response.ok) {
                const data = await response.json();
                populateDetailModal(data);
            } else {
                // Fallback nếu API lỗi
                populateDetailModal({
                    ma_hd: button.dataset.contractId,
                    ma_nv: button.dataset.employeeId,
                    ten_nv: button.dataset.employeeName,
                    loai_hd: button.dataset.contractType,
                    ngay_bd: button.dataset.startDate,
                    ngay_kt: button.dataset.endDate,
                    chuc_vu: button.dataset.position,
                    muc_luong: button.dataset.salary,
                    cccd: button.dataset.cccd,
                    ngay_sinh: button.dataset.birthDate,
                    sdt_nv: button.dataset.phoneNv,
                    dia_chi: button.dataset.address,
                    nguoi_dai_dien: button.dataset.representative,
                    chuc_vu_dai_dien: button.dataset.repPosition,
                    sdt_dai_dien: button.dataset.repPhone,
                    dia_diem_lv: button.dataset.workPlace,
                    so_gio_lam: button.dataset.workHours,
                    luong_theo_gio: button.dataset.hourlySalary,
                    ghi_chu: button.dataset.notes
                });
            }
        } catch (err) {
            console.error('Lỗi khi lấy chi tiết hợp đồng:', err);
        }

        if (detailPopup) {
            detailPopup.style.display = 'flex';
        }
    }

    function updateVisibleIndexes() {
        let visibleIndex = 1;
        getTableRows().forEach((row) => {
            if (row.classList.contains('contract-row-hidden')) return;
            const sttCell = row.querySelector('.contract-stt');
            if (sttCell) sttCell.textContent = visibleIndex++;
        });
    }

    function performSearch() {
        const keyword = normalizeText(searchInput ? searchInput.value : '');
        let visibleCount = 0;
        getTableRows().forEach((row) => {
            const searchText = normalizeText(row.innerText);
            const isMatch = !keyword || searchText.includes(keyword);
            row.classList.toggle('contract-row-hidden', !isMatch);
            if (isMatch) visibleCount++;
        });
        updateVisibleIndexes();
        if (searchEmpty) searchEmpty.classList.toggle('is-visible', visibleCount === 0);
    }

    function parseDisplayDate(value) {
        const parts = String(value || '').split('/');
        if (parts.length !== 3) return null;
        const [day, month, year] = parts.map((part) => parseInt(part, 10));
        return new Date(year, month - 1, day);
    }

    function isContractStillActive(endDateText) {
        const endDate = parseDisplayDate(endDateText);
        if (!endDate) return true;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        endDate.setHours(0, 0, 0, 0);
        return endDate >= today;
    }

    detailButtons.forEach((button) => {
        button.addEventListener('click', function () {
            openDetailFromButton(this);
        });
    });

    if (detailCloseBtn) {
        detailCloseBtn.addEventListener('click', () => detailPopup.style.display = 'none');
    }

    if (detailPopup) {
        detailPopup.addEventListener('click', (e) => { if (e.target === detailPopup) detailPopup.style.display = 'none'; });
    }

    if (searchBtn) searchBtn.addEventListener('click', performSearch);
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); performSearch(); } });
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
        deleteNoBtn.addEventListener('click', () => {
            if (deletePopup) deletePopup.style.display = 'none';
        });
    }

    if (deleteYesBtn) {
        deleteYesBtn.addEventListener('click', async function () {
            const deleteId = deletePopup.dataset.deleteId;
            if (deletePopup) deletePopup.style.display = 'none';

            try {
                const response = await fetch(`/contracts/${deleteId}/delete/`, {
                    method: 'DELETE',
                    headers: { 
                        'X-Requested-With': 'XMLHttpRequest', 
                        'X-CSRFToken': getCookie('csrftoken') 
                    },
                });
                
                const data = await response.json();

                if (response.ok && data.success) {
                    // Show Success Toast at bottom-right
                    if (deleteSuccessToast) {
                        deleteSuccessToast.classList.add('is-visible');
                        
                        // Wait 3 seconds then remove row and hide
                        setTimeout(() => {
                            deleteSuccessToast.classList.remove('is-visible');
                            // Remove row from UI
                            const row = document.querySelector(`.delete-btn[data-delete-id="${deleteId}"]`).closest('tr');
                            if (row) {
                                row.remove();
                                updateVisibleIndexes();
                            }
                        }, 3000);
                    } else {
                        location.reload();
                    }
                } else {
                    // Show Centered Alert (Active Contract or Other Error)
                    if (deleteAlert) {
                        deleteAlert.classList.add('is-visible');
                        
                        // Auto-hide alert after 3 seconds
                        setTimeout(() => {
                            deleteAlert.classList.remove('is-visible');
                        }, 3000);
                    } else {
                        alert(data.message || 'Không thể xóa hợp đồng này');
                    }
                }
            } catch (err) { 
                console.error('Lỗi khi xóa hợp đồng:', err);
            }
        });
    }

    if (deleteAlertClose) {
        deleteAlertClose.addEventListener('click', () => {
            if (deleteAlert) deleteAlert.classList.remove('is-visible');
        });
    }
});
