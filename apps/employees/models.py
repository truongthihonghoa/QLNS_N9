from django.core.validators import RegexValidator
from django.db import models


class NhanVien(models.Model):
    GIOI_TINH_CHOICES = [
        ("Nam", "Nam"),
        ("Nữ", "Nữ"),
        ("Khác", "Khác"),
    ]

    CHUC_VU_CHOICES = [
        ("Thu ngân", "Thu ngân"),
        ("Phục vụ", "Phục vụ"),
        ("Quản lý", "Quản lý"),
        ("Giữ xe", "Giữ xe"),
        ("Pha chế", "Pha chế"),
    ]

    ma_nv = models.CharField(max_length=10, primary_key=True, verbose_name="Mã nhân viên")
    ho_ten = models.CharField(max_length=100, verbose_name="Họ tên")
    ngay_sinh = models.DateField(verbose_name="Ngày sinh")
    cccd = models.CharField(max_length=12, unique=True, verbose_name="CCCD")
    sdt = models.CharField(
        max_length=15,
        unique=True,
        validators=[RegexValidator(r"^\d+$", "Số điện thoại chỉ được chứa chữ số")],
        verbose_name="Số điện thoại",
    )
    chuc_vu = models.CharField(max_length=50, choices=CHUC_VU_CHOICES, verbose_name="Chức vụ")
    dia_chi = models.CharField(max_length=255, null=True, blank=True, verbose_name="Địa chỉ")
    gioi_tinh = models.CharField(
        max_length=10,
        choices=GIOI_TINH_CHOICES,
        null=True,
        blank=True,
        verbose_name="Giới tính",
    )
    tk_ngan_hang = models.CharField(max_length=30, unique=True, verbose_name="Tài khoản ngân hàng")
    ma_chi_nhanh = models.ForeignKey(
        "branches.ChiNhanh",
        on_delete=models.CASCADE,
        related_name="nhan_viens",
        verbose_name="Chi nhánh",
    )

    def __str__(self):
        return f"{self.ma_nv} - {self.ho_ten}"

    class Meta:
        verbose_name = "Nhân viên"
        verbose_name_plural = "Danh sách nhân viên"
