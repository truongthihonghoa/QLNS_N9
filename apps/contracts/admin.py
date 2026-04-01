from django.contrib import admin

from .models import HopDongLaoDong, HopDongLD_CT


@admin.register(HopDongLaoDong)
class HopDongLaoDongAdmin(admin.ModelAdmin):
    list_display = (
        'ma_hd',
        'ma_nv',
        'ma_chi_nhanh',
        'loai_hd',
        'chuc_vu',
        'ngay_bat_dau',
        'ngay_ket_thuc',
        'trang_thai',
    )
    search_fields = ('ma_hd', 'ma_nv__ma_nv', 'ma_nv__ho_ten')
    list_filter = ('loai_hd', 'chuc_vu', 'trang_thai')
    raw_id_fields = ('ma_nv', 'ma_chi_nhanh')
    autocomplete_fields = ('ma_nv', 'ma_chi_nhanh')


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
