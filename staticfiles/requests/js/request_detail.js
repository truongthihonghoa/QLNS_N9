document.addEventListener('DOMContentLoaded', function() {
    const detailPopup = document.getElementById('request-detail-popup');
    const viewButtons = document.querySelectorAll('.btn-view-detail, .btn-action-view'); // Tùy thuộc class nút ở bảng

    viewButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Hiển thị popup
            detailPopup.style.display = 'flex';

            // Ở đây bạn có thể dùng AJAX hoặc lấy data từ dòng để fill vào các id:
            // detail-employee-name, detail-date-start, v.v.
        });
    });

    // Đóng popup
    document.getElementById('detail-close-btn').addEventListener('click', () => {
        detailPopup.style.display = 'none';
    });
});