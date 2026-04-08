# apps/accounts/models.py

from django.db import models

class TaiKhoan(models.Model):
    ma_tk = models.CharField(max_length=20, primary_key=True)
    ten_dang_nhap = models.CharField(max_length=100, unique=True)
    mat_khau = models.CharField(max_length=255)
    quyen = models.CharField(max_length=50)

    ma_nv = models.OneToOneField(
        'employees.NhanVien',
        on_delete=models.CASCADE
    )