from django.contrib import admin
from .models import ChamCong


@admin.register(ChamCong)
class ChamCongAdmin(admin.ModelAdmin):
    search_fields = ('ma_nv__ten_nv', 'ngay')


from django.contrib import admin

# Register your models here.
