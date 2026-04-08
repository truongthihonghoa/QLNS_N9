document.addEventListener('DOMContentLoaded', function () {
    const SUCCESS_TOAST_AUTO_HIDE_MS = 3000;
    const successToast = document.getElementById('employee-success-toast');
    const successToastMessage = document.getElementById('employee-success-toast-message');
    const successMessageData = document.getElementById('employee-success-message');
    let successToastTimer = null;

    function showSuccessToast(message) {
        if (!successToast) {
            return;
        }

        if (successToastMessage) {
            successToastMessage.textContent = message;
        }

        successToast.classList.add('is-visible');

        if (successToastTimer) {
            window.clearTimeout(successToastTimer);
        }

        successToastTimer = window.setTimeout(function () {
            successToast.classList.remove('is-visible');
        }, SUCCESS_TOAST_AUTO_HIDE_MS);
    }

    if (successMessageData) {
        showSuccessToast(successMessageData.dataset.message || 'Cập nhật thông tin nhân viên thành công');
    }
});
