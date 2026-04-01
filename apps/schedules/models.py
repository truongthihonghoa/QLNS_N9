from django.db import models

from apps.employees.models import NhanVien


class LichLamViec(models.Model):
    ma_llv = models.CharField(max_length=20, primary_key=True)
    ma_nv = models.ForeignKey(
        'employees.NhanVien',
        on_delete=models.CASCADE,
        related_name='lich_lam_viec',
        null=True, blank=True
    )
    ma_chi_nhanh = models.ForeignKey(
        'branches.ChiNhanh',
        on_delete=models.CASCADE,
        related_name='lich_lam_viec',
        null=True, blank=True
    )
    ngay_lam = models.DateField()
    ca_lam = models.CharField(max_length=50)
    trang_thai = models.CharField(max_length=50)
    ngay_tao = models.DateField()
<<<<<<< HEAD
    ghi_chu = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('ma_llv', 'ma_nv')
        verbose_name = "Lịch làm việc"
        verbose_name_plural = "Lịch làm việc"

    def __str__(self):
        return f"{self.ma_llv} - {self.ma_nv}"
=======

    def __str__(self):
        return self.ma_llv


class LichLamViec_CT(models.Model):
    ma_llv = models.ForeignKey(LichLamViec, on_delete=models.CASCADE)
    ma_nv = models.ForeignKey(NhanVien, on_delete=models.CASCADE)
    vi_tri_vl = models.CharField(max_length=100)

    class Meta:
        unique_together = ('ma_llv', 'ma_nv')

    def __str__(self):
        return f'{self.ma_llv_id} - {self.ma_nv_id}'
>>>>>>> 6c4e737 (Hop dong)
