# apps/branches/models.py

from django.db import models

class ChiNhanh(models.Model):
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

    def __str__(self):
        return f"{self.ten_chi_nhanh} ({self.ma_chi_nhanh})"