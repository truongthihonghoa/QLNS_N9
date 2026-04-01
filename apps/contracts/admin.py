from django.contrib import admin
from .models import HopDongLaoDong, HopDongLD_CT
# Register your models here.

@admin.register(HopDongLaoDong)
class HopDongLaoDongAdmin(admin.ModelAdmin):
    list_display = ('ma_hd', 'ma_nv', 'ten_nv', 'loai_hd', 'ngay_bd', 'ngay_kt', 'chuc_vu', 'trang_thai')
    search_fields = ('ma_hd', 'ma_nv', 'ten_nv')
    list_filter = ('loai_hd', 'trang_thai')
    raw_id_fields = ('ma_nv',)
    autocomplete_fields = ('ma_nv',)

@admin.register(HopDongLD_CT)
class HopDongLD_CTAdmin(admin.ModelAdmin):
    list_display = ('ma_hd', 'luong_co_ban', 'luong_theo_gio', 'so_gio_lam', 'thuong', 'phat')
    search_fields = ('ma_hd',)
    raw_id_fields = ('ma_hd',)
    autocomplete_fields = ('ma_hd',)