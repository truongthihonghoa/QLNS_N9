from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class LoginForm(forms.Form):
    """Login form with custom validation"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'id': 'username',
            'name': 'username',
            'required': True,
            'placeholder': 'Nhập tên đăng nhập'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'password',
            'name': 'password',
            'required': True,
            'placeholder': 'Nhập mật khẩu'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Check if username exists
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise ValidationError({
                    'username': 'Tên đăng nhập không hợp lệ'
                })

            # Authenticate user
            user = authenticate(username=username, password=password)
            if user is None:
                raise ValidationError({
                    'password': 'Mật khẩu không hợp lệ'
                })

            cleaned_data['user'] = user

        return cleaned_data


class ChangePasswordForm(forms.Form):
    """Change password form with comprehensive validation"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'id': 'change-username',
            'name': 'username',
            'required': True,
            'placeholder': 'Nhập tên đăng nhập'
        })
    )
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'old-password',
            'name': 'old_password',
            'required': True,
            'placeholder': 'Nhập mật khẩu hiện tại'
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'new-password',
            'name': 'new_password',
            'required': True,
            'placeholder': 'Nhập mật khẩu mới'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'confirm-password',
            'name': 'confirm_password',
            'required': True,
            'placeholder': 'Nhập lại mật khẩu mới'
        })
    )

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('Vui lòng nhập tên đăng nhập')

        # Verify username matches current user
        if self.user and username != self.user.username:
            raise ValidationError('Tên đăng nhập sai. Vui lòng thử lại')

        return username

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not old_password:
            raise ValidationError('Vui lòng nhập mật khẩu')

        # Verify old password is correct
        if self.user and not self.user.check_password(old_password):
            raise ValidationError('Mật khẩu sai. Vui lòng thử lại')

        return old_password

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        old_password = self.cleaned_data.get('old_password')

        if not new_password:
            raise ValidationError('Vui lòng nhập mật khẩu mới')

        # Check if new password is same as old password
        if old_password and new_password == old_password:
            raise ValidationError('Mật khẩu không hợp lệ, yêu cầu nhập lại')

        return new_password

    def clean_confirm_password(self):
        confirm_password = self.cleaned_data.get('confirm_password')
        new_password = self.cleaned_data.get('new_password')

        if not confirm_password:
            raise ValidationError('Vui lòng nhập lại mật khẩu')

        return confirm_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        # Check if passwords match
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError({
                'confirm_password': 'Mật khẩu mới không khớp, yêu cầu nhập lại'
            })

        return cleaned_data

    def save(self):
        """Save the new password"""
        if self.user:
            self.user.set_password(self.cleaned_data['new_password'])
            self.user.save()
        return self.user