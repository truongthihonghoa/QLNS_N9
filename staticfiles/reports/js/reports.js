/**
 * BÁO CÁO - JavaScript UI Controller
 * Xử lý tất cả tương tác UI cho chức năng Báo cáo (MOCK DATA - NO BACKEND)
 */

// ============================================
// MOCK DATA
// ============================================

const MOCK_EMPLOYEES = [
  { ma_nv: 'NV001', ten_nv: 'Nguyễn Văn A', gio_lam: 176, ca: '15/10/5', thuong: '500,000 ₫', phat: '0 ₫' },
  { ma_nv: 'NV002', ten_nv: 'Trần Thị B', gio_lam: 160, ca: '10/20/0', thuong: '200,000 ₫', phat: '50,000 ₫' },
  { ma_nv: 'NV003', ten_nv: 'Lê Văn C', gio_lam: 180, ca: '10/10/10', thuong: '1,000,000 ₫', phat: '0 ₫' },
  { ma_nv: 'NV004', ten_nv: 'Phạm Thị D', gio_lam: 165, ca: '12/8/10', thuong: '300,000 ₫', phat: '100,000 ₫' },
  { ma_nv: 'NV005', ten_nv: 'Hoàng Văn E', gio_lam: 170, ca: '14/12/4', thuong: '400,000 ₫', phat: '0 ₫' }
];

const MOCK_REPORTS = {
  'BC001': { start: '2026-01-01', end: '2026-01-31', thang: '01/2026' },
  'BC002': { start: '2026-02-01', end: '2026-02-28', thang: '02/2026' },
  'BC003': { start: '2026-03-01', end: '2026-03-31', thang: '03/2026' },
  'BC004': { start: '2025-12-01', end: '2025-12-31', thang: '12/2025' },
  'BC005': { start: '2025-11-01', end: '2025-11-30', thang: '11/2025' }
};

// ============================================
// STATE MANAGEMENT
// ============================================

let currentPopup = null;
let currentReportId = null;
let hasUnsavedChanges = false;
let aggregatedData = null;

// ============================================
// UTILITY FUNCTIONS
// ============================================

function showToast(message, duration = 3000) {
  const toast = document.getElementById('toast');
  const toastText = document.getElementById('toast-text');
  toastText.textContent = message;
  toast.style.display = 'block';
  
  setTimeout(() => {
    toast.style.display = 'none';
  }, duration);
}

function formatDateToVN(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}

function parseDateFromVN(dateString) {
  if (!dateString) return '';
  const parts = dateString.split('/');
  if (parts.length === 3) {
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }
  return dateString;
}

// ============================================
// POPUP MANAGEMENT
// ============================================

function openPopup(popupId) {
  const popup = document.getElementById(popupId);
  if (popup) {
    popup.style.display = 'flex';
    currentPopup = popupId;
    hasUnsavedChanges = false;
  }
}

function closePopup(popupId) {
  const popup = document.getElementById(popupId);
  if (popup) {
    popup.style.display = 'none';
    currentPopup = null;
    hasUnsavedChanges = false;
  }
}

function closeAllPopups() {
  const popups = document.querySelectorAll('.popup-overlay');
  popups.forEach(popup => {
    popup.style.display = 'none';
  });
  currentPopup = null;
  hasUnsavedChanges = false;
}

// ============================================
// VALIDATION
// ============================================

function validateDates(startDate, endDate, startErrorId, endErrorId) {
  let isValid = true;
  
  // Reset errors
  document.getElementById(startErrorId).textContent = '';
  document.getElementById(endErrorId).textContent = '';
  
  // Check empty start date
  if (!startDate) {
    document.getElementById(startErrorId).textContent = 'Vui lòng nhập ngày bắt đầu';
    isValid = false;
  }
  
  // Check empty end date
  if (!endDate) {
    document.getElementById(endErrorId).textContent = 'Vui lòng nhập ngày kết thúc';
    isValid = false;
  }
  
  // Check date range
  if (startDate && endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (end < start) {
      document.getElementById(endErrorId).textContent = 'Ngày kết thúc không được bé hơn ngày bắt đầu';
      isValid = false;
    }
  }
  
  return isValid;
}

// ============================================
// DATA GENERATION
// ============================================

function generateAggregatedData() {
  return MOCK_EMPLOYEES.map((emp, index) => ({
    ...emp,
    row_class: index === 0 ? 'row' : `row_0${index}`
  }));
}

function renderDataTable(containerId, data, isEditable = false) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  container.innerHTML = data.map((emp, index) => `
    <div class="${index === 0 ? 'row' : 'row row_0' + index}">
      <div class="${index === 0 ? 'data' : 'data_0' + (index * 7 + 1)}"><div class="${emp.ma_nv.toLowerCase()}"><span class="${emp.ma_nv.toLowerCase()}_span">${emp.ma_nv}</span></div></div>
      <div class="${index === 0 ? 'data_01' : 'data_0' + (index * 7 + 2)}"><div class="${emp.ten_nv.toLowerCase().replace(/\s+/g, '-').normalize('NFD').replace(/[\u0300-\u036f]/g, '')}"><span class="${emp.ten_nv.toLowerCase().replace(/\s+/g, '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')}_span">${emp.ten_nv}</span></div></div>
      <div class="${index === 0 ? 'data_02' : 'data_0' + (index * 7 + 3)}"><div class="text-${emp.gio_lam}"><span class="f${emp.gio_lam}_span">${emp.gio_lam}</span></div></div>
      <div class="${index === 0 ? 'data_03' : 'data_0' + (index * 7 + 4)}"><div class="text-${emp.ca.replace(/\//g, '')}"><span class="f${emp.ca.replace(/\//g, '')}_span">${emp.ca}</span></div></div>
      <div class="${index === 0 ? 'data_05' : 'data_0' + (index * 7 + 6)}"><div class="text-${emp.thuong.replace(/[^0-9]/g, '')}-"><span class="f${emp.thuong.replace(/[^0-9]/g, '')}_span">${emp.thuong}</span></div></div>
      <div class="${index === 0 ? 'data_06' : 'data_0' + (index * 7 + 7)}"><div class="text-${emp.phat.replace(/[^0-9]/g, '')}-"><span class="f${emp.phat.replace(/[^0-9]/g, '')}_span">${emp.phat}</span></div></div>
    </div>
  `).join('');
}

// ============================================
// CREATE REPORT POPUP
// ============================================

function initCreatePopup() {
  // Open popup
  document.getElementById('btn-create-report').addEventListener('click', () => {
    openPopup('popup-create');
    resetCreateForm();
  });
  
  // Close buttons
  document.getElementById('create-close-btn').addEventListener('click', () => {
    if (hasUnsavedChanges) {
      openPopup('popup-confirm-cancel');
      setupCancelConfirmation('popup-create');
    } else {
      closePopup('popup-create');
    }
  });
  
  document.getElementById('create-cancel-btn').addEventListener('click', () => {
    if (hasUnsavedChanges) {
      openPopup('popup-confirm-cancel');
      setupCancelConfirmation('popup-create');
    } else {
      closePopup('popup-create');
    }
  });
  
  // Tong hop button
  document.getElementById('create-tonghop-btn').addEventListener('click', () => {
    const startDate = document.getElementById('create-start-date').value;
    const endDate = document.getElementById('create-end-date').value;
    
    if (validateDates(startDate, endDate, 'error-create-start', 'error-create-end')) {
      // Generate mock data
      aggregatedData = generateAggregatedData();
      
      // Hide empty state
      document.getElementById('create-empty-state').style.display = 'none';
      document.getElementById('create-data-body').style.display = 'block';
      
      // Render data
      renderDataTable('create-data-body', aggregatedData);
      
      hasUnsavedChanges = true;
    }
  });
  
  // Save button
  document.getElementById('create-save-btn').addEventListener('click', () => {
    if (!aggregatedData) {
      showToast('Vui lòng tổng hợp dữ liệu trước khi lưu');
      return;
    }
    
    showToast('Tạo báo cáo thành công');
    closePopup('popup-create');
    resetCreateForm();
  });
  
  // Track input changes
  document.getElementById('create-start-date').addEventListener('change', () => {
    hasUnsavedChanges = true;
  });
  document.getElementById('create-end-date').addEventListener('change', () => {
    hasUnsavedChanges = true;
  });
}

function resetCreateForm() {
  document.getElementById('create-start-date').value = '';
  document.getElementById('create-end-date').value = '';
  document.getElementById('error-create-start').textContent = '';
  document.getElementById('error-create-end').textContent = '';
  document.getElementById('create-empty-state').style.display = 'block';
  document.getElementById('create-data-body').style.display = 'none';
  document.getElementById('create-data-body').innerHTML = '';
  aggregatedData = null;
  hasUnsavedChanges = false;
}

// ============================================
// EDIT REPORT POPUP
// ============================================

function initEditPopup() {
  // Edit buttons on rows
  document.querySelectorAll('.btn-edit').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const reportId = e.currentTarget.getAttribute('data-report-id');
      const row = document.querySelector(`[data-report-id="${reportId}"]`);
      const status = row ? row.getAttribute('data-status') : 'saved';
      
      if (status === 'saved') {
        // For saved reports, dates are disabled
        document.getElementById('edit-start-date').disabled = true;
        document.getElementById('edit-end-date').disabled = true;
      } else {
        document.getElementById('edit-start-date').disabled = false;
        document.getElementById('edit-end-date').disabled = false;
      }
      
      openEditPopup(reportId);
    });
  });
  
  // Close buttons
  document.getElementById('edit-close-btn').addEventListener('click', () => {
    if (hasUnsavedChanges) {
      openPopup('popup-confirm-cancel');
      setupCancelConfirmation('popup-edit');
    } else {
      closePopup('popup-edit');
    }
  });
  
  document.getElementById('edit-cancel-btn').addEventListener('click', () => {
    if (hasUnsavedChanges) {
      openPopup('popup-confirm-cancel');
      setupCancelConfirmation('popup-edit');
    } else {
      closePopup('popup-edit');
    }
  });
  
  // Tong hop button
  document.getElementById('edit-tonghop-btn').addEventListener('click', () => {
    const startDate = document.getElementById('edit-start-date').value;
    const endDate = document.getElementById('edit-end-date').value;
    
    if (validateDates(startDate, endDate, 'error-edit-start', 'error-edit-end')) {
      showToast('Tổng hợp dữ liệu thành công');
      hasUnsavedChanges = true;
    }
  });
  
  // Save button
  document.getElementById('edit-save-btn').addEventListener('click', () => {
    showToast('Cập nhật báo cáo thành công');
    closePopup('popup-edit');
    hasUnsavedChanges = false;
  });
  
  // Track input changes
  document.getElementById('edit-start-date').addEventListener('change', () => {
    hasUnsavedChanges = true;
  });
  document.getElementById('edit-end-date').addEventListener('change', () => {
    hasUnsavedChanges = true;
  });
}

function openEditPopup(reportId) {
  currentReportId = reportId;
  const reportData = MOCK_REPORTS[reportId];
  
  if (reportData) {
    document.getElementById('edit-report-id').value = reportId;
    document.getElementById('edit-start-date').value = reportData.start;
    document.getElementById('edit-end-date').value = reportData.end;
  }
  
  openPopup('popup-edit');
  hasUnsavedChanges = false;
}

// ============================================
// VIEW REPORT POPUP
// ============================================

function initViewPopup() {
  // View buttons on rows
  document.querySelectorAll('.btn-view').forEach(btn => {
    btn.addEventListener('click', (e) => {
      console.log('View button clicked'); // Debug line
      const reportId = e.currentTarget.getAttribute('data-report-id');
      console.log('Report ID:', reportId); // Debug line
      openViewPopup(reportId);
    });
  });
  
  // Close buttons
  document.getElementById('view-close-btn').addEventListener('click', () => {
    closePopup('popup-view');
  });
  
  document.getElementById('view-close-btn-bottom').addEventListener('click', () => {
    closePopup('popup-view');
  });
}

function openViewPopup(reportId) {
  console.log('Opening view popup for:', reportId); // Debug line
  currentReportId = reportId;
  const reportData = MOCK_REPORTS[reportId];
  
  if (reportData) {
    document.getElementById('view-title').textContent = `Chi tiết báo cáo #${reportId}`;
    document.getElementById('view-start-date').value = formatDateToVN(reportData.start);
    document.getElementById('view-end-date').value = formatDateToVN(reportData.end);
  }
  
  console.log('Calling openPopup with popup-view'); // Debug line
  openPopup('popup-view');
}

// ============================================
// DELETE CONFIRMATION
// ============================================

function initDeletePopup() {
  // Delete buttons on rows
  document.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const reportId = e.currentTarget.getAttribute('data-report-id');
      currentReportId = reportId;
      openPopup('popup-delete');
    });
  });
  
  // Cancel button
  document.getElementById('delete-cancel-btn').addEventListener('click', () => {
    closePopup('popup-delete');
    currentReportId = null;
  });
  
  // Confirm button
  document.getElementById('delete-confirm-btn').addEventListener('click', () => {
    showToast('Xóa báo cáo thành công');
    closePopup('popup-delete');
    
    // Remove row from UI (visual only)
    if (currentReportId) {
      const row = document.querySelector(`[data-report-id="${currentReportId}"]`);
      if (row) {
        row.style.display = 'none';
      }
    }
    
    currentReportId = null;
  });
}

// ============================================
// EXPORT POPUP
// ============================================

function initExportPopup() {
  // Export buttons on rows
  document.querySelectorAll('.btn-export').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const reportId = e.currentTarget.getAttribute('data-report-id');
      currentReportId = reportId;
      
      const reportData = MOCK_REPORTS[reportId];
      if (reportData) {
        const [month, year] = reportData.thang.split('/');
        document.getElementById('export-filename').textContent = `BaoCao_${month}_${year}.xlsx`;
      }
      
      openPopup('popup-export');
    });
  });
  
  // Close button
  document.getElementById('export-close-btn').addEventListener('click', () => {
    closePopup('popup-export');
  });
  
  // Cancel button
  document.getElementById('export-cancel-btn').addEventListener('click', () => {
    closePopup('popup-export');
  });
  
  // Export format change - update filename
  document.querySelectorAll('input[name="export-format"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      const reportData = MOCK_REPORTS[currentReportId];
      if (reportData) {
        const [month, year] = reportData.thang.split('/');
        const ext = e.target.value === 'excel' ? 'xlsx' : 'pdf';
        document.getElementById('export-filename').textContent = `BaoCao_${month}_${year}.${ext}`;
      }
    });
  });
  
  // Confirm button
  document.getElementById('export-confirm-btn').addEventListener('click', () => {
    const isError = Math.random() < 0.1; // 10% chance of error for demo
    
    if (isError) {
      showToast('Xuất file thất bại');
    } else {
      showToast('Xuất báo cáo thành công');
    }
    
    closePopup('popup-export');
  });
}

// ============================================
// CANCEL CONFIRMATION POPUP
// ============================================

function initCancelConfirmationPopup() {
  document.getElementById('confirm-cancel-no').addEventListener('click', () => {
    closePopup('popup-confirm-cancel');
  });
  
  document.getElementById('confirm-cancel-yes').addEventListener('click', () => {
    closePopup('popup-confirm-cancel');
    closeAllPopups();
    resetCreateForm();
    hasUnsavedChanges = false;
  });
}

function setupCancelConfirmation(popupToClose) {
  // Store which popup to close after confirmation
  document.getElementById('confirm-cancel-yes').onclick = () => {
    closePopup('popup-confirm-cancel');
    closePopup(popupToClose);
    if (popupToClose === 'popup-create') {
      resetCreateForm();
    }
    hasUnsavedChanges = false;
  };
}

// ============================================
// CLICK OUTSIDE TO CLOSE
// ============================================

function initClickOutside() {
  document.querySelectorAll('.popup-overlay').forEach(popup => {
    popup.addEventListener('click', (e) => {
      if (e.target === popup) {
        const popupId = popup.id;
        
        if (hasUnsavedChanges && (popupId === 'popup-create' || popupId === 'popup-edit')) {
          openPopup('popup-confirm-cancel');
          setupCancelConfirmation(popupId);
        } else {
          closePopup(popupId);
        }
      }
    });
  });
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  initCreatePopup();
  initEditPopup();
  initViewPopup();
  initDeletePopup();
  initExportPopup();
  initCancelConfirmationPopup();
  initClickOutside();
  
  console.log('Báo cáo module initialized');
});
