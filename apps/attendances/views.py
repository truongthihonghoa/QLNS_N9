from django.shortcuts import render
from .models import ChamCong

def attendance_list(request):
    attendances = ChamCong.objects.select_related('ma_nv').order_by('-ngay_lam')
    return render(request, 'attendances/attendance_list.html', {'attendances': attendances})
