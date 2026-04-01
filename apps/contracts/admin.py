from django.contrib import admin
from .models import HopDongLaoDong, HopDongLD_CT
# Register your models here.

@admin.register(HopDongLaoDong)
class HopDongLaoDongAdmin(admin.ModelAdmin):
    list_display = ('ma_hd', 'ma_nv', 'get_ten_nv', 'loai_hd', 'ngay_bat_dau', 'ngay_ket_thuc', 'chuc_vu', 'trang_thai')
    search_fields = ('ma_hd', 'ma_nv__ma_nv', 'ma_nv__ho_ten')
    list_filter = ('loai_hd', 'trang_thai')
    raw_id_fields = ('ma_nv',)
    autocomplete_fields = ('ma_nv',)

    def get_ten_nv(self, obj):
        return obj.ma_nv.ho_ten
    get_ten_nv.short_description = 'Tên nhân viên'

@admin.register(HopDongLD_CT)
class HopDongLD_CTAdmin(admin.ModelAdmin):
    list_display = ('ma_hd', 'luong_co_ban', 'luong_theo_gio', 'so_gio_lam', 'che_do_thuong')
    search_fields = ('ma_hd__ma_hd',)
    raw_id_fields = ('ma_hd',)
    autocomplete_fields = ('ma_hd',)