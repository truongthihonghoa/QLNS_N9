from django.db import models

class HopDongLaoDong(models.Model):

    # ===== CHOICES =====
    LOAI_HD_CHOICES = [
        ('FULLTIME', 'Full Time'),
        ('PARTTIME', 'Part Time'),
    ]

    CHUC_VU_CHOICES = [
        ('THU_NGAN', 'Thu ngân'),
        ('QUAN_LY', 'Quản lý'),
        ('PHUC_VU', 'Phục vụ'),
        ('PHA_CHE', 'Pha chế'),
    ]

    TRANG_THAI_CHOICES = [
        ('CON_HAN', 'Còn hạn'),
        ('HET_HAN', 'Hết hạn'),
        ('DA_HUY', 'Đã hủy'),
    ]

    # ===== FIELD =====
    ma_hd = models.CharField(max_length=20, primary_key=True)

    # 🔗 nhân viên
    ma_nv = models.ForeignKey(
        'employees.NhanVien',
        on_delete=models.CASCADE,
        related_name='hop_dong'
    )

    # 🔗 chi nhánh (địa điểm làm việc)
    ma_chi_nhanh = models.ForeignKey(
        'branches.ChiNhanh',
        on_delete=models.CASCADE,
        related_name='hop_dong'
    )

    loai_hd = models.CharField(
        max_length=20,
        choices=LOAI_HD_CHOICES
    )

    chuc_vu = models.CharField(
        max_length=20,
        choices=CHUC_VU_CHOICES
    )

    ngay_bat_dau = models.DateField()
    ngay_ket_thuc = models.DateField(null=True, blank=True)

    trang_thai = models.CharField(
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='CON_HAN'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ma_hd} - {self.ma_nv}"

class HopDongLD_CT(models.Model):

    ma_hd = models.OneToOneField(
        HopDongLaoDong,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='chi_tiet'
    )

    luong_co_ban = models.FloatField()
    luong_theo_gio = models.FloatField()
    so_gio_lam = models.FloatField()

    che_do_thuong = models.FloatField(default=0)

    dieu_khoan = models.TextField(blank=True, null=True)
    trach_nhiem = models.TextField(blank=True, null=True)
    ghi_chu = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Chi tiết {self.ma_hd}"