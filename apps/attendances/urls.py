from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_list_view, name='attendance_list'),
path('check/', views.check_in_out_view, name='check_in_out'),
]

