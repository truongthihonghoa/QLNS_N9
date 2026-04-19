from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction, connection
from django.views.decorators.http import require_http_methods
from .models import LichLamViec
from apps.employees.models import NhanVien
from apps.branches.models import ChiNhanh
import datetime
import json
import traceback

def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def schedule_list_view(request):
    # Đồng bộ hóa dữ liệu cũ
    LichLamViec.objects.filter(trang_thai='Chờ duyệt').update(trang_thai='Chờ gửi')
    
    # Lấy tham so loc tu URL
    branch_id = request.GET.get('branch', 'all')
    status_filter = request.GET.get('status', 'all')
    
    schedules = []
    try:
        query = LichLamViec.objects.select_related('ma_nv', 'ma_chi_nhanh').all()
        
        # Loc theo chi nhanh
        if branch_id != 'all':
            query = query.filter(ma_chi_nhanh_id=branch_id)
            
        # Loc theo trang thai
        if status_filter != 'all':
            query = query.filter(trang_thai=status_filter)
            
        schedule_objects = query.order_by('-ngay_lam', 'ca_lam')
        
        for schedule in schedule_objects:
            schedules.append({
                'ma_llv': schedule.ma_llv,
                'ngay_lam': schedule.ngay_lam.strftime('%d/%m/%Y'),
                'khung_gio': schedule.ca_lam,
                'trang_thai': schedule.trang_thai,
                'ma_nv': schedule.ma_nv.ma_nv if schedule.ma_nv else 'N/A',
                'ten_nv': schedule.ma_nv.ho_ten if schedule.ma_nv else 'N/A',
                'ten_chi_nhanh': schedule.ma_chi_nhanh.ten_chi_nhanh if schedule.ma_chi_nhanh else 'N/A',
            })
    except Exception as e:
        print(f"Error fetching schedules: {e}")

    # Lay danh sach chi nhanh de hien thi dropdown
    branches = ChiNhanh.objects.all().order_by('ten_chi_nhanh')

    return render(request, 'schedules/schedule_list.html', {
        'schedules': schedules,
        'branches': branches,
        'selected_branch': branch_id,
        'selected_status': status_filter,
        'is_admin': _is_admin(request.user),
    })

def schedule_create_view(request):
    if request.method == 'POST':
        ngay_lam_str = request.POST.get('ngay_lam')
        khung_gio = request.POST.get('khung_gio')
        selected_employees = request.POST.getlist('selected_employees')

        if not ngay_lam_str or not khung_gio or not selected_employees:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin')
            return redirect('schedule_create')

        try:
            ngay_lam = datetime.datetime.strptime(ngay_lam_str, '%Y-%m-%d').date()
            with transaction.atomic():
                for ma_nv in selected_employees:
                    emp = NhanVien.objects.filter(ma_nv=ma_nv).first()
                    if not emp: continue
                    vi_tri = request.POST.get(f'position_{ma_nv}', emp.chuc_vu)
                    new_ma_llv = f"LLV_{ma_nv}_{ngay_lam.strftime('%Y%m%d')}"
                    
                    LichLamViec.objects.update_or_create(
                        ma_llv=new_ma_llv,
                        defaults={
                            'ma_nv': emp,
                            'ma_chi_nhanh': emp.ma_chi_nhanh,
                            'ngay_lam': ngay_lam,
                            'ca_lam': khung_gio,
                            'trang_thai': 'Chờ gửi', 
                            'ngay_tao': datetime.date.today(),
                            'ghi_chu': f"Vị trí: {vi_tri}"
                        }
                    )
                messages.success(request, 'Đã tạo lịch làm việc thành công.')
                return redirect('schedule_list')
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống: {str(e)}')

    db_employees = NhanVien.objects.all().order_by('ma_nv')
    employees = [{'ma_nv': e.ma_nv, 'ho_ten': e.ho_ten, 'vi_tri_mac_dinh': e.chuc_vu or 'Nhân viên'} for e in db_employees]
    return render(request, 'schedules/schedule_create.html', {
        'employee_options': employees,
        'shift_options': ['06:00 - 12:00', '12:00 - 17:00', '17:00 - 22:00'],
    })

def schedule_edit_view(request, schedule_id):
    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
    if request.method == 'POST':
        khung_gio = request.POST.get('khung_gio')
        if khung_gio:
            try:
                schedule.ca_lam = khung_gio
                schedule.save()
                messages.success(request, 'Chỉnh sửa lịch làm thành công.')
                return redirect('schedule_list')
            except Exception as e:
                messages.error(request, f'Không thể lưu: {str(e)}')
    
    return render(request, 'schedules/schedule_edit.html', {
        'schedule': schedule,
        'shift_options': ['06:00 - 12:00', '12:00 - 17:00', '17:00 - 22:00'],
    })

def schedule_delete_view(request, schedule_id):
    try:
        connection.close() 
        with transaction.atomic():
            LichLamViec.objects.filter(ma_llv=schedule_id).delete()
        return JsonResponse({'success': True, 'message': 'Xóa lịch làm việc thành công'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Database đang bận, vui lòng thử lại sau giây lát'})

@require_http_methods(["POST"])
def schedule_send_notification_view(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        LichLamViec.objects.filter(ma_llv__in=ids).update(trang_thai='Chờ xác nhận')
        return JsonResponse({'success': True, 'message': 'Gửi thông báo thành công'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'})

def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
    return JsonResponse({'ma_llv': schedule.ma_llv, 'trang_thai': schedule.trang_thai})
