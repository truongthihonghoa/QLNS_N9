from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Sum
from .models import ChamCong
from apps.branches.models import ChiNhanh
from apps.schedules.models import LichLamViec
from apps.employees.models import NhanVien
import datetime


def attendance_list_view(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        # MANAGER VIEW
        branch_id = request.GET.get('branch', 'CN01')  # Default Hai Chau (CN01)
        search_query = request.GET.get('search', '')
        selected_month = request.GET.get('month', '')
        selected_year = request.GET.get('year', '')

        attendances = ChamCong.objects.all().order_by('-ngay_lam')

        # Logic lọc theo chi nhánh
        if branch_id and branch_id != '':
            attendances = attendances.filter(ma_nv__ma_chi_nhanh=branch_id)

        # Logic lọc theo tìm kiếm
        if search_query and search_query != '':
            attendances = attendances.filter(ma_nv__ho_ten__icontains=search_query)

        # Logic lọc theo tháng
        if selected_month and selected_month != '':
            attendances = attendances.filter(ngay_lam__month=selected_month)

        # Logic lọc theo năm
        if selected_year and selected_year != '':
            attendances = attendances.filter(ngay_lam__year=selected_year)

        branches = ChiNhanh.objects.all()

        context = {
            'is_manager': True,
            'attendances': attendances,
            'branches': branches,
            'selected_branch': branch_id,
            'search_query': search_query,
            'selected_month': selected_month,
            'selected_year': selected_year,
        }
    else:
        # EMPLOYEE VIEW
        try:
            employee = user.taikhoan.ma_nv
        except Exception:
            return render(request, 'error.html', {'message': 'Tài khoản chưa được liên kết với nhân viên.'})

        now = timezone.now()
        today = now.date()

        # Find today's shift
        current_shift_record = LichLamViec.objects.filter(ma_nv=employee, ngay_lam=today).first()

        shift_colleagues = []
        if current_shift_record:
            # Get everyone in the same shift at the same branch
            shift_colleagues_records = LichLamViec.objects.filter(
                ngay_lam=today,
                ca_lam=current_shift_record.ca_lam,
                ma_chi_nhanh=current_shift_record.ma_chi_nhanh
            ).select_related('ma_nv')

            for rec in shift_colleagues_records:
                # Get check-in status for this colleague and shift
                ca_code = get_ca_code(rec.ca_lam)

                # Check if ChamCong exists
                cc = ChamCong.objects.filter(ma_nv=rec.ma_nv, ngay_lam=today, ca_lam=ca_code).first()

                shift_colleagues.append({
                    'ma_nv': rec.ma_nv.ma_nv,
                    'ho_ten': rec.ma_nv.ho_ten,
                    'chuc_vu': rec.ma_nv.chuc_vu,
                    'gio_vao': cc.gio_vao if cc else None,
                    'gio_ra': cc.gio_ra if cc else None,
                    'trang_thai': cc.trang_thai if cc else 'Chưa vào',
                    'ghi_chu': cc.ghi_chu if cc else '-',
                    'is_self': rec.ma_nv == employee
                })

        # Monthly total hours
        month_start = today.replace(day=1)
        total_hours_month = ChamCong.objects.filter(
            ma_nv=employee,
            ngay_lam__gte=month_start,
            ngay_lam__lte=today
        ).aggregate(total=Sum('so_gio_lam'))['total'] or 0

        # Personal history
        history = ChamCong.objects.filter(ma_nv=employee).order_by('-ngay_lam')[:10]

        context = {
            'is_manager': False,
            'employee': employee,
            'current_shift': current_shift_record,
            'shift_colleagues': shift_colleagues,
            'total_hours_month': total_hours_month,
            'history': history,
            'today': today,
        }

    return render(request, 'attendances/attendance_list.html', context)


def get_ca_code(ca_str):
    mapping = {
        '06:00 - 12:00': 'SANG',
        '12:00 - 17:00': 'CHIEU',
        '17:00 - 22:00': 'TOI'
    }
    return mapping.get(ca_str, 'SANG')


from django.utils.timezone import localtime


def check_in_out_view(request):
    if request.method == 'POST':
        user = request.user
        action = request.POST.get('action')
        ma_nv = request.POST.get('ma_nv')

        # Security: chỉ cho phép nhân viên tự check-in cho chính họ
        if not user.is_superuser and not user.is_staff:
            try:
                if user.taikhoan.ma_nv.ma_nv != ma_nv:
                    return redirect('attendances:attendance_list')
            except Exception:
                return redirect('attendances:attendance_list')

        employee = NhanVien.objects.get(ma_nv=ma_nv)

        # --- SỬA LOGIC TẠI ĐÂY ---
        # Sử dụng localtime để lấy đúng giờ Việt Nam (GMT+7) thay vì UTC
        now = localtime(timezone.now())
        today = now.date()
        current_time = now.time()
        # -------------------------

        # Tìm lịch làm việc hôm nay
        current_shift_record = LichLamViec.objects.filter(ma_nv=employee, ngay_lam=today).first()
        if not current_shift_record:
            return redirect('attendances:attendance_list')

        ca_lam_str = current_shift_record.ca_lam
        ca_code = get_ca_code(ca_lam_str)

        if action == 'check_in':
            cc, created = ChamCong.objects.get_or_create(
                ma_nv=employee,
                ngay_lam=today,
                ca_lam=ca_code,
                defaults={'ma_cc': f"CC_{ma_nv}_{today.strftime('%Y%m%d')}_{ca_code}"}
            )
            if not cc.gio_vao:
                cc.gio_vao = current_time
                cc.trang_thai = 'Đang làm'

                try:
                    shift_start_str = ca_lam_str.split(' - ')[0]
                    shift_start_time = datetime.datetime.strptime(shift_start_str, '%H:%M').time()
                    start_dt = datetime.datetime.combine(today, shift_start_time)
                    current_dt = datetime.datetime.combine(today, current_time)

                    if current_dt > start_dt:
                        diff = current_dt - start_dt
                        total_minutes = int(diff.total_seconds() / 60)

                        # --- LOGIC QUY ĐỔI GIỜ PHÚT ---
                        hours = total_minutes // 60
                        minutes = total_minutes % 60

                        if hours > 0:
                            cc.ghi_chu = f"Đi muộn {hours}h {minutes}p"
                        else:
                            cc.ghi_chu = f"Đi muộn {minutes} phút"
                        # ------------------------------
                    else:
                        cc.ghi_chu = "Đúng giờ"
                except Exception:
                    cc.ghi_chu = "Đúng giờ"
                cc.save()

        elif action == 'check_out':
            # Tìm bản ghi chấm công đã có
            cc = ChamCong.objects.filter(
                ma_nv=employee,
                ngay_lam=today,
                ca_lam=ca_code
            ).first()
            
            if cc and cc.gio_vao and not cc.gio_ra:
                cc.gio_ra = current_time
                cc.trang_thai = 'Đã xong'
                
                # Tính giờ làm
                try:
                    # Chuyển đổi thời gian để tính toán
                    gio_vao_dt = datetime.datetime.combine(today, cc.gio_vao)
                    gio_ra_dt = datetime.datetime.combine(today, current_time)
                    
                    # Nếu giờ ra nhỏ hơn giờ vào (qua đêm), cộng 1 ngày
                    if gio_ra_dt < gio_vao_dt:
                        gio_ra_dt += datetime.timedelta(days=1)
                    
                    # Tính tổng phút làm việc
                    diff = gio_ra_dt - gio_vao_dt
                    total_minutes = int(diff.total_seconds() / 60)
                    
                    # Tính giờ làm (làm tròn đến 2 số thập phân)
                    work_hours = total_minutes / 60
                    cc.so_gio_lam = round(work_hours, 2)
                    
                    # Ghi chú
                    cc.ghi_chu += f" - Tổng giờ: {work_hours:.2f}h"
                    
                except Exception as e:
                    cc.so_gio_lam = 0
                    cc.ghi_chu += " - Lỗi tính giờ"
                
                cc.save()

    return redirect('attendances:attendance_list')