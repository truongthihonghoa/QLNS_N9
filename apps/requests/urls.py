from django.urls import path
from . import views

urlpatterns = [
    path('', views.request_list_view, name='request_list'),
    path('approval/', views.request_approval_view, name='request_approval'),
    path('review/', views.request_review_list_view, name='request_review_list'),
    path('approve/<str:ma_dk>/', views.approve_request, name='approve_request'),
    path('reject/<str:ma_dk>/', views.reject_request, name='reject_request'),
    path('submit-api/', views.api_submit_request, name='api_submit_request'),
]