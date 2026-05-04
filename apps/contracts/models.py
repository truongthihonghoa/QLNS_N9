from django.db import models
from django.utils import timezone
import datetime
class HopDongLaoDong(models.Model):

    # ===== CHOICES =====
    LOAI_HD_CHOICES = [
        ('FULLTIME', 'Full Time'),
        ('PARTTIME', 'Part Time'),
    ]

    CHUC_VU_CHOICES = [
        ('QUAN_LY', 'Quản lý'),
        ('PHUC_VU', 'Phục vụ'),
        ('PHA_CHE', 'Pha chế'),
        ('GIU_XE', 'Giữ xe'),
        ('THU_NGAN', 'Thu ngân'),
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
        related_name='hop_dong',
        null=True,
        blank=True,
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
    # created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    def __str__(self):
        return f"{self.ma_hd} - {self.ma_nv}"

    @property
    def trang_thai_thuc_te(self):
        """Tính toán trạng thái thực tế dựa trên ngày tháng hiện tại"""
        today = timezone.now().date()
        
        # 1. Hết hạn: Nếu có ngày kết thúc và đã qua ngày đó
        if self.ngay_ket_thuc and self.ngay_ket_thuc < today:
            return {'code': 'HET_HAN', 'display': 'Hết hạn'}
        
        # 2. Sắp hiệu lực: Nếu ngày bắt đầu ở tương lai
        if self.ngay_bat_dau > today:
            return {'code': 'SAP_HIEU_LUC', 'display': 'Sắp hiệu lực'}
        
        # 3. Còn hạn: Nếu đang trong thời gian hiệu lực (mặc định)
        # Nếu ghi chú là hủy thì mới hủy, còn không thì dựa trên ngày tháng
        if self.trang_thai == 'DA_HUY':
            return {'code': 'DA_HUY', 'display': 'Đã hủy'}
            
        return {'code': 'CON_HAN', 'display': 'Còn hạn'}

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