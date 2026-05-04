from django import forms

from .models import NhanVien
from apps.branches.models import ChiNhanh


class EmployeeBaseForm(forms.ModelForm):
    class Meta:
        model = NhanVien
        fields = [
            "ma_nv",
            "anh_dai_dien",
            "ho_ten",
            "gioi_tinh",
            "ngay_sinh",
            "cccd",
            "sdt",
            "tk_ngan_hang",
            "chuc_vu",
            "ma_chi_nhanh",
            "dia_chi",
        ]
        widgets = {
            "ma_nv": forms.TextInput(attrs={"placeholder": "Tự động sinh"}),
            "anh_dai_dien": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "ho_ten": forms.TextInput(attrs={"placeholder": "Nhập họ tên"}),
            "ngay_sinh": forms.DateInput(attrs={"type": "date"}),
            "cccd": forms.TextInput(attrs={"placeholder": "Nhập CCCD"}),
            "sdt": forms.TextInput(attrs={"placeholder": "Nhập số điện thoại"}),
            "tk_ngan_hang": forms.TextInput(attrs={"placeholder": "Nhập tài khoản ngân hàng"}),
            "dia_chi": forms.Textarea(attrs={"placeholder": "Nhập địa chỉ", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Override ma_chi_nhanh field to filter only active branches
        self.fields['ma_chi_nhanh'].queryset = ChiNhanh.objects.filter(trang_thai='active')
        
        for field_name, field in self.fields.items():
            widget = field.widget
            css_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{css_class} form-control".strip()

            # Add required attribute to required fields
            if field.required and field_name not in ["ma_nv", "anh_dai_dien", "dia_chi"]:
                widget.attrs["required"] = "required"

            if field_name == "gioi_tinh":
                field.empty_label = "Chọn giới tính"
            elif field_name == "chuc_vu":
                field.empty_label = "Chọn chức vụ"
            elif isinstance(field, forms.ModelChoiceField):
                field.empty_label = f"Chọn {field.label.lower()}"
            elif isinstance(widget, forms.Select):
                current_choices = list(field.choices)
                placeholder_text = f"Chọn {field.label.lower()}"
                if field_name == "gioi_tinh":
                    placeholder_text = "Chọn giới tính"
                elif field_name == "chuc_vu":
                    placeholder_text = "Chọn chức vụ"

                if current_choices and current_choices[0][0] != "":
                    field.choices = [("", placeholder_text), *current_choices]

        if "ma_nv" in self.fields:
            self.fields["ma_nv"].required = False
            self.fields["ma_nv"].widget.attrs["readonly"] = True

        if "anh_dai_dien" in self.fields:
            self.fields["anh_dai_dien"].required = False
            self.fields["anh_dai_dien"].widget.attrs["class"] = "employee-avatar-input"


class EmployeeCreateForm(EmployeeBaseForm):
    pass


class EmployeeUpdateForm(EmployeeBaseForm):
    class Meta(EmployeeBaseForm.Meta):
        fields = [
            "anh_dai_dien",
            "ho_ten",
            "gioi_tinh",
            "ngay_sinh",
            "cccd",
            "sdt",
            "tk_ngan_hang",
            "chuc_vu",
            "ma_chi_nhanh",
            "dia_chi",
        ]
