// Common Popup System
class CommonPopup {
    constructor() {
        // Delay initialization to ensure DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        this.initElements();
        this.initEventListeners();
    }

    initElements() {
        console.log('DEBUG: Initializing CommonPopup elements');
        this.confirmPopup = document.getElementById('common-confirm-popup');
        this.alertPopup = document.getElementById('common-alert-popup');
        
        console.log('DEBUG: confirmPopup:', this.confirmPopup);
        console.log('DEBUG: alertPopup:', this.alertPopup);
        
        // Confirm elements
        this.confirmTitle = document.getElementById('common-confirm-title');
        this.confirmMessage = document.getElementById('common-confirm-message');
        this.confirmCancelBtn = document.getElementById('common-confirm-cancel');
        this.confirmOkBtn = document.getElementById('common-confirm-ok');
        
        // Alert elements
        this.alertTitle = document.getElementById('common-alert-title');
        this.alertMessage = document.getElementById('common-alert-message');
        this.alertOkBtn = document.getElementById('common-alert-ok');
        
        console.log('DEBUG: confirmCancelBtn:', this.confirmCancelBtn);
        console.log('DEBUG: confirmOkBtn:', this.confirmOkBtn);
        console.log('DEBUG: alertOkBtn:', this.alertOkBtn);
        
        // Callback storage
        this.currentConfirmCallback = null;
        this.currentAlertCallback = null;
    }

    initEventListeners() {
        // Confirm popup events
        if (this.confirmCancelBtn) {
            this.confirmCancelBtn.addEventListener('click', () => {
                this.hideConfirm();
            });
        }
        
        if (this.confirmOkBtn) {
            this.confirmOkBtn.addEventListener('click', () => {
                if (this.currentConfirmCallback) {
                    this.currentConfirmCallback(true);
                }
                this.hideConfirm();
            });
        }
        
        // Alert popup events
        if (this.alertOkBtn) {
            this.alertOkBtn.addEventListener('click', () => {
                if (this.currentAlertCallback) {
                    this.currentAlertCallback();
                }
                this.hideAlert();
            });
        }
        
        // Close on overlay click
        if (this.confirmPopup) {
            this.confirmPopup.addEventListener('click', (e) => {
                if (e.target === this.confirmPopup) {
                    this.hideConfirm();
                }
            });
        }
        
        if (this.alertPopup) {
            this.alertPopup.addEventListener('click', (e) => {
                if (e.target === this.alertPopup) {
                    this.hideAlert();
                }
            });
        }
    }

    showConfirm(title, message, callback) {
        console.log('DEBUG: showConfirm called with:', title, message);
        if (this.confirmTitle) this.confirmTitle.textContent = title;
        if (this.confirmMessage) this.confirmMessage.textContent = message;
        this.currentConfirmCallback = callback;
        
        if (this.confirmPopup) {
            this.confirmPopup.style.display = 'flex';
            this.confirmPopup.classList.add('show');
            console.log('DEBUG: Confirm popup shown');
        } else {
            console.log('DEBUG: Confirm popup element not found');
        }
    }

    hideConfirm() {
        if (this.confirmPopup) {
            this.confirmPopup.style.display = 'none';
            this.confirmPopup.classList.remove('show');
        }
        this.currentConfirmCallback = null;
    }

    showAlert(title, message, callback) {
        console.log('DEBUG: showAlert called with:', title, message);
        if (this.alertTitle) this.alertTitle.textContent = title;
        if (this.alertMessage) this.alertMessage.textContent = message;
        this.currentAlertCallback = callback;
        
        if (this.alertPopup) {
            this.alertPopup.style.display = 'flex';
            this.alertPopup.classList.add('show');
            console.log('DEBUG: Alert popup shown');
        } else {
            console.log('DEBUG: Alert popup element not found');
        }
    }

    hideAlert() {
        if (this.alertPopup) {
            this.alertPopup.style.display = 'none';
            this.alertPopup.classList.remove('show');
        }
        this.currentAlertCallback = null;
    }
}

// Global instance
window.commonPopup = new CommonPopup();

// Global functions for easy access
window.showConfirm = (title, message, callback) => {
    window.commonPopup.showConfirm(title, message, callback);
};

window.hideConfirm = () => {
    window.commonPopup.hideConfirm();
};

window.showAlert = (title, message, callback) => {
    window.commonPopup.showAlert(title, message, callback);
};

window.hideAlert = () => {
    window.commonPopup.hideAlert();
};
