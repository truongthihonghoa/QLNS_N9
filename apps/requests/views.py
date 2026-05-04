import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime, now
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

from .models import YeuCau
from ..branches.models import ChiNhanh
from ..accounts.models import TaiKhoan
from ..employees.models import NhanVien

def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required(login_url='/accounts/login/')
def request_approval_view(request):
    is_admin = _is_admin(request.user)
    role = request.session.get('role', 'Nhân viên')
    
    query = YeuCau.objects.select_related('ma_nv__ma_chi_nhanh').all()

    # PHÂN QUYỀN
    if role == "Nhân viên":
        # Nhân viên chỉ thấy đơn của mình
        try:
            nhan_vien_me = TaiKhoan.objects.get(user=request.user).ma_nv
            query = query.filter(ma_nv=nhan_vien_me)
        except TaiKhoan.DoesNotExist:
            query = query.none()
    elif role == "Quản lý" and not request.user.is_superuser:
        # Quản lý chỉ thấy đơn của nhân viên thuộc chi nhánh mình
        try:
            user_branch_id = request.user.taikhoan.ma_nv.ma_chi_nhanh_id
            query = query.filter(ma_nv__ma_chi_nhanh_id=user_branch_id)
        except Exception:
            query = query.none()

    yeu_cau_list = query.order_by('-ma_yc')
    requests_data = []

    for yc in yeu_cau_list:
        loai_hien_thi = 'Ca làm' if yc.loai_yeu_cau == 'Đăng ký ca làm' else yc.loai_yeu_cau
        
        details = [
            ['Mã nhân viên', yc.ma_nv.ma_nv],
            ['Tên nhân viên', yc.ma_nv.ho_ten],
            ['Loại đề nghị', loai_hien_thi],
            ['Ngày bắt đầu', yc.ngay_bd.strftime('%d/%m/%Y') if yc.ngay_bd else ''],
            ['Ngày kết thúc', yc.ngay_kt.strftime('%d/%m/%Y') if yc.ngay_kt else ''],
            ['Lý do', yc.ly_do],
            ['Trạng thái', yc.trang_thai],
        ]

        requests_data.append({
            'ma_dk': yc.ma_yc,
            'ma_nv': yc.ma_nv.ma_nv,
            'ten_nv': yc.ma_nv.ho_ten,
            'ma_chi_nhanh': yc.ma_nv.ma_chi_nhanh.ma_chi_nhanh if yc.ma_nv.ma_chi_nhanh else '',
            'loai_yc': loai_hien_thi,
            'ngay_dk': yc.ngay_bd.strftime('%d/%m/%Y') if yc.ngay_bd else '',
            'trang_thai': yc.trang_thai,
            'trang_thai_key': 'approved' if yc.trang_thai == 'Đã duyệt' else 'rejected' if yc.trang_thai == 'Từ chối' else 'pending',
            'chi_tiet_json': json.dumps(details)
        })

    branches = ChiNhanh.objects.filter(trang_thai='active').order_by('ma_chi_nhanh')
    if role == "Quản lý" and not request.user.is_superuser:
        try:
            u_branch_id = request.user.taikhoan.ma_nv.ma_chi_nhanh_id
            branches = branches.filter(ma_chi_nhanh=u_branch_id)
        except Exception:
            branches = branches.none()

    return render(request, 'requests/request_approval.html', {
        'requests_data': requests_data,
        'types': ['Nghỉ phép', 'Ca làm'],
        'is_admin': is_admin or role != "Nhân viên",
        'branches': branches,
    })

@login_required(login_url='/accounts/login/')
def request_list_view(request):
    return redirect('request_approval')

@login_required(login_url='/accounts/login/')
def request_review_list_view(request):
    return redirect('request_approval')

@login_required(login_url='/accounts/login/')
@require_POST
def approve_request(request, ma_dk):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền duyệt đề nghị.'}, status=403)

    try:
        yc = YeuCau.objects.get(ma_yc=ma_dk)
        if yc.trang_thai != 'Chờ duyệt':
            return JsonResponse({'success': False, 'error': 'Yêu cầu này đã được xử lý.'})

        yc.trang_thai = 'Đã duyệt'
        yc.save()
        return JsonResponse({'success': True, 'message': 'Duyệt thành công'})
    except YeuCau.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy yêu cầu.'}, status=404)

@login_required(login_url='/accounts/login/')
@require_POST
def reject_request(request, ma_dk):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền từ chối đề nghị.'}, status=403)

    try:
        yc = YeuCau.objects.get(ma_yc=ma_dk)
        if yc.trang_thai != 'Chờ duyệt':
            return JsonResponse({'success': False, 'error': 'Yêu cầu này đã được xử lý.'})

        yc.trang_thai = 'Từ chối'
        yc.save()
        return JsonResponse({'success': True, 'message': 'Từ chối thành công'})
    except YeuCau.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy yêu cầu.'}, status=404)

@login_required(login_url='/accounts/login/')
@require_POST
def api_submit_request(request):
    try:
        data = json.loads(request.body)
        loai_chi_tiet = data.get('loai_yeu_cau')
        ngay_bd = data.get('ngay_bd')
        ngay_kt = data.get('ngay_kt')
        ly_do = data.get('ly_do')

        if not all([loai_chi_tiet, ngay_bd, ly_do]):
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập đầy đủ thông tin.'}, status=400)

        try:
            nhan_vien = TaiKhoan.objects.get(user=request.user).ma_nv
        except TaiKhoan.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tài khoản không gắn với nhân viên nào.'}, status=400)

        prefix = "YC"
        if 'nghỉ' in loai_chi_tiet.lower(): prefix = "NP"
        elif 'đăng ký' in loai_chi_tiet.lower() or 'làm' in loai_chi_tiet.lower(): prefix = "DK"

        ngay_gui_str = localtime(now()).strftime('%Y%m%d')
        ma_yc = f"{prefix}_{nhan_vien.ma_nv}_{ngay_gui_str}"

        if YeuCau.objects.filter(ma_yc=ma_yc).exists():
            ma_yc = f"{ma_yc}_{str(uuid.uuid4().int)[:3]}"

        YeuCau.objects.create(
            ma_yc=ma_yc, loai_yeu_cau=loai_chi_tiet,
            ngay_bd=ngay_bd, ngay_kt=ngay_kt or ngay_bd,
            ly_do=ly_do, trang_thai='Chờ duyệt', ma_nv=nhan_vien
        )
        return JsonResponse({'success': True, 'message': 'Đã gửi đề nghị thành công'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required(login_url='/accounts/login/')
@require_POST
def api_update_request(request, ma_dk):
    try:
        data = json.loads(request.body)
        yc = get_object_or_404(YeuCau, ma_yc=ma_dk)

        # SECURITY CHECK: Chỉ chủ nhân hoặc Admin mới được sửa
        is_admin = _is_admin(request.user)
        nhan_vien_me = None
        try:
            nhan_vien_me = request.user.taikhoan.ma_nv
        except Exception:
            pass

        if not is_admin and (not nhan_vien_me or yc.ma_nv != nhan_vien_me):
            return JsonResponse({'success': False, 'error': 'Bạn không có quyền sửa đơn này.'}, status=403)

        if yc.trang_thai != 'Chờ duyệt':
            return JsonResponse({'success': False, 'error': 'Không thể sửa yêu cầu đã được xử lý.'}, status=400)

        yc.loai_yeu_cau = data.get('loai_yeu_cau', yc.loai_yeu_cau)
        yc.ngay_bd = data.get('ngay_bd', yc.ngay_bd)
        yc.ngay_kt = data.get('ngay_kt', yc.ngay_kt)
        yc.ly_do = data.get('ly_do', yc.ly_do)
        yc.save()
        return JsonResponse({'success': True, 'message': 'Cập nhật đề nghị thành công'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required(login_url='/accounts/login/')
@require_POST
def api_delete_request(request, ma_dk):
    try:
        yc = get_object_or_404(YeuCau, ma_yc=ma_dk)

        # SECURITY CHECK: Chỉ chủ nhân hoặc Admin mới được xóa
        is_admin = _is_admin(request.user)
        nhan_vien_me = None
        try:
            nhan_vien_me = request.user.taikhoan.ma_nv
        except Exception:
            pass

        if not is_admin and (not nhan_vien_me or yc.ma_nv != nhan_vien_me):
            return JsonResponse({'success': False, 'error': 'Bạn không có quyền xóa đơn này.'}, status=403)

        if yc.trang_thai != 'Chờ duyệt':
            return JsonResponse({'success': False, 'error': 'Chỉ có thể xóa yêu cầu đang chờ duyệt.'}, status=400)

        yc.delete()
        return JsonResponse({'success': True, 'message': 'Đã xóa yêu cầu thành công'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)