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
