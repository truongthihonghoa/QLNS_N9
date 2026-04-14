from django.contrib import admin
from .models import BaoCao, BaoCao_CT

# Register your models here.
@admin.register(BaoCao)
class BaoCaoAdmin(admin.ModelAdmin):
    list_display = ('ma_bc', 'ngay_bd', 'ngay_kt', 'ngay_tao')
    search_fields = ('ma_bc',)
    list_filter = ('ngay_tao',)
    raw_id_fields = ('ma_tk',)
    autocomplete_fields = ('ma_tk',)
    ordering = ('ma_bc',)

@admin.register(BaoCao_CT)
class BaoCao_CTAdmin(admin.ModelAdmin):
    list_display = ('ma_nv', 'ma_cc', 'ma_bc')
    search_fields = ('ma_nv', 'ma_cc', 'ma_bc')
    list_filter = ('ma_nv', 'ma_cc', 'ma_bc')
    raw_id_fields = ('ma_nv', 'ma_cc', 'ma_bc')
    autocomplete_fields = ('ma_nv', 'ma_cc', 'ma_bc')
    ordering = ('ma_nv', 'ma_cc', 'ma_bc')
