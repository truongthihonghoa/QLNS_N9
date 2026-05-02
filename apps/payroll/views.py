import json
import calendar
import datetime
import re

from django.conf import settings
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction

from ..branches.models import ChiNhanh
from ..employees.models import NhanVien
from ..contracts.models import HopDongLaoDong
from ..attendances.models import ChamCong
from .models import Luong
from ..accounts.models import TaiKhoan

# --- HELPERS ---

def clean_money(val):
    if not val:
        return 0
    try:
        if isinstance(val, (int, float)):
            return float(val)
        return float(str(val).replace(".", "").replace(",", ""))
    except (ValueError, TypeError):
        return 0

def get_next_ma_luong():
    max_n = 0
    for s in Luong.objects.values_list('ma_luong', flat=True):
        if not s: continue
        m = re.fullmatch(r'ML(\d+)', str(s).strip())
        if m:
            try:
                n = int(m.group(1))
                if n > max_n: max_n = n
            except ValueError: continue
    return f"ML{(max_n + 1):04d}"

def _status_key(db_value: str) -> str:
    return {
        'cho_duyet': 'cho-duyet',
        'da_duyet': 'da-duyet',
        'da_tu_choi': 'da-tu-choi',
    }.get(db_value or '', 'cho-duyet')

# --- VIEWS ---

@login_required(login_url='/accounts/login/')
def payroll_list_view(request):
    role = request.session.get("role", "Nhân viên")
    if role == "Nhân viên":
        return redirect('payroll:my_salary')

    # Phân quyền chi nhánh
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

    month = request.GET.get('month')
    year = request.GET.get('year')
    search_q = (request.GET.get('q') or '').strip()

    qs = Luong.objects.select_related('nhan_vien', 'chi_nhanh').order_by('-updated_at')

    if selected_branch:
        qs = qs.filter(chi_nhanh_id=selected_branch)
    if month and month.isdigit():
        qs = qs.filter(thang=int(month))
    if year and year.isdigit():
        qs = qs.filter(nam=int(year))
    if search_q:
        qs = qs.filter(
            Q(ma_luong__icontains=search_q) |
            Q(nhan_vien__ma_nv__icontains=search_q) |
            Q(nhan_vien__ho_ten__icontains=search_q)
        )

    payroll_rows = []
    for row in qs:
        payroll_rows.append({
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
            'da_gui': row.da_gui,
        })

    branch_employees = []
    if selected_branch:
        branch_employees = list(
            NhanVien.objects.filter(ma_chi_nhanh_id=selected_branch)
            .order_by('ma_nv').values('ma_nv', 'ho_ten')
        )

    show_modal = request.GET.get('show_modal') == 'true'
    eligible_employees = []
    calculated_employees = []
    if show_modal:
        eligible_employees = request.session.pop('eligible_employees', [])
        calculated_employees = request.session.pop('calculated_employees', [])

    return render(request, 'payroll/payroll_list.html', {
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
    })

@login_required(login_url='/accounts/login/')
def payroll_export_view(request):
    return render(request, 'payroll/payroll_export.html', {'payroll_rows': []})

@login_required(login_url='/accounts/login/')
def payroll_calc_info_view(request):
    ma_nv = (request.GET.get('ma_nv') or '').strip()
    month = (request.GET.get('month') or '').strip()
    year = (request.GET.get('year') or '').strip()

    if not ma_nv or not month.isdigit() or not year.isdigit():
        return JsonResponse({'error': 'invalid_params'}, status=400)

    m, y = int(month), int(year)
    emp = get_object_or_404(NhanVien.objects.select_related('ma_chi_nhanh'), pk=ma_nv)

    first_day = datetime.date(y, m, 1)
    last_day = datetime.date(y, m, calendar.monthrange(y, m)[1])

    contract = HopDongLaoDong.objects.select_related('chi_tiet').filter(
        ma_nv_id=ma_nv, trang_thai='CON_HAN', ngay_bat_dau__lte=last_day
    ).filter(Q(ngay_ket_thuc__isnull=True) | Q(ngay_ket_thuc__gte=first_day)).order_by('-ngay_bat_dau').first()

    if not contract or not hasattr(contract, 'chi_tiet'):
        return JsonResponse({'error': 'missing_contract'}, status=404)

    qs_cc = ChamCong.objects.filter(ma_nv_id=ma_nv, ngay_lam__year=y, ngay_lam__month=m)
    total_hours = float(qs_cc.aggregate(total=Sum('so_gio_lam'))['total'] or 0)
    
    ct = contract.chi_tiet
    return JsonResponse({
        'ma_nv': emp.ma_nv,
        'ho_ten': emp.ho_ten,
        'luong_co_ban': float(ct.luong_co_ban or 0),
        'luong_theo_gio': float(ct.luong_theo_gio or 0),
        'so_gio_lam': total_hours,
    })

@login_required(login_url='/accounts/login/')
def payroll_period_employees_view(request):
    branch = (request.POST.get('branch') or request.GET.get('branch') or '').strip()
    month = (request.POST.get('month') or request.GET.get('month') or '').strip()
    year = (request.POST.get('year') or request.GET.get('year') or '').strip()

    if not branch or not month.isdigit() or not year.isdigit():
        if request.method == 'POST': return redirect('payroll_list')
        return JsonResponse({'error': 'invalid_params'}, status=400)

    m, y = int(month), int(year)
    period_start = datetime.date(y, m, 1)
    period_end = datetime.date(y, m, calendar.monthrange(y, m)[1])

    employees_qs = NhanVien.objects.filter(
        ma_chi_nhanh_id=branch,
        hop_dong__ngay_bat_dau__lte=period_end
    ).filter(Q(hop_dong__ngay_ket_thuc__isnull=True) | Q(hop_dong__ngay_ket_thuc__gte=period_start)).distinct().order_by('ma_nv')

    calculated_ids = set(Luong.objects.filter(chi_nhanh_id=branch, thang=m, nam=y).values_list('nhan_vien_id', flat=True))
    calculated_employees = list(employees_qs.filter(ma_nv__in=calculated_ids).values('ma_nv', 'ho_ten'))
    eligible_employees = list(employees_qs.exclude(ma_nv__in=calculated_ids).values('ma_nv', 'ho_ten'))

    if request.method == 'POST':
        request.session['eligible_employees'] = eligible_employees
        request.session['calculated_employees'] = calculated_employees
        return redirect(f'{reverse("payroll_list")}?branch={branch}&month={month}&year={year}&show_modal=true')

    return JsonResponse({
        'branch': branch, 'month': m, 'year': y,
        'eligible_employees': eligible_employees, 'calculated_employees': calculated_employees,
    })

@login_required(login_url='/accounts/login/')
@require_POST
def payroll_save_view(request):
    # Chỉ Chủ mới được quyền lưu/tính lương
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền thực hiện tính lương.'}, status=403)

    try:
        ma_luong = (request.POST.get('ma_luong') or '').strip()
        ma_nv = (request.POST.get('ma_nv') or '').strip()
        branch = (request.POST.get('branch') or '').strip()
        month = (request.POST.get('month') or '').strip()
        year = (request.POST.get('year') or '').strip()

        if not ma_nv or not month.isdigit() or not year.isdigit():
            return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

        m, y = int(month), int(year)
        emp = get_object_or_404(NhanVien, pk=ma_nv)
        chi_nhanh = ChiNhanh.objects.filter(pk=branch).first()

        l_cb = clean_money(request.POST.get('luong_co_ban'))
        l_gio = clean_money(request.POST.get('luong_theo_gio'))
        s_gio = float(request.POST.get('so_gio_lam') or 0)
        thuong = clean_money(request.POST.get('thuong'))
        phat = clean_money(request.POST.get('phat'))
        tong = l_cb + (l_gio * s_gio) + thuong - phat

        data = {
            'luong_co_ban': l_cb, 'luong_theo_gio': l_gio, 'so_gio_lam': s_gio,
            'thuong': thuong, 'phat': phat, 'tong_luong': tong,
        }

        if ma_luong:
            obj = get_object_or_404(Luong, pk=ma_luong)
            if obj.trang_thai != 'cho_duyet':
                return JsonResponse({'status': 'error', 'message': 'Record locked'}, status=409)
            for k, v in data.items(): setattr(obj, k, v)
            obj.save()
        else:
            obj, created = Luong.objects.update_or_create(
                nhan_vien=emp, thang=m, nam=y,
                defaults={
                    'ma_luong': get_next_ma_luong(), 'chi_nhanh': chi_nhanh,
                    'trang_thai': 'cho_duyet', **data
                }
            )

        return JsonResponse({'status': 'success', 'ma_luong': obj.ma_luong, 'ten_nv': obj.nhan_vien.ho_ten})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required(login_url='/accounts/login/')
@require_POST
def payroll_delete_view(request, ma_luong):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Bạn không có quyền xóa bảng lương.'}, status=403)
    get_object_or_404(Luong, pk=ma_luong).delete()
    return JsonResponse({'status': 'success', 'message': 'Deleted'})

@login_required(login_url='/accounts/login/')
@require_POST
def payroll_update_status_view(request, ma_luong):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền duyệt lương.'}, status=403)
    
    obj = get_object_or_404(Luong, pk=ma_luong)
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.content_type == 'application/json' else request.POST
    except Exception: payload = {}

    status_map = {'cho-duyet': 'cho_duyet', 'da-duyet': 'da_duyet', 'da-tu-choi': 'da_tu_choi'}
    next_status = status_map.get((payload.get('status') or '').strip().replace('_', '-'))
    
    if not next_status:
        return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)

    obj.trang_thai = next_status
    obj.save(update_fields=['trang_thai'])
    return JsonResponse({
        'status': 'success', 'ma_luong': obj.ma_luong,
        'trang_thai': obj.get_trang_thai_display()
    })

@login_required(login_url='/accounts/login/')
@require_POST
def payroll_send_view(request):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền gửi bảng lương.'}, status=403)

    ma_luongs = request.POST.getlist('ma_luongs[]') or request.POST.getlist('ma_luongs') or []
    updated = Luong.objects.filter(ma_luong__in=ma_luongs, trang_thai='da_duyet', da_gui=False).update(da_gui=True)
    return JsonResponse({'status': 'success', 'updated': updated})

@login_required(login_url='/accounts/login/')
@require_POST
def payroll_calculate_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền thực hiện tính lương.')
        return redirect('payroll_list')
    branch = request.POST.get('branch')
    month = request.POST.get('month')
    year = request.POST.get('year')
    selected_ids = request.POST.getlist('selected_employees')

    if not all([branch, month, year, selected_ids]):
        messages.error(request, 'Vui lòng chọn đầy đủ thông tin.')
        return redirect('payroll_list')

    m, y = int(month), int(year)
    period_start = datetime.date(y, m, 1)
    period_end = datetime.date(y, m, calendar.monthrange(y, m)[1])

    eligible, calculated = [], []
    for emp_id in selected_ids:
        try:
            nv = NhanVien.objects.get(ma_nv=emp_id)
            has_contract = HopDongLaoDong.objects.filter(
                ma_nv=nv, trang_thai='CON_HAN', ngay_bat_dau__lte=period_end
            ).filter(Q(ngay_ket_thuc__isnull=True) | Q(ngay_ket_thuc__gte=period_start)).exists()

            if has_contract:
                existing = Luong.objects.filter(nhan_vien=nv, thang=m, nam=y).exists()
                item = {'ma_nv': nv.ma_nv, 'ho_ten': nv.ho_ten}
                if existing: calculated.append(item)
                else: eligible.append(item)
        except NhanVien.DoesNotExist: continue

    request.session['eligible_employees'] = eligible
    request.session['calculated_employees'] = calculated
    return redirect(f'{reverse("payroll_list")}?branch={branch}&month={month}&year={year}&show_modal=true')

@login_required(login_url='/accounts/login/')
def payroll_add_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền thêm bảng lương.')
        return redirect('payroll_list')
    if request.method == "POST":
        branch, month, year = request.POST.get('branch'), request.POST.get('month'), request.POST.get('year')
        selected_ids = request.POST.getlist('selected_employees')
        chi_nhanh = ChiNhanh.objects.filter(ma_chi_nhanh=branch).first()

        for emp_id in selected_ids:
            try:
                nv = NhanVien.objects.get(ma_nv=emp_id)
                base = clean_money(request.POST.get(f'base_salary_{emp_id}', 0))
                rate = clean_money(request.POST.get(f'hourly_rate_{emp_id}', 0))
                hours = float(request.POST.get(f'hours_{emp_id}', 0))
                bonus = clean_money(request.POST.get(f'bonus_{emp_id}', 0))
                penalty = clean_money(request.POST.get(f'penalty_{emp_id}', 0))
                
                Luong.objects.update_or_create(
                    nhan_vien=nv, thang=int(month), nam=int(year),
                    defaults={
                        'ma_luong': get_next_ma_luong(), 'chi_nhanh': chi_nhanh,
                        'luong_co_ban': base, 'luong_theo_gio': rate, 'so_gio_lam': hours,
                        'thuong': bonus, 'phat': penalty, 'tong_luong': base + (rate * hours) + bonus - penalty,
                        'trang_thai': 'cho_duyet',
                    }
                )
            except Exception: continue
        messages.success(request, "Đã lưu bảng lương thành công!")
        return redirect('payroll_list')

    branch, month, year = request.GET.get('branch'), request.GET.get('month'), request.GET.get('year')
    employees_param = request.GET.get('employees')
    if not all([month, year, employees_param]): return redirect('payroll_list')

    m_int, y_int = int(month), int(year)
    employees_data = []
    for emp_id in employees_param.split(','):
        try:
            nv = NhanVien.objects.get(ma_nv=emp_id)
            hours = float(ChamCong.objects.filter(ma_nv_id=emp_id, ngay_lam__year=y_int, ngay_lam__month=m_int).aggregate(Sum('so_gio_lam'))['so_gio_lam__sum'] or 0)
            
            contract = HopDongLaoDong.objects.select_related('chi_tiet').filter(
                ma_nv_id=emp_id, trang_thai='CON_HAN', 
                ngay_bat_dau__lte=datetime.date(y_int, m_int, calendar.monthrange(y_int, m_int)[1])
            ).filter(Q(ngay_ket_thuc__isnull=True) | Q(ngay_ket_thuc__gte=datetime.date(y_int, m_int, 1))).order_by('-ngay_bat_dau').first()

            l_gio = float(contract.chi_tiet.luong_theo_gio or 0) if contract and hasattr(contract, 'chi_tiet') else 0
            l_cb = float(contract.chi_tiet.luong_co_ban or 0) if contract and hasattr(contract, 'chi_tiet') else 0

            employees_data.append({
                'ma_nv': nv.ma_nv, 'ho_ten': nv.ho_ten, 'sogio': hours,
                'luong_gio': l_gio, 'luong_co_ban': l_cb, 'tong_luong': (hours * l_gio) + l_cb,
            })
        except Exception: continue

    return render(request, 'payroll/payroll_add.html', {
        'branch': branch, 'month': m_int, 'year': y_int, 'employees': employees_data
    })

@login_required(login_url='/accounts/login/')
def payroll_edit_view(request, ma_luong):
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền sửa bảng lương.')
        return redirect('payroll_list')
    obj = get_object_or_404(Luong.objects.select_related('nhan_vien', 'chi_nhanh'), pk=ma_luong)
    if request.method == "POST":
        bonus = clean_money(request.POST.get(f'bonus_{obj.nhan_vien.ma_nv}', 0))
        penalty = clean_money(request.POST.get(f'penalty_{obj.nhan_vien.ma_nv}', 0))
        obj.thuong, obj.phat = bonus, penalty
        obj.tong_luong = (float(obj.luong_co_ban) + (float(obj.luong_theo_gio) * float(obj.so_gio_lam)) + bonus - penalty)
        obj.save()
        return redirect('payroll_list')

    return render(request, 'payroll/payroll_edit.html', {
        'branch': obj.chi_nhanh.ten_chi_nhanh if obj.chi_nhanh else "N/A",
        'month': obj.thang, 'year': obj.nam, 'ma_luong': obj.ma_luong,
        'employees': [{
            'ma_nv': obj.nhan_vien.ma_nv, 'ho_ten': obj.nhan_vien.ho_ten, 'sogio': obj.so_gio_lam,
            'luong_gio': obj.luong_theo_gio, 'luong_co_ban': obj.luong_co_ban, 
            'thuong': obj.thuong, 'phat': obj.phat, 'tong_luong': obj.tong_luong,
        }],
    })

@login_required(login_url='/accounts/login/')
def my_salary_view(request):
    month, year = request.GET.get('month'), request.GET.get('year')
    payroll_rows = []
    try:
        nhan_vien = TaiKhoan.objects.get(user_id=request.user.id).ma_nv
        payrolls = Luong.objects.filter(nhan_vien=nhan_vien).order_by('-nam', '-thang')
        if month and month.isdigit(): payrolls = payrolls.filter(thang=int(month))
        if year and year.isdigit(): payrolls = payrolls.filter(nam=int(year))
        for p in payrolls:
            payroll_rows.append({
                'ma_luong': p.ma_luong, 'ho_ten': p.nhan_vien.ho_ten, 'ky_luong': f"{p.thang:02d}/{p.nam}",
                'luong_co_ban': f"{p.luong_co_ban:,.0f}", 'luong_theo_gio': f"{p.luong_theo_gio:,.0f}",
                'so_gio_lam': p.so_gio_lam, 'thuong': f"{p.thuong:,.0f}", 'phat': f"{p.phat:,.0f}",
                'tong_luong': f"{p.tong_luong:,.0f}", 'trang_thai': p.get_trang_thai_display(),
            })
    except Exception: pass
    return render(request, 'payroll/payroll_detail.html', {
        'payroll_rows': payroll_rows, 'selected_month': month, 'selected_year': year
    })