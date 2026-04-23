from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChiNhanhForm
from .models import ChiNhanh


from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import ChiNhanh
from apps.employees.models import NhanVien


@login_required(login_url='/accounts/login/')
def branch_list(request):
    user = request.user

    # 1. Nếu là Admin/Staff (is_staff=True trong bảng auth_user)
    # Cứ cho xem danh sách, không cần quan tâm bảng TaiKhoan hay NhanVien
    if user.is_superuser or user.is_staff:
        branches = ChiNhanh.objects.all().order_by('ma_chi_nhanh')
        return render(request, 'branches/branch_list.html', {'branches': branches})

    # 2. Nếu là Nhân viên thường
    # Thử lấy qua bảng TaiKhoan trước (Cách chính thống)
    if hasattr(user, 'taikhoan'):
        nv = user.taikhoan.ma_nv
        if nv and nv.ma_chi_nhanh_id:
            return redirect('branches:branch_detail', pk=nv.ma_chi_nhanh_id)

    # 3. CÁCH FIX MỚI: Nếu không thấy TaiKhoan, thử tìm trực tiếp trong bảng NhanVien
    # (Giả định bạn đặt username trùng với mã nhân viên hoặc tên nhân viên)

    nv_backup = NhanVien.objects.filter(ho_ten__icontains=user.username).first()
    if nv_backup and nv_backup.ma_chi_nhanh_id:
        return redirect('branches:branch_detail', pk=nv_backup.ma_chi_nhanh_id)

    # Nếu tất cả đều thất bại
    return redirect('dashboard')

@login_required(login_url='/accounts/login/')
def branch_create(request):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền!')
        return redirect('branches:branch_list')

    if request.method == 'POST':
        form = ChiNhanhForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm chi nhánh mới thành công')
            return redirect('branches:branch_list')
    else:
        form = ChiNhanhForm()

    return render(request, 'branches/branch_form.html', {
        'form': form,
        'title': 'Thêm chi nhánh'
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.employees.models import NhanVien


@login_required(login_url='/accounts/login/')
def branch_detail(request, pk):
    # Lấy chi nhánh hoặc trả về 404
    branch = get_object_or_404(ChiNhanh.objects.select_related('ma_nv_ql'), pk=pk)
    user = request.user

    # 🔥 KIỂM TRA QUYỀN XEM
    if not (user.is_superuser or user.is_staff):
        try:
            # 1. Lấy thông tin nhân viên (Cách chuẩn)
            if hasattr(user, 'taikhoan'):
                nv = user.taikhoan.ma_nv
                # So sánh mã chi nhánh của nhân viên với mã chi nhánh đang xem
                if nv.ma_chi_nhanh_id != pk:
                    messages.error(request, 'Bạn không có quyền xem chi nhánh khác!')
                    return redirect('dashboard')

            # 2. Cách dự phòng cho User "Huy" (Thiếu bảng TaiKhoan)
            else:
                nv_backup = NhanVien.objects.filter(ho_ten__icontains=user.username).first()
                if nv_backup:
                    if nv_backup.ma_chi_nhanh_id != pk:
                        return redirect('dashboard')
                else:
                    # Không tìm thấy bất cứ thông tin gì về nhân viên này
                    return redirect('dashboard')

        except Exception as e:
            print(f"Lỗi phân quyền: {e}")
            return redirect('dashboard')

    # Nếu là Admin/Staff hoặc đúng nhân viên của chi nhánh -> Cho xem
    return render(request, 'branches/branch_detail.html', {'branch': branch})

@login_required(login_url='/accounts/login/')
def branch_update(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền!')
        return redirect('branches:branch_detail', pk=pk)

    branch = get_object_or_404(ChiNhanh, pk=pk)

    if request.method == 'POST':
        form = ChiNhanhForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sửa chi nhánh thành công')
            return redirect('branches:branch_list')
    else:
        form = ChiNhanhForm(instance=branch)

    return render(request, 'branches/branch_form.html', {
        'form': form,
        'title': 'Sửa chi nhánh'
    })

@login_required(login_url='/accounts/login/')
def branch_delete(request, pk):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền!')
        return redirect('branches:branch_detail', pk=pk)

    branch = get_object_or_404(ChiNhanh, pk=pk)
    branch.trang_thai = 'inactive'
    branch.save(update_fields=['trang_thai'])

    messages.success(request, 'Ngưng hoạt động chi nhánh thành công')
    return redirect('branches:branch_list')