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
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
        } else {
            // Fallback if showToast not defined
            alert(message);
        }
    }

    // Delete Account - Using Common Delete Confirmation Popup
    // MOVED TO TOP TO ENSURE EXECUTION
    const deletePopup = document.getElementById('confirm-delete-popup');
    const deleteButtons = document.querySelectorAll('.js-toggle-account');
    const deleteNoBtn = document.getElementById('delete-popup-no-btn');
    const deleteYesBtn = document.getElementById('delete-popup-yes-btn');

    console.log('Delete buttons found:', deleteButtons.length);
    console.log('Delete popup found:', !!deletePopup);
    console.log('Delete no btn found:', !!deleteNoBtn);
    console.log('Delete yes btn found:', !!deleteYesBtn);

    deleteButtons.forEach((button) => {
        button.addEventListener('click', function() {
            console.log('Toggle status button clicked, accountId:', this.dataset.accountId);
            if (deletePopup) {
                deletePopup.dataset.deleteId = this.dataset.accountId || '';
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
                const response = await fetch('/accounts/admin/toggle-status/', {
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
                console.error('Error during status toggle:', error);
                showMessage('error', 'Đã xảy ra lỗi khi cập nhật trạng thái tài khoản.');
            }
        });
    }

    // Autocomplete logic for Add Account
    const allEmployees = window.allEmployees || [];
    const employeesWithAccount = window.employeesWithAccount || [];

    const addEmpNameInput = document.getElementById('add-employee-name');
    const addEmpIdInput = document.getElementById('add-employee-id');
    const addSuggestionsList = document.getElementById('add-employee-suggestions');
    const addErrorText = document.getElementById('add-account-exists-error');

    if (addEmpNameInput) {
        addEmpNameInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            addSuggestionsList.innerHTML = '';
            addErrorText.style.display = 'none';
            addEmpIdInput.value = '';

            if (query.length < 1) {
                addSuggestionsList.style.display = 'none';
                return;
            }

            const matches = allEmployees.filter(emp =>
                emp.ho_ten.toLowerCase().includes(query) ||
                emp.ma_nv.toLowerCase().includes(query)
            );

            if (matches.length > 0) {
                matches.forEach(emp => {
                    const div = document.createElement('div');
                    div.className = 'suggestion-item';
                    div.innerHTML = `
                        <div class="emp-name-main">${emp.ho_ten}</div>
                        <div class="emp-code-sub">Mã NV: ${emp.ma_nv}</div>
                    `;
                    div.addEventListener('click', function() {
                        addEmpNameInput.value = emp.ho_ten;
                        addEmpIdInput.value = emp.ma_nv;
                        addSuggestionsList.style.display = 'none';

                        // Check if already has account
                        if (employeesWithAccount.includes(emp.ma_nv)) {
                            addErrorText.style.display = 'block';
                        }
                    });
                    addSuggestionsList.appendChild(div);
                });
                addSuggestionsList.style.display = 'block';
            } else {
                addSuggestionsList.style.display = 'none';
            }
        });

        // Close suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!addEmpNameInput.contains(e.target) && !addSuggestionsList.contains(e.target)) {
                addSuggestionsList.style.display = 'none';
            }
        });
    }

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
            if (modals.add) {
                modals.add.classList.add('is-visible');
                // Reset form
                document.getElementById('add-account-form').reset();
                addErrorText.style.display = 'none';
                addSuggestionsList.style.display = 'none';
            }
        });
    }

    // View Account
    document.querySelectorAll('.account-btn-view').forEach(btn => {
        btn.addEventListener('click', function() {
            const username = this.dataset.accountId;
            const row = this.closest('tr');
            const fullname = row.querySelector('td:nth-child(2)').textContent.trim();
            const role = row.querySelector('td:nth-child(4)').textContent.trim();

            const viewEmpName = document.getElementById('view-employee-name');
            const viewUsername = document.getElementById('view-username');
            const viewRole = document.getElementById('view-role');

            if (viewEmpName) viewEmpName.value = fullname;
            if (viewUsername) viewUsername.value = username;
            if (viewRole) viewRole.value = role;

            if (modals.view) {
                modals.view.classList.add('is-visible');
            }
        });
    });

    // Edit Account
    document.querySelectorAll('.account-btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const username = this.dataset.accountId;
            const row = this.closest('tr');
            const fullname = row.querySelector('td:nth-child(2)').textContent.trim();
            const role = row.querySelector('td:nth-child(4)').textContent.trim();

            const editEmpName = document.getElementById('edit-employee-name');
            const editUsername = document.getElementById('edit-username');
            const editRole = document.getElementById('edit-role');

            if (editEmpName) editEmpName.value = fullname;
            if (editUsername) editUsername.value = username;
            if (editRole) editRole.value = role;

            if (modals.edit) {
                modals.edit.classList.add('is-visible');
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
            const icon = this.querySelector('i');

            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
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