document.addEventListener("DOMContentLoaded", function () {
    // 1. DỮ LIỆU TỪ LOCALSTORAGE
    const storageKey = 'mock_schedules';
    let savedData = JSON.parse(localStorage.getItem(storageKey)) || {};

    const shifts = [
        { key: "morning", label: "Ca Sáng", time: "06:00 - 12:00", className: "is-morning" },
        { key: "afternoon", label: "Ca Chiều", time: "12:00 - 17:00", className: "is-afternoon" },
        { key: "evening", label: "Ca Tối", time: "17:00 - 22:00", className: "is-evening" },
    ];

    const weekdayLabels = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"];
    const scheduleBoard = document.getElementById("schedule-board");
    const miniCalendar = document.getElementById("mini-calendar");
    const calendarTitle = document.getElementById("calendar-title");
    const currentWeekLabel = document.getElementById("current-week-label");
    const prevWeekBtn = document.getElementById("prev-week-btn");
    const nextWeekBtn = document.getElementById("next-week-btn");
    const modal = document.getElementById("shift-detail-modal");
    const modalCloseBtn = document.getElementById("modal-close-btn");
    const modalConfirmBtn = document.getElementById("modal-confirm-btn");

    let currentWeekStart = startOfWeek(new Date()); // Bắt đầu từ tuần hiện tại
    let selectedDate = new Date(); // Ngày được chọn mặc định là hôm nay

    function addDays(date, days) {
        const next = new Date(date);
        next.setDate(next.getDate() + days);
        return next;
    }

    function formatKey(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
    }

    function startOfWeek(date) {
        const start = new Date(date);
        const day = start.getDay();
        const offset = day === 0 ? -6 : 1 - day; // Thứ 2 là 1, CN là 0. Chuyển CN thành 7 để tính offset
        start.setDate(start.getDate() + offset);
        start.setHours(0, 0, 0, 0);
        return start;
    }

    // 2. KIỂM TRA ĐIỀU KIỆN 1 NGÀY (USE CASE 4.2, 4.3)
    function canEditOrDelete(dateStr) {
        const shiftDate = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Chuẩn hóa về đầu ngày
        shiftDate.setHours(0, 0, 0, 0); // Chuẩn hóa về đầu ngày

        const diffTime = shiftDate.getTime() - today.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); // Tính số ngày chênh lệch

        return diffDays >= 1; // Chỉ cho phép chỉnh sửa/xóa nếu ca làm còn ít nhất 1 ngày
    }

    function renderBoard() {
        const days = Array.from({ length: 7 }, (_, i) => addDays(currentWeekStart, i));
        scheduleBoard.innerHTML = "";

        const corner = document.createElement("div");
        corner.className = "board-corner";
        scheduleBoard.appendChild(corner);

        days.forEach((day, index) => {
            const header = document.createElement("div");
            const dateKey = formatKey(day);
            header.className = `board-day${dateKey === formatKey(selectedDate) ? " is-highlight" : ""}`;
            header.innerHTML = `${weekdayLabels[index]}<span class="date">${day.getDate()}/${day.getMonth() + 1}</span>`;
            scheduleBoard.appendChild(header);
        });

        shifts.forEach((shift) => {
            const timeLabel = document.createElement("div");
            timeLabel.className = "board-time";
            timeLabel.textContent = shift.label;
            scheduleBoard.appendChild(timeLabel);

            days.forEach((day) => {
                const dateKey = formatKey(day);
                const shiftData = savedData[dateKey]?.[shift.key];

                // Tạo container cho mỗi ô ca làm để chứa button và icons
                const cellContainer = document.createElement("div");
                cellContainer.className = "shift-cell-container";
                cellContainer.style.position = "relative"; // Để định vị tuyệt đối cho icons

                const button = document.createElement("button");
                button.type = "button";
                button.className = `shift-pill ${shift.className}${shiftData ? "" : " is-empty"}`;

                if (shiftData && shiftData.details && shiftData.details.length > 0) {
                    // Hiển thị tên nhân viên kèm vị trí
                    const names = shiftData.details.map(e => `${e.name} (${e.role})`).join("<br>");
                    button.innerHTML = names;
                    button.onclick = () => openModal(dateKey, shift.key);

                    // THÊM BIỂU TƯỢNG EDIT/DELETE
                    if (canEditOrDelete(dateKey)) {
                        const actionGroup = document.createElement("div");
                        actionGroup.className = "shift-actions";
                        actionGroup.style.cssText = `
                            position: absolute;
                            bottom: 5px;
                            right: 5px;
                            display: flex;
                            gap: 8px;
                            z-index: 10;
                            background-color: rgba(255, 255, 255, 0.8); /* Nền nhẹ để dễ nhìn icon */
                            padding: 3px 5px;
                            border-radius: 5px;
                        `;

                        const editIcon = document.createElement("i");
                        editIcon.className = "fas fa-pencil-alt"; // Biểu tượng bút chì
                        editIcon.style.cssText = `
                            color: #406a45;
                            cursor: pointer;
                            font-size: 12px;
                            transition: color 0.2s ease;
                        `;
                        editIcon.title = "Chỉnh sửa lịch làm việc";
                        editIcon.onmouseover = () => editIcon.style.color = "#315235"; // Màu đậm hơn khi hover
                        editIcon.onmouseout = () => editIcon.style.color = "#406a45";
                        editIcon.onclick = (e) => {
                            e.stopPropagation(); // Ngăn sự kiện click của button cha
                            handleEditShift(shiftData, dateKey, shift.label);
                        };

                        const deleteIcon = document.createElement("i");
                        deleteIcon.className = "fas fa-trash-alt"; // Biểu tượng thùng rác
                        deleteIcon.style.cssText = `
                            color: #406a45;
                            cursor: pointer;
                            font-size: 12px;
                            transition: color 0.2s ease;
                        `;
                        deleteIcon.title = "Xóa lịch làm việc";
                        deleteIcon.onmouseover = () => deleteIcon.style.color = "#315235"; // Màu đậm hơn khi hover
                        deleteIcon.onmouseout = () => deleteIcon.style.color = "#406a45";
                        deleteIcon.onclick = (e) => {
                            e.stopPropagation(); // Ngăn sự kiện click của button cha
                            handleDeleteShift(dateKey, shift.key);
                        };

                        actionGroup.appendChild(editIcon);
                        actionGroup.appendChild(deleteIcon);
                        cellContainer.appendChild(actionGroup);
                    }
                } else {
                    button.textContent = shift.label; // Hiển thị tên ca nếu không có người
                }

                cellContainer.appendChild(button);
                scheduleBoard.appendChild(cellContainer);
            });
        });

        currentWeekLabel.textContent = `${days[0].getDate()}/${days[0].getMonth()+1} - ${days[6].getDate()}/${days[6].getMonth()+1}`;
        calendarTitle.textContent = `Tháng ${days[0].getMonth() + 1} ${days[0].getFullYear()}`;
    }

    // 3. LOGIC XỬ LÝ SỰ KIỆN (EVENT HANDLING)
    function handleEditShift(shiftData, dateKey, shiftLabel) {
        // Logic thực tế: Mở modal form chỉnh sửa và điền dữ liệu
        if (typeof window.showToast === 'function') {
            window.showToast(`Chỉnh sửa lịch làm việc: ${dateKey} - ${shiftLabel}`, 'info');
        } else {
            alert(`Chỉnh sửa lịch làm việc:\nNgày: ${dateKey}\nCa: ${shiftLabel}\nID Lịch: ${shiftData.id}\nNhân viên: ${shiftData.details.map(e => e.name).join(', ')}`);
        }
        // Ví dụ chuyển hướng đến trang chỉnh sửa:
        // window.location.href = `/schedules/edit/${shiftData.id}`;
    }

    function handleDeleteShift(dateKey, shiftKey) {
        if (confirm("Bạn có chắc chắn muốn xóa ca làm việc này?")) {
            if (savedData[dateKey] && savedData[dateKey][shiftKey]) {
                delete savedData[dateKey][shiftKey];
                localStorage.setItem(storageKey, JSON.stringify(savedData));
                if (typeof window.showToast === 'function') {
                    window.showToast("Đã xóa ca làm thành công!");
                } else {
                    alert("Đã xóa ca làm thành công!");
                }
                renderBoard(); // Render lại bảng để cập nhật giao diện
            } else {
                if (typeof window.showToast === 'function') {
                    window.showToast("Không tìm thấy ca làm việc để xóa.", "error");
                } else {
                    alert("Không tìm thấy ca làm việc để xóa.");
                }
            }
        }
    }

    function renderMiniCalendar() {
        const year = currentWeekStart.getFullYear();
        const month = currentWeekStart.getMonth();
        const firstDay = new Date(year, month, 1);
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const startOffset = (firstDay.getDay() + 6) % 7;

        miniCalendar.innerHTML = "";
        ["T2", "T3", "T4", "T5", "T6", "T7", "CN"].forEach(label => {
            const div = document.createElement("div");
            div.className = "mini-calendar-weekday";
            div.textContent = label;
            miniCalendar.appendChild(div);
        });

        for (let i = 0; i < startOffset; i++) miniCalendar.appendChild(document.createElement("div"));

        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day);
            const dateKey = formatKey(date);
            const cell = document.createElement("div");
            cell.className = `mini-calendar-day${dateKey === formatKey(selectedDate) ? " is-selected" : ""}`;
            cell.textContent = day;
            cell.onclick = () => {
                selectedDate = new Date(date);
                currentWeekStart = startOfWeek(selectedDate);
                renderBoard();
                renderMiniCalendar();
            };
            miniCalendar.appendChild(cell);
        }
    }

    function openModal(dateKey, shiftKey) {
        const shiftData = savedData[dateKey]?.[shiftKey];
        if (!shiftData) return;

        document.getElementById("modal-schedule-id").textContent = shiftData.id;
        document.getElementById("modal-date").textContent = dateKey;
        // Cập nhật các thông tin khác của modal nếu cần

        const list = document.getElementById("modal-employee-list");
        list.innerHTML = shiftData.details.map(e => `
            <tr>
                <td><input type="checkbox"></td>
                <td>${e.id}</td>
                <td>${e.name}</td>
                <td>${e.role}</td>
                <td>${e.status}</td>
            </tr>
        `).join("");

        modal.classList.add("show");
    }

    modalCloseBtn.onclick = () => modal.classList.remove("show");
    modalConfirmBtn.onclick = () => modal.classList.remove("show");
    prevWeekBtn.onclick = () => { currentWeekStart = addDays(currentWeekStart, -7); renderBoard(); renderMiniCalendar(); };
    nextWeekBtn.onclick = () => { currentWeekStart = addDays(currentWeekStart, 7); renderBoard(); renderMiniCalendar(); };

    // Khởi tạo bảng và lịch khi tải trang
    renderBoard();
    renderMiniCalendar();
});
