from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import YeuCau
import json

def request_approval_view(request):
    # Lay tat ca cac yeu cau tu database
    yeu_cau_list = YeuCau.objects.select_related('ma_nv').all().order_by('-ma_yc')
    
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
            'loai_yc': loai_hien_thi, # Dung gia tri da rut gon
            'ngay_dk': yc.ngay_bd.strftime('%d/%m/%Y') if yc.ngay_bd else '',
            'trang_thai': yc.trang_thai,
            'trang_thai_key': 'pending' if yc.trang_thai == 'Chờ duyệt' else 'approved' if yc.trang_thai == 'Đã duyệt' else 'rejected',
            'chi_tiet_json': json.dumps(details)
        })

    return render(request, 'requests/request_approval.html', {
        'requests_data': requests_data,
        'types': ['Nghỉ phép', 'Ca làm'], # Sua tai day
    })

def request_list_view(request):
    return redirect('request_approval')

def request_review_list_view(request):
    return redirect('request_approval')

def approve_request(request, ma_dk):
    try:
        yc = YeuCau.objects.get(ma_yc=ma_dk)
        yc.trang_thai = 'Đã duyệt'
        yc.save()
        return JsonResponse({'success': True})
    except YeuCau.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy yêu cầu'})

def reject_request(request, ma_dk):
    try:
        yc = YeuCau.objects.get(ma_yc=ma_dk)
        yc.trang_thai = 'Từ chối'
        yc.save()
        return JsonResponse({'success': True})
    except YeuCau.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy yêu cầu'})
