# apps/accounts/models.py

from django.contrib.auth.models import User
from django.db import models


class TaiKhoan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ma_nv = models.OneToOneField(
        'employees.NhanVien',
        on_delete=models.CASCADE
    )

    @property
    def vai_tro(self):
        if self.user.is_superuser:
            return 'Admin'
        elif self.user.is_staff:
            return 'Quản lý'
        else:
            return 'Nhân viên'

    @property
    def ten_dang_nhap(self):
        return self.user.username

    @property
    def trang_thai(self):
        return 'Đang hoạt động' if self.user.is_active else 'Ngừng hoạt động'