from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import YeuCau
from apps.branches.models import ChiNhanh
import json
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def request_approval_view(request):
    # Lay tat ca cac yeu cau tu database
    query = YeuCau.objects.select_related('ma_nv__ma_chi_nhanh').all()

    # PHÂN QUYỀN: Nhân viên chỉ xem đơn của mình
    is_admin = _is_admin(request.user)
    if not is_admin:
        try:
            ma_nv_me = request.user.taikhoan.ma_nv
            query = query.filter(ma_nv=ma_nv_me)
        except:
            query = query.none()

    yeu_cau_list = query.order_by('-ma_yc')

    requests_data = []
    for yc in yeu_cau_list:
        # Chuan bi du lieu chi tiet de hien thi trong popup - Sua thanh Loai de nghi
        loai_hien_thi = yc.loai_yeu_cau
        if loai_hien_thi == 'Đăng ký ca làm':
            loai_hien_thi = 'Ca làm'

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
            'loai_yc': loai_hien_thi,  # Dung gia tri da rut gon
            'ngay_dk': yc.ngay_bd.strftime('%d/%m/%Y') if yc.ngay_bd else '',
            'trang_thai': yc.trang_thai,
            'trang_thai_key': 'pending' if yc.trang_thai == 'Chờ duyệt' else 'approved' if yc.trang_thai == 'Đã duyệt' else 'rejected',
            'chi_tiet_json': json.dumps(details)
        })

    # Lấy tất cả chi nhánh trong bảng chi nhánh
    branches = ChiNhanh.objects.all().order_by('ma_chi_nhanh')

    return render(request, 'requests/request_approval.html', {
        'requests_data': requests_data,
        'types': ['Nghỉ phép', 'Ca làm'],
        'is_admin': is_admin,
        'branches': branches,
    })


def request_list_view(request):
    return redirect('request_approval')


def request_review_list_view(request):
    return redirect('request_approval')


def approve_request(request, ma_dk):
    if not _is_admin(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Bạn không có quyền thực hiện thao tác này'
        }, status=403)

    try:
        yc = YeuCau.objects.get(ma_yc=ma_dk)

        # Tránh duyệt lại nhiều lần
        if yc.trang_thai != 'Chờ duyệt':
            return JsonResponse({
                'success': False,
                'error': 'Yêu cầu này đã được xử lý'
            })

        yc.trang_thai = 'Đã duyệt'
        yc.save()

        return JsonResponse({
            'success': True,
            'message': 'Duyệt thành công'
        })

    except YeuCau.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Không tìm thấy yêu cầu'
        }, status=404)

def reject_request(request, ma_dk):
    if not _is_admin(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Bạn không có quyền thực hiện thao tác này'
        }, status=403)

    try:
        yc = YeuCau.objects.get(ma_yc=ma_dk)

        if yc.trang_thai != 'Chờ duyệt':
            return JsonResponse({
                'success': False,
                'error': 'Yêu cầu này đã được xử lý'
            })

        yc.trang_thai = 'Từ chối'
        yc.save()

        return JsonResponse({
            'success': True,
            'message': 'Từ chối thành công'
        })

    except YeuCau.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Không tìm thấy yêu cầu'
        }, status=404)

import json
import uuid
from django.http import JsonResponse
from django.utils.timezone import localtime, now
from .models import YeuCau  # Đảm bảo bạn đã import đúng Model


def api_submit_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            loai_chi_tiet = data.get('loai_yeu_cau')  # Ví dụ: 'Nghỉ phép' hoặc 'Đăng ký ca'
            ngay_bd = data.get('ngay_bd')
            ngay_kt = data.get('ngay_kt')
            ly_do = data.get('ly_do')

            if not loai_chi_tiet or not ngay_bd or not ly_do:
                return JsonResponse({'success': False, 'error': 'Vui lòng nhập đầy đủ thông tin.'}, status=400)

            # 1. Lấy thông tin nhân viên từ request.user
            try:
                nhan_vien = request.user.taikhoan.ma_nv
            except AttributeError:
                return JsonResponse({'success': False, 'error': 'Tài khoản không gắn với nhân viên nào.'}, status=400)

            # 2. Xác định tiền tố mã (Prefix)
            # Giả sử loai_chi_tiet truyền lên là 'Nghỉ phép' hoặc 'Đăng ký làm'
            prefix = "YC"  # Mặc định
            if 'nghỉ' in loai_chi_tiet.lower():
                prefix = "NP"
            elif 'đăng ký' in loai_chi_tiet.lower() or 'làm' in loai_chi_tiet.lower():
                prefix = "DK"

            # 3. Tạo mã yêu cầu theo định dạng: PREFIX_MANV_YYYYMMDD
            thoi_gian_hien_tai = localtime(now())
            ngay_gui_str = thoi_gian_hien_tai.strftime('%Y%m%d')

            # Mã cơ bản: NP_NV00003_20260430
            ma_yc = f"{prefix}_{nhan_vien.ma_nv}_{ngay_gui_str}"

            # 4. Kiểm tra trùng mã (phòng trường hợp 1 ngày gửi 2 đơn cùng loại)
            if YeuCau.objects.filter(ma_yc=ma_yc).exists():
                # Nếu trùng thì thêm 3 số ngẫu nhiên từ UUID vào cuối
                ma_yc = f"{ma_yc}_{str(uuid.uuid4().int)[:3]}"

            # 5. Lưu vào Database
            YeuCau.objects.create(
                ma_yc=ma_yc,
                loai_yeu_cau=loai_chi_tiet,
                ngay_bd=ngay_bd,
                ngay_kt=ngay_kt or ngay_bd,
                ly_do=ly_do,
                trang_thai='Chờ duyệt',
                ma_nv=nhan_vien
            )

            return JsonResponse({
                'success': True,
                'message': f'Đã gửi đề nghị thành công'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


# Bổ sung vào views.py

def api_update_request(request, ma_dk):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yc = YeuCau.objects.get(ma_yc=ma_dk)

            # KIỂM TRA: Chỉ được sửa khi trạng thái là 'Chờ duyệt'
            if yc.trang_thai != 'Chờ duyệt':
                return JsonResponse({'success': False, 'error': 'Không thể sửa yêu cầu đã được xử lý.'}, status=400)

            # Cập nhật thông tin
            yc.loai_yeu_cau = data.get('loai_yeu_cau', yc.loai_yeu_cau)
            yc.ngay_bd = data.get('ngay_bd', yc.ngay_bd)
            yc.ngay_kt = data.get('ngay_kt', yc.ngay_kt)
            yc.ly_do = data.get('ly_do', yc.ly_do)

            # Cập nhật lại mã YC nếu loại yêu cầu thay đổi (tùy chọn)
            # Ở đây giữ nguyên mã cũ để tránh lỗi liên kết dữ liệu

            yc.save()
            return JsonResponse({'success': True, 'message': 'Cập nhật đề nghị thành công'})
        except YeuCau.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Không tìm thấy yêu cầu.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


def api_delete_request(request, ma_dk):
    if request.method == 'POST':  # Dùng POST để bảo mật hơn GET
        try:
            yc = YeuCau.objects.get(ma_yc=ma_dk)

            # KIỂM TRA: Chỉ được xóa khi trạng thái là 'Chờ duyệt'
            if yc.trang_thai != 'Chờ duyệt':
                return JsonResponse({'success': False, 'error': 'Chỉ có thể xóa yêu cầu đang chờ duyệt.'}, status=400)

            yc.delete()
            return JsonResponse({'success': True, 'message': 'Đã xóa yêu cầu thành công'})
        except YeuCau.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Không tìm thấy yêu cầu.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)