from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from .models import ChamCong
from apps.branches.models import ChiNhanh

def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def attendance_list_view(request):
    branch_id = request.GET.get('branch', 'CN01')
    attendances = ChamCong.objects.all().order_by('-ngay_lam')

    is_admin = _is_admin(request.user)
    if not is_admin:
        try:
            ma_nv_me = request.user.taikhoan.ma_nv
            attendances = attendances.filter(ma_nv=ma_nv_me)
        except:
            attendances = attendances.none()
    elif branch_id:
        attendances = attendances.filter(ma_nv__ma_chi_nhanh=branch_id)

    branches = ChiNhanh.objects.all()

    context = {
        'attendances': attendances,
        'branches': branches,
        'selected_branch': branch_id,
        'is_admin': is_admin,
    }
    return render(request, 'attendances/attendance_list.html', context)
