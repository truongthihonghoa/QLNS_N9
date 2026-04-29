import json
from datetime import datetime, date
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.reports.models import BaoCao, BaoCao_CT
from apps.attendances.models import ChamCong
from apps.accounts.models import TaiKhoan
from apps.employees.models import NhanVien


def report_list_view(request):
    from django.utils import timezone
    from datetime import datetime
    from apps.branches.models import ChiNhanh
    from apps.employees.models import NhanVien
    from apps.attendances.models import ChamCong
    from apps.requests.models import YeuCau
    from django.db.models import Sum, Count, Q

    # Get current date for defaults
    now = timezone.now()
    default_month = now.strftime('%m/%Y')

    # Get filters from request
    branch_id = request.GET.get('branch', '')
    q = request.GET.get('q', '')
    month_year = request.GET.get('month', default_month)
    position = request.GET.get('position', '')

    # Check if 'view' was pressed (any filter present)
    is_view_pressed = 'branch' in request.GET or 'month' in request.GET or 'q' in request.GET or 'position' in request.GET

    # Initial employee queryset
    employees = NhanVien.objects.all()
    if branch_id:
        employees = employees.filter(ma_chi_nhanh_id=branch_id)
    if q:
        employees = employees.filter(ho_ten__icontains=q)
    if position:
        employees = employees.filter(chuc_vu=position)

    # Parse month/year
    try:
        m, y = map(int, month_year.split('/'))
    except ValueError:
        m, y = now.month, now.year

    # Attendance records for the period
    attendances = ChamCong.objects.filter(ma_nv__in=employees, ngay_lam__month=m, ngay_lam__year=y)

    # For Dashboard (Superuser or Staff)
    if request.user.is_superuser or request.user.is_staff:
        # 1. Summary Stats
        total_employees = employees.count()
        total_hours = attendances.aggregate(total=Sum('so_gio_lam'))['total'] or 0

        # Approved leave requests (YeuCau) - User refers to this as "lịch làm việc"
        leave_reqs = YeuCau.objects.filter(ma_nv__in=employees, trang_thai='Đã duyệt')
        # Filter leave by month
        leave_reqs = leave_reqs.filter(Q(ngay_bd__month=m, ngay_bd__year=y) | Q(ngay_kt__month=m, ngay_kt__year=y))

        paid_leave = leave_reqs.filter(loai_yeu_cau='Nghỉ phép').count()
        unpaid_leave = leave_reqs.filter(loai_yeu_cau='Nghỉ không phép').count()

        # 2. Hours by Position (Chart 1) - Aggregate from ChamCong
        positions_list = [choice[0] for choice in NhanVien.CHUC_VU_CHOICES]
        chart_hours_by_pos = []
        for pos in positions_list:
            pos_hours = attendances.filter(ma_nv__chuc_vu=pos).aggregate(total=Sum('so_gio_lam'))['total'] or 0
            chart_hours_by_pos.append({'label': pos, 'value': float(pos_hours)})

        # 3. Leave Status (Chart 2)
        chart_leave_status = [
            {'label': 'Nghỉ phép', 'value': paid_leave, 'color': '#C4A484'},
            {'label': 'Không phép', 'value': unpaid_leave, 'color': '#E53935'}
        ]

        # 4. Attendance Table Detail
        attendance_details = []
        for emp in employees:
            emp_attendances = attendances.filter(ma_nv=emp)
            emp_hours = emp_attendances.aggregate(total=Sum('so_gio_lam'))['total'] or 0

            emp_leave_reqs = leave_reqs.filter(ma_nv=emp)
            emp_paid = emp_leave_reqs.filter(loai_yeu_cau='Nghỉ phép').count()
            emp_unpaid = emp_leave_reqs.filter(loai_yeu_cau='Nghỉ không phép').count()

            # Show employee if they have data or if it's a fresh search
            if emp_hours > 0 or emp_paid > 0 or emp_unpaid > 0 or is_view_pressed:
                attendance_details.append({
                    'ma_nv': emp.ma_nv,
                    'ho_ten': emp.ho_ten,
                    'chuc_vu': emp.chuc_vu,
                    'tong_gio': float(emp_hours),
                    'nghi_phep': emp_paid,
                    'khong_phep': emp_unpaid
                })

        branches = ChiNhanh.objects.all()
        return render(request, 'reports/report_list.html', {
            'show_dashboard': True,
            'is_owner': request.user.is_superuser,
            'is_staff': request.user.is_staff,
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

    # For Managers (Existing view)
    baocaos = BaoCao.objects.all().order_by('-ma_bc')
    if branch_id:
        baocaos = baocaos.filter(ma_chi_nhanh=branch_id)
    if q:
        baocaos = baocaos.filter(ma_bc__icontains=q)

    return render(request, 'reports/report_list.html', {
        'show_dashboard': False,
        'baocaos': baocaos,
        'branches': branches,
        'selected_branch': branch_id,
        'q': q,
    })


@csrf_exempt
def api_aggregate_data(request):
    """
    Lấy dữ liệu chấm công từ ngày BĐ -> KT, nhóm theo nhân viên.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            branch_id = data.get('branch_id')

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            nhanviens = NhanVien.objects.all()
            if branch_id:
                nhanviens = nhanviens.filter(ma_chi_nhanh=branch_id)

            result = []
            for nv in nhanviens:
                ccs = ChamCong.objects.filter(ma_nv=nv, ngay_lam__gte=start_date, ngay_lam__lte=end_date)

                so_ca_lam = ccs.count()
                if so_ca_lam == 0:
                    continue

                so_gio_lam = sum(cc.so_gio_lam for cc in ccs)

                # Cộng dồn ghi chú từ các bản ghi chấm công
                ghi_chus = [cc.ghi_chu for cc in ccs if cc.ghi_chu]
                ghi_chu_str = ", ".join(ghi_chus) if ghi_chus else "-"

                # Lấy mã chấm công đại diện (ví dụ bản ghi cuối cùng trong khoảng)
                time_id = ccs.last().ma_cc if ccs.exists() else "-"

                result.append({
                    "empId": nv.ma_nv,
                    "empName": nv.ho_ten,
                    "timeId": time_id,
                    "hours": so_gio_lam,
                    "shifts": so_ca_lam,
                    "late": 0.0,
                    "early": 0.0,
                    "note": ghi_chu_str
                })

            return JsonResponse({"status": "success", "data": result})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)


@csrf_exempt
def api_save_report(request):
    """
    Lưu Báo Cáo và Báo Cáo chi tiết
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            report_data = data.get('report_data', [])
            report_id = data.get('report_id')

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            branch_id = data.get('branch_id')

            tk = TaiKhoan.objects.filter(user__username='admin').first()
            if not tk:
                tk = TaiKhoan.objects.first()

            from apps.branches.models import ChiNhanh
            chi_nhanh = ChiNhanh.objects.filter(ma_chi_nhanh=branch_id).first() if branch_id else None

            if report_id:
                bc = BaoCao.objects.filter(ma_bc=report_id).first()
                if not bc:
                    return JsonResponse({"status": "error", "message": "Report not found"})
                bc.ngay_bd = start_date
                bc.ngay_kt = end_date

                bc.save()

                BaoCao_CT.objects.filter(ma_bc=bc).delete()
            else:
                import uuid
                report_id = f"BC{str(uuid.uuid4().int)[:6]}"
                bc = BaoCao.objects.create(
                    ma_bc=report_id,
                    ngay_bd=start_date,
                    ngay_kt=end_date,
                    ngay_tao=date.today(),
                    ma_chi_nhanh=chi_nhanh,
                    ma_tk=tk
                )

            for item in report_data:
                nv = NhanVien.objects.filter(ma_nv=item.get('empId')).first()
                cc_obj = None
                if item.get('timeId'):
                    cc_obj = ChamCong.objects.filter(ma_cc=item.get('timeId')).first()

                if nv:
                    BaoCao_CT.objects.create(
                        ma_bc=bc,
                        ma_nv=nv,
                        ma_cc=cc_obj,
                        ten_nv=item.get('empName'),
                        so_gio_lam=item.get('hours'),
                        so_ca_lam=item.get('shifts'),
                        di_muon=item.get('late'),
                        dung_gio=item.get('early'),  # Changed from ve_som to dung_gio
                        ghi_chu=item.get('note')
                    )

            return JsonResponse({"status": "success", "report_id": bc.ma_bc})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)


def api_get_report_details(request, ma_bc):
    """
    Trả JSON chi tiết một bản ghi BaoCao
    """
    try:
        bc = BaoCao.objects.filter(ma_bc=ma_bc).first()
        if not bc:
            return JsonResponse({"status": "error", "message": "Not found"}, status=404)

        details = BaoCao_CT.objects.filter(ma_bc=bc)
        result = []
        for d in details:
            result.append({
                "empId": d.ma_nv_id,
                "empName": d.ten_nv,
                "timeId": d.ma_cc_id if d.ma_cc_id else "-",
                "hours": d.so_gio_lam,
                "shifts": d.so_ca_lam,
                "late": d.di_muon,
                "early": d.dung_gio,  # Changed from ve_som to dung_gio
                "note": d.ghi_chu if d.ghi_chu else "-"
            })

        return JsonResponse({"status": "success", "data": result})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)