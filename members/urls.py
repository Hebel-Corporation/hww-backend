from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from authentication.views import CustomUserViewSet

router = DefaultRouter()
router.register('',CustomUserViewSet, basename="users")
router.register('offices', OfficeViewSet, basename="offices")
router.register('packages', PackageViewSet, basename="packages")
router.register('subscriptions', SubscriptionViewSet, basename="subscriptions")
router.register('coutries', CountryViewSet, basename='countries')
router.register('locations', LocationViewSet, basename='locations')



urlpatterns = [
    path('', include(router.urls)),
]
