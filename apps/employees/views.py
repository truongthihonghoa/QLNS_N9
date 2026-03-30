from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EmployeeCreateForm, EmployeeUpdateForm
from .models import NhanVien


CARD_THEMES = (
    "theme-emerald",
    "theme-royal",
    "theme-amber",
    "theme-rose",
)

EMPLOYEE_IMAGE_MAP = {
    "NV00001": "employees/img/Nguyen_Van_An.png",
    "NV00002": "employees/img/Nguyen_Van_Tien.jpg",
    "NV00003": "employees/img/Tran_Vu_Anh.jpg",
    "NV00004": "employees/img/Vo_Thi_Anh_Thi.jpg",
    "NV00005": "employees/img/Le_Thuy_Vy.jpg",
    "NV00006": "employees/img/Trinh_Phan_Vu.jpg",
    "NV00007": "employees/img/Tran_Thi_Ly.jpg",
    "NV00008": "employees/img/Nguyen_Le_My.jpg",
}


def _build_employee_cards(queryset):
    cards = []
    for index, employee in enumerate(queryset):
        words = [part for part in employee.ho_ten.split() if part]
        initials = "".join(word[0] for word in words[:2]).upper() if words else "NV"
        cards.append(
            {
                "ma_nv": employee.ma_nv,
                "ho_ten": employee.ho_ten,
                "ngay_sinh": employee.ngay_sinh,
                "gioi_tinh": employee.gioi_tinh,
                "cccd": employee.cccd,
                "sdt": employee.sdt,
                "tk_ngan_hang": employee.tk_ngan_hang,
                "chuc_vu": employee.chuc_vu,
                "vi_tri_vl": employee.vi_tri_vl,
                "chi_nhanh": employee.ma_chi_nhanh,
                "dia_chi": employee.dia_chi,
                "detail_url": f"{employee.ma_nv}/",
                "initials": initials,
                "theme_class": CARD_THEMES[index % len(CARD_THEMES)],
                "image_path": EMPLOYEE_IMAGE_MAP.get(employee.ma_nv, ""),
            }
        )
    return cards


def employee_list_view(request):
    search_query = request.GET.get("q", "").strip()
    employees = NhanVien.objects.select_related("ma_chi_nhanh").order_by("ma_nv")

    if search_query:
        employees = employees.filter(
            Q(ho_ten__icontains=search_query)
            | Q(ma_nv__icontains=search_query)
            | Q(sdt__icontains=search_query)
            | Q(chuc_vu__icontains=search_query)
            | Q(vi_tri_vl__icontains=search_query)
            | Q(ma_chi_nhanh__Ten_ChiNhanh__icontains=search_query)
        )

    context = {
        "employee_cards": _build_employee_cards(employees),
        "search_query": search_query,
        "employee_count": employees.count(),
    }
    return render(request, "employees/employee_list.html", context)


def employee_add_view(request):
    form = EmployeeCreateForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Thêm nhân viên thành công!")
            return redirect("employee_list")

        messages.error(request, "Thông tin nhân viên không hợp lệ.", extra_tags="invalid_info_error")

    return render(request, "employees/employee_add.html", {"form": form})


def employee_detail_view(request, employee_id):
    employee = get_object_or_404(
        NhanVien.objects.select_related("ma_chi_nhanh", "ma_chi_nhanh__MaNV_QL"),
        pk=employee_id,
    )
    words = [part for part in employee.ho_ten.split() if part]
    context = {
        "employee": employee,
        "manager_name": employee.ma_chi_nhanh.MaNV_QL.ho_ten if employee.ma_chi_nhanh and employee.ma_chi_nhanh.MaNV_QL else "",
        "initials": "".join(word[0] for word in words[:2]).upper() if words else "NV",
        "image_path": EMPLOYEE_IMAGE_MAP.get(employee.ma_nv, ""),
    }
    return render(request, "employees/employee_detail.html", context)


def employee_edit_view(request, employee_id):
    employee = get_object_or_404(NhanVien, pk=employee_id)
    form = EmployeeUpdateForm(request.POST or None, instance=employee)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật thông tin thành công!")
            return redirect("employee_list")

        messages.error(request, "Thông tin nhân viên không hợp lệ.", extra_tags="invalid_info_error")

    context = {
        "employee": employee,
        "form": form,
    }
    return render(request, "employees/employee_edit.html", context)
