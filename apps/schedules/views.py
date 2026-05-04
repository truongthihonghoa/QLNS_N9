import datetime
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction, connection
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required

from .models import LichLamViec
from ..employees.models import NhanVien
from ..branches.models import ChiNhanh
from ..accounts.models import TaiKhoan

def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required(login_url='/accounts/login/')
def schedule_list_view(request):
    # Đồng bộ hóa trạng thái (giữ nguyên logic cũ)
    LichLamViec.objects.filter(trang_thai='Chờ duyệt').update(trang_thai='Chờ gửi')
    
    # Xác định chi nhánh của Quản lý
    user_branch_id = None
    if not request.user.is_superuser:
        try:
            user_branch_id = request.user.taikhoan.ma_nv.ma_chi_nhanh_id
        except Exception:
            pass

    branches = ChiNhanh.objects.filter(trang_thai='active').order_by('ten_chi_nhanh')
    if user_branch_id:
        branches = branches.filter(ma_chi_nhanh=user_branch_id)
        branch_id = user_branch_id
    else:
        branch_id = request.GET.get('branch', 'all')
    
    status_filter = request.GET.get('status', 'all')
    
    schedules_data = []
    query = LichLamViec.objects.select_related('ma_nv', 'ma_chi_nhanh').all()
    
    role = request.session.get('role', 'Nhân viên')
    is_admin_user = _is_admin(request.user) or role != "Nhân viên"

    # PHÂN QUYỀN
    if not is_admin_user:
        try:
            tk = TaiKhoan.objects.get(user=request.user)
            query = query.filter(ma_nv=tk.ma_nv).exclude(trang_thai='Chờ gửi')
        except TaiKhoan.DoesNotExist:
            query = query.none()
    elif user_branch_id:
        query = query.filter(ma_chi_nhanh_id=user_branch_id)
    
    if branch_id != 'all':
        query = query.filter(ma_chi_nhanh_id=branch_id)
        if user_branch_id and branch_id != user_branch_id:
            query = query.none()
    
    if status_filter != 'all':
        query = query.filter(trang_thai=status_filter)
        
    schedule_objects = query.order_by('-ngay_lam', 'ca_lam')
    
    for schedule in schedule_objects:
        schedules_data.append({
            'ma_llv': schedule.ma_llv,
            'ngay_lam': schedule.ngay_lam.strftime('%d/%m/%Y'),
            'khung_gio': schedule.ca_lam,
            'trang_thai': schedule.trang_thai,
            'ma_nv': schedule.ma_nv.ma_nv if schedule.ma_nv else 'N/A',
            'ten_nv': schedule.ma_nv.ho_ten if schedule.ma_nv else 'N/A',
            'chuc_vu': schedule.ma_nv.chuc_vu if schedule.ma_nv else 'Nhân viên',
            'ten_chi_nhanh': schedule.ma_chi_nhanh.ten_chi_nhanh if schedule.ma_chi_nhanh else 'N/A',
        })

    return render(request, 'schedules/schedule_list.html', {
        'schedules': schedules_data,
        'branches': branches,
        'selected_branch': branch_id,
        'selected_status': status_filter,
        'is_admin': is_admin_user,
    })

@login_required(login_url='/accounts/login/')
def schedule_create_view(request):
    # Chỉ Admin/Manager mới được tạo lịch
    role = request.session.get('role', 'Nhân viên')
    if not (_is_admin(request.user) or role != "Nhân viên"):
        messages.error(request, "Bạn không có quyền truy cập chức năng này.")
        return redirect('schedule_list')

    if request.method == 'POST':
        ngay_lam_str = request.POST.get('ngay_lam')
        khung_gio = request.POST.get('khung_gio')
        selected_employees = request.POST.getlist('selected_employees')

        if not all([ngay_lam_str, khung_gio, selected_employees]):
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin')
        else:
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

    db_employees = NhanVien.objects.all().select_related('ma_chi_nhanh').order_by('ma_nv')
    employees_data = [
        {
            'ma_nv': e.ma_nv, 
            'ho_ten': e.ho_ten, 
            'vi_tri_mac_dinh': e.chuc_vu or 'Nhân viên',
            'ten_chi_nhanh': e.ma_chi_nhanh.ten_chi_nhanh if e.ma_chi_nhanh else 'N/A'
        } for e in db_employees
    ]
    return render(request, 'schedules/schedule_create.html', {
        'employee_options': employees_data,
        'shift_options': ['06:00 - 12:00', '12:00 - 17:00', '17:00 - 22:00'],
    })

@login_required(login_url='/accounts/login/')
def schedule_edit_view(request, schedule_id):
    role = request.session.get('role', 'Nhân viên')
    if not (_is_admin(request.user) or role != "Nhân viên"):
        messages.error(request, "Bạn không có quyền sửa lịch làm việc.")
        return redirect('schedule_list')

    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
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

        if not all([khung_gio, selected_employees]):
            messages.error(request, 'Vui lòng chọn nhân viên và khung giờ')
        else:
            try:
                with transaction.atomic():
                    related_schedules.exclude(ma_nv_id__in=selected_employees).delete()
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
                                'trang_thai': schedule.trang_thai,
                                'ngay_tao': schedule.ngay_tao,
                                'ghi_chu': ghi_chu or schedule.ghi_chu
                            }
                        )
                messages.success(request, 'Cập nhật lịch làm thành công.')
                return redirect('schedule_list')
            except Exception as e:
                messages.error(request, f'Lỗi hệ thống: {str(e)}')
    
    db_employees = NhanVien.objects.filter(ma_chi_nhanh=schedule.ma_chi_nhanh).select_related('ma_chi_nhanh').order_by('ma_nv')
    employee_options = [
        {
            'ma_nv': e.ma_nv,
            'ho_ten': e.ho_ten,
            'chuc_vu': e.chuc_vu or 'Nhân viên',
            'ten_chi_nhanh': e.ma_chi_nhanh.ten_chi_nhanh if e.ma_chi_nhanh else 'N/A',
            'is_selected': e.ma_nv in current_employee_ids
        } for e in db_employees
    ]

    return render(request, 'schedules/schedule_edit.html', {
        'schedule': schedule,
        'employee_options': employee_options,
        'shift_options': ['06:00 - 12:00', '12:00 - 17:00', '17:00 - 22:00'],
    })

@login_required(login_url='/accounts/login/')
def schedule_delete_view(request, schedule_id):
    role = request.session.get('role', 'Nhân viên')
    if not (_is_admin(request.user) or role != "Nhân viên"):
        return JsonResponse({'success': False, 'error': 'Không có quyền thực hiện.'}, status=403)

    try:
        schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
        with transaction.atomic():
            LichLamViec.objects.filter(
                ngay_lam=schedule.ngay_lam,
                ca_lam=schedule.ca_lam,
                ma_chi_nhanh=schedule.ma_chi_nhanh
            ).delete()
        return JsonResponse({'success': True, 'message': 'Xóa ca làm việc thành công'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url='/accounts/login/')
@require_POST
def schedule_send_notification_view(request):
    role = request.session.get('role', 'Nhân viên')
    if not (_is_admin(request.user) or role != "Nhân viên"):
        return JsonResponse({'success': False, 'error': 'Không có quyền thực hiện.'}, status=403)

    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        LichLamViec.objects.filter(ma_llv__in=ids).update(trang_thai='Chờ xác nhận')
        return JsonResponse({'success': True, 'message': 'Gửi thông báo thành công'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url='/accounts/login/')
def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(LichLamViec, ma_llv=schedule_id)
    return JsonResponse({'ma_llv': schedule.ma_llv, 'trang_thai': schedule.trang_thai})
