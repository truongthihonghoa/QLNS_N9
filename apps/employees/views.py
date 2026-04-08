from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import EmployeeCreateForm, EmployeeUpdateForm
from .models import NhanVien


CARD_THEMES = (
    "theme-emerald",
    "theme-royal",
    "theme-amber",
    "theme-rose",
)


def get_next_employee_id():
    last_employee = NhanVien.objects.order_by("-ma_nv").first()
    if last_employee and last_employee.ma_nv:
        try:
            import re

            match = re.search(r"\d+", last_employee.ma_nv)
            if match:
                next_num = int(match.group()) + 1
            else:
                next_num = 1
        except (ValueError, AttributeError):
            next_num = 1
    else:
        next_num = 1

    return f"NV{next_num:05d}"


def api_next_employee_id(request):
    if request.method == "GET":
        return JsonResponse({"next_id": get_next_employee_id()})
    return JsonResponse({"error": "Invalid method"}, status=400)


def _build_employee_cards(queryset):
    cards = []
    for index, employee in enumerate(queryset):
        words = [part for part in employee.ho_ten.split() if part]
        initials = "".join(word[0] for word in words[:2]).upper() if words else "NV"

        detail_url = "#"
        if employee.ma_nv:
            try:
                detail_url = reverse("employee_detail", kwargs={"employee_id": employee.ma_nv})
            except Exception:
                pass

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
                "chi_nhanh": employee.ma_chi_nhanh,
                "dia_chi": employee.dia_chi,
                "detail_url": detail_url,
                "initials": initials,
                "theme_class": CARD_THEMES[index % len(CARD_THEMES)],
                "image_url": employee.anh_dai_dien.url if employee.anh_dai_dien else "",
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
            | Q(ma_chi_nhanh__ten_chi_nhanh__icontains=search_query)
        )

    context = {
        "employee_cards": _build_employee_cards(employees),
        "search_query": search_query,
        "employee_count": employees.count(),
    }
    return render(request, "employees/employee_list.html", context)


def employee_add_view(request):
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            if not employee.ma_nv:
                employee.ma_nv = get_next_employee_id()
            employee.save()
            messages.success(request, "Thêm nhân viên mới thành công!")
            return redirect("employee_list")

        messages.error(request, "Thông tin nhân viên không hợp lệ.", extra_tags="invalid_info_error")
    else:
        form = EmployeeCreateForm(initial={"ma_nv": get_next_employee_id()})

    return render(request, "employees/employee_add.html", {"form": form})


def employee_detail_view(request, employee_id):
    employee = get_object_or_404(
        NhanVien.objects.select_related("ma_chi_nhanh", "ma_chi_nhanh__ma_nv_ql"),
        pk=employee_id,
    )
    manager = employee.ma_chi_nhanh.ma_nv_ql if employee.ma_chi_nhanh else None
    words = [part for part in employee.ho_ten.split() if part]
    context = {
        "employee": employee,
        "manager_name": manager.ho_ten if manager else "",
        "initials": "".join(word[0] for word in words[:2]).upper() if words else "NV",
        "image_url": employee.anh_dai_dien.url if employee.anh_dai_dien else "",
    }
    return render(request, "employees/employee_detail.html", context)


def employee_edit_view(request, employee_id):
    employee = get_object_or_404(NhanVien, pk=employee_id)
    form = EmployeeUpdateForm(request.POST or None, request.FILES or None, instance=employee)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật thông tin nhân viên thành công")
            return redirect("employee_detail", employee_id=employee.ma_nv)

        messages.error(request, "Thông tin nhân viên không hợp lệ.", extra_tags="invalid_info_error")

    context = {
        "employee": employee,
        "form": form,
        "image_url": employee.anh_dai_dien.url if employee.anh_dai_dien else "",
    }
    return render(request, "employees/employee_edit.html", context)
