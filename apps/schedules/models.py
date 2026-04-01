# apps/schedules/models.py

from django.db import models

class LichLamViec(models.Model):
    ma_llv = models.CharField(max_length=20, primary_key=True)
    ngay_lam = models.DateField()
    ca_lam = models.CharField(max_length=50)
    trang_thai = models.CharField(max_length=50)
    ngay_tao = models.DateField()


class LichLamViec_CT(models.Model):
    ma_llv = models.ForeignKey(LichLamViec, on_delete=models.CASCADE)
    ma_nv = models.ForeignKey('employees.NhanVien', on_delete=models.CASCADE)
    vi_tri_vl = models.CharField(max_length=100)

    class Meta:
        unique_together = ('ma_llv', 'ma_nv')