from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaxiViewSet, RideViewSet

router = DefaultRouter()
router.register(r'taxis', TaxiViewSet, basename='taxi')
router.register(r'rides', RideViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
