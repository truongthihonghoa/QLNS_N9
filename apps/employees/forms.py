from django import forms

from .models import NhanVien


class EmployeeBaseForm(forms.ModelForm):
    class Meta:
        model = NhanVien
        fields = [
            "ma_nv",
            "ho_ten",
            "gioi_tinh",
            "ngay_sinh",
            "cccd",
            "sdt",
            "tk_ngan_hang",
            "chuc_vu",
            "vi_tri_vl",
            "ma_chi_nhanh",
            "dia_chi",
        ]
        widgets = {
            "ma_nv": forms.TextInput(attrs={"placeholder": "Nhập mã nhân viên"}),
            "ho_ten": forms.TextInput(attrs={"placeholder": "Nhập họ tên"}),
            "ngay_sinh": forms.DateInput(attrs={"type": "date"}),
            "cccd": forms.TextInput(attrs={"placeholder": "Nhập CCCD"}),
            "sdt": forms.TextInput(attrs={"placeholder": "Nhập số điện thoại"}),
            "tk_ngan_hang": forms.TextInput(attrs={"placeholder": "Nhập tài khoản ngân hàng"}),
            "dia_chi": forms.Textarea(attrs={"placeholder": "Nhập địa chỉ", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            widget = field.widget
            css_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{css_class} form-control".strip()

            if isinstance(field, forms.ModelChoiceField):
                field.empty_label = f"Chọn {field.label.lower()}"
            elif isinstance(widget, forms.Select):
                current_choices = list(field.choices)
                if current_choices and current_choices[0][0] != "":
                    field.choices = [("", f"Chọn {field.label.lower()}"), *current_choices]


class EmployeeCreateForm(EmployeeBaseForm):
    pass


class EmployeeUpdateForm(EmployeeBaseForm):
    class Meta(EmployeeBaseForm.Meta):
        fields = [
            "ho_ten",
            "gioi_tinh",
            "ngay_sinh",
            "cccd",
            "sdt",
            "tk_ngan_hang",
            "chuc_vu",
            "vi_tri_vl",
            "ma_chi_nhanh",
            "dia_chi",
        ]
