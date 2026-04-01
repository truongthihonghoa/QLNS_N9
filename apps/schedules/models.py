# apps/schedules/models.py

from django.db import models

class LichLamViec(models.Model):
    ma_llv = models.CharField(max_length=20, primary_key=True)
    ngay_lam = models.DateField()
    ca_lam = models.CharField(max_length=50)
    trang_thai = models.CharField(max_length=50)
    ngay_tao = models.DateField()
    ghi_chu = models.TextField(blank=True, null=True)



    class Meta:
        unique_together = ('ma_llv', 'ma_nv')