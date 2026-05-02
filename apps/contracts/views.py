from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
import datetime
from django.utils import timezone

from .models import HopDongLaoDong, HopDongLD_CT
from apps.employees.models import NhanVien
from apps.branches.models import ChiNhanh

def _json_requested(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def clean_money(val):
    if not val:
        return 0
    try:
        # Xử lý các định dạng như 5.000.000 hoặc 5,000,000
        return float(str(val).replace(".", "").replace(",", ""))
    except (ValueError, TypeError):
        return 0

def get_next_ma_hd():
    last_hd = HopDongLaoDong.objects.all().order_by('ma_hd').last()
    if not last_hd:
        return 'HD00001'
    
    try:
        last_id_num = int(last_hd.ma_hd[2:])
        new_id_num = last_id_num + 1
        return f"HD{new_id_num:05d}"
    except (ValueError, IndexError):
        return f"HD{datetime.datetime.now().strftime('%m%d%H%M%S')}"

def get_representative_info(nhan_vien):
    """Lấy thông tin người đại diện ký hợp đồng (Chủ hoặc Quản lý)"""
    if nhan_vien and nhan_vien.chuc_vu == 'Quản lý':
        owner = User.objects.filter(is_superuser=True).first()
        if owner:
            fullname = f"{owner.last_name} {owner.first_name}".strip()
            if not fullname:
                fullname = "Trương Thị Hồng Hoa"
            return {'ten': fullname, 'chuc_vu': "Chủ", 'sdt': "0901234567"}
    
    if nhan_vien and nhan_vien.ma_chi_nhanh:
        manager = NhanVien.objects.filter(ma_chi_nhanh=nhan_vien.ma_chi_nhanh, chuc_vu='Quản lý').first()
        if manager:
            return {'ten': manager.ho_ten, 'chuc_vu': "Quản lý Chi nhánh", 'sdt': manager.sdt}
            
    return {'ten': "Trương Thị Hồng Hoa", 'chuc_vu': "Chủ", 'sdt': "0901234567"}

@login_required(login_url='/accounts/login/')
def contract_list_view(request):
    role = request.session.get("role", "Nhân viên")
    branch_filter = request.GET.get("branch", "").strip()
    contracts_qs = HopDongLaoDong.objects.select_related("ma_nv", "ma_chi_nhanh", "chi_tiet").all().order_by("ma_hd")

    if role == "Nhân viên":
        try:
            user_ma_nv = request.user.taikhoan.ma_nv
            contracts_qs = contracts_qs.filter(ma_nv=user_ma_nv)
        except Exception:
            contracts_qs = contracts_qs.none()
    else:
        # Chủ và Quản lý thấy dữ liệu
        user_branch_id = None
        if not request.user.is_superuser:
            try:
                user_branch_id = request.user.taikhoan.ma_nv.ma_chi_nhanh_id
            except Exception:
                pass

        if user_branch_id:
            # Quản lý chỉ thấy chi nhánh của mình
            contracts_qs = contracts_qs.filter(ma_chi_nhanh_id=user_branch_id)
            if branch_filter and branch_filter != user_branch_id:
                contracts_qs = contracts_qs.none()
        else:
            # Chủ thấy tất cả theo bộ lọc
            if branch_filter:
                contracts_qs = contracts_qs.filter(ma_chi_nhanh_id=branch_filter)

    contracts_list = []
    for hd in contracts_qs:
        ct = getattr(hd, "chi_tiet", None)
        nv = hd.ma_nv
        rep = get_representative_info(nv)
        status = hd.trang_thai_thuc_te

        contracts_list.append({
            "ma_hd": hd.ma_hd,
            "ma_nv": nv.ma_nv if nv else "",
            "ten_nv": nv.ho_ten if nv else "",
            "loai_hd": hd.get_loai_hd_display(),
            "ngay_bd": hd.ngay_bat_dau.strftime("%d/%m/%Y"),
            "ngay_kt": hd.ngay_ket_thuc.strftime("%d/%m/%Y") if hd.ngay_ket_thuc else "",
            "chuc_vu": nv.chuc_vu if nv else hd.get_chuc_vu_display(),
            "muc_luong": ct.luong_co_ban if ct else 0,
            "cccd": nv.cccd if nv else "",
            "nguoi_dai_dien": rep["ten"],
            "chuc_vu_dai_dien": rep["chuc_vu"],
            "trang_thai_code": status["code"],
            "trang_thai_display": status["display"],
        })

    # Lọc danh sách chi nhánh và nhân viên trong context
    all_branches = ChiNhanh.objects.all()
    all_employees = NhanVien.objects.all()
    if not request.user.is_superuser:
        try:
            u_branch_id = request.user.taikhoan.ma_nv.ma_chi_nhanh_id
            all_branches = all_branches.filter(ma_chi_nhanh=u_branch_id)
            all_employees = all_employees.filter(ma_chi_nhanh=u_branch_id)
        except Exception:
            all_branches = all_branches.none()
            all_employees = all_employees.none()

    return render(request, "contracts/contract_list.html", {
        "contracts": contracts_list,
        "branches": all_branches,
        "current_branch": branch_filter,
        "employees": all_employees,
        "contract_types": HopDongLaoDong.LOAI_HD_CHOICES,
        "role": role,
    })

@login_required(login_url='/accounts/login/')
@require_http_methods(["GET"])
def contract_detail_view(request, contract_id):
    role = request.session.get("role", "Nhân viên")
    hd = get_object_or_404(HopDongLaoDong, ma_hd=contract_id)

    if role == "Nhân viên":
        try:
            if hd.ma_nv != request.user.taikhoan.ma_nv:
                return JsonResponse({"success": False, "message": "Bạn không có quyền xem hợp đồng này."}, status=403)
        except Exception:
            return JsonResponse({"success": False, "message": "Không tìm thấy thông tin nhân viên."}, status=403)

    ct = getattr(hd, "chi_tiet", None)
    nv = hd.ma_nv
    rep = get_representative_info(nv)

    return JsonResponse({
        "ma_hd": hd.ma_hd,
        "ma_nv": nv.ma_nv,
        "ten_nv": nv.ho_ten,
        "loai_hd": hd.get_loai_hd_display(),
        "ngay_bd": hd.ngay_bat_dau.strftime("%d/%m/%Y"),
        "ngay_kt": hd.ngay_ket_thuc.strftime("%d/%m/%Y") if hd.ngay_ket_thuc else "",
        "chuc_vu": nv.chuc_vu,
        "cccd": nv.cccd,
        "nguoi_dai_dien": rep["ten"],
        "sdt_dai_dien": rep["sdt"],
        "luong_co_ban": ct.luong_co_ban if ct else 0,
        "luong_theo_gio": ct.luong_theo_gio if ct else 0,
        "so_gio_lam": ct.so_gio_lam if ct else 0,
        "ghi_chu": (ct.ghi_chu if ct else "") or "Không có ghi chú.",
    })

@login_required(login_url='/accounts/login/')
def contract_add_view(request):
    if request.session.get("role") == "Nhân viên":
        return JsonResponse({"success": False, "message": "Bạn không có quyền thực hiện chức năng này."}, status=403)

    if request.method == "POST":
        try:
            with transaction.atomic():
                ma_nv = request.POST.get("ma_nv")
                nhan_vien = get_object_or_404(NhanVien, ma_nv=ma_nv)
                
                ngay_bd_str = request.POST.get("ngay_bd")
                ngay_kt_str = request.POST.get("ngay_kt")
                
                # Convert to date objects for safe comparison
                ngay_bd = datetime.datetime.strptime(ngay_bd_str, "%Y-%m-%d").date()
                ngay_kt = datetime.datetime.strptime(ngay_kt_str, "%Y-%m-%d").date() if ngay_kt_str else None

                if ngay_kt and ngay_kt < ngay_bd:
                    return JsonResponse({"success": False, "message": "Ngày kết thúc không thể trước ngày bắt đầu"}, status=400)

                new_ma_hd = get_next_ma_hd()
                hd = HopDongLaoDong.objects.create(
                    ma_hd=new_ma_hd,
                    ma_nv=nhan_vien,
                    ma_chi_nhanh_id=request.POST.get("dia_diem_lam_viec"),
                    loai_hd=request.POST.get("loai_hd"),
                    chuc_vu=request.POST.get("chuc_vu"),
                    ngay_bat_dau=ngay_bd,
                    ngay_ket_thuc=ngay_kt,
                )

                HopDongLD_CT.objects.create(
                    ma_hd=hd,
                    luong_co_ban=clean_money(request.POST.get("luong_co_ban")),
                    luong_theo_gio=clean_money(request.POST.get("luong_theo_gio")),
                    so_gio_lam=float(request.POST.get("so_gio_lam_toi_thieu") or 0),
                    che_do_thuong=clean_money(request.POST.get("thuong")),
                    ghi_chu=request.POST.get("ghi_chu"),
                )

                return JsonResponse({"success": True, "message": f"Thêm hợp đồng {new_ma_hd} thành công"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}, status=500)

    return render(request, "contracts/contract_add.html", {
        "next_ma_hd": get_next_ma_hd(),
        "employees": NhanVien.objects.all().order_by("-ma_nv"),
        "positions": HopDongLaoDong.CHUC_VU_CHOICES,
        "branches": ChiNhanh.objects.all(),
        "contract_types": HopDongLaoDong.LOAI_HD_CHOICES,
    })

@login_required(login_url='/accounts/login/')
def contract_edit_view(request, contract_id):
    if request.session.get("role") == "Nhân viên":
        return JsonResponse({"success": False, "message": "Bạn không có quyền thực hiện chức năng này."}, status=403)

    hd = get_object_or_404(HopDongLaoDong, ma_hd=contract_id)
    ct = getattr(hd, "chi_tiet", None)

    if request.method == "POST":
        try:
            with transaction.atomic():
                ngay_bd_str = request.POST.get("ngay_bd")
                ngay_kt_str = request.POST.get("ngay_kt")
                
                ngay_bd = datetime.datetime.strptime(ngay_bd_str, "%Y-%m-%d").date()
                ngay_kt = datetime.datetime.strptime(ngay_kt_str, "%Y-%m-%d").date() if ngay_kt_str else None

                if ngay_kt and ngay_kt < ngay_bd:
                    return JsonResponse({"success": False, "message": "Ngày kết thúc không thể trước ngày bắt đầu"}, status=400)

                hd.loai_hd = request.POST.get("loai_hd")
                hd.chuc_vu = request.POST.get("chuc_vu")
                hd.ma_chi_nhanh_id = request.POST.get("dia_diem_lam_viec")
                hd.ngay_bat_dau = ngay_bd
                hd.ngay_ket_thuc = ngay_kt
                hd.save()

                detail, _ = HopDongLD_CT.objects.get_or_create(ma_hd=hd)
                detail.luong_co_ban = clean_money(request.POST.get("luong_co_ban"))
                detail.luong_theo_gio = clean_money(request.POST.get("luong_theo_gio"))
                detail.so_gio_lam = float(request.POST.get("so_gio_lam_toi_thieu") or 0)
                detail.che_do_thuong = clean_money(request.POST.get("thuong"))
                detail.ghi_chu = request.POST.get("ghi_chu")
                detail.save()

                return JsonResponse({"success": True, "message": f"Cập nhật hợp đồng {hd.ma_hd} thành công"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}, status=500)

    return render(request, "contracts/contract_edit.html", {
        "contract": hd,
        "ct": ct,
        "branches": ChiNhanh.objects.all(),
        "positions": HopDongLaoDong.CHUC_VU_CHOICES,
        "luong_co_ban": ct.luong_co_ban if ct else 0,
        "luong_theo_gio": ct.luong_theo_gio if ct else 0,
        "so_gio_lam": ct.so_gio_lam if ct else 0,
        "thuong": ct.che_do_thuong if ct else 0,
        "ghi_chu": ct.ghi_chu if ct else "",
        "ngay_bd_iso": hd.ngay_bat_dau.strftime("%Y-%m-%d") if hd.ngay_bat_dau else "",
        "ngay_kt_iso": hd.ngay_ket_thuc.strftime("%Y-%m-%d") if hd.ngay_ket_thuc else "",
    })

@login_required(login_url='/accounts/login/')
@require_http_methods(["DELETE"])
def contract_delete_view(request, contract_id):
    if request.session.get("role") == "Nhân viên":
        return JsonResponse({"success": False, "message": "Bạn không có quyền thực hiện chức năng này."}, status=403)

    hd = get_object_or_404(HopDongLaoDong, ma_hd=contract_id)
    status = hd.trang_thai_thuc_te
    if status["code"] not in ["HET_HAN", "DA_HUY"]:
        return JsonResponse({"success": False, "message": "Không thể xóa hợp đồng đang có hiệu lực"}, status=400)

    hd.delete()
    return JsonResponse({"success": True, "message": "Đã xóa hợp đồng thành công"})
