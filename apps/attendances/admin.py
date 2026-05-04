from django.contrib import admin
from .models import ChamCong


@admin.register(ChamCong)
class ChamCongAdmin(admin.ModelAdmin):
    list_display = ('ma_cc', 'ma_nv', 'ngay_lam', 'ca_lam', 'gio_vao', 'gio_ra', 'so_gio_lam')
    search_fields = ('ma_nv__ten_nv', 'ngay_lam')
    list_filter = ('ngay_lam', 'ca_lam')
