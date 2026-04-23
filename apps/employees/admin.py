from django.contrib import admin
from .models import NhanVien


@admin.register(NhanVien)
class NhanVienAdmin(admin.ModelAdmin):
    list_display = (
        "ma_nv",
        "ho_ten",
        "gioi_tinh",
        "ngay_sinh",
        "cccd",
        "sdt",
        "tk_ngan_hang",
        "chuc_vu",
        "ma_chi_nhanh",
    )
    search_fields = ("ma_nv", "ho_ten", "cccd", "sdt", "tk_ngan_hang")
    list_filter = ("gioi_tinh", "chuc_vu", "ma_chi_nhanh")
    ordering = ("ma_nv",)
    list_per_page = 25

    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("ma_nv", "ho_ten", "gioi_tinh", "ngay_sinh", "cccd", "sdt"),
        }),
        ("Công việc", {
            "fields": ("chuc_vu", "ma_chi_nhanh"),
        }),
        ("Bổ sung", {
            "fields": ("tk_ngan_hang", "dia_chi"),
        }),
    )

    # --- LOGIC PHÂN QUYỀN ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Lọc nhân viên theo chi nhánh của người đang đăng nhập
        try:
            return qs.filter(ma_chi_nhanh=request.user.taikhoan.ma_nv.ma_chi_nhanh)
        except AttributeError:
            return qs.none()  # Trả về trống nếu user không có hồ sơ nhân viên

    def save_model(self, request, obj, form, change):
        # Tự động gán chi nhánh nếu là quản lý chi nhánh thêm nhân viên
        if not request.user.is_superuser:
            try:
                obj.ma_chi_nhanh = request.user.taikhoan.ma_nv.ma_chi_nhanh
            except AttributeError:
                pass
        super().save_model(request, obj, form, change)