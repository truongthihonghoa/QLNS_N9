from django.shortcuts import render
from .models import ChamCong
from apps.branches.models import ChiNhanh

def attendance_list_view(request):
    branch_id = request.GET.get('branch', 'CN01')  # Mac dinh Hai Chau (CN01)
    attendances = ChamCong.objects.all().order_by('-ngay_lam')
    
    if branch_id:
        attendances = attendances.filter(ma_nv__ma_chi_nhanh=branch_id)
        
    branches = ChiNhanh.objects.all()
    
    context = {
        'attendances': attendances,
        'branches': branches,
        'selected_branch': branch_id,
    }
    return render(request, 'attendances/attendance_list.html', context)
