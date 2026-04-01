from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import TaiKhoan
from apps.employees.models import NhanVien
import traceback # Import traceback module to get detailed error info


def _get_tai_khoan_data(tai_khoan_list):
    """Chuyển đổi danh sách TaiKhoan thành format cho template"""
    data = []
    for idx, tai_khoan in enumerate(tai_khoan_list, 1):
        data.append({
            'stt': idx,
            'ho_ten': tai_khoan.ma_nv.ho_ten,
            'ten_dang_nhap': tai_khoan.ten_dang_nhap,
            'quyen': tai_khoan.vai_tro,
            'trang_thai': tai_khoan.trang_thai,
            'trang_thai_key': 'active' if tai_khoan.user.is_active else 'inactive',
        })
    return data


def _admin_accounts():
    """Return only admin accounts - separate management list"""
    admin_tai_khoans = TaiKhoan.objects.filter(
        user__is_superuser=True
    ).select_related('ma_nv', 'user')
    return _get_tai_khoan_data(admin_tai_khoans)


def _employee_accounts():
    """Return only employee accounts - separate management list"""
    employee_tai_khoans = TaiKhoan.objects.filter(
        user__is_staff=False,
        user__is_superuser=False
    ).select_related('ma_nv', 'user')
    return _get_tai_khoan_data(employee_tai_khoans)


def login_view(request):
    """
    Xử lý đăng nhập người dùng
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Chuyển hướng dựa trên vai trò
            if user.is_superuser:
                return redirect('accounts:dashboard')
            elif user.is_staff:
                return redirect('accounts:dashboard')
            else:
                # Nhân viên không có giao diện, logout và chuyển về login
                logout(request)
                messages.error(request, 'Tài khoản nhân viên không có quyền truy cập giao diện!')
                return redirect('accounts:login')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng!')
    
    return render(request, 'accounts/login.html')

@login_required(login_url='/accounts/login/')
def dashboard_view(request):
    """
    Dashboard chính - chỉ cho Admin và Quản lý
    """
    user = request.user
    
    if user.is_superuser:
        return render(request, 'accounts/dashboard.html', {'user_role': 'Admin'})
    elif user.is_staff:
        return render(request, 'accounts/dashboard.html', {'user_role': 'Quản lý'})
    else:
        # Nhân viên sẽ không có giao diện, có thể redirect về login hoặc trang thông báo
        logout(request)
        return redirect('accounts:login')


@login_required(login_url='/accounts/login/')
def account_employee_list_view(request):
    """Danh sách tài khoản nhân viên - chỉ admin/quản lý được xem"""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền truy cập!')
        return redirect('accounts:dashboard')
    
    return render(
        request,
        'accounts/employee_list.html',
        {
            'account_rows': _employee_accounts(),
        },
    )


@login_required(login_url='/accounts/login/')
def account_admin_list_view(request):
    """Danh sách tài khoản admin - chỉ superadmin được xem"""
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền truy cập!')
        return redirect('accounts:dashboard')
    
    return render(
        request,
        'accounts/admin_list.html',
        {
            'account_rows': _admin_accounts(),
        },
    )


@login_required(login_url='/accounts/login/')
def admin_dashboard_view(request):
    """Dashboard cho Super Admin"""
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền truy cập!')
        return redirect('accounts:dashboard')
    
    return render(request, 'accounts/dashboard.html', {'user_role': 'Admin'})


@login_required(login_url='/accounts/login/')
def manager_dashboard_view(request):
    """Dashboard cho Quản lý"""
    if not request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền truy cập!')
        return redirect('accounts:dashboard')
    
    return render(request, 'accounts/dashboard.html', {'user_role': 'Quản lý'})


def logout_view(request):
    """

    Handles user logout
    """
    logout(request)
    return redirect('accounts:login')


def forgot_password_view(request):
    """Xử lý yêu cầu đặt lại mật khẩu"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Phương thức không hợp lệ!'}, status=405)

    try:
        username = request.POST.get('reset_username')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_new_password')
        
        print(f"DEBUG: Received request for username: {username}")
        
        # Kiểm tra username có tồn tại không
        try:
            user = User.objects.get(username=username)
            print(f"DEBUG: Found user: {user.username}")
        except User.DoesNotExist:
            print(f"DEBUG: User not found: {username}")
            return JsonResponse({'success': False, 'message': 'Tên đăng nhập không tồn tại!'})
        
        # Kiểm tra mật khẩu mới
        if len(new_password) < 8:
            return JsonResponse({'success': False, 'message': 'Mật khẩu phải có ít nhất 8 ký tự!'})
        
        if not any(c.isdigit() for c in new_password):
            return JsonResponse({'success': False, 'message': 'Mật khẩu phải chứa ít nhất 1 số!'})
        
        if not any(c.isalpha() for c in new_password):
            return JsonResponse({'success': False, 'message': 'Mật khẩu phải chứa ít nhất 1 chữ cái!'})
        
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Mật khẩu xác nhận không khớp!'})
        
        # Cập nhật mật khẩu
        user.set_password(new_password)
        user.save()
        
        print(f"DEBUG: Password for user {user.username} has been reset successfully.")
        return JsonResponse({'success': True, 'message': 'Đặt lại mật khẩu thành công!'})

    except Exception as e:
        # This is the crucial part. It will catch ANY error inside the view.
        print("--- AN EXCEPTION OCCURRED ---")
        # Print the full traceback to the console
        traceback.print_exc()
        print("-----------------------------")
        # Return a JSON response with the error, so the frontend knows what happened.
        return JsonResponse({'success': False, 'message': f'Lỗi server nội bộ: {str(e)}'}, status=500)
