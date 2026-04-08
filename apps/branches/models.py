# apps/branches/models.py

from django.db import models

class ChiNhanh(models.Model):
    TRANG_THAI_CHOICES = [
        ('active', 'Đang hoạt động'),
        ('inactive', 'Ngưng hoạt động'),
    ]

    ma_chi_nhanh = models.CharField(max_length=20, primary_key=True)
    ten_chi_nhanh = models.CharField(max_length=255)
    dia_chi = models.TextField()
    sdt = models.CharField(max_length=15)
    ma_nv_ql = models.ForeignKey(
        'employees.NhanVien',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    trang_thai = models.CharField(
        max_length=10,
        choices=TRANG_THAI_CHOICES,
        default='active',
    )

    def save(self, *args, **kwargs):
        if not self.ma_chi_nhanh:
            # Lấy chi nhánh có mã lớn nhất hiện tại
            last_branch = ChiNhanh.objects.all().order_by('ma_chi_nhanh').last()
            if not last_branch:
                # Nếu chưa có chi nhánh nào, bắt đầu từ CN01
                self.ma_chi_nhanh = 'CN01'
            else:
                # Lấy phần số từ mã cũ (ví dụ 'CN02' -> '02')
                last_id = int(last_branch.ma_chi_nhanh[2:])
                # Tăng số lên và định dạng lại thành 2 chữ số (03, 04...)
                new_id = last_id + 1
                self.ma_chi_nhanh = f'CN{new_id:02d}'

        super(ChiNhanh, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.ten_chi_nhanh}"
