from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('referrals', ReferralViewSet, basename="referrals")
router.register('matchings', MatchingViewSet, basename="matchings")


urlpatterns = [
    path('', include(router.urls)),
]
