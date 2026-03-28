from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list_view, name='employee_list'),
    path('add/', views.employee_add_view, name='employee_add'),
    path('<str:employee_id>/', views.employee_detail_view, name='employee_detail'),
    path('<str:employee_id>/edit/', views.employee_edit_view, name='employee_edit'),
]
