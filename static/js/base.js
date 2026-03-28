document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // User dropdown functionality
    const userDropdown = document.querySelector('.user-dropdown');
    const userDropdownContent = document.querySelector('.user-dropdown-content');
    
    console.log('User dropdown:', userDropdown);
    console.log('User dropdown content:', userDropdownContent);
    
    if (userDropdown && userDropdownContent) {
        // Toggle dropdown on avatar click
        userDropdown.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Avatar clicked!');
            
            // Toggle display
            if (userDropdownContent.style.display === 'block') {
                userDropdownContent.style.display = 'none';
                console.log('Dropdown hidden');
            } else {
                userDropdownContent.style.display = 'block';
                console.log('Dropdown shown');
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userDropdown.contains(e.target)) {
                userDropdownContent.style.display = 'none';
                console.log('Dropdown closed (outside click)');
            }
        });
    }
    
    // Logout popup functionality
    const logoutLink = document.getElementById('logout-link');
    const logoutPopup = document.getElementById('confirm-logout-popup');
    const logoutNoBtn = document.getElementById('logout-no-btn');
    const logoutYesBtn = document.getElementById('logout-yes-btn');
    
    console.log('Logout link:', logoutLink);
    console.log('Logout popup:', logoutPopup);
    
    if (logoutLink && logoutPopup) {
        // Show popup when logout link is clicked
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Logout link clicked!');
            logoutPopup.style.display = 'flex';
            console.log('Logout popup shown');
        });
        
        // Hide popup when clicking "Không" button
        if (logoutNoBtn) {
            logoutNoBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                logoutPopup.style.display = 'none';
                console.log('Logout popup hidden (No button)');
            });
        }
        
        // Redirect to logout when clicking "Đồng ý" button
        if (logoutYesBtn) {
            logoutYesBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Redirecting to logout');
                window.location.href = '/accounts/logout/';
            });
        }
        
        // Hide popup when clicking overlay
        logoutPopup.addEventListener('click', function(e) {
            if (e.target === logoutPopup) {
                logoutPopup.style.display = 'none';
                console.log('Logout popup hidden (overlay click)');
            }
        });
    }
});
