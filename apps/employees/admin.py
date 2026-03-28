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
        "vi_tri_vl",
        "ma_chi_nhanh",
    )
    search_fields = ("ma_nv", "ho_ten", "cccd", "sdt", "tk_ngan_hang")
    list_filter = ("gioi_tinh", "chuc_vu", "vi_tri_vl", "ma_chi_nhanh")
    raw_id_fields = ("ma_chi_nhanh",)
    autocomplete_fields = ("ma_chi_nhanh",)
    ordering = ("ma_nv",)
    list_per_page = 25
    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("ma_nv", "ho_ten", "gioi_tinh", "ngay_sinh", "cccd", "sdt"),
        }),
        ("Công việc", {
            "fields": ("chuc_vu", "vi_tri_vl", "ma_chi_nhanh"),
        }),
        ("Bổ sung", {
            "fields": ("tk_ngan_hang", "dia_chi"),
        }),
    )
