import json
import calendar
import datetime
import re

from django.conf import settings
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

    return render(
        request,
        'payroll/payroll_list.html',
        {
            'payroll_rows': payroll_rows,
            'branches': branches,
            'selected_branch': selected_branch,
            'branch_employees': branch_employees,
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
    For a selected branch and period, return:
      - eligible_employees: employees in that branch that do not yet have payroll for this period
      - calculated_employees: employees already calculated for this period
    Query params:
      - branch: ma_chi_nhanh
      - month: 01..12
      - year: yyyy
    """
    branch = (request.GET.get('branch') or '').strip()
    month = (request.GET.get('month') or '').strip()
    year = (request.GET.get('year') or '').strip()

    if not branch or not month.isdigit() or not year.isdigit():
        return JsonResponse({'error': 'invalid_params'}, status=400)

    m = int(month)
    y = int(year)
    if m < 1 or m > 12 or y < 1900 or y > 2100:
        return JsonResponse({'error': 'invalid_params'}, status=400)

    # Employees in selected branch
    employees_qs = NhanVien.objects.filter(ma_chi_nhanh_id=branch).order_by('ma_nv')

    calculated_ids = set(
        Luong.objects.filter(chi_nhanh_id=branch, thang=m, nam=y).values_list('nhan_vien_id', flat=True)
    )

    calculated_employees = list(
        employees_qs.filter(ma_nv__in=calculated_ids).values('ma_nv', 'ho_ten')
    )
    eligible_employees = list(
        employees_qs.exclude(ma_nv__in=calculated_ids).values('ma_nv', 'ho_ten')
    )

    return JsonResponse(
        {
            'branch': branch,
            'month': m,
            'year': y,
            'eligible_employees': eligible_employees,
            'calculated_employees': calculated_employees,
        }
    )


def _parse_money(value: str) -> float:
    if value is None:
        return 0.0
    s = str(value).strip()
    # Remove all non-digit characters except first minus sign
    # Handle formats: "1234567", "1.234.567", "1,234,567", "-1234567", etc.
    s = s.replace(',', '')  # Remove comma separators
    s = s.replace('.', '')  # Remove all dot separators
    # Now we should have just "-1234567" or "1234567"
    try:
        result = float(s) if s and s not in ('-', '') else 0.0
        return result
    except Exception:
        return 0.0


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
    """
    Create/update payroll record in DB from salary detail modal.
    POST fields:
      - ma_luong (optional for update)
      - ma_nv (required)
      - branch (ma_chi_nhanh, optional)
      - month, year (required)
      - luong_co_ban, luong_theo_gio, so_gio_lam, so_ca_lam, thuong, phat, tong_luong (optional)
    """
    demo_mode = bool(getattr(settings, 'DEBUG', False))
    if not request.user.is_authenticated and not demo_mode:
        return redirect('login')
    if not demo_mode and not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)

    ma_luong = (request.POST.get('ma_luong') or '').strip()
    ma_nv = (request.POST.get('ma_nv') or '').strip()
    branch = (request.POST.get('branch') or '').strip()
    month = (request.POST.get('month') or '').strip()
    year = (request.POST.get('year') or '').strip()

    if not ma_nv or not month.isdigit() or not year.isdigit():
        return JsonResponse({'error': 'invalid_params'}, status=400)

    m = int(month)
    y = int(year)
    if m < 1 or m > 12 or y < 1900 or y > 2100:
        return JsonResponse({'error': 'invalid_params'}, status=400)

    emp = get_object_or_404(NhanVien, pk=ma_nv)
    chi_nhanh = None
    if branch:
        chi_nhanh = get_object_or_404(ChiNhanh, pk=branch)

    payload = {
        'luong_co_ban': _parse_money(request.POST.get('luong_co_ban')),
        'luong_theo_gio': _parse_money(request.POST.get('luong_theo_gio')),
        'so_gio_lam': float(request.POST.get('so_gio_lam') or 0) if str(request.POST.get('so_gio_lam') or '').strip() else 0.0,
        'so_ca_lam': float(request.POST.get('so_ca_lam') or 0) if str(request.POST.get('so_ca_lam') or '').strip() else 0.0,
        'thuong': _parse_money(request.POST.get('thuong')),
        'phat': _parse_money(request.POST.get('phat')),
        'tong_luong': _parse_money(request.POST.get('tong_luong')),
    }

    if ma_luong:
        obj = get_object_or_404(Luong, pk=ma_luong)
        if obj.trang_thai != 'cho_duyet':
            return JsonResponse({'error': 'not_editable'}, status=409)
        obj.nhan_vien = emp
        obj.chi_nhanh = chi_nhanh
        obj.thang = m
        obj.nam = y
        for k, v in payload.items():
            setattr(obj, k, v)
        obj.save()
    else:
        obj = Luong(
            ma_luong=_next_ma_luong(),
            nhan_vien=emp,
            chi_nhanh=chi_nhanh,
            thang=m,
            nam=y,
            trang_thai='cho_duyet',
            **payload,
        )
        obj.save()

    return JsonResponse(
        {
            'ma_luong': obj.ma_luong,
            'ma_nv': obj.nhan_vien.ma_nv,
            'ten_nv': obj.nhan_vien.ho_ten,
            'ky_luong': f'{obj.thang:02d}/{obj.nam}',
            'luong_co_ban': f'{obj.luong_co_ban:,.0f}',
            'luong_theo_gio': f'{obj.luong_theo_gio:,.0f}',
            'so_gio_lam': obj.so_gio_lam,
            'so_ca_lam': obj.so_ca_lam,
            'thuong': f'{obj.thuong:,.0f}',
            'phat': f'{obj.phat:,.0f}',
            'tong_luong': f'{obj.tong_luong:,.0f}',
            'trang_thai': obj.get_trang_thai_display(),
            'trang_thai_key': _status_key(obj.trang_thai),
        }
    )


@require_POST
def payroll_delete_view(request, ma_luong: str):
    demo_mode = bool(getattr(settings, 'DEBUG', False))
    if not request.user.is_authenticated and not demo_mode:
        return redirect('login')
    if not demo_mode and not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)

    obj = get_object_or_404(Luong, pk=ma_luong)
    if obj.trang_thai != 'cho_duyet':
        return JsonResponse({'error': 'not_deletable'}, status=409)

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
    # This project currently uses a demo/stub login flow (no real auth session is created),
    # so in DEBUG we allow status updates without authentication.
    demo_mode = bool(getattr(settings, 'DEBUG', False))

    if not request.user.is_authenticated and not demo_mode:
        if request.content_type.startswith('application/json'):
            return JsonResponse({'error': 'unauthenticated'}, status=401)
        return redirect('login')

    if not demo_mode and not (request.user.is_staff or request.user.is_superuser):
        if request.content_type.startswith('application/json'):
            return JsonResponse({'error': 'forbidden'}, status=403)
        return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'payroll_list')

    obj = get_object_or_404(Luong, pk=ma_luong)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = {}

    raw_status = (payload.get('status') or request.POST.get('status') or '').strip()
    raw_status = raw_status.replace('_', '-')

    status_map = {
        'cho-duyet': 'cho_duyet',
        'da-duyet': 'da_duyet',
        'da-tu-choi': 'da_tu_choi',
    }
    next_status = status_map.get(raw_status)
    if not next_status:
        return JsonResponse({'error': 'invalid_status'}, status=400)

    obj.trang_thai = next_status
    obj.save(update_fields=['trang_thai'])

    wants_json = request.content_type.startswith('application/json') or 'application/json' in (
        request.headers.get('Accept', '') or ''
    )
    if wants_json:
        return JsonResponse(
            {
                'ma_luong': obj.ma_luong,
                'trang_thai': obj.get_trang_thai_display(),
                'trang_thai_key': _status_key(obj.trang_thai),
            }
        )

    next_url = (request.POST.get('next') or request.META.get('HTTP_REFERER') or '').strip()
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('payroll_list')
