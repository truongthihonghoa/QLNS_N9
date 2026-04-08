from django.urls import path
from . import views
app_name = 'branches'
urlpatterns = [

    path('admin/', views.branch_list, name='branch_admin'),
    path('', views.branch_list, name='branch_list'),
    path('detail/<str:pk>/', views.branch_detail, name='branch_detail'),
    path('create/', views.branch_create, name='branch_create'),
    path('edit/<str:pk>/', views.branch_update, name='branch_update'),
    path('delete/<str:pk>/', views.branch_delete, name='branch_delete'),
]
