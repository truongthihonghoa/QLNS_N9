import datetime

from django import forms
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import HopDongLD_CT

_RUNTIME_CONTRACTS = []
_DELETED_CONTRACT_IDS = set()
_UPDATED_CONTRACTS = {}


class ContractForm(forms.Form):
    ma_nv = forms.CharField(max_length=20, required=True)
    loai_hd = forms.CharField(max_length=100, required=True)
    ngay_bd = forms.DateField(required=True)
    ngay_kt = forms.DateField(required=True)
    chuc_vu = forms.CharField(max_length=100, required=True)
    luong_co_ban = forms.FloatField(required=False, min_value=0)
    luong_theo_gio = forms.FloatField(required=False, min_value=0)
    so_gio_lam = forms.FloatField(required=False, min_value=0)
    thuong = forms.FloatField(required=False, min_value=0)
    phat = forms.FloatField(required=False, min_value=0)


def _sample_contracts():
    return [
        {'ma_hd': 'HD00001', 'ma_nv': 'NV00001', 'ten_nv': 'Nguyễn Văn An', 'loai_hd': 'Part-time', 'ngay_bd': '25/12/2025', 'ngay_kt': '25/03/2026', 'ngay_bd_iso': '2025-12-25', 'ngay_kt_iso': '2026-03-25', 'chuc_vu': 'Pha chế', 'muc_luong': '2.000.000'},
        {'ma_hd': 'HD00002', 'ma_nv': 'NV00002', 'ten_nv': 'Lê Hoài Bảo An', 'loai_hd': 'Full-time', 'ngay_bd': '10/01/2026', 'ngay_kt': '10/01/2027', 'ngay_bd_iso': '2026-01-10', 'ngay_kt_iso': '2027-01-10', 'chuc_vu': 'Giữ xe', 'muc_luong': '6.500.000'},
        {'ma_hd': 'HD00003', 'ma_nv': 'NV00003', 'ten_nv': 'Trần Thị Mai Loan', 'loai_hd': 'Thời vụ', 'ngay_bd': '15/02/2026', 'ngay_kt': '15/08/2026', 'ngay_bd_iso': '2026-02-15', 'ngay_kt_iso': '2026-08-15', 'chuc_vu': 'Phục vụ', 'muc_luong': '4.800.000'},
        {'ma_hd': 'HD00004', 'ma_nv': 'NV00004', 'ten_nv': 'Phạm Quang Bảo', 'loai_hd': 'Part-time', 'ngay_bd': '01/03/2026', 'ngay_kt': '01/03/2027', 'ngay_bd_iso': '2026-03-01', 'ngay_kt_iso': '2027-03-01', 'chuc_vu': 'Phục vụ', 'muc_luong': '2.600.000'},
        {'ma_hd': 'HD00005', 'ma_nv': 'NV00005', 'ten_nv': 'Nguyễn Viết Bảo', 'loai_hd': 'Thử việc', 'ngay_bd': '20/03/2026', 'ngay_kt': '20/05/2026', 'ngay_bd_iso': '2026-03-20', 'ngay_kt_iso': '2026-05-20', 'chuc_vu': 'Pha chế', 'muc_luong': '3.500.000'},
        {'ma_hd': 'HD00006', 'ma_nv': 'NV00006', 'ten_nv': 'Lê Văn Nhật Anh', 'loai_hd': 'Full-time', 'ngay_bd': '05/04/2026', 'ngay_kt': '05/04/2027', 'ngay_bd_iso': '2026-04-05', 'ngay_kt_iso': '2027-04-05', 'chuc_vu': 'Giữ xe', 'muc_luong': '6.200.000'},
        {'ma_hd': 'HD00007', 'ma_nv': 'NV00007', 'ten_nv': 'Nguyễn Văn Anh', 'loai_hd': 'Part-time', 'ngay_bd': '12/04/2026', 'ngay_kt': '12/10/2026', 'ngay_bd_iso': '2026-04-12', 'ngay_kt_iso': '2026-10-12', 'chuc_vu': 'Pha chế', 'muc_luong': '2.400.000'},
        {'ma_hd': 'HD00008', 'ma_nv': 'NV00008', 'ten_nv': 'Trần Lê Văn Khoa', 'loai_hd': 'Full-time', 'ngay_bd': '22/04/2026', 'ngay_kt': '22/04/2027', 'ngay_bd_iso': '2026-04-22', 'ngay_kt_iso': '2027-04-22', 'chuc_vu': 'Giữ xe', 'muc_luong': '6.000.000'},
    ]


def _get_employees():
    return [
        {'ma_nv': 'NV00001', 'ho_ten': 'Nguyễn Văn An'},
        {'ma_nv': 'NV00002', 'ho_ten': 'Lê Hoài Bảo An'},
        {'ma_nv': 'NV00003', 'ho_ten': 'Trần Thị Mai Loan'},
        {'ma_nv': 'NV00004', 'ho_ten': 'Phạm Quang Bảo'},
        {'ma_nv': 'NV00005', 'ho_ten': 'Nguyễn Viết Bảo'},
    ]


def _positions():
    return ['Pha chế', 'Phục vụ', 'Giữ xe', 'Quản lý']


def _all_contracts(_request):
    all_contracts = _sample_contracts() + list(_RUNTIME_CONTRACTS)
    contracts = []
    for contract in all_contracts:
        if contract['ma_hd'] in _DELETED_CONTRACT_IDS:
            continue
        merged_contract = contract.copy()
        merged_contract.update(_UPDATED_CONTRACTS.get(contract['ma_hd'], {}))
        contracts.append(merged_contract)
    return contracts


def _next_contract_id():
    numeric_ids = []
    for contract in _sample_contracts() + list(_RUNTIME_CONTRACTS):
        digits = ''.join(character for character in contract['ma_hd'] if character.isdigit())
        if digits:
            numeric_ids.append(int(digits))
    return f'HD{(max(numeric_ids, default=0) + 1):05d}'


def _next_manual_employee_code():
    numeric_ids = []
    for contract in _RUNTIME_CONTRACTS:
        ma_nv = contract['ma_nv']
        if ma_nv.startswith('NVTAY'):
            digits = ''.join(character for character in ma_nv if character.isdigit())
            if digits:
                numeric_ids.append(int(digits))
    return f'NVTAY{(max(numeric_ids, default=0) + 1):02d}'


def _json_requested(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _parse_money_string(value):
    return int(str(value or '0').replace('.', '').replace(',', '').strip() or 0)


def contract_list_view(request):
    return render(request, 'contracts/contract_list.html', {
        'contracts': _all_contracts(request),
        'form': ContractForm(),
        'employees': _get_employees(),
        'contract_types': ['Full-time', 'Part-time', 'Thời vụ', 'Thử việc'],
        'positions': _positions(),
    })


def contract_add_view(request):
    if request.method == 'POST':
        try:
            ten_nv = request.POST.get('ten_nv', '').strip()
            ma_nv = request.POST.get('ma_nv', '').strip() or _next_manual_employee_code()
            loai_hd = request.POST.get('loai_hd', '').strip()
            ngay_bd = request.POST.get('ngay_bd', '').strip()
            ngay_kt = request.POST.get('ngay_kt', '').strip()
            chuc_vu = request.POST.get('chuc_vu', '').strip()

            if not all([ten_nv, loai_hd, ngay_bd, ngay_kt, chuc_vu]):
                if _json_requested(request):
                    return JsonResponse({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin hợp đồng.'}, status=400)
                messages.error(request, 'Vui lòng nhập đầy đủ thông tin hợp đồng.')
                return redirect('contract_add')

            luong_co_ban = float(request.POST.get('luong_co_ban') or 0)
            so_gio_lam_toi_thieu = float(request.POST.get('so_gio_lam_toi_thieu') or 0)
            if request.POST.get('luong_theo_gio') == 'khac':
                luong_theo_gio = float(request.POST.get('luong_theo_gio_khac') or 0)
            else:
                luong_theo_gio = float(request.POST.get('luong_theo_gio') or 0)

            muc_luong = luong_co_ban if loai_hd == 'FULL_TIME' else luong_theo_gio * so_gio_lam_toi_thieu
            contract = {
                'ma_hd': _next_contract_id(),
                'ma_nv': ma_nv,
                'ten_nv': ten_nv,
                'loai_hd': 'Full-time' if loai_hd == 'FULL_TIME' else 'Part-time',
                'ngay_bd': datetime.datetime.strptime(ngay_bd, '%Y-%m-%d').strftime('%d/%m/%Y'),
                'ngay_kt': datetime.datetime.strptime(ngay_kt, '%Y-%m-%d').strftime('%d/%m/%Y'),
                'ngay_bd_iso': ngay_bd,
                'ngay_kt_iso': ngay_kt,
                'chuc_vu': chuc_vu,
                'muc_luong': f"{int(muc_luong):,}".replace(',', '.'),
            }
            _RUNTIME_CONTRACTS.append(contract)

            if _json_requested(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Thêm hợp đồng lao động thành công',
                    'redirect_url': '/contracts/',
                })

            messages.success(request, 'Tạo hợp đồng thành công')
            return redirect('contract_list')
        except Exception:
            if _json_requested(request):
                return JsonResponse({'success': False, 'message': 'Không thể tạo hợp đồng. Vui lòng thử lại sau.'}, status=500)
            messages.error(request, 'Không thể tạo hợp đồng. Vui lòng thử lại sau.')
            return redirect('contract_add')

    return render(request, 'contracts/contract_add.html', {
        'form': ContractForm(),
        'employees': _get_employees(),
        'contract_types': ['Full-time', 'Part-time', 'Thời vụ', 'Thử việc'],
        'positions': _positions(),
    })


def contract_edit_view(request, contract_id):
    contracts = _all_contracts(request)
    contract = next((c for c in contracts if c['ma_hd'] == contract_id), None)
    if not contract:
        return redirect('contract_list')

    if request.method == 'POST':
        try:
            loai_hd = request.POST.get('loai_hd', '').strip()
            ngay_bd = request.POST.get('ngay_bd', '').strip()
            ngay_kt = request.POST.get('ngay_kt', '').strip()
            chuc_vu = request.POST.get('chuc_vu', '').strip()
            dia_diem_lam_viec = request.POST.get('dia_diem_lam_viec', '').strip()
            ly_do_cham_dut = request.POST.get('ly_do_cham_dut', '').strip()
            che_do_thuong = float(request.POST.get('thuong') or 0)
            luong_co_ban = float(request.POST.get('luong_co_ban') or 0)
            so_gio_lam_toi_thieu = float(request.POST.get('so_gio_lam_toi_thieu') or 0)

            if request.POST.get('luong_theo_gio') == 'khac':
                luong_theo_gio = float(request.POST.get('luong_theo_gio_khac') or 0)
            else:
                luong_theo_gio = float(request.POST.get('luong_theo_gio') or 0)

            muc_luong = luong_co_ban if loai_hd == 'FULL_TIME' else luong_theo_gio * so_gio_lam_toi_thieu
            _UPDATED_CONTRACTS[contract_id] = {
                'loai_hd': 'Full-time' if loai_hd == 'FULL_TIME' else 'Part-time',
                'ngay_bd': datetime.datetime.strptime(ngay_bd, '%Y-%m-%d').strftime('%d/%m/%Y'),
                'ngay_kt': datetime.datetime.strptime(ngay_kt, '%Y-%m-%d').strftime('%d/%m/%Y'),
                'ngay_bd_iso': ngay_bd,
                'ngay_kt_iso': ngay_kt,
                'chuc_vu': chuc_vu,
                'muc_luong': f"{int(muc_luong):,}".replace(',', '.'),
                'dia_diem_lam_viec': dia_diem_lam_viec,
                'ly_do_cham_dut': ly_do_cham_dut,
                'che_do_thuong': che_do_thuong,
                'luong_co_ban_value': luong_co_ban,
                'luong_theo_gio_value': luong_theo_gio,
                'so_gio_lam_toi_thieu_value': so_gio_lam_toi_thieu,
            }

            if _json_requested(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Cập nhật hợp đồng lao động thành công',
                    'redirect_url': '/contracts/',
                })

            messages.success(request, 'Cập nhật hợp đồng thành công')
            return redirect('contract_list')
        except Exception:
            if _json_requested(request):
                return JsonResponse({'success': False, 'message': 'Không thể cập nhật hợp đồng. Vui lòng thử lại sau.'}, status=500)
            messages.error(request, 'Không thể cập nhật hợp đồng. Vui lòng thử lại sau.')
            return redirect('contract_edit', contract_id=contract_id)

    contract_type_value = 'FULL_TIME' if contract['loai_hd'] == 'Full-time' else 'PART_TIME'
    muc_luong_value = _parse_money_string(contract['muc_luong'])
    luong_co_ban_value = contract.get('luong_co_ban_value', muc_luong_value if contract_type_value == 'FULL_TIME' else 0)
    luong_theo_gio_value = contract.get('luong_theo_gio_value', 20000 if contract_type_value == 'PART_TIME' else 0)
    so_gio_lam_toi_thieu_value = contract.get('so_gio_lam_toi_thieu_value', 174 if contract_type_value == 'FULL_TIME' else 80)

    return render(request, 'contracts/contract_edit.html', {
        'contract': contract,
        'contract_type_value': contract_type_value,
        'contract_types': ['Full-time', 'Part-time', 'Thời vụ', 'Thử việc'],
        'positions': _positions(),
        'muc_luong_value': muc_luong_value,
        'luong_co_ban_value': luong_co_ban_value,
        'luong_theo_gio_value': luong_theo_gio_value,
        'so_gio_lam_toi_thieu_value': so_gio_lam_toi_thieu_value,
        'che_do_thuong_value': contract.get('che_do_thuong', 0),
        'dia_diem_lam_viec': contract.get('dia_diem_lam_viec', ''),
        'ly_do_cham_dut': contract.get('ly_do_cham_dut', ''),
    })


def _render_edit_form(request, contract):
    context = {
        'contract': contract,
        'employees': _get_employees(),
        'contract_types': ['Full-time', 'Part-time', 'Thời vụ', 'Thử việc'],
        'positions': _positions(),
        'luong_co_ban': 0,
        'luong_theo_gio': 0,
        'so_gio_lam': 0,
        'thuong': 0,
        'phat': 0,
    }

    try:
        ct = contract.hopdongld_ct
        context.update({
            'luong_co_ban': ct.luong_co_ban,
            'luong_theo_gio': ct.luong_theo_gio,
            'so_gio_lam': ct.so_gio_lam,
            'thuong': getattr(ct, 'thuong', 0),
            'phat': getattr(ct, 'phat', 0),
        })
    except HopDongLD_CT.DoesNotExist:
        pass

    return render(request, 'contracts/contract_edit.html', context)


@require_http_methods(["DELETE"])
def contract_delete_view(request, contract_id):
    contract = next((item for item in _all_contracts(request) if item['ma_hd'] == contract_id), None)
    if not contract:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy hợp đồng'}, status=404)

    end_date = datetime.datetime.strptime(contract['ngay_kt_iso'], '%Y-%m-%d').date()
    if end_date >= datetime.date.today():
        return JsonResponse({
            'success': False,
            'error_code': 'ACTIVE_CONTRACT',
            'message': 'Không thể xóa hợp đồng đang có hiệu lực',
        }, status=400)

    _DELETED_CONTRACT_IDS.add(contract_id)
    if any(item['ma_hd'] == contract_id for item in _RUNTIME_CONTRACTS):
        _RUNTIME_CONTRACTS[:] = [item for item in _RUNTIME_CONTRACTS if item['ma_hd'] != contract_id]

    return JsonResponse({'success': True, 'message': 'Đã xóa hợp đồng lao động thành công'})


@require_http_methods(["GET"])
def contract_detail_view(request, contract_id):
    contracts = _all_contracts(request)
    contract = next((c for c in contracts if c['ma_hd'] == contract_id), None)
    if not contract:
        return JsonResponse({'error': 'Không tìm thấy hợp đồng'}, status=404)

    return JsonResponse({
        'ma_hd': contract['ma_hd'],
        'ma_nv': contract['ma_nv'],
        'ten_nv': contract['ten_nv'],
        'loai_hd': contract['loai_hd'],
        'ngay_bd': contract['ngay_bd'],
        'ngay_kt': contract['ngay_kt'],
        'chuc_vu': contract['chuc_vu'],
        'trang_thai': 'Đang hiệu lực',
        'luong_co_ban': '0' if contract['loai_hd'] == 'Part-time' else '5.000.000',
        'luong_theo_gio': '20.000' if contract['loai_hd'] == 'Part-time' else '0',
        'so_gio_lam': '0',
        'thuong': '500.000',
        'phat': '0',
        'tong_luong': contract['muc_luong'],
    })
