let payrollIdToDelete = null;
let rowToDelete = null;

// 1. Mở Popup khi nhấn thùng rác
function openDeletePayrollPopup(button) {
    const row = button.closest('tr');
    payrollIdToDelete = row.getAttribute('data-ma-luong');
    rowToDelete = row;

    const popup = document.getElementById('confirm-delete-popup');
    if (popup) {
        // Ép kiểu hiển thị flex để căn giữa theo CSS của GÉ CAFE
        popup.style.display = 'flex';
    } else {
        console.error("Không tìm thấy ID confirm-delete-popup");
    }
}

// 2. Đóng Popup
function closeDeletePayrollPopup() {
    const popup = document.getElementById('confirm-delete-popup');
    if (popup) {
        popup.style.display = 'none';
    }
    payrollIdToDelete = null;
    rowToDelete = null;
}

// 3. Xử lý xóa thật qua AJAX
// 3. Xử lý xóa thật qua AJAX
function confirmDeletePayroll() {
    if (!payrollIdToDelete) return;

    fetch(`/payroll/delete/${payrollIdToDelete}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // --- BƯỚC 1: GỬI TIN NHẮN CHO TRANG LIST (Ghi vào bộ nhớ trình duyệt) ---
            sessionStorage.setItem('payroll_success', 'true');
            sessionStorage.setItem('payroll_action', 'delete');

            // --- BƯỚC 2: ĐÓNG POPUP VÀ RELOAD ---
            closeDeletePayrollPopup();

            // Lệnh này sẽ làm trang List nạp lại, và nó sẽ tự đọc sessionStorage để hiện Toast
            window.location.reload();

        } else {
            // Nếu có lỗi cũng reload để đồng bộ dữ liệu
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Lỗi xóa:', error);
        if (typeof window.showToast === 'function') {
            window.showToast('Có lỗi xảy ra khi kết nối máy chủ!', 'error');
        } else {
            alert('Có lỗi xảy ra khi kết nối máy chủ!');
        }
    });
}

// Gán sự kiện cho các nút trong popup sau khi trang load xong
document.addEventListener('DOMContentLoaded', function() {
    const cancelBtn = document.getElementById('delete-popup-no-btn');
    if (cancelBtn) cancelBtn.onclick = closeDeletePayrollPopup;

    const confirmBtn = document.getElementById('delete-popup-yes-btn');
    if (confirmBtn) confirmBtn.onclick = confirmDeletePayroll;

    // Đóng khi click ra ngoài vùng popup
    const popupOverlay = document.getElementById('confirm-delete-popup');
    if (popupOverlay) {
        popupOverlay.onclick = function(e) {
            if (e.target === popupOverlay) closeDeletePayrollPopup();
        };
    }
});