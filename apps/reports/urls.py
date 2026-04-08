from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list_view, name='report_list'),
    path('api/aggregate/', views.api_aggregate_data, name='api_aggregate'),
    path('api/save/', views.api_save_report, name='api_save'),
    path('api/get/<str:ma_bc>/', views.api_get_report_details, name='api_get_details'),
]
