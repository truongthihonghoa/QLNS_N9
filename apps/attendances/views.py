from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Sum
from .models import ChamCong
from apps.branches.models import ChiNhanh
from apps.schedules.models import LichLamViec
from apps.employees.models import NhanVien
import datetime


def mark_absences_for_date_range(start_date, end_date):
    now = timezone.now()
    today = now.date()
    current_time = now.time()
    
    shifts_in_range = LichLamViec.objects.filter(ngay_lam__gte=start_date, ngay_lam__lte=end_date)
    for shift in shifts_in_range:
        try:
            shift_end_str = shift.ca_lam.split(' - ')[1]
            shift_end_time = datetime.datetime.strptime(shift_end_str, '%H:%M').time()
            
            if shift.ngay_lam > today:
                continue
            if shift.ngay_lam == today and current_time <= shift_end_time:
                continue
                
            ca_code = get_ca_code(shift.ca_lam)
            cc_exists = ChamCong.objects.filter(ma_nv=shift.ma_nv, ngay_lam=shift.ngay_lam, ca_lam=ca_code).exists()
            if not cc_exists:
                ChamCong.objects.create(
                    ma_cc=f"CC_{shift.ma_nv.ma_nv}_{shift.ngay_lam.strftime('%Y%m%d')}_{ca_code}",
                    ma_nv=shift.ma_nv,
                    ngay_lam=shift.ngay_lam,
                    ca_lam=ca_code,
                    trang_thai='Vắng',
                    so_gio_lam=0,
                    ghi_chu='Vắng mặt'
                )
        except Exception:
            pass


def attendance_list_view(request):
    user = request.user
    
    # Check for absences today
    today = timezone.now().date()
    mark_absences_for_date_range(today, today)
    
    if user.is_superuser or user.is_staff:
        # MANAGER VIEW
        branch_id = request.GET.get('branch', 'CN01')  # Default Hai Chau (CN01)
        search_query = request.GET.get('search', '')
        
        attendances = ChamCong.objects.all().order_by('-ngay_lam')

        if branch_id:
            attendances = attendances.filter(ma_nv__ma_chi_nhanh=branch_id)
            
        if search_query:
            attendances = attendances.filter(ma_nv__ho_ten__icontains=search_query)

        branches = ChiNhanh.objects.all()

        context = {
            'is_manager': True,
            'attendances': attendances,
            'branches': branches,
            'selected_branch': branch_id,
            'search_query': search_query,
        }
    else:
        # EMPLOYEE VIEW
        try:
            employee = user.taikhoan.ma_nv
        except Exception:
            return render(request, 'error.html', {'message': 'Tài khoản chưa được liên kết với nhân viên.'})

        now = timezone.now()
        today = now.date()
        
        # Find today's shifts
        all_shifts_today = LichLamViec.objects.filter(ma_nv=employee, ngay_lam=today)
        
        active_shifts_data = []
        current_time = now.time()
        
        for shift in all_shifts_today:
            try:
                shift_start_str = shift.ca_lam.split(' - ')[0]
                shift_start_time = datetime.datetime.strptime(shift_start_str, '%H:%M').time()
                
                start_dt = datetime.datetime.combine(today, shift_start_time)
                current_dt = datetime.datetime.combine(today, current_time)
                
                # Visible from 30 minutes before the shift starts
                visible_from = start_dt - datetime.timedelta(minutes=30)
                
                if current_dt >= visible_from:
                    # Get colleagues for THIS shift
                    shift_colleagues_records = LichLamViec.objects.filter(
                        ngay_lam=today,
                        ca_lam=shift.ca_lam,
                        ma_chi_nhanh=shift.ma_chi_nhanh
                    ).select_related('ma_nv')
                    
                    shift_colleagues = []
                    ca_code = get_ca_code(shift.ca_lam)
                    
                    for rec in shift_colleagues_records:
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
                    
                    active_shifts_data.append({
                        'shift_record': shift,
                        'colleagues': shift_colleagues
                    })
            except Exception:
                pass

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
            'active_shifts_data': active_shifts_data,
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


def check_in_out_view(request):
    if request.method == 'POST':
        user = request.user
        action = request.POST.get('action') # 'check_in' or 'check_out'
        ma_nv = request.POST.get('ma_nv')
        
        # Security: only allow users to check in for themselves
        if not user.is_superuser and not user.is_staff:
            try:
                if user.taikhoan.ma_nv.ma_nv != ma_nv:
                    return redirect('attendances:attendance_list')
            except Exception:
                return redirect('attendances:attendance_list')
        
        employee = NhanVien.objects.get(ma_nv=ma_nv)
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        ca_lam_str = request.POST.get('ca_lam')
        
        # Verify the shift exists for this employee today
        current_shift_record = LichLamViec.objects.filter(ma_nv=employee, ngay_lam=today, ca_lam=ca_lam_str).first()
        if not current_shift_record:
            return redirect('attendances:attendance_list')
            
        ca_code = get_ca_code(ca_lam_str)
        
        if action == 'check_in':
            # Create or update ChamCong record
            cc, created = ChamCong.objects.get_or_create(
                ma_nv=employee,
                ngay_lam=today,
                ca_lam=ca_code,
                defaults={'ma_cc': f"CC_{ma_nv}_{today.strftime('%Y%m%d')}_{ca_code}"}
            )
            if not cc.gio_vao:
                cc.gio_vao = current_time
                cc.trang_thai = 'Đang làm'
                
                # Check late/on-time
                try:
                    shift_start_str = ca_lam_str.split(' - ')[0]
                    shift_start_time = datetime.datetime.strptime(shift_start_str, '%H:%M').time()
                    
                    start_dt = datetime.datetime.combine(today, shift_start_time)
                    current_dt = datetime.datetime.combine(today, current_time)
                    
                    if current_dt > start_dt:
                        diff = current_dt - start_dt
                        minutes_late = int(diff.total_seconds() / 60)
                        cc.ghi_chu = f"Đi muộn {minutes_late} phút"
                    else:
                        cc.ghi_chu = "Đúng giờ"
                except Exception:
                    cc.ghi_chu = "Đúng giờ"
                    
                cc.save()
        
        elif action == 'check_out':
            cc = ChamCong.objects.filter(ma_nv=employee, ngay_lam=today, ca_lam=ca_code).first()
            if cc and cc.gio_vao and not cc.gio_ra:
                cc.gio_ra = current_time
                cc.trang_thai = 'Hoàn thành'
                
                # Calculate so_gio_lam
                start_cc = datetime.datetime.combine(today, cc.gio_vao)
                end_cc = datetime.datetime.combine(today, current_time)
                duration = end_cc - start_cc
                cc.so_gio_lam = round(duration.total_seconds() / 3600, 2)
                
                # Check early/overtime leave
                try:
                    shift_end_str = ca_lam_str.split(' - ')[1]
                    shift_end_time = datetime.datetime.strptime(shift_end_str, '%H:%M').time()
                    
                    end_shift_dt = datetime.datetime.combine(today, shift_end_time)
                    
                    if end_cc < end_shift_dt:
                        diff = end_shift_dt - end_cc
                        minutes_early = int(diff.total_seconds() / 60)
                        if cc.ghi_chu and cc.ghi_chu != "Đúng giờ":
                            cc.ghi_chu += f", Về sớm {minutes_early} phút"
                        else:
                            cc.ghi_chu = f"Về sớm {minutes_early} phút"
                    elif end_cc > end_shift_dt:
                        diff = end_cc - end_shift_dt
                        minutes_ot = int(diff.total_seconds() / 60)
                        if cc.ghi_chu and cc.ghi_chu != "Đúng giờ":
                            cc.ghi_chu += f", Tăng ca {minutes_ot} phút"
                        else:
                            cc.ghi_chu = f"Tăng ca {minutes_ot} phút"
                except Exception:
                    pass
                
                cc.save()
                
    return redirect('attendances:attendance_list')
