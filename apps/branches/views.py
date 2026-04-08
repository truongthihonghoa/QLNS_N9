from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChiNhanhForm
from .models import ChiNhanh


def branch_list(request):
    keyword = (request.GET.get('q') or '').strip()

    branches = ChiNhanh.objects.select_related('ma_nv_ql').order_by('ma_chi_nhanh')

    if keyword:
        branches = branches.filter(
            Q(ten_chi_nhanh__icontains=keyword)
            | Q(dia_chi__icontains=keyword)
            | Q(ma_nv_ql__ho_ten__icontains=keyword)
            | Q(ma_nv_ql__ma_nv__icontains=keyword)
        )

    return render(request, 'branches/branch_list.html', {'branches': branches, 'keyword': keyword})


def branch_create(request):
    if request.method == 'POST':
        form = ChiNhanhForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm chi nhánh mới thành công')
            return redirect('branches:branch_list')
    else:
        form = ChiNhanhForm()

    return render(request, 'branches/branch_form.html', {'form': form, 'title': 'Thêm chi nhánh'})


def branch_detail(request, pk):
    branch = get_object_or_404(ChiNhanh.objects.select_related('ma_nv_ql'), pk=pk)
    return render(request, 'branches/branch_detail.html', {'branch': branch})


def branch_update(request, pk):
    branch = get_object_or_404(ChiNhanh, pk=pk)

    if request.method == 'POST':
        form = ChiNhanhForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sửa chi nhánh thành công')
            return redirect('branches:branch_list')
    else:
        form = ChiNhanhForm(instance=branch)

    return render(request, 'branches/branch_form.html', {'form': form, 'title': 'Sửa chi nhánh'})


def branch_delete(request, pk):
    branch = get_object_or_404(ChiNhanh, pk=pk)
    branch.trang_thai = 'inactive'
    branch.save(update_fields=['trang_thai'])
    messages.success(request, 'Ngưng hoạt động chi nhánh thành công')
    return redirect('branches:branch_list')

