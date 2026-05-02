import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import localtime
from django.core.exceptions import ObjectDoesNotExist

from .models import ChamCong
from ..branches.models import ChiNhanh
from ..schedules.models import LichLamViec
from ..employees.models import NhanVien
from ..accounts.models import TaiKhoan

def get_ca_code(ca_str):
    mapping = {
        '06:00 - 12:00': 'SANG',
        '12:00 - 17:00': 'CHIEU',
        '17:00 - 22:00': 'TOI'
    }
    return mapping.get(ca_str, 'SANG')

@login_required(login_url='/accounts/login/')
def attendance_list_view(request):
    user = request.user
    role = request.session.get('role', 'Nhân viên')
    
    if user.is_superuser or user.is_staff or role != "Nhân viên":
        branch_id = request.GET.get('branch') or (ChiNhanh.objects.filter(trang_thai='active').first().ma_chi_nhanh if ChiNhanh.objects.filter(trang_thai='active').exists() else None)
        search_query = (request.GET.get('search') or '').strip()
        selected_month = request.GET.get('month', '')
        selected_year = request.GET.get('year', '')

        attendances = ChamCong.objects.all().select_related('ma_nv').order_by('-ngay_lam')

        if branch_id:
            attendances = attendances.filter(ma_nv__ma_chi_nhanh=branch_id)
        if search_query:
            attendances = attendances.filter(ma_nv__ho_ten__icontains=search_query)
        if selected_month and selected_month.isdigit():
            attendances = attendances.filter(ngay_lam__month=int(selected_month))
        if selected_year and selected_year.isdigit():
            attendances = attendances.filter(ngay_lam__year=int(selected_year))

        branches = ChiNhanh.objects.filter(trang_thai='active')

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
        try:
            employee = TaiKhoan.objects.get(user=user).ma_nv
        except (ObjectDoesNotExist, AttributeError):
            messages.error(request, 'Tài khoản chưa được liên kết với thông tin nhân viên.')
            return render(request, 'error.html', {'message': 'Tài khoản chưa được liên kết với nhân viên.'})

        now = timezone.now()
        today = now.date()
        current_shift_record = LichLamViec.objects.filter(ma_nv=employee, ngay_lam=today).first()
        shift_colleagues = []

        if current_shift_record:
            shift_colleagues_records = LichLamViec.objects.filter(
                ngay_lam=today,
                ca_lam=current_shift_record.ca_lam,
                ma_chi_nhanh=current_shift_record.ma_chi_nhanh
            ).select_related('ma_nv')

            for rec in shift_colleagues_records:
                ca_code = get_ca_code(rec.ca_lam)
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

        month_start = today.replace(day=1)
        total_hours_month = ChamCong.objects.filter(
            ma_nv=employee,
            ngay_lam__gte=month_start,
            ngay_lam__lte=today
        ).aggregate(total=Sum('so_gio_lam'))['total'] or 0

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

@login_required(login_url='/accounts/login/')
def check_in_out_view(request):
    if request.method == 'POST':
        user = request.user
        action = request.POST.get('action')
        ma_nv_id = request.POST.get('ma_nv')

        if not (user.is_superuser or user.is_staff):
            try:
                tk = TaiKhoan.objects.get(user=user)
                if tk.ma_nv.ma_nv != ma_nv_id:
                    messages.error(request, 'Bạn không có quyền chấm công cho người khác.')
                    return redirect('attendances:attendance_list')
            except TaiKhoan.DoesNotExist:
                return redirect('attendances:attendance_list')

        employee = get_object_or_404(NhanVien, pk=ma_nv_id)
        now = localtime(timezone.now())
        today = now.date()
        current_time = now.time()

        current_shift_record = LichLamViec.objects.filter(ma_nv=employee, ngay_lam=today).first()
        if not current_shift_record:
            messages.warning(request, 'Bạn không có lịch làm việc trong ngày hôm nay.')
            return redirect('attendances:attendance_list')

        ca_code = get_ca_code(current_shift_record.ca_lam)

        if action == 'check_in':
            cc, created = ChamCong.objects.get_or_create(
                ma_nv=employee,
                ngay_lam=today,
                ca_lam=ca_code,
                defaults={'ma_cc': f"CC_{ma_nv_id}_{today.strftime('%Y%m%d')}_{ca_code}"}
            )
            if not cc.gio_vao:
                cc.gio_vao = current_time
                cc.trang_thai = 'Đang làm'

                try:
                    shift_start_str = current_shift_record.ca_lam.split(' - ')[0]
                    shift_start_time = datetime.datetime.strptime(shift_start_str, '%H:%M').time()
                    start_dt = datetime.datetime.combine(today, shift_start_time)
                    current_dt = datetime.datetime.combine(today, current_time)

                    if current_dt > start_dt:
                        diff = current_dt - start_dt
                        total_minutes = int(diff.total_seconds() / 60)
                        hours = total_minutes // 60
                        minutes = total_minutes % 60
                        cc.ghi_chu = f"Đi muộn {hours}h {minutes}p" if hours > 0 else f"Đi muộn {minutes} phút"
                    else:
                        cc.ghi_chu = "Đúng giờ"
                except Exception:
                    cc.ghi_chu = "Đúng giờ"
                cc.save()
                messages.success(request, f'Nhân viên {employee.ho_ten} đã vào ca thành công.')
            else:
                messages.info(request, 'Bạn đã vào ca trước đó rồi.')

        elif action == 'check_out':
            cc = ChamCong.objects.filter(ma_nv=employee, ngay_lam=today, ca_lam=ca_code).first()
            
            if cc and cc.gio_vao and not cc.gio_ra:
                cc.gio_ra = current_time
                cc.trang_thai = 'Đã xong'
                
                try:
                    gio_vao_dt = datetime.datetime.combine(today, cc.gio_vao)
                    gio_ra_dt = datetime.datetime.combine(today, current_time)
                    if gio_ra_dt < gio_vao_dt:
                        gio_ra_dt += datetime.timedelta(days=1)
                    
                    diff = gio_ra_dt - gio_vao_dt
                    work_hours = round(diff.total_seconds() / 3600, 2)
                    cc.so_gio_lam = work_hours
                    cc.ghi_chu = f"{cc.ghi_chu or ''} - Tổng giờ: {work_hours}h".strip(' - ')
                except Exception:
                    cc.so_gio_lam = 0
                
                cc.save()
                messages.success(request, f'Nhân viên {employee.ho_ten} đã ra ca thành công. Tổng cộng {cc.so_gio_lam}h.')
            else:
                messages.warning(request, 'Không tìm thấy thông tin vào ca hoặc bạn đã ra ca rồi.')

    return redirect('attendances:attendance_list')