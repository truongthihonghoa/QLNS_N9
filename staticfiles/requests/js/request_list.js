document.addEventListener('DOMContentLoaded', function() {
    // Mock data for 5 requests
    const mockRequests = [
        {
            id: 'DK000001',
            ma_dk: 'DK000001',
            ten_nv: 'Nguyễn Văn An',
            ma_nv: 'NV001',
            loai: 'nghi-phep',
            loai_display: 'Nghỉ phép',
            ngay_dang_ky: '26/12/2026',
            trang_thai: 'cho-duyet',
            trang_thai_display: 'Chờ duyệt',
            ngay_bat_dau: '26/12/2026',
            ngay_ket_thuc: '27/12/2026',
            ly_do: 'Đi khám sức khỏe',
            ngay_lam: '',
            gio_bat_dau: '',
            gio_ket_thuc: '',
            ghi_chu: ''
        },
        {
            id: 'DK000002',
            ma_dk: 'DK000002',
            ten_nv: 'Nguyễn Thanh Anh',
            ma_nv: 'NV002',
            loai: 'nghi-phep',
            loai_display: 'Nghỉ phép',
            ngay_dang_ky: '26/02/2025',
            trang_thai: 'cho-duyet',
            trang_thai_display: 'Chờ duyệt',
            ngay_bat_dau: '26/02/2025',
            ngay_ket_thuc: '28/02/2025',
            ly_do: 'Việc gia đình',
            ngay_lam: '',
            gio_bat_dau: '',
            gio_ket_thuc: '',
            ghi_chu: ''
        },
        {
            id: 'DK000003',
            ma_dk: 'DK000003',
            ten_nv: 'Nguyễn Văn Anh',
            ma_nv: 'NV003',
            loai: 'ca-lam',
            loai_display: 'Ca làm',
            ngay_dang_ky: '08/02/2026',
            trang_thai: 'da-duyet',
            trang_thai_display: 'Đã duyệt',
            ngay_lam: '08/02/2026',
            gio_bat_dau: '08:00',
            gio_ket_thuc: '17:00',
            ghi_chu: 'Làm ca sáng',
            ngay_bat_dau: '',
            ngay_ket_thuc: '',
            ly_do: ''
        },
        {
            id: 'DK000004',
            ma_dk: 'DK000004',
            ten_nv: 'Trần Minh Quân',
            ma_nv: 'NV004',
            loai: 'nghi-phep',
            loai_display: 'Nghỉ phép',
            ngay_dang_ky: '02/06/2025',
            trang_thai: 'tu-choi',
            trang_thai_display: 'Đã từ chối',
            ngay_bat_dau: '05/06/2025',
            ngay_ket_thuc: '06/06/2025',
            ly_do: 'Du lịch',
            ngay_lam: '',
            gio_bat_dau: '',
            gio_ket_thuc: '',
            ghi_chu: ''
        },
        {
            id: 'DK000005',
            ma_dk: 'DK000005',
            ten_nv: 'Lê Thị Hồng',
            ma_nv: 'NV005',
            loai: 'ca-lam',
            loai_display: 'Ca làm',
            ngay_dang_ky: '05/06/2025',
            trang_thai: 'cho-duyet',
            trang_thai_display: 'Chờ duyệt',
            ngay_lam: '05/06/2025',
            gio_bat_dau: '14:00',
            gio_ket_thuc: '22:00',
            ghi_chu: 'Làm ca chiều',
            ngay_bat_dau: '',
            ngay_ket_thuc: '',
            ly_do: ''
        }
    ];

    // State
    let currentRequestId = '';
    let currentFilterStatus = 'all';
    let currentFilterType = '';
    let currentSearch = '';

    // DOM Elements
    const formPopup = document.getElementById('request-form-popup');
    const detailPopup = document.getElementById('request-detail-popup');
    const deletePopup = document.getElementById('delete-confirm-popup');
    const rejectPopup = document.getElementById('reject-reason-popup');
    const toast = document.getElementById('toast-message');

    // Form elements
    const requestForm = document.getElementById('request-form');
    const requestType = document.getElementById('request-type');
    const caLamFields = document.getElementById('ca-lam-fields');
    const nghiPhepFields = document.getElementById('nghi-phep-fields');

    // Tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');

    // Search and filter
    const searchInput = document.getElementById('search-input');
    const btnSearch = document.getElementById('btn-search');
    const filterType = document.getElementById('filter-type');

    // Helper functions
    function showPopup(popup) {
        if (popup) popup.style.display = 'flex';
    }

    function hidePopup(popup) {
        if (popup) popup.style.display = 'none';
    }

    function showToast(message, type = 'success') {
        const toastText = document.getElementById('toast-text');
        if (toastText) toastText.textContent = message;
        if (toast) {
            toast.className = 'toast ' + type;
            toast.style.display = 'block';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        } else {
            alert(message);
        }
    }

    function clearErrors() {
        document.querySelectorAll('.error-message').forEach(el => {
            el.textContent = '';
            el.style.display = 'none';
        });
    }

    function showError(fieldId, message) {
        const errorEl = document.getElementById('error-' + fieldId);
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }
    }

    // Toggle form fields based on request type
    requestType?.addEventListener('change', function() {
        const type = this.value;
        if (type === 'ca-lam') {
            caLamFields.style.display = 'block';
            nghiPhepFields.style.display = 'none';
        } else if (type === 'nghi-phep') {
            caLamFields.style.display = 'none';
            nghiPhepFields.style.display = 'block';
        } else {
            caLamFields.style.display = 'none';
            nghiPhepFields.style.display = 'none';
        }
    });

    // Validation
    function validateForm() {
        clearErrors();
        let isValid = true;

        const type = requestType.value;
        if (!type) {
            showError('request-type', 'Vui lòng chọn loại yêu cầu');
            isValid = false;
        }

        if (type === 'ca-lam') {
            const ngayLam = document.getElementById('ngay-lam').value;
            const gioBatDau = document.getElementById('gio-bat-dau').value;
            const gioKetThuc = document.getElementById('gio-ket-thuc').value;

            if (!ngayLam) {
                showError('ngay-lam', 'Vui lòng chọn ngày làm');
                isValid = false;
            }

            if (!gioBatDau) {
                showError('gio-bat-dau', 'Vui lòng chọn giờ bắt đầu');
                isValid = false;
            }

            if (!gioKetThuc) {
                showError('gio-ket-thuc', 'Vui lòng chọn giờ kết thúc');
                isValid = false;
            }

            if (gioBatDau && gioKetThuc && gioKetThuc <= gioBatDau) {
                showError('gio-ket-thuc', 'Giờ kết thúc phải sau giờ bắt đầu');
                isValid = false;
            }
        }

        if (type === 'nghi-phep') {
            const ngayBatDau = document.getElementById('ngay-bat-dau').value;
            const ngayKetThuc = document.getElementById('ngay-ket-thuc').value;
            const lyDo = document.getElementById('ly-do').value.trim();

            if (!ngayBatDau) {
                showError('ngay-bat-dau', 'Vui lòng chọn ngày bắt đầu');
                isValid = false;
            }

            if (!ngayKetThuc) {
                showError('ngay-ket-thuc', 'Vui lòng chọn ngày kết thúc');
                isValid = false;
            }

            if (ngayBatDau && ngayKetThuc && ngayKetThuc < ngayBatDau) {
                showError('ngay-ket-thuc', 'Ngày kết thúc phải sau ngày bắt đầu');
                isValid = false;
            }

            if (!lyDo) {
                showError('ly-do', 'Vui lòng nhập lý do');
                isValid = false;
            }
        }

        return isValid;
    }

    // Create/Edit form submission
    requestForm?.addEventListener('submit', function(event) {
        event.preventDefault();

        if (!validateForm()) return;

        const requestId = document.getElementById('request-id').value;
        const isEdit = !!requestId;

        // Mock success
        hidePopup(formPopup);
        requestForm.reset();
        caLamFields.style.display = 'none';
        nghiPhepFields.style.display = 'none';

        if (isEdit) {
            showToast('Cập nhật thành công');
        } else {
            showToast('Gửi đăng ký thành công');
        }
    });

    // Open create form
    document.getElementById('btn-create-request')?.addEventListener('click', function() {
        document.getElementById('form-title').textContent = 'Tạo đăng ký';
        document.getElementById('request-id').value = '';
        requestForm.reset();
        caLamFields.style.display = 'none';
        nghiPhepFields.style.display = 'none';
        clearErrors();
        showPopup(formPopup);
    });

    // Close form popup
    document.getElementById('form-close-btn')?.addEventListener('click', function() {
        hidePopup(formPopup);
    });

    document.getElementById('form-cancel-btn')?.addEventListener('click', function() {
        hidePopup(formPopup);
    });

    // View detail
    document.querySelectorAll('.btn-view').forEach(btn => {
        btn.addEventListener('click', function() {
            const requestId = this.dataset.requestId;
            const request = mockRequests.find(r => r.id === requestId);
            if (request) {
                showDetailPopup(request);
            }
        });
    });

    function showDetailPopup(request) {
        document.getElementById('detail-employee-name').textContent = request.ten_nv;
        document.getElementById('detail-employee-code').textContent = 'Mã nhân viên - ' + request.ma_nv;
        document.getElementById('detail-request-code').textContent = request.ma_dk;
        document.getElementById('detail-request-type').textContent = request.loai_display;
        document.getElementById('detail-ngay-dang-ky').textContent = request.ngay_dang_ky;
        
        const statusEl = document.getElementById('detail-status');
        statusEl.textContent = request.trang_thai_display;
        statusEl.className = 'value status-' + request.trang_thai;

        // Show/hide fields based on request type
        const ngayLamRow = document.getElementById('detail-ngay-lam-row');
        const gioRow = document.getElementById('detail-gio-row');
        const ngayNghiRow = document.getElementById('detail-ngay-nghi-row');
        const lyDoRow = document.getElementById('detail-ly-do-row');

        if (request.loai === 'ca-lam') {
            ngayLamRow.style.display = 'flex';
            gioRow.style.display = 'flex';
            ngayNghiRow.style.display = 'none';
            lyDoRow.style.display = 'none';
            document.getElementById('detail-ngay-lam').textContent = request.ngay_lam;
            document.getElementById('detail-gio').textContent = request.gio_bat_dau + ' - ' + request.gio_ket_thuc;
        } else {
            ngayLamRow.style.display = 'none';
            gioRow.style.display = 'none';
            ngayNghiRow.style.display = 'flex';
            lyDoRow.style.display = 'flex';
            document.getElementById('detail-ngay-nghi').textContent = request.ngay_bat_dau + ' - ' + request.ngay_ket_thuc;
            document.getElementById('detail-ly-do').textContent = request.ly_do;
        }

        // Show/hide approve/reject buttons
        const actionsEl = document.getElementById('detail-actions');
        if (request.trang_thai === 'cho-duyet') {
            actionsEl.style.display = 'flex';
        } else {
            actionsEl.style.display = 'none';
        }

        currentRequestId = requestId;
        showPopup(detailPopup);
    }

    document.getElementById('detail-close-btn')?.addEventListener('click', function() {
        hidePopup(detailPopup);
    });

    // Edit request
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const requestId = this.dataset.requestId;
            const request = mockRequests.find(r => r.id === requestId);
            if (!request) return;

            // Only allow editing if status is "cho-duyet"
            if (request.trang_thai !== 'cho-duyet') {
                showToast('Chỉ được sửa yêu cầu đang chờ duyệt', 'error');
                return;
            }

            document.getElementById('form-title').textContent = 'Chỉnh sửa đăng ký';
            document.getElementById('request-id').value = request.id;
            requestType.value = request.loai;

            if (request.loai === 'ca-lam') {
                caLamFields.style.display = 'block';
                nghiPhepFields.style.display = 'none';
                document.getElementById('ngay-lam').value = request.ngay_lam;
                document.getElementById('gio-bat-dau').value = request.gio_bat_dau;
                document.getElementById('gio-ket-thuc').value = request.gio_ket_thuc;
                document.getElementById('ghi-chu').value = request.ghi_chu || '';
            } else {
                caLamFields.style.display = 'none';
                nghiPhepFields.style.display = 'block';
                document.getElementById('ngay-bat-dau').value = request.ngay_bat_dau;
                document.getElementById('ngay-ket-thuc').value = request.ngay_ket_thuc;
                document.getElementById('ly-do').value = request.ly_do || '';
            }

            clearErrors();
            showPopup(formPopup);
        });
    });

    // Delete request
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            const requestId = this.dataset.requestId;
            const request = mockRequests.find(r => r.id === requestId);
            if (!request) return;

            // Only allow deleting if status is "cho-duyet"
            if (request.trang_thai !== 'cho-duyet') {
                showToast('Chỉ được xóa yêu cầu đang chờ duyệt', 'error');
                return;
            }

            currentRequestId = requestId;
            showPopup(deletePopup);
        });
    });

    document.getElementById('btn-delete-no')?.addEventListener('click', function() {
        hidePopup(deletePopup);
    });

    document.getElementById('btn-delete-yes')?.addEventListener('click', function() {
        hidePopup(deletePopup);
        showToast('Xóa đăng ký thành công');
    });

    // Approve request
    document.getElementById('btn-approve')?.addEventListener('click', function() {
        hidePopup(detailPopup);
        showToast('Duyệt yêu cầu thành công');
    });

    // Reject request
    document.getElementById('btn-reject')?.addEventListener('click', function() {
        hidePopup(detailPopup);
        showPopup(rejectPopup);
    });

    document.getElementById('reject-close-btn')?.addEventListener('click', function() {
        hidePopup(rejectPopup);
    });

    document.getElementById('btn-cancel-reject')?.addEventListener('click', function() {
        hidePopup(rejectPopup);
    });

    document.getElementById('btn-confirm-reject')?.addEventListener('click', function() {
        const reason = document.getElementById('reject-reason').value.trim();
        if (!reason) {
            showError('reject-reason', 'Vui lòng nhập lý do từ chối');
            return;
        }
        hidePopup(rejectPopup);
        document.getElementById('reject-reason').value = '';
        showToast('Từ chối yêu cầu thành công');
    });

    // Tab filtering
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            tabButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentFilterStatus = this.dataset.status;
            filterTable();
        });
    });

    // Type filtering
    filterType?.addEventListener('change', function() {
        currentFilterType = this.value;
        filterTable();
    });

    // Search
    btnSearch?.addEventListener('click', function() {
        currentSearch = searchInput.value.toLowerCase().trim();
        filterTable();
    });

    searchInput?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            currentSearch = this.value.toLowerCase().trim();
            filterTable();
        }
    });

    function filterTable() {
        const rows = document.querySelectorAll('.request-row');
        rows.forEach(row => {
            const status = row.dataset.status;
            const type = row.dataset.type;
            const name = row.cells[2].textContent.toLowerCase();

            const matchStatus = currentFilterStatus === 'all' || status === currentFilterStatus;
            const matchType = !currentFilterType || type === currentFilterType;
            const matchSearch = !currentSearch || name.includes(currentSearch);

            row.style.display = (matchStatus && matchType && matchSearch) ? '' : 'none';
        });
    }

    // Close popups on overlay click
    [formPopup, detailPopup, deletePopup, rejectPopup].forEach(popup => {
        if (popup) {
            popup.addEventListener('click', function(event) {
                if (event.target === popup) {
                    hidePopup(popup);
                }
            });
        }
    });
});
