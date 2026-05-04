document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // User dropdown functionality
    const userDropdown = document.querySelector('.user-dropdown');
    const userDropdownContent = document.querySelector('.user-dropdown-content');

    if (userDropdown && userDropdownContent) {
        // Toggle dropdown on avatar click
        userDropdown.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            // Toggle display
            if (userDropdownContent.style.display === 'block') {
                userDropdownContent.style.display = 'none';
            } else {
                userDropdownContent.style.display = 'block';
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userDropdown.contains(e.target)) {
                userDropdownContent.style.display = 'none';
            }
        });
    }
    
    // Logout functionality - Direct redirect without popup
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Redirecting to logout directly');
            window.location.href = '/accounts/logout/';
        });
    }
});
