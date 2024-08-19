from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
# router.register('offices', OfficeViewSet, basename="offices")
# router.register('packages', PackageViewSet, basename="packages")
# router.register('members', MemberViewSet, basename="members")
# router.register('accounts', AccountViewSet, basename="accounts")
# router.register('subscriptions', SubscriptionViewSet, basename="subscriptions")


urlpatterns = [
    path('', include(router.urls))
]
