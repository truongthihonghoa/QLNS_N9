from django.contrib import admin
from .models import LichLamViec

# Register your models here.
@admin.register(LichLamViec)
class LichLamViecAdmin(admin.ModelAdmin):
    list_display = ('ma_llv', 'ma_nv', 'ngay_lam', 'ca_lam', 'ghi_chu', 'ma_chi_nhanh', 'trang_thai', 'ngay_tao')
    search_fields = ('ma_llv', 'ngay_lam', 'ma_nv__ho_ten', 'ma_nv__ma_nv')
    list_filter = ('ca_lam', 'trang_thai')
    ordering = ('ma_llv',)
    raw_id_fields = ('ma_nv', 'ma_chi_nhanh')
    autocomplete_fields = ('ma_nv', 'ma_chi_nhanh')
