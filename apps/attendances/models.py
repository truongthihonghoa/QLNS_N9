# attendance/models.py

from django.db import models


class ChamCong(models.Model):
    ma_cc = models.CharField(max_length=20, primary_key=True)

    ma_nv = models.ForeignKey(
        'employees.NhanVien',
        on_delete=models.CASCADE
    )

    ngay_lam = models.DateField()

    gio_vao = models.TimeField(null=True, blank=True)
    gio_ra = models.TimeField(null=True, blank=True)

    so_gio_lam = models.FloatField(default=0)   # hệ thống tự tính
    trang_thai = models.CharField(max_length=20, default='')

    ghi_chu = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('ma_nv', 'ngay_lam')

    def __str__(self):
        return f"{self.ma_nv} - {self.ngay_lam}"
