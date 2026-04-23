from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list_view, name='employee_list'),
    path('add/', views.employee_add_view, name='employee_add'),
    path('api/next-id/', views.api_next_employee_id, name='api_next_employee_id'),
    path('<str:employee_id>/', views.employee_detail_view, name='employee_detail'),
    path('<str:employee_id>/edit/', views.employee_edit_view, name='employee_edit'),
]
