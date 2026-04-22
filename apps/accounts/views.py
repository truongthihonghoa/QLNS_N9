from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .forms import LoginForm, ChangePasswordForm

# Giá trị GET `branch` = xem tất cả chi nhánh (khớp với option trong template)
BRANCH_FILTER_ALL = '__all__'


def _resolve_selected_branch(request, branches_qs):
    """
    Lấy mã chi nhánh từ GET (hợp lệ và active), hoặc BRANCH_FILTER_ALL để không lọc theo chi nhánh,
    không có GET hợp lệ thì mặc định chi nhánh active đầu tiên.
    """
    branch_from_get = (request.GET.get('branch') or '').strip()
    if branch_from_get == BRANCH_FILTER_ALL:
        return BRANCH_FILTER_ALL
    if branch_from_get and branches_qs.filter(ma_chi_nhanh=branch_from_get).exists():
        return branch_from_get
    first = branches_qs.first()
    return first.ma_chi_nhanh if first else None


def _branch_scope_filters_qs(selected_branch):
    """True nếu cần lọc queryset theo một chi nhánh cụ thể."""
    return bool(selected_branch and selected_branch != BRANCH_FILTER_ALL)


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
    from apps.employees.models import NhanVien
    from apps.requests.models import YeuCau
    from apps.attendances.models import ChamCong
    from apps.payroll.models import Luong
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
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("Bạn không có quyền truy cập chức năng này.")

    from apps.branches.models import ChiNhanh

    branches = ChiNhanh.objects.filter(trang_thai='active').order_by('ma_chi_nhanh')
    selected_branch = _resolve_selected_branch(request, branches)
    search_term = (request.GET.get('q') or '').strip()

    # Tài khoản nhân viên: không phải admin hệ thống / quản lý (staff)
    all_users = User.objects.filter(is_superuser=False, is_staff=False).select_related(
        'taikhoan__ma_nv'
    )

    if _branch_scope_filters_qs(selected_branch):
        all_users = all_users.filter(taikhoan__ma_nv__ma_chi_nhanh_id=selected_branch)

    if search_term:
        all_users = all_users.filter(
            Q(username__icontains=search_term)
            | Q(taikhoan__ma_nv__ho_ten__icontains=search_term)
        )

    account_rows = []
    for idx, user in enumerate(all_users, 1):
        try:
            nv = user.taikhoan.ma_nv
        except Exception:
            nv = None

        quyen = 'Nhân viên'
        trang_thai = 'Đang hoạt động' if user.is_active else 'Ngừng hoạt động'
        trang_thai_key = 'active' if user.is_active else 'inactive'
        ho_ten = nv.ho_ten if nv else (user.get_full_name() or user.username)

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
        'accounts/employee_list.html',
        {
            'account_rows': account_rows,
            'branches': branches,
            'selected_branch': selected_branch,
            'branch_all': BRANCH_FILTER_ALL,
        },
    )


def account_admin_list_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("Bạn không có quyền truy cập chức năng này.")

    from apps.branches.models import ChiNhanh

    branches = ChiNhanh.objects.filter(trang_thai='active').order_by('ma_chi_nhanh')
    selected_branch = _resolve_selected_branch(request, branches)

    # Get search term
    search_term = request.GET.get('q', '').strip()

    # Query all accounts from database (not just admin accounts)
    # Changed to query all users to show all accounts
    all_users = User.objects.all().select_related('taikhoan__ma_nv')

    if _branch_scope_filters_qs(selected_branch):
        all_users = all_users.filter(taikhoan__ma_nv__ma_chi_nhanh_id=selected_branch)

    # Apply search filter if search term is provided
    if search_term:
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
            'branch_all': BRANCH_FILTER_ALL,
        },
    )


@require_http_methods(["GET"])
def api_employee_name_search(request):
    """Gợi ý nhân viên theo họ tên (khớp gần đúng, icontains)."""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied()

    from apps.employees.models import NhanVien

    q = (request.GET.get("q") or "").strip()
    if len(q) < 1:
        return JsonResponse({"results": []})

    qs = (
        NhanVien.objects.filter(ho_ten__icontains=q)
        .order_by("ho_ten")
        .values("ma_nv", "ho_ten")[:20]
    )
    return JsonResponse({"results": list(qs)})


@require_http_methods(["GET"])
def api_employee_has_account(request):
    """Kiểm tra nhân viên đã có bản ghi TaiKhoan hay chưa."""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied()

    from apps.accounts.models import TaiKhoan
    from apps.employees.models import NhanVien

    ma_nv = (request.GET.get("ma_nv") or "").strip()
    if not ma_nv:
        return JsonResponse({"has_account": False, "ho_ten": "", "error": "missing_ma_nv"})

    nv = NhanVien.objects.filter(pk=ma_nv).first()
    if not nv:
        return JsonResponse({"has_account": False, "ho_ten": "", "error": "not_found"})

    has_account = TaiKhoan.objects.filter(ma_nv=nv).exists()
    return JsonResponse({"has_account": has_account, "ho_ten": nv.ho_ten})


@csrf_exempt
@require_http_methods(["POST"])
def add_admin_account(request):
    """Thêm tài khoản, bắt buộc liên kết nhân viên (ma_nv) chưa có TaiKhoan."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'message': 'Bạn không có quyền thao tác.'}, status=403)

    try:
        from apps.accounts.models import TaiKhoan
        from apps.employees.models import NhanVien

        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password")
        role = (request.POST.get("role") or "").strip()
        ma_nv = (request.POST.get("ma_nv") or "").strip()

        if not all([username, password, role, ma_nv]):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Vui lòng chọn nhân viên và điền đầy đủ thông tin bắt buộc.",
                }
            )

        nv = NhanVien.objects.filter(pk=ma_nv).first()
        if not nv:
            return JsonResponse({"success": False, "message": "Không tìm thấy nhân viên."})

        if TaiKhoan.objects.filter(ma_nv=nv).exists():
            return JsonResponse({"success": False, "message": "Nhân viên này đã có tài khoản."})

        if User.objects.filter(username=username).exists():
            return JsonResponse({"success": False, "message": "Tên đăng nhập đã tồn tại."})

        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password)
            if role == "Admin":
                user.is_superuser = True
                user.is_staff = True
            elif role == "Quản lý":
                user.is_staff = True
            user.save()
            TaiKhoan.objects.create(user=user, ma_nv=nv)

        return JsonResponse({"success": True, "message": "Thêm tài khoản thành công!"})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Đã xảy ra lỗi: {str(e)}"})


@csrf_exempt
@require_http_methods(["POST"])
def edit_admin_account(request):
    """Chỉnh sửa tài khoản admin"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'message': 'Bạn không có quyền thao tác.'}, status=403)

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
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'message': 'Bạn không có quyền thao tác.'}, status=403)

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
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'message': 'Bạn không có quyền thao tác.'}, status=403)

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