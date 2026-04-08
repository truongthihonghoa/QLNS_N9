from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChiNhanhViewSet

router = DefaultRouter()
router.register(r'branches', ChiNhanhViewSet)

urlpatterns = [
    path('', include(router.urls)),
]