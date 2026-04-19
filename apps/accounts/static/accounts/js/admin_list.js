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

    // Get accounts data from Django template
    const accounts = window.accountsData || {};

    // Modal elements
    const modals = {
        add: document.getElementById('add-account-modal'),
        edit: document.getElementById('edit-account-modal'),
        view: document.getElementById('view-account-modal')
    };

    // Open Add Modal
    const addModalBtn = document.querySelector('[data-open-modal="add-account-modal"]');
    if (addModalBtn) {
        addModalBtn.addEventListener('click', function() {
            console.log('Add modal button clicked');
            const modal = document.getElementById('add-account-modal');
            if (modal) {
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
            const viewPassword = document.getElementById('view-password');
            const viewRole = document.getElementById('view-role');

            if (viewUsername && viewPassword && viewRole) {
                viewUsername.value = username;
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
            const editPassword = document.getElementById('edit-password');
            const editRole = document.getElementById('edit-role');

            if (editUsername && editPassword && editRole) {
                editUsername.value = username;
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
                modal.classList.remove('is-visible');
                console.log('Modal closed via closest');
            } else if (this.dataset.closeModal) {
                // Handle buttons with data-close-modal attribute
                const targetModal = document.getElementById(this.dataset.closeModal);
                if (targetModal) {
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

    // Add Account
    document.getElementById('add-account-btn').addEventListener('click', function() {
        const form = document.getElementById('add-account-form');
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
                modals.add.classList.remove('is-visible');
                form.reset();
                // Reload page to show new data
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

    // View Account
    document.getElementById('view-account-btn').addEventListener('click', function() {
        console.log('View account confirmed');
        modals.view.classList.remove('is-visible');
    });

    // Edit Account
    document.getElementById('edit-account-btn').addEventListener('click', function() {
        const form = document.getElementById('edit-account-form');
        const formData = new FormData(form);

        fetch('/accounts/admin/edit/', {
            method: 'POST',
            'body': formData,
            'headers': {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('success', data.message);
                modals.edit.classList.remove('is-visible');
                form.reset();
                // Reload page to show updated data
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

    // Search
    document.getElementById('account-search-btn').addEventListener('click', function() {
        const searchTerm = document.getElementById('account-search-input').value.trim();
        if (searchTerm) {
            // Reload page with search parameter
            const url = new URL(window.location.href);
            url.searchParams.set('q', searchTerm);
            window.location.href = url.toString();
        } else {
            // Clear search and reload
            const url = new URL(window.location.href);
            url.searchParams.delete('q');
            window.location.href = url.toString();
        }
    });

    // Handle Enter key in search input
    document.getElementById('account-search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('account-search-btn').click();
        }
    });

    // Pre-fill search input from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const searchParam = urlParams.get('q');
    if (searchParam) {
        document.getElementById('account-search-input').value = searchParam;
    }
});