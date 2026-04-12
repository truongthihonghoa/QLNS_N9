import datetime
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

def _json_requested(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def get_representative_info(nhan_vien):
    if nhan_vien.chuc_vu == 'Quản lý':
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
    all_employees = NhanVien.objects.all()
    with transaction.atomic():
        for nv in all_employees:
            if not HopDongLaoDong.objects.filter(ma_nv=nv).exists():
                new_ma_hd = f"HD{nv.ma_nv}"
                hd = HopDongLaoDong.objects.create(
                    ma_hd=new_ma_hd,
                    ma_nv=nv,
                    ma_chi_nhanh=nv.ma_chi_nhanh,
                    loai_hd='FULLTIME',
                    chuc_vu=nv.chuc_vu if nv.chuc_vu else 'NHAN_VIEN',
                    ngay_bat_dau=datetime.date.today(),
                    ngay_ket_thuc=datetime.date.today() + datetime.timedelta(days=365),
                    trang_thai='CON_HAN'
                )
                HopDongLD_CT.objects.create(
                    ma_hd=hd, luong_co_ban=3480000, luong_theo_gio=25000, so_gio_lam=174,
                    che_do_thuong=0, trach_nhiem="Thực hiện đúng quy trình phục vụ khách hàng.", ghi_chu="Hệ thống tự động khởi tạo."
                )

    contracts_qs = HopDongLaoDong.objects.select_related('ma_nv', 'ma_chi_nhanh', 'chi_tiet').all()
    contracts_list = []
    today = datetime.date.today()

    for hd in contracts_qs:
        ct = getattr(hd, 'chi_tiet', None)
        nv = hd.ma_nv
        rep = get_representative_info(nv)
        is_expired = hd.ngay_ket_thuc and hd.ngay_ket_thuc < today
        trang_thai_code = 'HET_HAN' if is_expired else hd.trang_thai

        contracts_list.append({
            'ma_hd': hd.ma_hd, 'ma_nv': nv.ma_nv if nv else '', 'ten_nv': nv.ho_ten if nv else '',
            'loai_hd': hd.get_loai_hd_display(), 'ngay_bd': hd.ngay_bat_dau.strftime('%d/%m/%Y'),
            'ngay_kt': hd.ngay_ket_thuc.strftime('%d/%m/%Y') if hd.ngay_ket_thuc else '',
            'chuc_vu': nv.chuc_vu if nv else hd.get_chuc_vu_display(), 'muc_luong': ct.luong_co_ban if ct else 0,
            'cccd': nv.cccd if nv else '', 'ngay_sinh': nv.ngay_sinh.strftime('%d/%m/%Y') if nv and nv.ngay_sinh else '',
            'sdt_nv': nv.sdt if nv else '', 'dia_chi': nv.dia_chi if nv else '',
            'nguoi_dai_dien': rep['ten'], 'chuc_vu_dai_dien': rep['chuc_vu'], 'sdt_dai_dien': rep['sdt'],
            'dia_diem_lv': nv.ma_chi_nhanh.ten_chi_nhanh if nv and nv.ma_chi_nhanh else '',
            'so_gio_lam': ct.so_gio_lam if ct else 0, 'luong_theo_gio': ct.luong_theo_gio if ct else 0,
            'ghi_chu': (ct.ghi_chu if ct else '') or 'Không có ghi chú.',
            'trang_thai_code': trang_thai_code, 'trang_thai_display': 'Hết hạn' if is_expired else hd.get_trang_thai_display(),
        })

    return render(request, 'contracts/contract_list.html', {
        'contracts': contracts_list,
        'employees': NhanVien.objects.all(),
        'contract_types': HopDongLaoDong.LOAI_HD_CHOICES,
        'positions': [choice[0] for choice in NhanVien.CHUC_VU_CHOICES],
    })

def contract_add_view(request):
    if request.method == 'POST':
        # Xử lý lưu hợp đồng thực tế...
        pass
    
    return render(request, 'contracts/contract_add.html', {
        'employees': NhanVien.objects.all(),
        'branches': ChiNhanh.objects.all(), # Lấy Chi nhánh thật
        'contract_types': HopDongLaoDong.LOAI_HD_CHOICES,
        'positions': [choice[0] for choice in NhanVien.CHUC_VU_CHOICES],
    })

def contract_edit_view(request, contract_id):
    hd = get_object_or_404(HopDongLaoDong, ma_hd=contract_id)
    return render(request, 'contracts/contract_edit.html', {
        'contract': hd,
        'branches': ChiNhanh.objects.all(),
        'positions': [choice[0] for choice in NhanVien.CHUC_VU_CHOICES]
    })

@require_http_methods(["DELETE"])
def contract_delete_view(request, contract_id):
    hd = get_object_or_404(HopDongLaoDong, ma_hd=contract_id)
    if hd.ngay_ket_thuc and hd.ngay_ket_thuc >= datetime.date.today():
        return JsonResponse({'success': False, 'message': 'Không thể xóa hợp đồng đang có hiệu lực'}, status=400)
    hd.delete()
    return JsonResponse({'success': True, 'message': 'Đã xóa hợp đồng lao động thành công'})

@require_http_methods(["GET"])
def contract_detail_view(request, contract_id):
    hd = get_object_or_404(HopDongLaoDong, ma_hd=contract_id)
    ct = getattr(hd, 'chi_tiet', None)
    nv = hd.ma_nv
    rep = get_representative_info(nv)
    return JsonResponse({
        'ma_hd': hd.ma_hd, 'ma_nv': nv.ma_nv, 'ten_nv': nv.ho_ten,
        'loai_hd': hd.get_loai_hd_display(), 'ngay_bd': hd.ngay_bat_dau.strftime('%d/%m/%Y'),
        'ngay_kt': hd.ngay_ket_thuc.strftime('%d/%m/%Y') if hd.ngay_ket_thuc else '',
        'chuc_vu': nv.chuc_vu, 'cccd': nv.cccd, 'ngay_sinh': nv.ngay_sinh.strftime('%d/%m/%Y') if nv.ngay_sinh else '',
        'dia_chi': nv.dia_chi, 'sdt_nv': nv.sdt, 'nguoi_dai_dien': rep['ten'], 'sdt_dai_dien': rep['sdt'],
        'luong_co_ban': ct.luong_co_ban if ct else 0, 'luong_theo_gio': ct.luong_theo_gio if ct else 0,
        'so_gio_lam': ct.so_gio_lam if ct else 0, 'ghi_chu': (ct.ghi_chu if ct else '') or 'Không có ghi chú.',
    })
