import json
import calendar
import datetime
import re

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from ..branches.models import ChiNhanh
from ..employees.models import NhanVien
from ..contracts.models import HopDongLaoDong
from ..attendances.models import ChamCong
from .models import Luong

# HELPER FUNCTIONS - T�ch logic kinh doanh

# HELPER FUNCTIONS - T�ch logic kinh doanh
def _validate_payroll_request(request):

    branch = request.POST.get('branch')
    month = request.POST.get('month')
    year = request.POST.get('year')
    selected_employees = request.POST.getlist('selected_employees')
    
    errors = []
    if not branch:
        errors.append('Vui l?ng ch n chi nh�nh')
    if not month:
        errors.append('Vui l?ng ch n th�ng')
    if not year:
        errors.append('Vui l?ng ch n n m')
    if not selected_employees:
        errors.append('Vui l?ng ch n �t nh t m t nh�n vi�n')
    
    if errors:
        for error in errors:
            messages.error(request, error)
        return None
    
    return {
        'branch': branch,
        'month': month, 
        'year': year,
        'selected_employees': selected_employees
    }


def _get_period_dates(month, year):

    start_date = datetime.date(int(year), int(month), 1)
    end_date = datetime.date(
        int(year), 
        int(month), 
        calendar.monthrange(int(year), int(month))[1]
    )
    return start_date, end_date


def _get_employee_data(employee_id, start_date, end_date, ky_luong):

    try:
        employee = NhanVien.objects.get(ma_nv=employee_id)
        
        # Ki m tra h p ng
        contract = HopDongLaoDong.objects.filter(
            ma_nv=employee,
            ngay_bat_dau__lte=end_date,
            ngay_ket_thuc__gte=start_date
        ).first()
        
        if not contract:
            return None
        
        # Ki m tra luoong ton tai
        existing_payroll = Luong.objects.filter(
            ma_nv=employee,
            ky_luong=ky_luong
        ).first()
        
        emp_data = {
            'ma_nv': employee.ma_nv,
            'ho_ten': employee.ho_ten,
            'chi_nhanh': employee.ma_chi_nhanh.ten_chi_nhanh if employee.ma_chi_nhanh else '',
            'hop_dong': {
                'ma_hop_dong': contract.ma_hop_dong,
                'ngay_bat_dau': contract.ngay_bat_dau,
                'ngay_ket_thuc': contract.ngay_ket_thuc,
                'luong_co_ban': contract.luong_co_ban,
                'luong_theo_gio': contract.luong_theo_gio,
            }
        }
        
        return emp_data, existing_payroll is not None
        
    except NhanVien.DoesNotExist:
        return None, False


def _process_selected_employees(selected_employees, month, year):

    start_date, end_date = _get_period_dates(month, year)
    ky_luong = f"{month}/{year}"
    
    eligible_employees = []
    calculated_employees = []
    
    for emp_id in selected_employees:
        result = _get_employee_data(emp_id, start_date, end_date, ky_luong)
        
        if result[0]:  # C� d liu nh�n vi�n
            emp_data, is_calculated = result
            if is_calculated:
                calculated_employees.append(emp_data)
            else:
                eligible_employees.append(emp_data)
    
    return eligible_employees, calculated_employees


def _save_calculation_to_session(request, data, eligible, calculated):

    request.session['payroll_calculation_data'] = {
        'branch': data['branch'],
        'month': data['month'],
        'year': data['year'],
        'eligible_employees': eligible,
        'calculated_employees': calculated,
        'selected_employees': data['selected_employees']
    }


def _build_add_context(request, branch, month, year):

    calc_data = request.session.get('payroll_calculation_data', {})
    
    return {
        'branch': branch,
        'month': month,
        'year': year,
        'ky_luong': f"{month}/{year}",
        'eligible_employees': calc_data.get('eligible_employees', []),
        'calculated_employees': calc_data.get('calculated_employees', []),
        'selected_employees': calc_data.get('selected_employees', []),
    }




def _status_key(db_value: str) -> str:
    # DB uses underscores, UI/JS expects hyphens.
    return {
        'cho_duyet': 'cho-duyet',
        'da_duyet': 'da-duyet',
        'da_tu_choi': 'da-tu-choi',
    }.get(db_value or '', 'cho-duyet')


def payroll_list_view(request):
    branches = ChiNhanh.objects.filter(trang_thai='active').order_by('ma_chi_nhanh')
    selected_branch = request.GET.get('branch') or (branches.first().ma_chi_nhanh if branches.exists() else None)

    month = request.GET.get('month')
    year = request.GET.get('year')
    search_q = (request.GET.get('q') or '').strip()

    qs = Luong.objects.select_related('nhan_vien', 'chi_nhanh').order_by('-updated_at', '-created_at')

    if selected_branch:
        qs = qs.filter(chi_nhanh_id=selected_branch)

    if month and year and month.isdigit() and year.isdigit():
        qs = qs.filter(thang=int(month), nam=int(year))

    if search_q:
        qs = qs.filter(
            Q(ma_luong__icontains=search_q)
            | Q(nhan_vien__ma_nv__icontains=search_q)
            | Q(nhan_vien__ho_ten__icontains=search_q)
        )

    payroll_rows = [
        {
            'ma_luong': row.ma_luong,
            'ma_nv': row.nhan_vien.ma_nv,
            'ten_nv': row.nhan_vien.ho_ten,
            'ky_luong': f"{row.thang:02d}/{row.nam}",
            'luong_co_ban': f"{row.luong_co_ban:,.0f}",
            'luong_theo_gio': f"{row.luong_theo_gio:,.0f}",
            'so_gio_lam': row.so_gio_lam,
            'thuong': f"{row.thuong:,.0f}",
            'phat': f"{row.phat:,.0f}",
            'tong_luong': f"{row.tong_luong:,.0f}",
            'trang_thai': row.get_trang_thai_display(),
            'trang_thai_key': _status_key(row.trang_thai),
        }
        for row in qs
    ]

    branch_employees = []
    if selected_branch:
        branch_employees = list(
            NhanVien.objects.filter(ma_chi_nhanh_id=selected_branch).order_by('ma_nv').values('ma_nv', 'ho_ten')
        )

    # Get data from session if modal was submitted
    eligible_employees = []
    calculated_employees = []
    show_modal = request.GET.get('show_modal') == 'true'
    
    if show_modal:
        eligible_employees = request.session.get('eligible_employees', [])
        calculated_employees = request.session.get('calculated_employees', [])
        # Clear session data after using
        request.session.pop('eligible_employees', None)
        request.session.pop('calculated_employees', None)
        request.session.pop('selected_month', None)
        request.session.pop('selected_year', None)

    return render(
        request,
        'payroll/payroll_list.html',
        {
            'payroll_rows': payroll_rows,
            'branches': branches,
            'selected_branch': selected_branch,
            'branch_employees': branch_employees,
            'eligible_employees': eligible_employees,
            'calculated_employees': calculated_employees,
            'show_modal': show_modal,
            'calc_info_url': reverse('payroll_calc_info'),
            'period_employees_url': reverse('payroll_period_employees'),
            'payroll_save_url': reverse('payroll_save'),
        },
    )


def payroll_export_view(request):
    # Keep existing export page as-is for now (no branch filter requested).
    return render(request, 'payroll/payroll_export.html', {'payroll_rows': []})


def payroll_calc_info_view(request):
    """
    Returns contract-based salary rates and attendance-based working hours for one employee and period.
    Query params:
      - ma_nv: employee id
      - month: 01..12
      - year: yyyy
    """
    ma_nv = (request.GET.get('ma_nv') or '').strip()
    month = (request.GET.get('month') or '').strip()
    year = (request.GET.get('year') or '').strip()

    if not ma_nv or not month.isdigit() or not year.isdigit():
        return JsonResponse({'error': 'invalid_params'}, status=400)

    m = int(month)
    y = int(year)
    if m < 1 or m > 12 or y < 1900 or y > 2100:
        return JsonResponse({'error': 'invalid_params'}, status=400)

    emp = get_object_or_404(NhanVien.objects.select_related('ma_chi_nhanh'), pk=ma_nv)

    first_day = datetime.date(y, m, 1)
    last_day = datetime.date(y, m, calendar.monthrange(y, m)[1])

    # Pick the active contract for this employee that overlaps the selected month.
    contract = (
        HopDongLaoDong.objects.select_related('chi_tiet')
        .filter(ma_nv_id=ma_nv, trang_thai='CON_HAN', ngay_bat_dau__lte=last_day)
        .filter(Q(ngay_ket_thuc__isnull=True) | Q(ngay_ket_thuc__gte=first_day))
        .order_by('-ngay_bat_dau')
        .first()
    )

    if not contract or not getattr(contract, 'chi_tiet', None):
        return JsonResponse({'error': 'missing_contract'}, status=404)

    # Attendance hours for the period.
    qs_cc = ChamCong.objects.filter(ma_nv_id=ma_nv, ngay_lam__year=y, ngay_lam__month=m)
    agg = qs_cc.aggregate(total_hours=Sum('so_gio_lam'))
    total_hours = float(agg.get('total_hours') or 0.0)
    # Treat each ChamCong row as one shift record.
    shift_count = qs_cc.count()
    workday_count = qs_cc.values('ngay_lam').distinct().count()

    ct = contract.chi_tiet
    return JsonResponse(
        {
            'ma_nv': emp.ma_nv,
            'ho_ten': emp.ho_ten,
            'ma_chi_nhanh': getattr(emp.ma_chi_nhanh, 'ma_chi_nhanh', None),
            'period': f'{m:02d}/{y}',
            'contract': {
                'ma_hd': contract.ma_hd,
                'loai_hd': contract.loai_hd,
                'loai_hd_display': contract.get_loai_hd_display(),
            },
            'luong_co_ban': float(getattr(ct, 'luong_co_ban', 0) or 0),
            'luong_theo_gio': float(getattr(ct, 'luong_theo_gio', 0) or 0),
            'so_gio_lam': total_hours,
            'so_ca_lam': shift_count,
            'so_ngay_lam': workday_count,
        }
    )


def payroll_period_employees_view(request):
    """
    Handle POST/GET requests for payroll period employees
    POST: Get employees with valid contracts for selected period and render template
    GET: Return JSON response for AJAX requests
    """
    if request.method == 'POST':
        # Handle form POST from modal
        branch = (request.POST.get('branch') or '').strip()
        month = (request.POST.get('month') or '').strip()
        year = (request.POST.get('year') or '').strip()
        
        print(f"DEBUG: POST request - branch: {branch}, month: {month}, year: {year}")
        
        if not branch or not month.isdigit() or not year.isdigit():
            print(f"DEBUG: Invalid POST params - branch: {branch}, month: {month}, year: {year}")
            return redirect('payroll_list')
        
        m = int(month)
        y = int(year)
        if m < 1 or m > 12 or y < 1900 or y > 2100:
            print(f"DEBUG: Invalid date range - month: {m}, year: {y}")
            return redirect('payroll_list')
        
        # Get employees with valid contracts during selected period
        period_start = datetime.date(y, m, 1)
        period_end = datetime.date(y, m, calendar.monthrange(y, m)[1])
        
        print(f"DEBUG: Period range - start: {period_start}, end: {period_end}")
        
        employees_qs = NhanVien.objects.filter(
            ma_chi_nhanh_id=branch,
            hop_dong__ngay_bat_dau__lte=period_end,
            hop_dong__ngay_ket_thuc__gte=period_start
        ).distinct().order_by('ma_nv')
        
        print(f"DEBUG: Found {employees_qs.count()} employees with active contracts")
        
        calculated_ids = set(
            Luong.objects.filter(chi_nhanh_id=branch, thang=m, nam=y).values_list('nhan_vien_id', flat=True)
        )
        
        print(f"DEBUG: Found {len(calculated_ids)} calculated employee IDs: {calculated_ids}")
        
        calculated_employees = list(
            employees_qs.filter(ma_nv__in=calculated_ids).values('ma_nv', 'ho_ten')
        )
        eligible_employees = list(
            employees_qs.exclude(ma_nv__in=calculated_ids).values('ma_nv', 'ho_ten')
        )
        
        print(f"DEBUG: Eligible employees: {eligible_employees}")
        print(f"DEBUG: Calculated employees: {calculated_employees}")
        
        # Store data in session to display in modal
        request.session['eligible_employees'] = eligible_employees
        request.session['calculated_employees'] = calculated_employees
        request.session['selected_month'] = month
        request.session['selected_year'] = year
        
        # Redirect back to payroll list with query params to show modal
        return redirect(f'{reverse("payroll_list")}?branch={branch}&month={month}&year={year}&show_modal=true')
    
    else:
        # Handle GET request (AJAX)
        branch = (request.GET.get('branch') or '').strip()
        month = (request.GET.get('month') or '').strip()
        year = (request.GET.get('year') or '').strip()

        print(f"DEBUG: GET request - branch: {branch}, month: {month}, year: {year}")

        if not branch or not month.isdigit() or not year.isdigit():
            print(f"DEBUG: Invalid GET params - branch: {branch}, month: {month}, year: {year}")
            return JsonResponse({'error': 'invalid_params'}, status=400)

        m = int(month)
        y = int(year)
        if m < 1 or m > 12 or y < 1900 or y > 2100:
            print(f"DEBUG: Invalid date range - month: {m}, year: {y}")
            return JsonResponse({'error': 'invalid_params'}, status=400)

        # Employees in selected branch with valid contracts during selected period
        period_start = datetime.date(y, m, 1)
        period_end = datetime.date(y, m, calendar.monthrange(y, m)[1])
        
        print(f"DEBUG: Period range - start: {period_start}, end: {period_end}")
        
        employees_qs = NhanVien.objects.filter(
            ma_chi_nhanh_id=branch,
            hop_dong__ngay_bat_dau__lte=period_end,
            hop_dong__ngay_ket_thuc__gte=period_start
        ).distinct().order_by('ma_nv')
        
        print(f"DEBUG: Found {employees_qs.count()} employees with active contracts")

        calculated_ids = set(
            Luong.objects.filter(chi_nhanh_id=branch, thang=m, nam=y).values_list('nhan_vien_id', flat=True)
        )

        print(f"DEBUG: Found {len(calculated_ids)} calculated employee IDs: {calculated_ids}")

        calculated_employees = list(
            employees_qs.filter(ma_nv__in=calculated_ids).values('ma_nv', 'ho_ten')
        )
        eligible_employees = list(
            employees_qs.exclude(ma_nv__in=calculated_ids).values('ma_nv', 'ho_ten')
        )

        print(f"DEBUG: Eligible employees: {eligible_employees}")
        print(f"DEBUG: Calculated employees: {calculated_employees}")

        response_data = {
            'branch': branch,
            'month': m,
            'year': y,
            'eligible_employees': eligible_employees,
            'calculated_employees': calculated_employees,
        }

        print(f"DEBUG: Response data: {response_data}")
        return JsonResponse(response_data)


def _parse_money(value):
    if value is None:
        return 0

    # Fast-path for numeric values to avoid mis-parsing "3480000.0" as "34800000".
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:
            return 0

    if not value:
        return 0

    value = re.sub(r'[^0-9,.\-+]', '', str(value).strip())
    if not value or value in ('-', '+'):
        return 0

    # bỏ dấu chấm ngăn cách nghìn
    dot = value.rfind('.')
    comma = value.rfind(',')

    if dot != -1 and comma != -1:
        # Rightmost separator is decimal.
        if dot > comma:
            value = value.replace(',', '')  # commas as thousands
        else:
            value = value.replace('.', '').replace(',', '.')  # dots as thousands
    elif dot != -1:
        if value.count('.') > 1:
            value = value.replace('.', '')  # thousands
        else:
            head, tail = value.split('.', 1)
            if tail.isdigit() and len(tail) == 3 and head.lstrip('+-').isdigit():
                value = value.replace('.', '')  # thousands
            # else: keep decimal dot (prevents "...0" -> extra zero)
    elif comma != -1:
        if value.count(',') > 1:
            value = value.replace(',', '')  # thousands
        else:
            head, tail = value.split(',', 1)
            if tail.isdigit() and len(tail) == 3 and head.lstrip('+-').isdigit():
                value = value.replace(',', '')  # thousands
            else:
                value = head + '.' + tail  # decimal

    # đổi dấu phẩy thành chấm nếu có
    # value already normalized above

    try:
        return float(value)
    except:
        return 0

def _next_ma_luong() -> str:
    # Try to generate sequential ML0001, ML0002... based on existing numeric suffixes.
    max_n = 0
    for s in Luong.objects.values_list('ma_luong', flat=True):
        if not s:
            continue
        m = re.fullmatch(r'ML(\d+)', str(s).strip())
        if not m:
            continue
        try:
            n = int(m.group(1))
        except Exception:
            continue
        if n > max_n:
            max_n = n
    return f"ML{(max_n + 1):04d}"


@require_POST
def payroll_save_view(request):
    # --- Phần kiểm tra quyền (Giữ nguyên của bạn) ---
    demo_mode = bool(getattr(settings, 'DEBUG', False))
    if not request.user.is_authenticated and not demo_mode:
        return JsonResponse({'error': 'unauthenticated'}, status=401)
    if not demo_mode and not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)

    try:
        # 1. Lấy dữ liệu cơ bản
        ma_luong = (request.POST.get('ma_luong') or '').strip()
        ma_nv = (request.POST.get('ma_nv') or '').strip()
        branch = (request.POST.get('branch') or '').strip()
        month = (request.POST.get('month') or '').strip()
        year = (request.POST.get('year') or '').strip()

        if not ma_nv or not month.isdigit() or not year.isdigit():
            return JsonResponse({'status': 'error', 'message': 'Thiếu thông tin nhân viên hoặc kỳ lương'}, status=400)

        m, y = int(month), int(year)
        emp = get_object_or_404(NhanVien, pk=ma_nv)
        chi_nhanh = ChiNhanh.objects.filter(pk=branch).first() if branch else None

        # 2. Xử lý Payload dữ liệu số
        payload = {
            'luong_co_ban': _parse_money(request.POST.get('luong_co_ban')),
            'luong_theo_gio': _parse_money(request.POST.get('luong_theo_gio')),
            'so_gio_lam': float(request.POST.get('so_gio_lam') or 0),
            'so_ca_lam': float(request.POST.get('so_ca_lam') or 0),
            'thuong': _parse_money(request.POST.get('thuong')),
            'phat': _parse_money(request.POST.get('phat')),
            # Always compute on the server for consistency/safety.
            'tong_luong': (
                _parse_money(request.POST.get('luong_co_ban'))
                + (_parse_money(request.POST.get('luong_theo_gio')) * float(request.POST.get('so_gio_lam') or 0))
                + _parse_money(request.POST.get('thuong'))
                - _parse_money(request.POST.get('phat'))
            ),
        }

        # 3. Lưu hoặc cập nhật
        if ma_luong:
            obj = get_object_or_404(Luong, pk=ma_luong)
            if obj.trang_thai != 'cho_duyet':
                return JsonResponse({'status': 'error', 'message': 'Bản ghi đã khóa, không thể sửa'}, status=409)

            for k, v in payload.items():
                setattr(obj, k, v)
            obj.nhan_vien = emp
            obj.chi_nhanh = chi_nhanh
            obj.thang, obj.nam = m, y
            obj.save()
        else:
            # KIỂM TRA TRÙNG: Nếu đã tính lương cho người này rồi thì không tạo mới nữa
            existing = Luong.objects.filter(nhan_vien=emp, thang=m, nam=y).first()
            if existing:
                obj = existing
                for k, v in payload.items():
                    setattr(obj, k, v)
                obj.save()
            else:
                obj = Luong.objects.create(
                    ma_luong=_next_ma_luong(),
                    nhan_vien=emp,
                    chi_nhanh=chi_nhanh,
                    thang=m,
                    nam=y,
                    trang_thai='cho_duyet',
                    **payload
                )

        # Trả về JSON chuẩn để JS nhận diện thành công
        return JsonResponse({
            'status': 'success',
            'ma_luong': obj.ma_luong,
            'ten_nv': obj.nhan_vien.ho_ten
        })

    except Exception as e:
        # Nếu có bất kỳ lỗi gì phát sinh (DB lỗi, logic sai...), trả về lỗi 500 kèm tin nhắn
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_POST
def payroll_delete_view(request, ma_luong: str):
    demo_mode = bool(getattr(settings, 'DEBUG', False))
    if not request.user.is_authenticated and not demo_mode:
        return redirect('login')
    if not demo_mode and not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)

    obj = get_object_or_404(Luong, pk=ma_luong)

    obj.delete()

    # Kiểm xem có phải AJAX request không
    wants_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in (
        request.headers.get('Accept', '') or ''
    )
    if wants_json:
        return JsonResponse({'status': 'success', 'message': 'Xóa bảng lương thành công'})

    next_url = (request.POST.get('next') or request.META.get('HTTP_REFERER') or '').strip()
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('payroll_list')


@require_POST
def payroll_update_status_view(request, ma_luong: str):
    demo_mode = bool(getattr(settings, 'DEBUG', False))

    # Kiểm tra quyền truy cập
    if not request.user.is_authenticated and not demo_mode:
        return JsonResponse({'status': 'error', 'message': 'unauthenticated'}, status=401)

    if not demo_mode and not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'status': 'error', 'message': 'forbidden'}, status=403)

    obj = get_object_or_404(Luong, pk=ma_luong)

    # Đọc dữ liệu gửi lên (hỗ trợ cả JSON và Form POST)
    if request.method == "POST":
        try:
            if request.content_type == 'application/json':
                payload = json.loads(request.body.decode('utf-8') or '{}')
            else:
                payload = request.POST
        except Exception:
            payload = {}

        raw_status = (payload.get('status') or '').strip().replace('_', '-')

        status_map = {
            'cho-duyet': 'cho_duyet',
            'da-duyet': 'da_duyet',
            'da-tu-choi': 'da_tu_choi',
        }

        next_status = status_map.get(raw_status)
        if not next_status:
            return JsonResponse({'status': 'error', 'message': 'Trạng thái không hợp lệ'}, status=400)

        # Cập nhật trạng thái
        obj.trang_thai = next_status
        obj.save(update_fields=['trang_thai'])

        # PHẢN HỒI CHUẨN ĐỂ JS NHẬN BIẾT
        return JsonResponse({
            'status': 'success',
            'ma_luong': obj.ma_luong,
            'action_type': raw_status,  # Gửi về để JS biết là vừa 'da-duyet' hay 'da-tu-choi'
            'trang_thai': obj.get_trang_thai_display()
        })

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@require_POST
def payroll_calculate_view(request):
    """
    X l? POST request t modal t�nh l ng
    L c nh�n vi�n, ph�n lo i v� redirect sang payroll_add
    """
    branch = request.POST.get('branch')
    month = request.POST.get('month')
    year = request.POST.get('year')
    selected_employees = request.POST.getlist('selected_employees')

    if not all([branch, month, year, selected_employees]):
        messages.error(request, 'Vui l?ng ch n ? th�ng tin: chi nh�nh, th�ng, n m v� nh�n vi�n')
        return redirect('payroll_list')

    try:
        # L c nh�n vi�n c� h p ng h p l trong kho ng th i gian a ch n
        eligible_employees = []
        calculated_employees = []

        for emp_id in selected_employees:
            try:
                employee = NhanVien.objects.get(ma_nv=emp_id)

                # Ki m tra h p ng c?n hi u l c trong kho ng th i gian
                start_date = datetime.date(int(year), int(month), 1)
                end_date = datetime.date(int(year), int(month), calendar.monthrange(int(year), int(month))[1])

                valid_contract = HopDongLaoDong.objects.filter(
                    ma_nv=employee,
                    ngay_bat_dau__lte=end_date,
                    ngay_ket_thuc__gte=start_date
                ).first()

                if valid_contract:
                    # Ki m tra nh�n vi�n a  c t�nh luong trong ky ny
                    existing_payroll = Luong.objects.filter(
                        ma_nv=employee,
                        ky_luong=f"{month}/{year}"
                    ).first()

                    emp_data = {
                        'ma_nv': employee.ma_nv,
                        'ho_ten': employee.ho_ten,
                        'chi_nhanh': employee.ma_chi_nhanh.ten_chi_nhanh if employee.ma_chi_nhanh else '',
                        'hop_dong': {
                            'ma_hop_dong': valid_contract.ma_hop_dong,
                            'ngay_bat_dau': valid_contract.ngay_bat_dau,
                            'ngay_ket_thuc': valid_contract.ngay_ket_thuc,
                            'luong_co_ban': valid_contract.luong_co_ban,
                            'luong_theo_gio': valid_contract.luong_theo_gio,
                        }
                    }

                    if existing_payroll:
                        calculated_employees.append(emp_data)
                    else:
                        eligible_employees.append(emp_data)

            except NhanVien.DoesNotExist:
                continue

        # L u v�o session
        request.session['payroll_calculation_data'] = {
            'branch': branch,
            'month': month,
            'year': year,
            'eligible_employees': eligible_employees,
            'calculated_employees': calculated_employees,
            'selected_employees': selected_employees
        }

        # Redirect sang trang payroll_add v i query params
        redirect_url = reverse('payroll_add')
        query_params = f"?branch={branch}&month={month}&year={year}"
        return redirect(f"{redirect_url}{query_params}")

    except Exception as e:
        messages.error(request, f'L i khi x l? d li u t�nh l ng: {str(e)}')
        return redirect('payroll_list')


def payroll_add_view(request):
    # ==========================================
    # XỬ LÝ LƯU DỮ LIỆU (KHI NHẤN NÚT LƯU)
    # ==========================================
    if request.method == "POST":
        month = request.POST.get('month')
        year = request.POST.get('year')
        branch_id = request.POST.get('branch')

        # Tìm các ID nhân viên có trong form gửi lên
        employee_ids = [k.split('_')[1] for k in request.POST.keys() if k.startswith('bonus_')]

        chi_nhanh = None
        if branch_id:
            chi_nhanh = ChiNhanh.objects.filter(ma_chi_nhanh=branch_id).first()

        for emp_id in employee_ids:
            try:
                nv = NhanVien.objects.get(ma_nv=emp_id)

                # Lấy dữ liệu từ các input ẩn và input nhập liệu
                bonus = _parse_money(request.POST.get(f'bonus_{emp_id}', 0))
                penalty = _parse_money(request.POST.get(f'penalty_{emp_id}', 0))
                total_salary = _parse_money(request.POST.get(f'total_salary_{emp_id}', 0))

                base_salary = _parse_money(request.POST.get(f'base_salary_{emp_id}', 0))
                hourly_rate = _parse_money(request.POST.get(f'hourly_rate_{emp_id}', 0))
                hours = float(request.POST.get(f'hours_{emp_id}', 0) or 0)

                # Lưu vào Database
                # Nếu đã tồn tại lương cho NV này trong kỳ này thì cập nhật, chưa có thì tạo mới
                Luong.objects.update_or_create(
                    nhan_vien=nv,
                    thang=int(month),
                    nam=int(year),
                    defaults={
                        'ma_luong': _next_ma_luong(),  # Chỉ gán mã nếu là tạo mới hoàn toàn
                        'chi_nhanh': chi_nhanh,
                        'luong_co_ban': base_salary,
                        'luong_theo_gio': hourly_rate,
                        'so_gio_lam': hours,
                        'thuong': bonus,
                        'phat': penalty,
                        'tong_luong': total_salary,
                        'trang_thai': 'cho_duyet',
                    }
                )
            except (NhanVien.DoesNotExist, ValueError):
                continue

        messages.success(request, f"Đã lưu bảng lương kỳ {month}/{year} thành công!")

        # ĐÂY LÀ CHỖ QUAN TRỌNG: Redirect để xóa trạng thái POST
        return redirect('payroll_list')

    # ==========================================
    # HIỂN THỊ DỮ LIỆU TẠM THỜI (KHI MỚI VÀO TRANG)
    # ==========================================
    branch = request.GET.get('branch')
    month = request.GET.get('month')
    year = request.GET.get('year')
    employees_param = request.GET.get('employees')

    if not all([month, year, employees_param]):
        messages.error(request, 'Dữ liệu không đầy đủ để tính lương.')
        return redirect('payroll_list')

    try:
        month_int = int(month)
        year_int = int(year)
        selected_ids = employees_param.split(',')
    except ValueError:
        return redirect('payroll_list')

    employees = []
    warnings = []

    for emp_id in selected_ids:
        try:
            nv = NhanVien.objects.get(ma_nv=emp_id)

            # Lấy dữ liệu chấm công thực tế
            qs_cc = ChamCong.objects.filter(ma_nv_id=emp_id, ngay_lam__year=year_int, ngay_lam__month=month_int)
            total_hours = float(qs_cc.aggregate(total=Sum('so_gio_lam'))['total'] or 0)

            if qs_cc.count() == 0:
                warnings.append(f"Nhân viên {nv.ho_ten} ({nv.ma_nv}) không có dữ liệu chấm công.")

            # Lấy hợp đồng để lấy mức lương
            first_day = datetime.date(year_int, month_int, 1)
            last_day = datetime.date(year_int, month_int, calendar.monthrange(year_int, month_int)[1])

            contract = HopDongLaoDong.objects.select_related('chi_tiet').filter(
                ma_nv_id=emp_id, trang_thai='CON_HAN', ngay_bat_dau__lte=last_day
            ).filter(Q(ngay_ket_thuc__isnull=True) | Q(ngay_ket_thuc__gte=first_day)).order_by('-ngay_bat_dau').first()

            luong_gio = 0
            luong_co_ban = 0
            if contract and hasattr(contract, 'chi_tiet'):
                luong_gio = float(contract.chi_tiet.luong_theo_gio or 0)
                luong_co_ban = float(contract.chi_tiet.luong_co_ban or 0)

            employees.append({
                'ma_nv': nv.ma_nv,
                'ho_ten': nv.ho_ten,
                'sogio': total_hours,
                'luong_gio': luong_gio,
                'luong_co_ban': luong_co_ban,
                'tong_luong': (total_hours * luong_gio) + luong_co_ban,
            })
        except NhanVien.DoesNotExist:
            continue

    return render(request, 'payroll/payroll_add.html', {
        'branch': branch,
        'month': month_int,
        'year': year_int,
        'employees': employees,
        'warnings': warnings
    })


def payroll_edit_view(request, ma_luong):
    # 1. Lấy bản ghi bảng lương
    obj = get_object_or_404(Luong.objects.select_related('nhan_vien', 'chi_nhanh'), pk=ma_luong)


    # 3. XỬ LÝ LƯU (POST)
    if request.method == "POST":
        # Lấy dữ liệu Thưởng/Phạt từ form gửi lên
        # Template của bạn đang dùng name="bonus_{{ emp.ma_nv }}"
        bonus = _parse_money(request.POST.get(f'bonus_{obj.nhan_vien.ma_nv}', 0))
        penalty = _parse_money(request.POST.get(f'penalty_{obj.nhan_vien.ma_nv}', 0))

        # Cập nhật dữ liệu
        obj.thuong = bonus
        obj.phat = penalty

        # Tính toán lại tổng lương (Lương CB + Lương Giờ*Số Giờ + Thưởng - Phạt)
        obj.tong_luong = (float(obj.luong_co_ban) +
                          (float(obj.luong_theo_gio) * float(obj.so_gio_lam)) +
                          float(bonus) - float(penalty))

        obj.save()

        # Sau khi lưu xong, redirect về danh sách.
        # (JS ở trang list sẽ nhận diện sessionStorage để hiện Toast)
        return redirect('payroll_list')

    # 4. HIỂN THỊ DỮ LIỆU (GET)
    # Mapping dữ liệu để tương thích với template payroll_add.html (hoặc edit)
    # Vì template đang dùng vòng lặp {% for emp in employees %}
    employee_data = {
        'ma_nv': obj.nhan_vien.ma_nv,
        'ho_ten': obj.nhan_vien.ho_ten,
        'sogio': obj.so_gio_lam,
        'luong_gio': obj.luong_theo_gio,
        'luong_co_ban': obj.luong_co_ban,
        'thuong': obj.thuong,
        'phat': obj.phat,
        'tong_luong': obj.tong_luong,
    }

    return render(request, 'payroll/payroll_edit.html', {
        'branch': obj.chi_nhanh.ten_chi_nhanh if obj.chi_nhanh else "Chi nhánh GÉ",
        'month': obj.thang,
        'year': obj.nam,
        'employees': [employee_data],  # Truyền vào list
        'ma_luong': obj.ma_luong,
    })
