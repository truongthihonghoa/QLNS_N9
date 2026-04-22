document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Script started');

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Helper function to show messages
    function showMessage(type, message) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.alert-message');
        existingMessages.forEach(msg => msg.remove());

        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert-message alert-${type}`;
        messageDiv.textContent = message;
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease;
        `;

        if (type === 'success') {
            messageDiv.style.backgroundColor = '#174d17';
        } else if (type === 'error') {
            messageDiv.style.backgroundColor = '#dc3545';
        }

        document.body.appendChild(messageDiv);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }

    // Delete Account - Using Common Delete Confirmation Popup
    // MOVED TO TOP TO ENSURE EXECUTION
    const deletePopup = document.getElementById('confirm-delete-popup');
    const deleteButtons = document.querySelectorAll('.js-delete-account');
    const deleteNoBtn = document.getElementById('delete-popup-no-btn');
    const deleteYesBtn = document.getElementById('delete-popup-yes-btn');

    console.log('Delete buttons found:', deleteButtons.length);
    console.log('Delete popup found:', !!deletePopup);
    console.log('Delete no btn found:', !!deleteNoBtn);
    console.log('Delete yes btn found:', !!deleteYesBtn);

    deleteButtons.forEach((button) => {
        button.addEventListener('click', function() {
            console.log('Delete button clicked, deleteId:', this.dataset.deleteId);
            if (deletePopup) {
                deletePopup.dataset.deleteId = this.dataset.deleteId || '';
                deletePopup.style.display = 'flex';
                console.log('Popup shown with deleteId:', deletePopup.dataset.deleteId);
            } else {
                console.error('Delete popup not found');
            }
        });
    });

    if (deleteNoBtn) {
        deleteNoBtn.addEventListener('click', function() {
            if (deletePopup) {
                deletePopup.style.display = 'none';
            }
        });
    }

    if (deleteYesBtn) {
        deleteYesBtn.addEventListener('click', async function() {
            console.log('Delete yes button clicked');
            if (!deletePopup) {
                console.error('Delete popup not found');
                return;
            }

            const deleteId = deletePopup.dataset.deleteId || '';
            console.log('Delete ID from popup:', deleteId);
            if (!deleteId) {
                console.error('No delete ID found');
                return;
            }

            const formData = new FormData();
            formData.append('username', deleteId);

            console.log('Sending delete request for username:', deleteId);

            try {
                const response = await fetch('/accounts/admin/delete/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });

                console.log('Delete response status:', response.status);
                const data = await response.json();
                console.log('Delete response data:', data);

                if (data.success) {
                    showMessage('success', data.message);
                    deletePopup.style.display = 'none';
                    // Remove the row from table
                    const targetButton = Array.from(deleteButtons).find((button) => (button.dataset.deleteId || '') === deleteId);
                    if (targetButton) {
                        const row = targetButton.closest('tr');
                        if (row) row.remove();
                    }
                    // Reload page to refresh data
                    setTimeout(() => location.reload(), 1500);
                } else {
                    console.error('Delete failed:', data.message);
                    showMessage('error', data.message);
                }
            } catch (error) {
                console.error('Error during delete:', error);
                showMessage('error', 'Đã xảy ra lỗi khi xóa tài khoản.');
            }
        });
    }

    // Accounts data is now purely read from the DOM when needed.

    // Modal elements
    const modals = {
        add: document.getElementById('add-account-modal'),
        edit: document.getElementById('edit-account-modal'),
        view: document.getElementById('view-account-modal')
    };

    function resetAddAccountEmployeeFormState() {
        const form = document.getElementById('add-account-form');
        if (!form) return;
        const displayInput = document.getElementById('add-employee-display');
        const hiddenMaNv = document.getElementById('add-ma-nv');
        const suggestions = document.getElementById('add-employee-suggestions');
        const accountMsg = document.getElementById('add-employee-account-msg');
        if (displayInput) displayInput.value = '';
        if (hiddenMaNv) hiddenMaNv.value = '';
        if (suggestions) {
            suggestions.innerHTML = '';
            suggestions.hidden = true;
        }
        if (accountMsg) {
            accountMsg.textContent = '';
            accountMsg.hidden = true;
        }
        const u = document.getElementById('add-username');
        const p = document.getElementById('add-password');
        const r = document.getElementById('add-role');
        if (u) u.value = '';
        if (p) p.value = '';
        if (r) r.value = '';
    }

    function initAddAccountEmployeeAutocomplete() {
        const form = document.getElementById('add-account-form');
        const displayInput = document.getElementById('add-employee-display');
        const hiddenMaNv = document.getElementById('add-ma-nv');
        const suggestions = document.getElementById('add-employee-suggestions');
        const accountMsg = document.getElementById('add-employee-account-msg');
        if (!form || !displayInput || !hiddenMaNv || !suggestions || !accountMsg) {
            return;
        }

        let debounceTimer = null;
        let activeIndex = -1;

        function hideSuggestions() {
            suggestions.innerHTML = '';
            suggestions.hidden = true;
            activeIndex = -1;
        }

        function hideAccountMsg() {
            accountMsg.textContent = '';
            accountMsg.hidden = true;
        }

        function selectEmployee(maNv, hoTen) {
            hiddenMaNv.value = maNv;
            displayInput.value = hoTen;
            hideSuggestions();
            fetch('/accounts/admin/employees/has-account/?ma_nv=' + encodeURIComponent(maNv))
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    if (!data || data.error === 'not_found' || data.error === 'missing_ma_nv') {
                        showMessage('error', 'Không tìm thấy nhân viên.');
                        return;
                    }
                    if (!data || typeof data.has_account === 'undefined') {
                        showMessage('error', 'Không kiểm tra được trạng thái tài khoản.');
                        return;
                    }
                    if (data.has_account) {
                        accountMsg.textContent = 'Đã có tài khoản';
                        accountMsg.hidden = false;
                    } else {
                        hideAccountMsg();
                    }
                })
                .catch(function () {
                    showMessage('error', 'Lỗi kết nối khi kiểm tra tài khoản.');
                });
        }

        displayInput.addEventListener('input', function () {
            hiddenMaNv.value = '';
            hideAccountMsg();
            const q = displayInput.value.trim();
            if (debounceTimer) clearTimeout(debounceTimer);
            if (q.length < 1) {
                hideSuggestions();
                return;
            }
            debounceTimer = setTimeout(function () {
                fetch('/accounts/admin/employees/search/?q=' + encodeURIComponent(q))
                    .then(function (r) {
                        return r.json();
                    })
                    .then(function (data) {
                        const results = data.results || [];
                        suggestions.innerHTML = '';
                        activeIndex = -1;
                        if (results.length === 0) {
                            suggestions.hidden = true;
                            return;
                        }
                        results.forEach(function (row) {
                            const li = document.createElement('li');
                            li.setAttribute('data-ma-nv', row.ma_nv);
                            li.setAttribute('data-ho-ten', row.ho_ten);
                            const nameSpan = document.createElement('span');
                            nameSpan.className = 'suggestion-name';
                            nameSpan.textContent = row.ho_ten;
                            const metaSpan = document.createElement('span');
                            metaSpan.className = 'suggestion-meta';
                            metaSpan.textContent = 'Mã NV: ' + row.ma_nv;
                            li.appendChild(nameSpan);
                            li.appendChild(metaSpan);
                            suggestions.appendChild(li);
                        });
                        suggestions.hidden = false;
                    })
                    .catch(function () {
                        hideSuggestions();
                    });
            }, 280);
        });

        suggestions.addEventListener('mousedown', function (e) {
            const li = e.target.closest('li[data-ma-nv]');
            if (!li) return;
            e.preventDefault();
            selectEmployee(li.getAttribute('data-ma-nv'), li.getAttribute('data-ho-ten'));
        });

        document.addEventListener('click', function (e) {
            const addModal = document.getElementById('add-account-modal');
            if (!addModal || !addModal.classList.contains('is-visible')) return;
            if (suggestions.hidden) return;
            if (displayInput.contains(e.target) || suggestions.contains(e.target)) return;
            hideSuggestions();
        });

        displayInput.addEventListener('keydown', function (e) {
            if (suggestions.hidden || !suggestions.children.length) return;
            const items = suggestions.querySelectorAll('li');
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeIndex = Math.min(activeIndex + 1, items.length - 1);
                items.forEach(function (el, i) {
                    el.classList.toggle('is-active', i === activeIndex);
                });
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeIndex = Math.max(activeIndex - 1, 0);
                items.forEach(function (el, i) {
                    el.classList.toggle('is-active', i === activeIndex);
                });
            } else if (e.key === 'Enter' && activeIndex >= 0) {
                e.preventDefault();
                const li = items[activeIndex];
                selectEmployee(li.getAttribute('data-ma-nv'), li.getAttribute('data-ho-ten'));
            } else if (e.key === 'Escape') {
                hideSuggestions();
            }
        });
    }

    initAddAccountEmployeeAutocomplete();

    // Open Add Modal
    const addModalBtn = document.querySelector('[data-open-modal="add-account-modal"]');
    if (addModalBtn) {
        addModalBtn.addEventListener('click', function() {
            console.log('Add modal button clicked');
            const modal = document.getElementById('add-account-modal');
            if (modal) {
                resetAddAccountEmployeeFormState();
                modal.classList.add('is-visible');
                console.log('Add modal opened');
            } else {
                console.error('Add modal not found');
            }
        });
    } else {
        console.error('Add modal button not found');
    }

    // View Account
    document.querySelectorAll('.account-btn-view').forEach(btn => {
        btn.addEventListener('click', function() {
            console.log('View button clicked');

            // Get data from table row
            const row = this.closest('tr');
            const cells = row.querySelectorAll('td');
            const username = this.dataset.accountId;
            const hoTen = cells[1].textContent.trim();
            const quyen = cells[3].textContent.trim();
            const trangThai = cells[4].querySelector('.account-status').textContent.trim();

            console.log('Account data:', { username, hoTen, quyen, trangThai });

            // Fill view form with real data
            const viewUsername = document.getElementById('view-username');
            const viewEmployee = document.getElementById('view-employee');
            const viewPassword = document.getElementById('view-password');
            const viewRole = document.getElementById('view-role');

            if (viewUsername && viewPassword && viewRole) {
                viewUsername.value = username;
                if (viewEmployee) viewEmployee.value = hoTen;
                viewRole.value = quyen;

                // Fetch password from backend
                fetch(`/accounts/admin/password/?username=${username}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.password) {
                            viewPassword.value = data.password;
                        } else {
                            // Password is hashed, cannot retrieve original
                            viewPassword.value = 'Mật khẩu đã mã hóa (không thể hiển thị)';
                            console.log(data.message);
                        }

                        if (modals.view) {
                            modals.view.classList.add('is-visible');
                            console.log('View modal opened with real data');
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching password:', error);
                        viewPassword.value = 'Lỗi khi tải mật khẩu';

                        if (modals.view) {
                            modals.view.classList.add('is-visible');
                        }
                    });
            } else {
                console.error('View form elements not found');
            }
        });
    });

    // Edit Account
    document.querySelectorAll('.account-btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            console.log('Edit button clicked');

            // Get data from table row
            const row = this.closest('tr');
            const cells = row.querySelectorAll('td');
            const username = this.dataset.accountId;
            const hoTen = cells[1].textContent.trim();
            const quyen = cells[3].textContent.trim();
            const trangThai = cells[4].querySelector('.account-status').textContent.trim();

            console.log('Account data:', { username, hoTen, quyen, trangThai });

            // Fill edit form with real data
            const editUsername = document.getElementById('edit-username');
            const editEmployee = document.getElementById('edit-employee');
            const editPassword = document.getElementById('edit-password');
            const editRole = document.getElementById('edit-role');

            if (editUsername && editPassword && editRole) {
                editUsername.value = username;
                if (editEmployee) editEmployee.value = hoTen;
                editPassword.value = ''; // Don't pre-fill password for security
                editRole.value = quyen;

                if (modals.edit) {
                    modals.edit.classList.add('is-visible');
                    console.log('Edit modal opened with real data');
                } else {
                    console.error('Edit modal not found');
                }
            } else {
                console.error('Edit form elements not found');
            }
        });
    });

    // Close Modals
    document.querySelectorAll('.modal-close-btn, .modal-cancel-btn, .account-modal-close, [data-close-modal]').forEach(btn => {
        btn.addEventListener('click', function() {
            console.log('Close button clicked:', this.className, this.dataset.closeModal);
            const modal = this.closest('.account-modal-overlay') || this.closest('.modal-overlay');
            if (modal) {
                if (modal.id === 'add-account-modal') {
                    resetAddAccountEmployeeFormState();
                }
                modal.classList.remove('is-visible');
                console.log('Modal closed via closest');
            } else if (this.dataset.closeModal) {
                // Handle buttons with data-close-modal attribute
                const targetModal = document.getElementById(this.dataset.closeModal);
                if (targetModal) {
                    if (targetModal.id === 'add-account-modal') {
                        resetAddAccountEmployeeFormState();
                    }
                    targetModal.classList.remove('is-visible');
                    console.log('Modal closed via data-close-modal:', this.dataset.closeModal);
                } else {
                    console.error('Target modal not found:', this.dataset.closeModal);
                }
            } else {
                console.error('No modal found to close');
            }
        });
    });

    // Close modal when clicking on overlay background
    document.querySelectorAll('.account-modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                if (this.id === 'add-account-modal') {
                    resetAddAccountEmployeeFormState();
                }
                this.classList.remove('is-visible');
            }
        });
    });

    // Password toggle functionality
    document.querySelectorAll('.toggle-password-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const input = document.getElementById(targetId);
            const icon = this.querySelector('.eye-icon');

            if (input.type === 'password') {
                input.type = 'text';
                icon.src = icon.src.replace('eye_opened.png', 'eye_closed.png');
            } else {
                input.type = 'password';
                icon.src = icon.src.replace('eye_closed.png', 'eye_opened.png');
            }
        });
    });

    const addAccountBtn = document.getElementById('add-account-btn');
    if (addAccountBtn) {
        addAccountBtn.addEventListener('click', function() {
            const form = document.getElementById('add-account-form');
            if (!form) return;
            const maNv = (document.getElementById('add-ma-nv') || {}).value;
            if (!maNv || !maNv.trim()) {
                showMessage('error', 'Vui lòng chọn nhân viên từ danh sách gợi ý.');
                return;
            }
            const accountMsg = document.getElementById('add-employee-account-msg');
            if (accountMsg && !accountMsg.hidden && accountMsg.textContent === 'Đã có tài khoản') {
                showMessage('error', 'Không thể lưu: nhân viên đã có tài khoản.');
                return;
            }
            const formData = new FormData(form);

            fetch('/accounts/admin/add/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage('success', data.message);
                        if (modals.add) modals.add.classList.remove('is-visible');
                        form.reset();
                        resetAddAccountEmployeeFormState();
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        showMessage('error', data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('error', 'Đã xảy ra lỗi khi thêm tài khoản.');
                });
        });
    }

    const viewAccountBtn = document.getElementById('view-account-btn');
    if (viewAccountBtn && modals.view) {
        viewAccountBtn.addEventListener('click', function() {
            modals.view.classList.remove('is-visible');
        });
    }

    const editAccountBtn = document.getElementById('edit-account-btn');
    if (editAccountBtn) {
        editAccountBtn.addEventListener('click', function() {
            const form = document.getElementById('edit-account-form');
            if (!form) return;
            const formData = new FormData(form);

            fetch('/accounts/admin/edit/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage('success', data.message);
                        if (modals.edit) modals.edit.classList.remove('is-visible');
                        form.reset();
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        showMessage('error', data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('error', 'Đã xảy ra lỗi khi cập nhật tài khoản.');
                });
        });
    }

    // Search (chỉ gắn nếu trang có ô tìm kiếm JS — admin_list dùng form GET)
    const accountSearchBtn = document.getElementById('account-search-btn');
    const accountSearchInput = document.getElementById('account-search-input');
    if (accountSearchBtn && accountSearchInput) {
        accountSearchBtn.addEventListener('click', function() {
            const searchTerm = accountSearchInput.value.trim();
            const url = new URL(window.location.href);
            if (searchTerm) {
                url.searchParams.set('q', searchTerm);
            } else {
                url.searchParams.delete('q');
            }
            window.location.href = url.toString();
        });

        accountSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                accountSearchBtn.click();
            }
        });

        const searchParam = new URLSearchParams(window.location.search).get('q');
        if (searchParam) {
            accountSearchInput.value = searchParam;
        }
    }
});