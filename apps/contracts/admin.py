from django.contrib import admin
from .models import HopDongLaoDong, HopDongLD_CT


@admin.register(HopDongLaoDong)
class HopDongLaoDongAdmin(admin.ModelAdmin):
    list_display = (
        'ma_hd',
        'ma_nv',
        'ten_nv',
        'ten_chi_nhanh',
        'loai_hd',
        'ngay_bat_dau',
        'ngay_ket_thuc',
        'chuc_vu',
        'trang_thai'
    )

    search_fields = (
        'ma_hd',
        'ma_nv__ten_nv',          # ⚠️ đúng field bên NhanVien
        'ma_chi_nhanh__ten_chi_nhanh'
    )

    list_filter = ('loai_hd', 'trang_thai')

    raw_id_fields = ('ma_nv', 'ma_chi_nhanh')
    autocomplete_fields = ('ma_nv', 'ma_chi_nhanh')

    list_select_related = ('ma_nv', 'ma_chi_nhanh')

    # ===== HIỂN THỊ TÊN NHÂN VIÊN =====
    def ten_nv(self, obj):
        return str(obj.ma_nv)  # an toàn nhất

    ten_nv.short_description = "Tên nhân viên"

    # ===== HIỂN THỊ CHI NHÁNH =====
    def ten_chi_nhanh(self, obj):
        return obj.ma_chi_nhanh.ten_chi_nhanh

    ten_chi_nhanh.short_description = "Chi nhánh"


@admin.register(HopDongLD_CT)
class HopDongLD_CTAdmin(admin.ModelAdmin):
    list_display = (
        'ma_hd',
        'luong_co_ban',
        'luong_theo_gio',
        'so_gio_lam',
        'che_do_thuong',

    )

    search_fields = ('ma_hd__ma_hd',)

    raw_id_fields = ('ma_hd',)
    autocomplete_fields = ('ma_hd',)

    list_select_related = ('ma_hd',)