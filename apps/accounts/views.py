
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from .forms import LoginForm, ChangePasswordForm


def _account_rows():
    return [
        {
            'stt': 1,
            'ho_ten': 'Nguyễn Văn An',
            'ten_dang_nhap': 'NGUYENVANAN',
            'quyen': 'Nhân viên',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
        {
            'stt': 2,
            'ho_ten': 'Lê Thị Hồng Châu',
            'ten_dang_nhap': 'LETHIHONGCHAU',
            'quyen': 'Nhân viên',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
        {
            'stt': 3,
            'ho_ten': 'Trần Tuấn Anh',
            'ten_dang_nhap': 'TRANTUANANH',
            'quyen': 'Nhân viên',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
        {
            'stt': 4,
            'ho_ten': 'Trình Phúc Lâm',
            'ten_dang_nhap': 'TRINHPHUCLAM',
            'quyen': 'Nhân viên',
            'trang_thai': 'Ngừng hoạt động',
            'trang_thai_key': 'inactive',
        },
        {
            'stt': 5,
            'ho_ten': 'Nguyễn Thị Anh',
            'ten_dang_nhap': 'NGUYENTHIANH',
            'quyen': 'Quản lý',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
    ]


def _admin_accounts():
    """Return only admin accounts - separate management list"""
    return [
        {
            'stt': 1,
            'ho_ten': 'Lê Minh Tuấn',
            'ten_dang_nhap': 'LEMINHTUAN',
            'quyen': 'Admin',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
        {
            'stt': 2,
            'ho_ten': 'Trần Thị Mai',
            'ten_dang_nhap': 'TRANTHIMAI',
            'quyen': 'Admin',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
        {
            'stt': 3,
            'ho_ten': 'Nguyễn Thị Anh',
            'ten_dang_nhap': 'NGUYENTHIANH',
            'quyen': 'Quản lý',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
    ]


def _employee_accounts():
    """Return only employee accounts - separate management list"""
    return [
        {
            'stt': 1,
            'ho_ten': 'Nguyễn Văn An',
            'ten_dang_nhap': 'NGUYENVANAN',
            'quyen': 'Nhân viên',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
        {
            'stt': 2,
            'ho_ten': 'Lê Thị Hồng Châu',
            'ten_dang_nhap': 'LETHIHONGCHAU',
            'quyen': 'Nhân viên',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
        {
            'stt': 3,
            'ho_ten': 'Trần Tuấn Anh',
            'ten_dang_nhap': 'TRANTUANANH',
            'quyen': 'Nhân viên',
            'trang_thai': 'Đang hoạt động',
            'trang_thai_key': 'active',
        },
        {
            'stt': 4,
            'ho_ten': 'Trình Phúc Lâm',
            'ten_dang_nhap': 'TRINHPHUCLAM',
            'quyen': 'Nhân viên',
            'trang_thai': 'Ngừng hoạt động',
            'trang_thai_key': 'inactive',
        },
    ]


def login_view(request):
    """
    Handle user login with form validation and authentication.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, 'Đăng nhập thành công')

            # Identify role and redirect (same destination for now, but structure supports role-based)
            if user.is_superuser or user.is_staff:
                return redirect('dashboard')
            else:
                return redirect('dashboard')
        else:
            # Handle specific errors
            for field, errors in form.errors.items():
                if field == '__all__':
                    # System error case
                    messages.error(request, 'Đăng nhập thất bại, vui lòng thử lại sau')
                elif field == 'username':
                    messages.error(request, 'Tên đăng nhập không hợp lệ')
                elif field == 'password':
                    messages.error(request, 'Mật khẩu không hợp lệ')

    return render(request, 'accounts/login.html', {'form': form})


# @login_required(login_url='/accounts/login/') # Kept commented out for easy frontend testing
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


def account_employee_list_view(request):
    from apps.branches.models import ChiNhanh
    branches = ChiNhanh.objects.filter(trang_thai='active').order_by('ma_chi_nhanh')
    selected_branch = request.GET.get('branch') or (branches.first().ma_chi_nhanh if branches.exists() else None)
    return render(
        request,
        'accounts/employee_list.html',
        {
            'account_rows': _employee_accounts(),
            'branches': branches,
            'selected_branch': selected_branch,
        },
    )


def account_admin_list_view(request):
    from apps.branches.models import ChiNhanh
    from django.contrib.auth.models import User
    from apps.accounts.models import TaiKhoan
    from apps.employees.models import NhanVien

    branches = ChiNhanh.objects.filter(trang_thai='active').order_by('ma_chi_nhanh')
    selected_branch = request.GET.get('branch') or (branches.first().ma_chi_nhanh if branches.exists() else None)

    # Get search term
    search_term = request.GET.get('q', '').strip()

    # Query all accounts from database (not just admin accounts)
    # Changed to query all users to show all accounts
    all_users = User.objects.all().select_related('taikhoan__ma_nv')

    # Apply search filter if search term is provided
    if search_term:
        from django.db.models import Q
        all_users = all_users.filter(
            Q(username__icontains=search_term) |
            Q(taikhoan__ma_nv__ho_ten__icontains=search_term)
        )

    account_rows = []
    for idx, user in enumerate(all_users, 1):
        # Get TaiKhoan if exists
        try:
            tai_khoan = user.taikhoan
            nv = tai_khoan.ma_nv
        except:
            tai_khoan = None
            nv = None

        # Get role name
        if user.is_superuser:
            quyen = 'Admin'
        elif user.is_staff:
            quyen = 'Quản lý'
        else:
            quyen = 'Nhân viên'

        # Get status
        trang_thai = 'Đang hoạt động' if user.is_active else 'Ngừng hoạt động'
        trang_thai_key = 'active' if user.is_active else 'inactive'

        # Get full name
        if nv:
            ho_ten = nv.ho_ten
        else:
            ho_ten = user.get_full_name() or user.username

        account_rows.append({
            'stt': idx,
            'ho_ten': ho_ten,
            'ten_dang_nhap': user.username,
            'quyen': quyen,
            'trang_thai': trang_thai,
            'trang_thai_key': trang_thai_key,
        })

    return render(
        request,
        'accounts/admin_list.html',
        {
            'account_rows': account_rows,
            'branches': branches,
            'selected_branch': selected_branch,
        },
    )


@csrf_exempt
@require_http_methods(["POST"])
def add_admin_account(request):
    """Thêm mới tài khoản admin"""
    try:
        from apps.accounts.models import TaiKhoan
        from apps.employees.models import NhanVien

        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if not all([username, password, role]):
            return JsonResponse({
                'success': False,
                'message': 'Vui lòng điền đầy đủ thông tin bắt buộc.'
            })

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': 'Tên đăng nhập đã tồn tại.'
            })

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password
        )

        # Set role
        if role == 'Admin':
            user.is_superuser = True
            user.is_staff = True
        elif role == 'Quản lý':
            user.is_staff = True
        user.save()

        # For admin accounts, we need to handle ma_nv differently
        # Since admin accounts might not have corresponding employees,
        # we'll create a dummy employee or handle this case
        try:
            # Try to find an existing employee or create a dummy one
            dummy_employee = NhanVien.objects.filter(ho_ten=username).first()
            if not dummy_employee:
                # Create a dummy employee for admin account
                dummy_employee = NhanVien.objects.create(
                    ho_ten=username,
                    email=f"{username}@admin.com",
                    so_dien_thoai="0000000000",
                    trang_thai='active'
                )

            # Create TaiKhoan with employee
            tai_khoan = TaiKhoan.objects.create(
                user=user,
                ma_nv=dummy_employee
            )
        except Exception as emp_error:
            # If employee creation fails, we'll skip TaiKhoan creation for now
            # This is a temporary solution - in production, you should handle this properly
            print(f"Warning: Could not create TaiKhoan for admin {username}: {str(emp_error)}")

        return JsonResponse({
            'success': True,
            'message': 'Thêm tài khoản thành công!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Đã xảy ra lỗi: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["POST"])
def edit_admin_account(request):
    """Chỉnh sửa tài khoản admin"""
    try:
        from apps.accounts.models import TaiKhoan

        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if not all([username, role]):
            return JsonResponse({
                'success': False,
                'message': 'Vui lòng điền đầy đủ thông tin bắt buộc.'
            })

        # Get user
        user = User.objects.get(username=username)

        # Update password if provided
        if password and password.strip():
            user.set_password(password)

        # Update role
        user.is_superuser = False
        user.is_staff = False
        if role == 'Admin':
            user.is_superuser = True
            user.is_staff = True
        elif role == 'Quản lý':
            user.is_staff = True
        user.save()

        # Update TaiKhoan if exists
        try:
            tai_khoan = TaiKhoan.objects.get(user=user)
            # TaiKhoan doesn't have additional fields to update based on current model
            pass
        except TaiKhoan.DoesNotExist:
            # Create TaiKhoan if it doesn't exist
            try:
                from apps.employees.models import NhanVien
                dummy_employee = NhanVien.objects.filter(ho_ten=username).first()
                if not dummy_employee:
                    dummy_employee = NhanVien.objects.create(
                        ho_ten=username,
                        email=f"{username}@admin.com",
                        so_dien_thoai="0000000000",
                        trang_thai='active'
                    )
                TaiKhoan.objects.create(
                    user=user,
                    ma_nv=dummy_employee
                )
            except Exception as emp_error:
                print(f"Warning: Could not create TaiKhoan for admin {username}: {str(emp_error)}")

        return JsonResponse({
            'success': True,
            'message': 'Cập nhật tài khoản thành công!'
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Tài khoản không tồn tại.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Đã xảy ra lỗi: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["POST"])
def delete_admin_account(request):
    """Xóa tài khoản admin"""
    try:
        from apps.accounts.models import TaiKhoan

        username = request.POST.get('username')

        if not username:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu thông tin tài khoản.'
            })

        # Get user
        user = User.objects.get(username=username)

        # Check if user has TaiKhoan and delete it first
        try:
            tai_khoan = TaiKhoan.objects.get(user=user)
            tai_khoan.delete()
        except TaiKhoan.DoesNotExist:
            pass  # TaiKhoan doesn't exist, continue with user deletion

        # Delete user (this will cascade delete related records)
        user.delete()

        return JsonResponse({
            'success': True,
            'message': 'Xóa tài khoản thành công!'
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Tài khoản không tồn tại.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Đã xảy ra lỗi: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["GET"])
def get_admin_password(request):
    """Lấy mật khẩu thật của tài khoản admin"""
    try:
        username = request.GET.get('username')

        if not username:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu thông tin tài khoản.'
            })

        # Get user
        user = User.objects.get(username=username)

        # Note: Django doesn't store passwords in plain text, they are hashed
        # We cannot retrieve the original password
        # For demonstration purposes, we'll return a message
        return JsonResponse({
            'success': False,
            'message': 'Không thể lấy mật khẩu gốc vì mật khẩu đã được mã hóa (hashed) trong database. Đây là chuẩn bảo mật của Django.',
            'password': None
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Tài khoản không tồn tại.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Đã xảy ra lỗi: {str(e)}'
        })


@login_required(login_url='/accounts/login/')
def logout_view(request):
    """
    Handle user logout with confirmation.
    """
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Đã đăng xuất thành công')
        return redirect('login')

    # For GET requests, redirect to dashboard (logout should be POST)
    return redirect('dashboard')


@login_required(login_url='/accounts/login/')
def change_password_view(request):
    """
    Handle change password via AJAX/POST from popup.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Hệ thống lỗi, không thể thay đổi mật khẩu'
        }, status=405)

    form = ChangePasswordForm(user=request.user, data=request.POST)

    if form.is_valid():
        try:
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Đổi mật khẩu thành công'
            })
        except Exception:
            return JsonResponse({
                'success': False,
                'message': 'Hệ thống lỗi, không thể thay đổi mật khẩu'
            }, status=500)
    else:
        # Extract first error message
        for field, errors in form.errors.items():
            return JsonResponse({
                'success': False,
                'message': errors[0],
                'field': field
            }, status=400)

    return JsonResponse({
        'success': False,
        'message': 'Hệ thống lỗi, không thể thay đổi mật khẩu'
    }, status=500)
