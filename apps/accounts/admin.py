from django.contrib import admin
from .models import TaiKhoan

@admin.register(TaiKhoan)
class TaiKhoanAdmin(admin.ModelAdmin):
    list_display = ('ma_nv', 'user', 'vai_tro', 'trang_thai')
    search_fields = ('user__username', 'ma_nv__ho_ten')
    list_filter = ('user__is_staff', 'user__is_superuser', 'user__is_active')
    
    def vai_tro(self, obj):
        return obj.vai_tro
    vai_tro.short_description = 'Vai trò'
    
    def trang_thai(self, obj):
        return obj.trang_thai
    trang_thai.short_description = 'Trạng thái'