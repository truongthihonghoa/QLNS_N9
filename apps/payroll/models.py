from django.db import models

class Luong(models.Model):
    ma_luong = models.CharField(max_length=20, primary_key=True)

    nhan_vien = models.ForeignKey(
        'employees.NhanVien',
        on_delete=models.CASCADE,
        related_name='luongs'
    )
    chi_nhanh = models.ForeignKey(
        'branches.ChiNhanh',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # ✅ Tách tháng & năm riêng
    thang = models.IntegerField(default=1)
    nam = models.IntegerField(default=2023)

    # ✅ Trạng thái có choice (chuẩn)
    TRANG_THAI_CHOICES = [
        ('cho_duyet', 'Đang chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('da_tu_choi', 'Đã từ chối'),
    ]
    trang_thai = models.CharField(
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='cho_duyet'
    )

    # --- Lương ---
    luong_co_ban = models.FloatField(default=0)
    luong_theo_gio = models.FloatField(default=0)

    so_ca_lam = models.FloatField(default=0)
    so_gio_lam = models.FloatField(default=0)

    thuong = models.FloatField(default=0)
    phat = models.FloatField(default=0)

    # ✅ Tổng lương (auto)
    tong_luong = models.FloatField(default=0)

    # Đánh dấu đã gửi bảng lương cho nhân viên (UI: Chưa gửi/Đã gửi)
    da_gui = models.BooleanField(default=False)

    # --- Thời gian ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ma_luong} - {self.nhan_vien}"
