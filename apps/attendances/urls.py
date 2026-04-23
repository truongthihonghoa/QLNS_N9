from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_list_view, name='attendance_list'),
]

