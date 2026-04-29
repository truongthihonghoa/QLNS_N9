
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from .forms import LoginForm, ChangePasswordForm
from ..attendances.models import ChamCong
from ..employees.models import NhanVien
from ..payroll.models import Luong
from ..requests.models import YeuCau


def login_view(request):
    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data['user']

            # ❗ check active
            if not user.is_active:
                messages.error(request, 'Tài khoản đã bị khóa!')
                return render(request, 'accounts/login.html', {'form': form})

            login(request, user)

            messages.success(request, 'Đăng nhập thành công 🎉')

            # ✅ set role
            if user.is_superuser:
                role = 'Chủ'
            elif user.is_staff:
                role = 'Quản lý'
            else:
                role = 'Nhân viên'

            request.session['role'] = role

            return redirect('dashboard')

        else:
            # ❌ xử lý lỗi chi tiết
            if '__all__' in form.errors:
                messages.error(request, 'Sai tài khoản hoặc mật khẩu!')

            if 'username' in form.errors:
                messages.error(request, 'Tên đăng nhập không được để trống!')

            if 'password' in form.errors:
                messages.error(request, 'Mật khẩu không được để trống!')

    return render(request, 'accounts/login.html', {'form': form})


@login_required(login_url='/accounts/login/') # Kept commented out for easy frontend testing
def dashboard_view(request):

    from django.db.models import Sum
    from datetime import date

    today = date.today()
    current_month = today.month
    current_year = today.year

    # 1. Tổng nhân viên
    total_employees = NhanVien.objects.count()

    # 2. Yêu cầu chờ duyệt
    # Giả định trạng thái 'Chờ duyệt' và loại yêu cầu chứa 'nghỉ phép' hoặc 'đăng ký ca'
    pending_leave = YeuCau.objects.filter(trang_thai__icontains='Chờ', loai_yeu_cau__icontains='nghỉ phép').count()
    pending_shift = YeuCau.objects.filter(trang_thai__icontains='Chờ', loai_yeu_cau__icontains='đăng ký ca').count()
    # Các yêu cầu khác chờ duyệt
    other_pending = YeuCau.objects.filter(trang_thai__icontains='Chờ').exclude(
        loai_yeu_cau__icontains='nghỉ phép').exclude(loai_yeu_cau__icontains='đăng ký ca').count()
    total_pending = pending_leave + pending_shift + other_pending

    # 3. Chấm công hôm nay
    attendance_today = ChamCong.objects.filter(ngay_lam=today).values('ma_nv').distinct().count()
    attendance_percent = int((attendance_today / total_employees * 100) if total_employees > 0 else 0)

    # 4. Tổng lương chi (đã duyệt)
    total_salary_this_month = Luong.objects.filter(
        trang_thai='da_duyet',
        thang=current_month,
        nam=current_year
    ).aggregate(total=Sum('tong_luong'))['total'] or 0

    last_month = current_month - 1 if current_month > 1 else 12
    last_year = current_year if current_month > 1 else current_year - 1

    total_salary_last_month = Luong.objects.filter(
        trang_thai='da_duyet',
        thang=last_month,
        nam=last_year
    ).aggregate(total=Sum('tong_luong'))['total'] or 0

    if total_salary_last_month > 0:
        salary_change_percent = round(
            (total_salary_this_month - total_salary_last_month) / total_salary_last_month * 100, 1)
    else:
        salary_change_percent = 100 if total_salary_this_month > 0 else 0

    is_salary_positive = salary_change_percent >= 0

    # Format salary to millions (tr)
    total_salary_millions = round(total_salary_this_month / 1000000, 1)
    if total_salary_millions.is_integer():
        total_salary_millions = int(total_salary_millions)

    context = {
        'total_employees': total_employees,
        'total_pending': total_pending,
        'pending_leave': pending_leave,
        'pending_shift': pending_shift,
        'attendance_today': attendance_today,
        'attendance_percent': attendance_percent,
        'total_salary_millions': total_salary_millions,
        'salary_change_percent': abs(salary_change_percent),
        'is_salary_positive': is_salary_positive,
    }

    return render(request, 'accounts/dashboard.html', context)

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

@login_required(login_url='/accounts/login/')
def account_admin_list_view(request):
    from apps.branches.models import ChiNhanh
    from django.contrib.auth.models import User

    branches = ChiNhanh.objects.filter(trang_thai='active').order_by('ma_chi_nhanh')
    selected_branch = request.GET.get('branch') or (branches.first().ma_chi_nhanh if branches.exists() else None)

    search_term = request.GET.get('q', '').strip()

    # 🔥 PHÂN QUYỀN TẠI ĐÂY
    if request.user.is_superuser or request.user.is_staff:
        # Admin / Chủ → xem tất cả
        all_users = User.objects.all().select_related('taikhoan__ma_nv')
    else:
        # Nhân viên → chỉ xem chính mình
        all_users = User.objects.filter(id=request.user.id).select_related('taikhoan__ma_nv')

    # 🔍 SEARCH (sau khi đã phân quyền)
    if search_term:
        from django.db.models import Q
        all_users = all_users.filter(
            Q(username__icontains=search_term) |
            Q(taikhoan__ma_nv__ho_ten__icontains=search_term)
        )

    account_rows = []
    for idx, user in enumerate(all_users, 1):
        try:
            tai_khoan = user.taikhoan
            nv = tai_khoan.ma_nv
        except:
            nv = None

        # 🎯 ROLE
        if user.is_superuser:
            quyen = 'Chủ'
        elif user.is_staff:
            quyen = 'Quản lý'
        else:
            quyen = 'Nhân viên'

        # 🎯 TRẠNG THÁI
        trang_thai = 'Đang hoạt động' if user.is_active else 'Ngừng hoạt động'
        trang_thai_key = 'active' if user.is_active else 'inactive'

        # 🎯 TÊN
        ho_ten = nv.ho_ten if nv else user.username

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
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({
            'success': False,
            'message': 'Bạn không có quyền!'
        }, status=403)

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
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({
            'success': False,
            'message': 'Bạn không có quyền!'
        }, status=403)
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
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({
            'success': False,
            'message': 'Bạn không có quyền!'
        }, status=403)
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
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({
            'success': False,
            'message': 'Bạn không có quyền!'
        }, status=403)
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
    logout(request)
    request.session.flush()

    return redirect('accounts:login')



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


