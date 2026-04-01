from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
import json # Import thư viện json

def _sample_requests():
    return [
        {
            'ma_dk': 'DK000001',
            'ma_nv': 'NV001',
            'ten_nv': 'Nguyễn Văn An',
            'loai_yc': 'Nghỉ phép',
            'ngay_dk': '26/12/2026',
            'trang_thai': 'Chờ duyệt',
            'trang_thai_key': 'pending',
            'chi_tiet_json': json.dumps([ # Sử dụng json.dumps
                ['Mã nhân viên', 'NV001'],
                ['Loại yêu cầu', 'Nghỉ phép'],
                ['Ngày bắt đầu', '26/12/2026'],
                ['Ngày kết thúc', '27/12/2026'],
                ['Lý do', 'Đi khám sức khỏe'],
                ['Ngày đăng ký', '25/12/2026'],
            ])
        },
        {
            'ma_dk': 'DK000002',
            'ma_nv': 'NV002',
            'ten_nv': 'Nguyễn Thanh Anh',
            'loai_yc': 'Nghỉ phép',
            'ngay_dk': '26/02/2025',
            'trang_thai': 'Chờ duyệt',
            'trang_thai_key': 'pending',
            'chi_tiet_json': json.dumps([ # Sử dụng json.dumps
                ['Mã nhân viên', 'NV002'],
                ['Loại yêu cầu', 'Nghỉ phép'],
                ['Ngày bắt đầu', '26/02/2025'],
                ['Ngày kết thúc', '27/12/2025'],
                ['Lý do', 'Giải quyết việc gia đình'],
                ['Ngày đăng ký', '25/02/2025'],
            ])
        },
        {
            'ma_dk': 'DK000003',
            'ma_nv': 'NV003',
            'ten_nv': 'Nguyễn Văn Anh',
            'loai_yc': 'Nghỉ phép',
            'ngay_dk': '26/03/2025',
            'trang_thai': 'Chờ duyệt',
            'trang_thai_key': 'pending',
            'chi_tiet_json': json.dumps([ # Sử dụng json.dumps
                ['Mã nhân viên', 'NV003'],
                ['Loại yêu cầu', 'Nghỉ phép'],
                ['Ngày bắt đầu', '26/03/2025'],
                ['Ngày kết thúc', '26/03/2025'],
                ['Lý do', 'Nghỉ cá nhân'],
                ['Ngày đăng ký', '25/03/2025'],
            ])
        },
        {
            'ma_dk': 'DK000006',
            'ma_nv': 'NV006',
            'ten_nv': 'Trần Minh Quân',
            'loai_yc': 'Ca làm',
            'ngay_dk': '02/06/2025',
            'trang_thai': 'Chờ duyệt',
            'trang_thai_key': 'pending',
            'chi_tiet_json': json.dumps([ # Sử dụng json.dumps
                ['Mã nhân viên', 'NV006'],
                ['Loại yêu cầu', 'Ca làm việc'],
                ['Ngày làm', '02/06/2025'],
                ['Giờ bắt đầu', '13:00'],
                ['Giờ kết thúc', '21:00'],
                ['Ngày đăng ký', '01/06/2025'],
            ])
        }
    ]

def request_approval_view(request):
    return render(request, 'requests/request_approval.html', {
        'requests_data': _sample_requests(),
        'types': ['Nghỉ phép', 'Ca làm'],
    })

def request_list_view(request):
    return redirect('request_approval')

def request_review_list_view(request):
    return redirect('request_approval')

def approve_request(request, ma_dk):
    return JsonResponse({'success': True})

def reject_request(request, ma_dk):
    return JsonResponse({'success': True})
