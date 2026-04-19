import datetime
from django.utils import timezone
from django import forms
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import HopDongLaoDong, HopDongLD_CT
from apps.employees.models import NhanVien
from apps.branches.models import ChiNhanh
from django.contrib.auth.models import User
from django.db import transaction

from django.core.exceptions import PermissionDenied

def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def _json_requested(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def get_next_ma_hd():
    last_hd = HopDongLaoDong.objects.all().order_by('ma_hd').last()
    if not last_hd:
        return 'HD00001'
    
    try:
        # Extract the number from 'HD00015'
        last_id_num = int(last_hd.ma_hd[2:])
        new_id_num = last_id_num + 1
        return f"HD{new_id_num:05d}"
    except (ValueError, IndexError):
        # Fallback if ma_hd doesn't follow the pattern
        return f"HD{datetime.datetime.now().strftime('%m%d%H%M%S')}"

def get_representative_info(nhan_vien):
    if nhan_vien and nhan_vien.chuc_vu == 'Quản lý':
        owner = User.objects.filter(is_superuser=True).first()
        if owner:
            fullname = f"{owner.last_name} {owner.first_name}".strip()
            if not fullname or fullname == "":
                fullname = "Trương Thị Hồng Hoa"
            return {'ten': fullname, 'chuc_vu': "Chủ", 'sdt': "0901234567"}
    
    if nhan_vien and nhan_vien.ma_chi_nhanh:
        manager = NhanVien.objects.filter(ma_chi_nhanh=nhan_vien.ma_chi_nhanh, chuc_vu='Quản lý').first()
        if manager:
            return {'ten': manager.ho_ten, 'chuc_vu': "Quản lý Chi nhánh", 'sdt': manager.sdt}
            
    return {'ten': "Trương Thị Hồng Hoa", 'chuc_vu': "Chủ", 'sdt': "0901234567"}

def contract_list_view(request):
    branch_filter = request.GET.get('branch', '').strip()
    contracts_qs = HopDongLaoDong.objects.select_related('ma_nv', 'ma_chi_nhanh', 'chi_tiet').all().order_by('ma_hd')
    
    if branch_filter and branch_filter != '':
        contracts_qs = contracts_qs.filter(ma_chi_nhanh_id=branch_filter)
        
    contracts_list = []
    today = datetime.date.today()

    for hd in contracts_qs:
        ct = getattr(hd, 'chi_tiet', None)
        nv = hd.ma_nv
        rep = get_representative_info(nv)
        
        # Sử dụng logic tính toán tập trung từ Model
        status = hd.trang_thai_thuc_te
        trang_thai_code = status['code']
        trang_thai_display = status['display']

        # Lấy địa chỉ thật của chi nhánh
        dia_chi_chi_nhanh = nv.ma_chi_nhanh.dia_chi if nv and nv.ma_chi_nhanh else ''

        contracts_list.append({
            'ma_hd': hd.ma_hd, 'ma_nv': nv.ma_nv if nv else '', 'ten_nv': nv.ho_ten if nv else '',
            'loai_hd': hd.get_loai_hd_display(), 'ngay_bd': hd.ngay_bat_dau.strftime('%d/%m/%Y'),
            'ngay_kt': hd.ngay_ket_thuc.strftime('%d/%m/%Y') if hd.ngay_ket_thuc else '',
            'chuc_vu': nv.chuc_vu if nv else hd.get_chuc_vu_display(), 'muc_luong': ct.luong_co_ban if ct else 0,
            'cccd': nv.cccd if nv else '', 'ngay_sinh': nv.ngay_sinh.strftime('%d/%m/%Y') if nv and nv.ngay_sinh else '',
            'sdt_nv': nv.sdt if nv else '', 'dia_chi': nv.dia_chi if nv else '',
            'nguoi_dai_dien': rep['ten'], 'chuc_vu_dai_dien': rep['chuc_vu'], 'sdt_dai_dien': rep['sdt'],
            'dia_diem_lv': dia_chi_chi_nhanh,
            'so_gio_lam': ct.so_gio_lam if ct else 0, 'luong_theo_gio': ct.luong_theo_gio if ct else 0,
            'ghi_chu': (ct.ghi_chu if ct else '') or 'Không có ghi chú.',
            'trang_thai_code': trang_thai_code, 'trang_thai_display': trang_thai_display,
        })

    return render(request, 'contracts/contract_list.html', {
        'contracts': contracts_list,
        'branches': ChiNhanh.objects.all(),
        'current_branch': branch_filter,
        'employees': NhanVien.objects.all(),
        'contract_types': HopDongLaoDong.LOAI_HD_CHOICES,
        'positions': [choice[0] for choice in NhanVien.CHUC_VU_CHOICES],
    })

@require_http_methods(["GET"])
def contract_detail_view(request, contract_id):
    if not _is_admin(request.user):
        raise PermissionDenied()
        
    hd = get_object_or_404(HopDongLaoDong, ma_hd=contract_id)
    ct = getattr(hd, 'chi_tiet', None)
    nv = hd.ma_nv
    rep = get_representative_info(nv)
    
    # Lấy địa chỉ thật của chi nhánh
    dia_chi_chi_nhanh = nv.ma_chi_nhanh.dia_chi if nv and nv.ma_chi_nhanh else ''
    
    return JsonResponse({
        'ma_hd': hd.ma_hd, 'ma_nv': nv.ma_nv, 'ten_nv': nv.ho_ten,
        'loai_hd': hd.get_loai_hd_display(), 'ngay_bd': hd.ngay_bat_dau.strftime('%d/%m/%Y'),
        'ngay_kt': hd.ngay_ket_thuc.strftime('%d/%m/%Y') if hd.ngay_ket_thuc else '',
        'chuc_vu': nv.chuc_vu, 'cccd': nv.cccd, 'ngay_sinh': nv.ngay_sinh.strftime('%d/%m/%Y') if nv.ngay_sinh else '',
        'dia_chi': nv.dia_chi, 'sdt_nv': nv.sdt, 'nguoi_dai_dien': rep['ten'], 'sdt_dai_dien': rep['sdt'],
        'dia_diem_lv': dia_chi_chi_nhanh, # ĐỊA CHỈ CHI NHÁNH
        'luong_co_ban': ct.luong_co_ban if ct else 0, 'luong_theo_gio': ct.luong_theo_gio if ct else 0,
        'so_gio_lam': ct.so_gio_lam if ct else 0, 'ghi_chu': (ct.ghi_chu if ct else '') or 'Không có ghi chú.',
    })

def contract_add_view(request):
    if not _is_admin(request.user):
        raise PermissionDenied()
        
    if request.method == 'POST':
        try:
            with transaction.atomic():
                ma_nv = request.POST.get('ma_nv')
                nhan_vien = get_object_or_404(NhanVien, ma_nv=ma_nv)
                
                new_ma_hd = get_next_ma_hd()
                
                # Extract and clean monetary values
                def clean_money(val):
                    if not val: return 0
                    return float(str(val).replace('.', '').replace(',', ''))

                ngay_bd = request.POST.get('ngay_bd')
                ngay_kt = request.POST.get('ngay_kt') or None

                # Ràng buộc ngày tháng
                if ngay_kt and ngay_kt < ngay_bd:
                    return JsonResponse({'success': False, 'message': 'Ngày kết thúc không thể trước ngày bắt đầu'}, status=400)

                hd = HopDongLaoDong.objects.create(
                    ma_hd=new_ma_hd,
                    ma_nv=nhan_vien,
                    ma_chi_nhanh_id=request.POST.get('dia_diem_lam_viec'),
                    loai_hd=request.POST.get('loai_hd'),
                    chuc_vu=request.POST.get('chuc_vu'),
                    ngay_bat_dau=ngay_bd,
                    ngay_ket_thuc=ngay_kt,
                    trang_thai='CON_HAN'
                )

                HopDongLD_CT.objects.create(
                    ma_hd=hd,
                    luong_co_ban=clean_money(request.POST.get('luong_co_ban')),
                    luong_theo_gio=clean_money(request.POST.get('luong_theo_gio')),
                    so_gio_lam=float(request.POST.get('so_gio_lam_toi_thieu') or 0),
                    che_do_thuong=clean_money(request.POST.get('thuong')),
                    ghi_chu=request.POST.get('ghi_chu')
                )

                return JsonResponse({'success': True, 'message': f'Thêm hợp đồng {new_ma_hd} thành công'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}, status=500)

    return render(request, 'contracts/contract_add.html', {
        'next_ma_hd': get_next_ma_hd(),
        'employees': NhanVien.objects.all().order_by('-ma_nv'),
        'branches': ChiNhanh.objects.all(),
        'contract_types': HopDongLaoDong.LOAI_HD_CHOICES,
        'positions': [choice[0] for choice in NhanVien.CHUC_VU_CHOICES],
    })

def contract_edit_view(request, contract_id):
    if not _is_admin(request.user):
        raise PermissionDenied()
        
    hd = get_object_or_404(HopDongLaoDong, ma_hd=contract_id)
    ct = getattr(hd, 'chi_tiet', None)
    
    # Định dạng ngày để hiện lên input type="date"
    ngay_bd_iso = hd.ngay_bat_dau.strftime('%Y-%m-%d') if hd.ngay_bat_dau else ''
    ngay_kt_iso = hd.ngay_ket_thuc.strftime('%Y-%m-%d') if hd.ngay_ket_thuc else ''

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Extract and clean monetary values
                def clean_money(val):
                    if not val: return 0
                    return float(str(val).replace('.', '').replace(',', ''))

                ngay_bd = request.POST.get('ngay_bd')
                ngay_kt = request.POST.get('ngay_kt') or None

                # Ràng buộc ngày tháng
                if ngay_kt and ngay_kt < ngay_bd:
                    return JsonResponse({'success': False, 'message': 'Ngày kết thúc không thể trước ngày bắt đầu'}, status=400)

                # Update main contract
                hd.loai_hd = request.POST.get('loai_hd')
                hd.chuc_vu = request.POST.get('chuc_vu')
                hd.ma_chi_nhanh_id = request.POST.get('dia_diem_lam_viec')
                hd.ngay_bat_dau = ngay_bd
                hd.ngay_ket_thuc = ngay_kt
                hd.save()

                # Update or create detail
                detail, created = HopDongLD_CT.objects.get_or_create(ma_hd=hd)
                detail.luong_co_ban = clean_money(request.POST.get('luong_co_ban'))
                detail.luong_theo_gio = clean_money(request.POST.get('luong_theo_gio'))
                detail.so_gio_lam = float(request.POST.get('so_gio_lam_toi_thieu') or 0)
                detail.che_do_thuong = clean_money(request.POST.get('thuong'))
                detail.ghi_chu = request.POST.get('ghi_chu')
                detail.save()

                return JsonResponse({'success': True, 'message': f'Cập nhật hợp đồng {hd.ma_hd} thành công'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}, status=500)

    context = {
        'contract': hd,
        'ct': ct,
        'ngay_bd_iso': ngay_bd_iso,
        'ngay_kt_iso': ngay_kt_iso,
        'branches': ChiNhanh.objects.all(),
        'positions': [choice[0] for choice in NhanVien.CHUC_VU_CHOICES],
        # Trích xuất giá trị để template dùng dễ hơn
        'luong_co_ban': int(ct.luong_co_ban) if ct else 0,
        'luong_theo_gio': int(ct.luong_theo_gio) if ct else 0,
        'so_gio_lam': ct.so_gio_lam if ct else 0,
        'thuong': int(ct.che_do_thuong) if ct else 0,
        'ghi_chu': ct.ghi_chu if ct else '',
        'muc_luong': int(ct.luong_co_ban) if ct and hd.loai_hd == 'FULLTIME' else (int(ct.luong_theo_gio * ct.so_gio_lam) if ct else 0)
    }
    return render(request, 'contracts/contract_edit.html', context)

@require_http_methods(["DELETE"])
def contract_delete_view(request, contract_id):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Bạn không có quyền thao tác.'}, status=403)
        
    hd = get_object_or_404(HopDongLaoDong, ma_hd=contract_id)
    
    # Kiểm tra trạng thái thực tế từ Model
    status = hd.trang_thai_thuc_te
    if status['code'] != 'HET_HAN' and status['code'] != 'DA_HUY':
        return JsonResponse({'success': False, 'message': 'Không thể xóa hợp đồng đang có hiệu lực hoặc sắp hiệu lực'}, status=400)
        
    hd.delete()
    return JsonResponse({'success': True, 'message': 'Đã xóa hợp đồng lao động thành công'})
