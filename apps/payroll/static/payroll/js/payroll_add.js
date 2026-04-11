document.addEventListener("DOMContentLoaded", function () {
    const card = document.querySelector(".payroll-employee-card");
    const saveBtn = document.querySelector(".save-btn");

    function parse(v) {
        if (!v) return 0;
        return Number(String(v).replace(/[^\d.-]/g, "")) || 0;
    }

    function recalc() {
        if (!card) return;
        const hours = parse(card.dataset.hours);
        const hourly = parse(card.dataset.hourly);
        const base = parse(card.dataset.base);
        const bonus = parse(card.querySelector(".bonus-input")?.value);
        const penalty = parse(card.querySelector(".penalty-input")?.value);

        const total = (hours * hourly) + base + bonus - penalty;
        const output = card.querySelector(".total-salary-input");
        if (output) output.value = total.toLocaleString('vi-VN') + " ₫";
        return total;
    }

    if (card) {
        card.querySelectorAll(".bonus-input, .penalty-input").forEach(el => {
            el.addEventListener("input", recalc);
        });
        recalc();
    }

    if (saveBtn && card) {
        saveBtn.addEventListener("click", function (e) {
            e.preventDefault();
            const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
            const remaining = document.getElementById("remaining_ids")?.value;

            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ĐANG LƯU...';

            const payload = new URLSearchParams({
                'ma_nv': card.dataset.maNv,
                'branch': document.querySelector("[name='branch']")?.value,
                'month': document.querySelector("[name='month']")?.value,
                'year': document.querySelector("[name='year']")?.value,
                'so_gio_lam': card.dataset.hours,
                'luong_theo_gio': card.dataset.hourly,
                'luong_co_ban': card.dataset.base,
                'tong_luong': recalc(),
                'thuong': card.querySelector(".bonus-input")?.value || 0,
                'phat': card.querySelector(".penalty-input")?.value || 0,
            });

            fetch(window.PAYROLL_SAVE_URL, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: payload
            })
            .then(res => res.json())
            .then(data => {
                if (!remaining || remaining.trim() === "" || remaining === "None") {
                    // --- KHỚP VỚI LOGIC CỦA FILE LIST BẠN GỬI ---
                    sessionStorage.setItem('payroll_success', 'true'); // Kích hoạt biến isSuccess ở List
                    sessionStorage.setItem('payroll_action', 'add');   // Để List hiện chữ "Thêm bảng lương thành công"
                    window.location.href = window.PAYROLL_LIST_URL;
                } else {
                    // Còn người thì nhảy sang người tiếp theo
                    const nextUrl = new URL(window.location.href);
                    nextUrl.searchParams.set('employees', remaining);
                    window.location.href = nextUrl.toString();
                }
            })
            .catch(err => {
                console.error("Lỗi:", err);
                saveBtn.innerText = "LỖI LƯU (F12)";
                saveBtn.disabled = false;
            });
        });
    }
});