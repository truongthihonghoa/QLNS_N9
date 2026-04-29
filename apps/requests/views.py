from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import YeuCau
import json

from django.core.exceptions import PermissionDenied


def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def request_approval_view(request):
    # Lay tat ca cac yeu cau tu database
    query = YeuCau.objects.select_related('ma_nv').all()

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
            'loai_yc': loai_hien_thi,  # Dung gia tri da rut gon
            'ngay_dk': yc.ngay_bd.strftime('%d/%m/%Y') if yc.ngay_bd else '',
            'trang_thai': yc.trang_thai,
            'trang_thai_key': 'pending' if yc.trang_thai == 'Chờ duyệt' else 'approved' if yc.trang_thai == 'Đã duyệt' else 'rejected',
            'chi_tiet_json': json.dumps(details)
        })

    return render(request, 'requests/request_approval.html', {
        'requests_data': requests_data,
        'types': ['Nghỉ phép', 'Ca làm'],
        'is_admin': is_admin,
    })


def request_list_view(request):
    return redirect('request_approval')


def request_review_list_view(request):
    return redirect('request_approval')


def approve_request(request, ma_dk):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền thực hiện thao tác này'}, status=403)

    try:
        yc = YeuCau.objects.get(ma_yc=ma_dk)
        yc.trang_thai = 'Đã duyệt'
        yc.save()
        return JsonResponse({'success': True})
    except YeuCau.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy yêu cầu'})


def reject_request(request, ma_dk):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền thực hiện thao tác này'}, status=403)

    try:
        yc = YeuCau.objects.get(ma_yc=ma_dk)
        yc.trang_thai = 'Từ chối'
        yc.save()
        return JsonResponse({'success': True})
    except YeuCau.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy yêu cầu'})


import uuid
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def api_submit_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            loai = data.get('loai_yeu_cau')
            ngay_bd = data.get('ngay_bd')
            ngay_kt = data.get('ngay_kt')
            ly_do = data.get('ly_do')

            if not loai or not ngay_bd or not ly_do:
                return JsonResponse({'success': False, 'error': 'Vui lòng nhập đầy đủ thông tin.'}, status=400)

            # Lay thong tin nhan vien tu request.user
            try:
                nhan_vien = request.user.taikhoan.ma_nv
            except:
                return JsonResponse({'success': False, 'error': 'Tài khoản không gắn với nhân viên nào.'}, status=400)

            # Tao ma yeu cau ngau nhien
            ma_yc = f"YC{str(uuid.uuid4().int)[:6]}"

            YeuCau.objects.create(
                ma_yc=ma_yc,
                loai_yeu_cau=loai,
                ngay_bd=ngay_bd,
                ngay_kt=ngay_kt or ngay_bd,
                ly_do=ly_do,
                trang_thai='Chờ duyệt',
                ma_nv=nhan_vien
            )
            return JsonResponse({'success': True, 'message': 'Đã gửi đề nghị thành công!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)