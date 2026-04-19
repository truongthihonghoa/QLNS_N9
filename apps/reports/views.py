import json
from datetime import datetime, date
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.reports.models import BaoCao, BaoCao_CT
from apps.attendances.models import ChamCong
from apps.accounts.models import TaiKhoan
from apps.employees.models import NhanVien


def report_list_view(request):
    from apps.branches.models import ChiNhanh
    branch_id = request.GET.get('branch', 'CN01')
    q = request.GET.get('q', '')
    baocaos = BaoCao.objects.all().order_by('-ma_bc')
    if branch_id:
        baocaos = baocaos.filter(ma_chi_nhanh=branch_id)
    if q:
        baocaos = baocaos.filter(ma_bc__icontains=q)
    branches = ChiNhanh.objects.all()
    return render(request, 'reports/report_list.html', {
        'baocaos': baocaos,
        'branches': branches,
        'selected_branch': branch_id,
        'q': q,
    })


@csrf_exempt
def api_aggregate_data(request):
    """
    Lấy dữ liệu chấm công từ ngày BĐ -> KT, nhóm theo nhân viên.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            branch_id = data.get('branch_id')

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            nhanviens = NhanVien.objects.all()
            if branch_id:
                nhanviens = nhanviens.filter(ma_chi_nhanh=branch_id)

            result = []
            for nv in nhanviens:
                ccs = ChamCong.objects.filter(ma_nv=nv, ngay_lam__gte=start_date, ngay_lam__lte=end_date)

                so_ca_lam = ccs.count()
                if so_ca_lam == 0:
                    continue

                so_gio_lam = sum(cc.so_gio_lam for cc in ccs)

                # Cộng dồn ghi chú từ các bản ghi chấm công
                ghi_chus = [cc.ghi_chu for cc in ccs if cc.ghi_chu]
                ghi_chu_str = ", ".join(ghi_chus) if ghi_chus else "-"

                # Lấy mã chấm công đại diện (ví dụ bản ghi cuối cùng trong khoảng)
                time_id = ccs.last().ma_cc if ccs.exists() else "-"

                result.append({
                    "empId": nv.ma_nv,
                    "empName": nv.ho_ten,
                    "timeId": time_id,
                    "hours": so_gio_lam,
                    "shifts": so_ca_lam,
                    "late": 0.0,
                    "early": 0.0,
                    "note": ghi_chu_str
                })

            return JsonResponse({"status": "success", "data": result})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)


@csrf_exempt
def api_save_report(request):
    """
    Lưu Báo Cáo và Báo Cáo chi tiết
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            report_data = data.get('report_data', [])
            report_id = data.get('report_id')

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            branch_id = data.get('branch_id')

            tk = TaiKhoan.objects.filter(user__username='admin').first()
            if not tk:
                tk = TaiKhoan.objects.first()

            from apps.branches.models import ChiNhanh
            chi_nhanh = ChiNhanh.objects.filter(ma_chi_nhanh=branch_id).first() if branch_id else None

            if report_id:
                bc = BaoCao.objects.filter(ma_bc=report_id).first()
                if not bc:
                    return JsonResponse({"status": "error", "message": "Report not found"})
                bc.ngay_bd = start_date
                bc.ngay_kt = end_date

                bc.save()

                BaoCao_CT.objects.filter(ma_bc=bc).delete()
            else:
                import uuid
                report_id = f"BC{str(uuid.uuid4().int)[:6]}"
                bc = BaoCao.objects.create(
                    ma_bc=report_id,
                    ngay_bd=start_date,
                    ngay_kt=end_date,
                    ngay_tao=date.today(),
                    ma_chi_nhanh=chi_nhanh,
                    ma_tk=tk
                )

            for item in report_data:
                nv = NhanVien.objects.filter(ma_nv=item.get('empId')).first()
                cc_obj = None
                if item.get('timeId'):
                    cc_obj = ChamCong.objects.filter(ma_cc=item.get('timeId')).first()

                if nv:
                    BaoCao_CT.objects.create(
                        ma_bc=bc,
                        ma_nv=nv,
                        ma_cc=cc_obj,
                        ten_nv=item.get('empName'),
                        so_gio_lam=item.get('hours'),
                        so_ca_lam=item.get('shifts'),
                        di_muon=item.get('late'),
                        dung_gio=item.get('early'),  # Changed from ve_som to dung_gio
                        ghi_chu=item.get('note')
                    )

            return JsonResponse({"status": "success", "report_id": bc.ma_bc})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)


def api_get_report_details(request, ma_bc):
    """
    Trả JSON chi tiết một bản ghi BaoCao
    """
    try:
        bc = BaoCao.objects.filter(ma_bc=ma_bc).first()
        if not bc:
            return JsonResponse({"status": "error", "message": "Not found"}, status=404)

        details = BaoCao_CT.objects.filter(ma_bc=bc)
        result = []
        for d in details:
            result.append({
                "empId": d.ma_nv_id,
                "empName": d.ten_nv,
                "timeId": d.ma_cc_id if d.ma_cc_id else "-",
                "hours": d.so_gio_lam,
                "shifts": d.so_ca_lam,
                "late": d.di_muon,
                "early": d.dung_gio,  # Changed from ve_som to dung_gio
                "note": d.ghi_chu if d.ghi_chu else "-"
            })

        return JsonResponse({"status": "success", "data": result})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
