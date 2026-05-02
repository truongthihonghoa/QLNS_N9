
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from .forms import LoginForm, ChangePasswordForm
from django.utils import timezone
from django.db.models import Sum
from apps.employees.models import NhanVien
from apps.requests.models import YeuCau
from apps.attendances.models import ChamCong
from apps.payroll.models import Luong
from apps.schedules.models import LichLamViec



def login_view(request):
    if request.user.is_authenticated:
        role = request.session.get('role')
        if not role:
            if request.user.is_superuser: role = 'Chủ'
            elif request.user.is_staff: role = 'Quản lý'
            else: role = 'Nhân viên'
            request.session['role'] = role

        if role == 'Nhân viên':
            # Chuyển về danh sách tài khoản thay vì trang chi tiết
            return redirect('accounts:account_employee_list')
        return redirect('dashboard')

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

            if role == 'Nhân viên':
                try:
                    # ma_nv = user.taikhoan.ma_nv.ma_nv
                    return redirect('accounts:account_employee_list', employee_id=ma_nv)
                except Exception:
                    return redirect('accounts:account_employee_list')

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


@login_required(login_url='/accounts/login/')
def dashboard_view(request):
    role = request.session.get('role', 'Nhân viên')
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # 1. Tổng nhân viên
    total_employees = NhanVien.objects.count()

    # 2. Yêu cầu chờ duyệt
    pending_requests = YeuCau.objects.filter(trang_thai='Chờ duyệt')
    pending_count = pending_requests.count()
    leave_requests = pending_requests.filter(loai_yeu_cau__icontains='nghỉ').count()
    shift_requests = pending_requests.exclude(loai_yeu_cau__icontains='nghỉ').count()

    # 3. Chấm công
    attendance_checked_in = ChamCong.objects.filter(ngay_lam=today, gio_vao__isnull=False).count()
    attendance_total = LichLamViec.objects.filter(ngay_lam=today).count()
    if attendance_total == 0:
        attendance_total = total_employees if total_employees > 0 else 1

    # 4. Tổng lương chi (Tháng hiện tại)
    payroll_sum = Luong.objects.filter(thang=current_month, nam=current_year).aggregate(Sum('tong_luong'))['tong_luong__sum'] or 0
    payroll_display = f"{payroll_sum:,.0f} VNĐ".replace(",", ".")

    context = {
        'role': role,
        'total_employees': total_employees,
        'pending_count': pending_count,
        'leave_requests': leave_requests,
        'shift_requests': shift_requests,
        'attendance_checked_in': attendance_checked_in,
        'attendance_total': attendance_total,
        'payroll_display': payroll_display,
    }

    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='/accounts/login/')
def account_employee_list_view(request):
    user = request.user
    try:
        # Lấy thông tin nhân viên từ bảng TaiKhoan
        nv = user.taikhoan.ma_nv
        ho_ten = nv.ho_ten
    except Exception:
        ho_ten = user.username

    # Tạo dữ liệu 1 hàng duy nhất như trong hình ảnh
    account_rows = [{
        'stt': 1,
        'ho_ten': ho_ten,
        'ten_dang_nhap': user.username,
        'quyen': 'Nhân viên',
        'trang_thai': 'Đang hoạt động',
        'trang_thai_key': 'active',
    }]

    return render(request, 'accounts/employee_list.html', {
        'account_rows': account_rows,
        'selected_branch_name': "Hải Châu", # Có thể thay bằng nv.ma_chi_nhanh.ten_chi_nhanh
    })

@login_required(login_url='/accounts/login/')
def account_admin_list_view(request):
    from apps.branches.models import ChiNhanh
    from django.contrib.auth.models import User

    # Xác định chi nhánh của Quản lý
    user_branch_id = None
    if not request.user.is_superuser:
        try:
            user_branch_id = request.user.taikhoan.ma_nv.ma_chi_nhanh_id
        except Exception:
            pass

    branches = ChiNhanh.objects.filter(trang_thai='active').order_by('ma_chi_nhanh')
    if user_branch_id:
        branches = branches.filter(ma_chi_nhanh=user_branch_id)
        selected_branch = user_branch_id
    else:
        selected_branch = request.GET.get('branch') or (branches.first().ma_chi_nhanh if branches.exists() else None)

    search_term = request.GET.get('q', '').strip()

    # 🔥 PHÂN QUYỀN TẠI ĐÂY
    if request.user.is_superuser:
        # Chủ → xem tất cả
        all_users = User.objects.all().select_related('taikhoan__ma_nv')
    elif request.user.is_staff:
        # Quản lý → xem người cùng chi nhánh
        all_users = User.objects.filter(taikhoan__ma_nv__ma_chi_nhanh=user_branch_id).select_related('taikhoan__ma_nv')
    else:
        # Nhân viên → chỉ xem chính mình
        all_users = User.objects.filter(id=request.user.id).select_related('taikhoan__ma_nv')

    # 🔍 SEARCH & FILTER (sau khi đã phân quyền)
    if selected_branch:
        all_users = all_users.filter(taikhoan__ma_nv__ma_chi_nhanh=selected_branch)
        if user_branch_id and selected_branch != user_branch_id:
            all_users = all_users.none()

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

    # Lấy tất cả nhân viên để gợi ý (Autocomplete)
    from apps.employees.models import NhanVien
    from apps.accounts.models import TaiKhoan
    
    all_employees = NhanVien.objects.all().only('ma_nv', 'ho_ten')
    employees_with_account = list(TaiKhoan.objects.values_list('ma_nv_id', flat=True))

    return render(
        request,
        'accounts/admin_list.html',
        {
            'account_rows': account_rows,
            'branches': branches,
            'selected_branch': selected_branch,
            'all_employees': all_employees,
            'employees_with_account': employees_with_account,
        },
    )

@login_required(login_url='/accounts/login/')
@require_http_methods(["POST"])
def add_admin_account(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({
            'success': False,
            'message': 'Bạn không có quyền!'
        }, status=403)

    try:
        from apps.accounts.models import TaiKhoan
        from django.contrib.auth.models import User

        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        ma_nv = request.POST.get('ma_nv')

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

        # Create TaiKhoan record linked to employee if provided
        TaiKhoan.objects.create(
            user=user,
            ma_nv_id=ma_nv if ma_nv else None
        )

        return JsonResponse({
            'success': True,
            'message': 'Thêm tài khoản thành công!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Đã xảy ra lỗi: {str(e)}'
        })


@login_required(login_url='/accounts/login/')
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


@login_required(login_url='/accounts/login/')
@require_http_methods(["POST"])
def toggle_admin_account_status(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({
            'success': False,
            'message': 'Bạn không có quyền!'
        }, status=403)
    try:
        username = request.POST.get('username')

        if not username:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu thông tin tài khoản.'
            })

        # Get user
        user = User.objects.get(username=username)

        # Toggle active status
        user.is_active = not user.is_active
        user.save()

        trang_thai = "kích hoạt lại" if user.is_active else "ngưng"

        return JsonResponse({
            'success': True,
            'message': f'Đã {trang_thai} tài khoản thành công!'
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
