
from django.urls import path
from . import views
from django.views.generic import RedirectView
app_name = 'accounts'
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('dashboard/', views.dashboard_view, name='dashboard'),
    path("", RedirectView.as_view(pattern_name="login", permanent=False)),
    path('change-password/', views.change_password_view, name='change_password'),
    path('employee/', views.account_employee_list_view, name='account_employee_list'),
    path('admin/', views.account_admin_list_view, name='account_admin_list'),
    path('admin/add/', views.add_admin_account, name='add_admin_account'),
    path('admin/edit/', views.edit_admin_account, name='edit_admin_account'),
    path('admin/delete/', views.delete_admin_account, name='delete_admin_account'),
    path('admin/password/', views.get_admin_password, name='get_admin_password'),
]
