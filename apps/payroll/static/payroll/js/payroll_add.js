document.addEventListener("DOMContentLoaded", function () {

    // 1. Hàm parse siêu sạch: giải quyết lỗi nhảy số hàng tỷ
    function parse(v) {
    if (v === undefined || v === null || v === "") return 0;

    return Number(
        String(v)
            .replace(/[^\d.-]/g, "") // chỉ giữ số, . và -
    ) || 0;
}

    // 2. Tính toán lại lương cho từng thẻ nhân viên
    function recalc(card) {
        const hours = parse(card.dataset.hours);    // ví dụ: 16.9
        const hourly = parse(card.dataset.hourly);  // ví dụ: 25000
        const base = parse(card.dataset.base);      // ví dụ: 3480000.0

        const bonus = parse(card.querySelector(".bonus-input")?.value);
        const penalty = parse(card.querySelector(".penalty-input")?.value);

        // Công thức chuẩn: (Giờ x Mức lương) + Lương cơ bản + Thưởng - Phạt
        const total = (hours * hourly) + base + bonus - penalty;

        // Lưu vào dataset để chuẩn bị gửi POST
        card.dataset.total = total;

        // Cập nhật UI với định dạng VN
        const output = card.querySelector(".total-salary-input");
        if (output) {
            output.value = total.toLocaleString('vi-VN') + " ₫";
        }
        return total;
    }

    // 3. Gán sự kiện cho các ô nhập liệu
    document.querySelectorAll(".payroll-employee-card").forEach(card => {

    const bonus = card.querySelector(".bonus-input");
    const penalty = card.querySelector(".penalty-input");

    if (bonus && !bonus.dataset.bound) {
        bonus.addEventListener("input", () => recalc(card));
        bonus.dataset.bound = "1";
    }

    if (penalty && !penalty.dataset.bound) {
        penalty.addEventListener("input", () => recalc(card));
        penalty.dataset.bound = "1";
    }

    recalc(card);
});

    // 4. Xử lý lưu dữ liệu
    const saveBtn = document.querySelector(".save-btn");
if (saveBtn) {
    saveBtn.addEventListener("click", function (e) {
        e.preventDefault();

        // Kiểm tra CSRF token
        const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
        const cards = document.querySelectorAll(".payroll-employee-card");

        // Lấy thông tin từ các thẻ input ẩn
        const branch = document.querySelector("input[name='branch']")?.value;
        const month = document.querySelector("input[name='month']")?.value;
        const year = document.querySelector("input[name='year']")?.value;

        if (!branch || !month || !year) {
            console.error("Thiếu thông tin chi nhánh hoặc kỳ lương!");
            return;
        }

        saveBtn.innerText = "ĐANG LƯU...";
        saveBtn.disabled = true;

        let done = 0;
        cards.forEach(card => {
            const ma_nv = card.dataset.maNv; // camelCase từ data-ma-nv
            const total = recalc(card); // Đảm bảo lấy số đã tính toán

            fetch(window.PAYROLL_SAVE_URL, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: new URLSearchParams({
                    'ma_nv': ma_nv,
                    'branch': branch,
                    'month': month,
                    'year': year,
                    'so_gio_lam': card.dataset.hours,
                    'luong_theo_gio': card.dataset.hourly,
                    'luong_co_ban': card.dataset.base,
                    'tong_luong': total,
                    'thuong': card.querySelector(".bonus-input")?.value || 0,
                    'phat': card.querySelector(".penalty-input")?.value || 0,
                })
            })
            .then(response => response.json())
            .then(data => {
                done++;
                if (done === cards.length) {
                    window.location.href = window.PAYROLL_LIST_URL;
                }
            })
            .catch(error => {
                console.error("Lỗi khi lưu nhân viên:", ma_nv, error);
                saveBtn.innerText = "LỖI LƯU (F12)";
                saveBtn.disabled = false;
            });
        });
    });
}
});