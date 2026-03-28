from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('employee/', views.account_employee_list_view, name='account_employee_list'),
    path('admin/', views.account_admin_list_view, name='account_admin_list'),
]
