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
        
        # Phân quyền: Nếu không phải admin thì chỉ lấy ca làm việc của bản thân
        if not _is_admin(request.user):
            if hasattr(request.user, 'taikhoan') and request.user.taikhoan.ma_nv:
                query = query.filter(ma_nv=request.user.taikhoan.ma_nv).exclude(trang_thai='Chờ gửi')
            else:
                query = query.none()
        
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
                'chuc_vu': schedule.ma_nv.chuc_vu if schedule.ma_nv else 'Nhân viên',
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

    db_employees = NhanVien.objects.select_related('ma_chi_nhanh').all().order_by('ma_nv')
    employees = [
        {
            'ma_nv': e.ma_nv, 
            'ho_ten': e.ho_ten, 
            'vi_tri_mac_dinh': e.chuc_vu or 'Nhân viên',
            'ten_chi_nhanh': e.ma_chi_nhanh.ten_chi_nhanh if e.ma_chi_nhanh else 'N/A'
        } for e in db_employees
    ]
    return render(request, 'schedules/schedule_create.html', {
        'employee_options': employees,
        'shift_options': ['06:00 - 12:00', '12:00 - 17:00', '17:00 - 22:00'],
    })

def schedule_edit_view(request, schedule_id):
    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
    
    # Tìm tất cả nhân viên trong cùng ca làm này (cùng ngày, cùng khung giờ, cùng chi nhánh)
    related_schedules = LichLamViec.objects.filter(
        ngay_lam=schedule.ngay_lam,
        ca_lam=schedule.ca_lam,
        ma_chi_nhanh=schedule.ma_chi_nhanh
    )
    
    current_employee_ids = list(related_schedules.values_list('ma_nv_id', flat=True))
    
    if request.method == 'POST':
        khung_gio = request.POST.get('khung_gio')
        selected_employees = request.POST.getlist('selected_employees')
        ghi_chu = request.POST.get('ghi_chu', '')

        if not khung_gio or not selected_employees:
            messages.error(request, 'Vui lòng chọn ít nhất một nhân viên và khung giờ')
        else:
            try:
                with transaction.atomic():
                    # 1. Xóa những nhân viên không còn trong danh sách chọn
                    related_schedules.exclude(ma_nv_id__in=selected_employees).delete()
                    
                    # 2. Cập nhật hoặc tạo mới cho những nhân viên được chọn
                    for ma_nv in selected_employees:
                        emp = NhanVien.objects.filter(ma_nv=ma_nv).first()
                        if not emp: continue
                        
                        new_ma_llv = f"LLV_{ma_nv}_{schedule.ngay_lam.strftime('%Y%m%d')}"
                        
                        LichLamViec.objects.update_or_create(
                            ma_llv=new_ma_llv,
                            defaults={
                                'ma_nv': emp,
                                'ma_chi_nhanh': schedule.ma_chi_nhanh,
                                'ngay_lam': schedule.ngay_lam,
                                'ca_lam': khung_gio,
                                'trang_thai': schedule.trang_thai, # Giữ nguyên trạng thái cũ
                                'ngay_tao': schedule.ngay_tao,
                                'ghi_chu': ghi_chu or schedule.ghi_chu
                            }
                        )
                messages.success(request, 'Cập nhật lịch làm thành công.')
                return redirect('schedule_list')
            except Exception as e:
                messages.error(request, f'Lỗi hệ thống: {str(e)}')
    
    # Lấy danh sách nhân viên trong chi nhánh để chọn lại
    db_employees = NhanVien.objects.filter(ma_chi_nhanh=schedule.ma_chi_nhanh).select_related('ma_chi_nhanh').order_by('ma_nv')
    employee_options = []
    for e in db_employees:
        employee_options.append({
            'ma_nv': e.ma_nv,
            'ho_ten': e.ho_ten,
            'chuc_vu': e.chuc_vu or 'Nhân viên',
            'ten_chi_nhanh': e.ma_chi_nhanh.ten_chi_nhanh if e.ma_chi_nhanh else 'N/A',
            'is_selected': e.ma_nv in current_employee_ids
        })

    return render(request, 'schedules/schedule_edit.html', {
        'schedule': schedule,
        'employee_options': employee_options,
        'shift_options': ['06:00 - 12:00', '12:00 - 17:00', '17:00 - 22:00'],
    })

def schedule_delete_view(request, schedule_id):
    try:
        schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
        connection.close() 
        with transaction.atomic():
            # Xóa toàn bộ các bản ghi thuộc cùng một ca làm (cùng ngày, khung giờ, chi nhánh)
            LichLamViec.objects.filter(
                ngay_lam=schedule.ngay_lam,
                ca_lam=schedule.ca_lam,
                ma_chi_nhanh=schedule.ma_chi_nhanh
            ).delete()
        return JsonResponse({'success': True, 'message': 'Xóa ca làm việc thành công'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Database đang bận hoặc có lỗi mã: ' + str(e)})

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
