from django.db import models


class ChamCong(models.Model):
    CA_CHOICES = [
        ('SANG', 'Ca sáng'),
        ('CHIEU', 'Ca chiều'),
        ('TOI', 'Ca tối'),
    ]

    ma_cc = models.CharField(max_length=50, primary_key=True)

    ma_nv = models.ForeignKey(
        'employees.NhanVien',
        on_delete=models.CASCADE
    )

    ngay_lam = models.DateField()
    ca_lam = models.CharField(max_length=10, choices=CA_CHOICES)

    gio_vao = models.TimeField(null=True, blank=True)
    gio_ra = models.TimeField(null=True, blank=True)

    so_gio_lam = models.FloatField(default=0)
    trang_thai = models.CharField(max_length=20, default='')

    ghi_chu = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ma_nv', 'ngay_lam', 'ca_lam'],
                name='unique_nv_ngay_ca'
            )
        ]

    def __str__(self):
        return f"{self.ma_nv} - {self.ngay_lam} - {self.ca_lam}"