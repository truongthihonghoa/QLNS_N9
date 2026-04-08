from django import forms
from django.db.models import Q

from .models import ChiNhanh
from ..employees.models import NhanVien


class ChiNhanhForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ma_nv_ql points to employees.NhanVien, but we only want employees who have an
        # account (TaiKhoan -> User) with staff/superuser privileges.
        self.fields['ma_nv_ql'].queryset = (
            NhanVien.objects.filter(Q(taikhoan__user__is_staff=True) | Q(taikhoan__user__is_superuser=True))
            .order_by('ma_nv')
        )

    class Meta:
        model = ChiNhanh
        fields = ['ten_chi_nhanh', 'dia_chi', 'sdt', 'ma_nv_ql', 'trang_thai']
        widgets = {
            'ten_chi_nhanh': forms.TextInput(),
            'dia_chi': forms.TextInput(),
            'sdt': forms.TextInput(),
            'ma_nv_ql': forms.Select(),
            'trang_thai': forms.Select(),
        }

