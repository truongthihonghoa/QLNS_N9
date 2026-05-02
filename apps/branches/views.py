from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChiNhanhForm
from .models import ChiNhanh
from apps.employees.models import NhanVien


@login_required(login_url='/accounts/login/')
def branch_list(request):
    user = request.user

    # 1. Nếu là Admin/Staff
    if user.is_superuser:
        branches = ChiNhanh.objects.all().order_by('ma_chi_nhanh')
        return render(request, 'branches/branch_list.html', {'branches': branches})
    
    if user.is_staff:
        # Quản lý chỉ thấy chi nhánh của mình
        try:
            user_branch_id = user.taikhoan.ma_nv.ma_chi_nhanh_id
            branches = ChiNhanh.objects.filter(ma_chi_nhanh=user_branch_id).order_by('ma_chi_nhanh')
            return render(request, 'branches/branch_list.html', {'branches': branches})
        except Exception:
            pass

    # 2. Nếu là Nhân viên thường
    try:
        nv = user.taikhoan.ma_nv
        if nv and nv.ma_chi_nhanh_id:
            return redirect('branches:branch_detail', pk=nv.ma_chi_nhanh_id)
    except Exception:
        pass

    # Nếu không thuộc chi nhánh nào hoặc lỗi quan hệ
    messages.warning(request, 'Bạn chưa được phân bổ vào chi nhánh nào.')
    return redirect('dashboard')


@login_required(login_url='/accounts/login/')
def branch_create(request):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này!')
        return redirect('branches:branch_list')

    form = ChiNhanhForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm chi nhánh mới thành công')
            return redirect('branches:branch_list')

    return render(request, 'branches/branch_form.html', {
        'form': form,
        'title': 'Thêm chi nhánh'
    })


@login_required(login_url='/accounts/login/')
def branch_detail(request, pk):
    # Lấy chi nhánh hoặc trả về 404
    branch = get_object_or_404(ChiNhanh.objects.select_related('ma_nv_ql'), pk=pk)
    user = request.user

    # Kiểm tra quyền xem: Admin/Staff hoặc đúng nhân viên của chi nhánh
    if not (user.is_superuser or user.is_staff):
        try:
            nv = user.taikhoan.ma_nv
            if nv.ma_chi_nhanh_id != pk:
                messages.error(request, 'Bạn không có quyền xem thông tin chi nhánh khác!')
                return redirect('dashboard')
        except Exception:
            return redirect('dashboard')

    return render(request, 'branches/branch_detail.html', {'branch': branch})


@login_required(login_url='/accounts/login/')
def branch_update(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này!')
        return redirect('branches:branch_detail', pk=pk)

    branch = get_object_or_404(ChiNhanh, pk=pk)
    form = ChiNhanhForm(request.POST or None, instance=branch)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật chi nhánh thành công')
            return redirect('branches:branch_list')

    return render(request, 'branches/branch_form.html', {
        'form': form,
        'title': 'Cập nhật chi nhánh'
    })


@login_required(login_url='/accounts/login/')
def branch_delete(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền thực hiện hành động này!')
        return redirect('branches:branch_detail', pk=pk)

    branch = get_object_or_404(ChiNhanh, pk=pk)
    # Thực hiện xóa mềm
    branch.trang_thai = 'inactive'
    branch.save(update_fields=['trang_thai'])

    messages.success(request, 'Đã ngưng hoạt động chi nhánh thành công')
    return redirect('branches:branch_list')