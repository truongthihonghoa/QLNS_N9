from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    
    # Dashboard cho Admin và Quản lý
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/manager/', views.manager_dashboard_view, name='manager_dashboard'),
    
    # Quản lý tài khoản
    path('employee/', views.account_employee_list_view, name='account_employee_list'),
    path('admin/', views.account_admin_list_view, name='account_admin_list'),
]
