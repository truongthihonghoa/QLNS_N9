from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.utils import OperationalError, ProgrammingError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import LichLamViec
from apps.employees.models import NhanVien
from apps.branches.models import ChiNhanh
import datetime


class ScheduleForm(forms.Form):
    ngay_lam = forms.DateField(required=True)
    khung_gio = forms.CharField(max_length=50, required=True)

def _is_admin(user):
    return user.is_authenticated and user.is_staff

def _get_sample_employees():
    """Dữ liệu mẫu với vị trí quy định sẵn"""
    return [
        {'ma_nv': 'NV001', 'ho_ten': 'Nguyễn Văn A', 'vi_tri_mac_dinh': 'Pha chế'},
        {'ma_nv': 'NV002', 'ho_ten': 'Trần Thị B', 'vi_tri_mac_dinh': 'Phục vụ'},
        {'ma_nv': 'NV003', 'ho_ten': 'Lê Minh C', 'vi_tri_mac_dinh': 'Giữ xe'},
        {'ma_nv': 'NV004', 'ho_ten': 'Phạm Khánh D', 'vi_tri_mac_dinh': 'Quản lý'},
        {'ma_nv': 'NV005', 'ho_ten': 'Đỗ Hoàng E', 'vi_tri_mac_dinh': 'Thu ngân'},
    ]

def _get_week_boundaries():
    """Trả về ngày bắt đầu và kết thúc của tuần hiện tại (Thứ 2 - Chủ nhật)"""
    today = datetime.date.today()
    # Tìm ngày thứ 2 của tuần hiện tại
    start_of_week = today - datetime.timedelta(days=today.weekday())
    # Ngày chủ nhật của tuần hiện tại
    end_of_week = start_of_week + datetime.timedelta(days=6)
    return start_of_week, end_of_week

def _get_month_boundaries():
    """Trả về ngày đầu tháng và cuối tháng hiện tại"""
    today = datetime.date.today()
    # Ngày đầu tháng
    start_of_month = today.replace(day=1)
    # Ngày cuối tháng
    if today.month == 12:
        end_of_month = today.replace(year=today.year + 1, month=1, day=1) - datetime.timedelta(days=1)
    else:
        end_of_month = today.replace(month=today.month + 1, day=1) - datetime.timedelta(days=1)
    return start_of_month, end_of_month


def schedule_list_view(request):
    filter_type = request.GET.get('filter', 'week')  # Default to week
    
    if filter_type == 'month':
        start_date, end_date = _get_month_boundaries()
    else:  # default to week
        start_date, end_date = _get_week_boundaries()
    
    schedules = []
    try:
        schedule_objects = LichLamViec.objects.all().order_by('ngay_lam', 'ca_lam')
        for schedule in schedule_objects:
            schedules.append({
                'ma_llv': schedule.ma_llv,
                'ngay_lam': schedule.ngay_lam.strftime('%d/%m/%Y'),
                'khung_gio': schedule.ca_lam,
                'trang_thai': schedule.trang_thai,
                'ma_nv': schedule.ma_nv.ma_nv if schedule.ma_nv else '',
                'ten_nv': schedule.ma_nv.ho_ten if schedule.ma_nv else '',
            })
    except:
        pass

    context = {
        'schedules': schedules,
        'shift_options': ['Ca sáng: 06:00 - 12:00', 'Ca chiều: 12:00 - 17:00', 'Ca tối: 17:00 - 22:00'],
        'is_admin': _is_admin(request.user),
    }
    return render(request, 'schedules/schedule_list.html', context)

def schedule_create_view(request):
    if request.method == 'POST':
        ngay_lam_str = request.POST.get('ngay_lam')
        khung_gio = request.POST.get('khung_gio')
        selected_employees = request.POST.getlist('selected_employees')

        if not all([ngay_lam_str, khung_gio, selected_employees]):
            messages.error(request, 'Vui lòng điền đầy đủ thông tin và chọn ít nhất một nhân viên')
            return _render_create_form(request)

        try:
            ngay_lam = datetime.datetime.strptime(ngay_lam_str, '%Y-%m-%d').date()
            # Mặc định lấy chi nhánh đầu tiên nếu DB có, hoặc null
            branch = ChiNhanh.objects.first()

            with transaction.atomic():
                base_id = int(datetime.datetime.now().timestamp())
                for i, ma_nv in enumerate(selected_employees):
                    vi_tri = request.POST.get(f'position_{ma_nv}', '')
                    new_ma_llv = f'LLV{base_id}{i}'

                    emp = NhanVien.objects.filter(ma_nv=ma_nv).first()

                    if emp:
                        LichLamViec.objects.create(
                            ma_llv=new_ma_llv,
                            ma_nv=emp,
                            ma_chi_nhanh=branch,
                            ngay_lam=ngay_lam,
                            ca_lam=khung_gio,
                            trang_thai='Chưa Gửi',
                            ngay_tao=datetime.date.today(),
                            ghi_chu=f"Vị trí: {vi_tri}"
                        )

                messages.success(request, 'Lưu lịch làm việc thành công')
                return redirect('schedule_list')
                
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
    
    return _render_create_form(request)

def _render_create_form(request):
    db_employees = NhanVien.objects.all()
    employees = []

    if db_employees.exists():
        for emp in db_employees:
            employees.append({
                'ma_nv': emp.ma_nv,
                'ho_ten': emp.ho_ten,
                'vi_tri_mac_dinh': emp.chuc_vu or 'Nhân viên'
            })
    else:
        employees = _get_sample_employees()

    context = {
        'form': ScheduleForm(),
        'employee_options': employees,
        'shift_options': ['Ca sáng: 06:00 - 12:00', 'Ca chiều: 12:00 - 17:00', 'Ca tối: 17:00 - 22:00'],
        'is_admin': _is_admin(request.user),
    }
    
    return render(request, 'schedules/schedule_create.html', context)


def schedule_edit_view(request, schedule_id):
    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
    return render(request, 'schedules/schedule_edit.html', {'schedule': schedule})

def schedule_delete_view(request, schedule_id):
    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
    schedule.delete()
    return JsonResponse({'success': True})


@require_http_methods(["POST"])
def schedule_send_notification_view(request):
    return JsonResponse({'success': True})

def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
    return JsonResponse({'ma_llv': schedule.ma_llv})
