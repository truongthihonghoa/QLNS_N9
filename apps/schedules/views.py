from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from .models import LichLamViec
from apps.employees.models import NhanVien
from apps.branches.models import ChiNhanh
import datetime


def _is_admin(user):
    return user.is_authenticated and user.is_staff


def schedule_list_view(request):
    schedules = []
    try:
        # Lay tat ca lich lam viec tu database va sap xep theo ngay lam moi nhat
        schedule_objects = LichLamViec.objects.select_related('ma_nv').all().order_by('-ngay_lam', 'ca_lam')
        for schedule in schedule_objects:
            schedules.append({
                'ma_llv': schedule.ma_llv,
                'ngay_lam': schedule.ngay_lam.strftime('%d/%m/%Y'),
                'khung_gio': schedule.ca_lam,
                'trang_thai': schedule.trang_thai,
                'ma_nv': schedule.ma_nv.ma_nv if schedule.ma_nv else '',
                'ten_nv': schedule.ma_nv.ho_ten if schedule.ma_nv else '',
            })
    except Exception as e:
        print(f"Error fetching schedules: {e}")

    context = {
        'schedules': schedules,
        # Chinh lai khung gio chi con mốc thoi gian
        'shift_options': ['06:00 - 12:00', '12:00 - 17:00', '17:00 - 22:00'],
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
            
            with transaction.atomic():
                for ma_nv in selected_employees:
                    emp = NhanVien.objects.filter(ma_nv=ma_nv).first()
                    if not emp:
                        continue
                        
                    vi_tri = request.POST.get(f'position_{ma_nv}', emp.chuc_vu)
                    # Tao ma LLV theo format: LLV_MANV_YYYYMMDD
                    new_ma_llv = f"LLV_{ma_nv}_{ngay_lam.strftime('%Y%m%d')}"
                    
                    # Su dung update_or_create de tranh loi trung khoa chinh (Primary Key)
                    LichLamViec.objects.update_or_create(
                        ma_llv=new_ma_llv,
                        defaults={
                            'ma_nv': emp,
                            'ma_chi_nhanh': emp.ma_chi_nhanh,
                            'ngay_lam': ngay_lam,
                            'ca_lam': khung_gio, # Se luu dung mốc thoi gian ban chon
                            'trang_thai': 'Đã xếp lịch',
                            'ngay_tao': datetime.date.today(),
                            'ghi_chu': f"Vị trí: {vi_tri}"
                        }
                    )

                messages.success(request, 'Đã lưu lịch làm việc cho các nhân viên được chọn')
                return redirect('schedule_list')

        except Exception as e:
            messages.error(request, f'Không thể lưu lịch làm việc: {str(e)}')

    return _render_create_form(request)


def _render_create_form(request):
    db_employees = NhanVien.objects.all().order_by('ma_nv')
    employees = []

    for emp in db_employees:
        employees.append({
            'ma_nv': emp.ma_nv,
            'ho_ten': emp.ho_ten,
            'vi_tri_mac_dinh': emp.chuc_vu or 'Nhân viên'
        })

    context = {
        'employee_options': employees,
        # Chinh lai khung gio chi con mốc thoi gian
        'shift_options': ['06:00 - 12:00', '12:00 - 17:00', '17:00 - 22:00'],
        'is_admin': _is_admin(request.user),
    }

    return render(request, 'schedules/schedule_create.html', context)


def schedule_edit_view(request, schedule_id):
    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
    return render(request, 'schedules/schedule_edit.html', {'schedule': schedule})


def schedule_delete_view(request, schedule_id):
    try:
        schedule = LichLamViec.objects.get(ma_llv=schedule_id)
        schedule.delete()
        return JsonResponse({'success': True})
    except LichLamViec.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch'})


@require_http_methods(["POST"])
def schedule_send_notification_view(request):
    return JsonResponse({'success': True})


def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
    return JsonResponse({
        'ma_llv': schedule.ma_llv,
        'ma_nv': schedule.ma_nv.ma_nv if schedule.ma_nv else '',
        'ten_nv': schedule.ma_nv.ho_ten if schedule.ma_nv else '',
        'ngay_lam': schedule.ngay_lam.strftime('%d/%m/%Y'),
        'ca_lam': schedule.ca_lam,
        'trang_thai': schedule.trang_thai
    })
