from django.contrib import admin
from .models import TaiKhoan


@admin.register(TaiKhoan)
class TaiKhoanAdmin(admin.ModelAdmin):
    # 1. 'user' và 'ma_nv' là trường thật nên hiện được luôn.
    # 2. 'vai_tro', 'ten_dang_nhap' là @property nên bạn phải viết đúng tên hàm đó.
    list_display = ('get_username', 'ma_nv', 'get_vai_tro', 'get_trang_thai')
    search_fields = ('user__username', 'user__email', 'ma_nv__ho_ten')
    # Vì @property không lọc (filter) được trực tiếp,
    # nên list_filter bạn nên lọc theo các trường thật của User:
    list_filter = ('user__is_active', 'user__is_staff')

    # Hàm bổ trợ để hiển thị @property lên Admin
    @admin.display(description='Tên đăng nhập')
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description='Vai trò')
    def get_vai_tro(self, obj):
        return obj.vai_tro

    @admin.display(description='Trạng thái')
    def get_trang_thai(self, obj):
        return obj.trang_thai