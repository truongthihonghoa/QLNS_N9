import json
from datetime import datetime, date
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.exceptions import ObjectDoesNotExist

from .models import BaoCao, BaoCao_CT
from ..attendances.models import ChamCong
from ..accounts.models import TaiKhoan
from ..employees.models import NhanVien
from ..branches.models import ChiNhanh
from ..requests.models import YeuCau

@login_required(login_url='/accounts/login/')
def report_list_view(request):
    role = request.session.get('role', 'Nhân viên')
    is_manager = request.user.is_superuser or request.user.is_staff or role != "Nhân viên"
    
    # SECURITY: Regular employees cannot see company-wide reports
    if not is_manager:
        return redirect('accounts:account_view')

    now = timezone.now()
    default_month = now.strftime('%m/%Y')

    branch_id = request.GET.get('branch', '')
    q = (request.GET.get('q') or '').strip()
    month_year = request.GET.get('month', default_month)
    position = request.GET.get('position', '')

    is_view_pressed = any(k in request.GET for k in ['branch', 'month', 'q', 'position'])

    employees = NhanVien.objects.all()
    if branch_id:
        employees = employees.filter(ma_chi_nhanh_id=branch_id)
    if q:
        employees = employees.filter(Q(ho_ten__icontains=q) | Q(ma_nv__icontains=q))
    if position:
        employees = employees.filter(chuc_vu=position)

    try:
        m, y = map(int, month_year.split('/'))
    except (ValueError, AttributeError):
        m, y = now.month, now.year

    attendances = ChamCong.objects.filter(ma_nv__in=employees, ngay_lam__month=m, ngay_lam__year=y)

    # Dashboard view for privileged users
    if is_manager:
        total_employees = employees.count()
        total_hours = attendances.aggregate(total=Sum('so_gio_lam'))['total'] or 0

        leave_reqs = YeuCau.objects.filter(ma_nv__in=employees, trang_thai='Đã duyệt')
        leave_reqs = leave_reqs.filter(Q(ngay_bd__month=m, ngay_bd__year=y) | Q(ngay_kt__month=m, ngay_kt__year=y))

        paid_leave = leave_reqs.filter(loai_yeu_cau__icontains='Nghỉ phép').count()
        unpaid_leave = leave_reqs.filter(loai_yeu_cau__icontains='Nghỉ không phép').count()

        positions_list = [choice[0] for choice in NhanVien.CHUC_VU_CHOICES]
        chart_hours_by_pos = []
        for pos in positions_list:
            pos_hours = attendances.filter(ma_nv__chuc_vu=pos).aggregate(total=Sum('so_gio_lam'))['total'] or 0
            chart_hours_by_pos.append({'label': pos, 'value': float(pos_hours)})

        chart_leave_status = [
            {'label': 'Nghỉ phép', 'value': paid_leave, 'color': '#C4A484'},
            {'label': 'Không phép', 'value': unpaid_leave, 'color': '#E53935'}
        ]

        attendance_details = []
        for emp in employees:
            emp_attendances = attendances.filter(ma_nv=emp)
            emp_hours = emp_attendances.aggregate(total=Sum('so_gio_lam'))['total'] or 0
            emp_leave_reqs = leave_reqs.filter(ma_nv=emp)
            emp_paid = emp_leave_reqs.filter(loai_yeu_cau__icontains='Nghỉ phép').count()
            emp_unpaid = emp_leave_reqs.filter(loai_yeu_cau__icontains='Nghỉ không phép').count()

            if emp_hours > 0 or emp_paid > 0 or emp_unpaid > 0 or is_view_pressed:
                attendance_details.append({
                    'ma_nv': emp.ma_nv,
                    'ho_ten': emp.ho_ten,
                    'chuc_vu': emp.chuc_vu,
                    'tong_gio': float(emp_hours),
                    'nghi_phep': emp_paid,
                    'khong_phep': emp_unpaid
                })

        # Xác định chi nhánh của Quản lý
        user_branch_id = None
        if not request.user.is_superuser:
            try:
                user_branch_id = request.user.taikhoan.ma_nv.ma_chi_nhanh_id
            except Exception:
                pass

        branches = ChiNhanh.objects.filter(trang_thai='active')
        if user_branch_id:
            branches = branches.filter(ma_chi_nhanh=user_branch_id)
            branch_id = user_branch_id

        return render(request, 'reports/report_list.html', {
            'show_dashboard': True,
            'is_owner': request.user.is_superuser,
            'is_staff': request.user.is_staff or role != "Nhân viên",
            'branches': branches,
            'positions': positions_list,
            'selected_branch': branch_id,
            'selected_month': month_year,
            'selected_position': position,
            'q': q,
            'stats': {
                'total_employees': total_employees,
                'total_hours': float(total_hours),
                'paid_leave': paid_leave,
                'unpaid_leave': unpaid_leave
            },
            'chart_hours_by_pos': json.dumps(chart_hours_by_pos),
            'chart_leave_status': json.dumps(chart_leave_status),
            'attendance_details': attendance_details
        })

    # Legacy view for non-dashboard reports if needed (though restricted above)
    return redirect('accounts:account_view')

@login_required(login_url='/accounts/login/')
def api_aggregate_data(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
    
    role = request.session.get('role', 'Nhân viên')
    if not (request.user.is_staff or request.user.is_superuser or role != "Nhân viên"):
        return JsonResponse({"status": "error", "message": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body)
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        branch_id = data.get('branch_id')

        nhanviens = NhanVien.objects.all()
        if branch_id:
            nhanviens = nhanviens.filter(ma_chi_nhanh=branch_id)

        result = []
        for nv in nhanviens:
            ccs = ChamCong.objects.filter(ma_nv=nv, ngay_lam__gte=start_date, ngay_lam__lte=end_date)
            if not ccs.exists(): continue

            so_ca_lam = ccs.count()
            so_gio_lam = sum(cc.so_gio_lam for cc in ccs)
            ghi_chu_str = ", ".join([cc.ghi_chu for cc in ccs if cc.ghi_chu]) or "-"
            time_id = ccs.last().ma_cc if ccs.exists() else "-"

            result.append({
                "empId": nv.ma_nv, "empName": nv.ho_ten, "timeId": time_id,
                "hours": so_gio_lam, "shifts": so_ca_lam, "late": 0.0, "early": 0.0, "note": ghi_chu_str
            })

        return JsonResponse({"status": "success", "data": result})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@login_required(login_url='/accounts/login/')
def api_save_report(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

    role = request.session.get('role', 'Nhân viên')
    if not (request.user.is_staff or request.user.is_superuser or role != "Nhân viên"):
        return JsonResponse({"status": "error", "message": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body)
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        report_data = data.get('report_data', [])
        report_id = data.get('report_id')
        branch_id = data.get('branch_id')

        # Use current user's account
        try:
            tk = TaiKhoan.objects.get(user=request.user)
        except TaiKhoan.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Account not linked"}, status=400)

        chi_nhanh = ChiNhanh.objects.filter(ma_chi_nhanh=branch_id).first() if branch_id else None

        if report_id:
            bc = BaoCao.objects.filter(ma_bc=report_id).first()
            if not bc: return JsonResponse({"status": "error", "message": "Report not found"})
            bc.ngay_bd, bc.ngay_kt = start_date, end_date
            bc.save()
            BaoCao_CT.objects.filter(ma_bc=bc).delete()
        else:
            import uuid
            report_id = f"BC{str(uuid.uuid4().int)[:6]}"
            bc = BaoCao.objects.create(
                ma_bc=report_id, ngay_bd=start_date, ngay_kt=end_date,
                ngay_tao=date.today(), ma_chi_nhanh=chi_nhanh, ma_tk=tk
            )

        for item in report_data:
            nv = NhanVien.objects.filter(ma_nv=item.get('empId')).first()
            if nv:
                cc_obj = ChamCong.objects.filter(ma_cc=item.get('timeId')).first()
                BaoCao_CT.objects.create(
                    ma_bc=bc, ma_nv=nv, ma_cc=cc_obj, ten_nv=item.get('empName'),
                    so_gio_lam=item.get('hours'), so_ca_lam=item.get('shifts'),
                    di_muon=item.get('late'), dung_gio=item.get('early'), ghi_chu=item.get('note')
                )

        return JsonResponse({"status": "success", "report_id": bc.ma_bc})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@login_required(login_url='/accounts/login/')
def api_get_report_details(request, ma_bc):
    role = request.session.get('role', 'Nhân viên')
    if not (request.user.is_staff or request.user.is_superuser or role != "Nhân viên"):
        return JsonResponse({"status": "error", "message": "Forbidden"}, status=403)

    try:
        bc = get_object_or_404(BaoCao, ma_bc=ma_bc)
        details = BaoCao_CT.objects.filter(ma_bc=bc)
        result = []
        for d in details:
            result.append({
                "empId": d.ma_nv_id, "empName": d.ten_nv, "timeId": d.ma_cc_id or "-",
                "hours": d.so_gio_lam, "shifts": d.so_ca_lam, "late": d.di_muon,
                "early": d.dung_gio, "note": d.ghi_chu or "-"
            })
        return JsonResponse({"status": "success", "data": result})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)