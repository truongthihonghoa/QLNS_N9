from django.urls import path

from . import views


urlpatterns = [
    path('', views.payroll_list_view, name='payroll_list'),
    path('export/', views.payroll_export_view, name='payroll_export'),
    path('send/', views.payroll_send_view, name='payroll_send'),
    path('status/<str:ma_luong>/', views.payroll_update_status_view, name='payroll_update_status'),
    path('calc-info/', views.payroll_calc_info_view, name='payroll_calc_info'),
    path('period-employees/', views.payroll_period_employees_view, name='payroll_period_employees'),
    path('save/', views.payroll_save_view, name='payroll_save'),
    path('delete/<str:ma_luong>/', views.payroll_delete_view, name='payroll_delete'),
    path('calculate/', views.payroll_calculate_view, name='payroll_calculate'),
    path('add/', views.payroll_add_view, name='payroll_add'),
    path('edit/<str:ma_luong>/', views.payroll_edit_view, name='payroll_edit'),
    path('my-salary/', views.my_salary_view, name='my_salary'),
]
