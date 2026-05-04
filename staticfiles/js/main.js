document.addEventListener('DOMContentLoaded', function() {
    const notificationBell = document.getElementById('notification-bell');
    const notificationDropdown = document.getElementById('notification-dropdown');

    // Toggle dropdown visibility
    if (notificationBell) {
        notificationBell.addEventListener('click', function(event) {
            event.stopPropagation();
            notificationDropdown.classList.toggle('show');
        });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (notificationDropdown && !notificationBell.contains(event.target)) {
            notificationDropdown.classList.remove('show');
        }
    });
});

/**
 * Global Toast Notification Function
 * @param {string} message - The message to display
 * @param {string} type - 'success', 'error', 'warning', 'info' (default: 'success')
 */
window.showToast = function(message, type = 'success') {
    const toast = document.getElementById("toast-notification");
    const toastMsg = document.getElementById("toast-message");
    const toastIcon = toast ? toast.querySelector('.toast-icon i') : null;

    if (toast && toastMsg) {
        // Clear previous timeout if any
        if (window.toastTimeout) {
            clearTimeout(window.toastTimeout);
        }

        // Set message
        toastMsg.textContent = message;

        // Set type classes and icons
        toast.classList.remove('success', 'error', 'warning', 'info');
        toast.classList.add(type);

        if (toastIcon) {
            toastIcon.className = ''; // Clear all classes
            if (type === 'success') {
                toastIcon.className = 'fas fa-check-circle';
            } else if (type === 'error') {
                toastIcon.className = 'fas fa-exclamation-circle';
            } else if (type === 'warning') {
                toastIcon.className = 'fas fa-exclamation-triangle';
            } else {
                toastIcon.className = 'fas fa-info-circle';
            }
        }

        // Show toast
        toast.classList.add("show");

        // Auto hide after 4 seconds (standard for project)
        window.toastTimeout = setTimeout(() => {
            toast.classList.remove("show");
        }, 4000);
    } else {
        console.warn('Toast element not found');
    }
};
