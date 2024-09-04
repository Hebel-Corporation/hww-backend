from django.urls import path, include
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import CustomTokenObtainPairView, CustomGroupViewSet

router = DefaultRouter()
router.register('groups', CustomGroupViewSet, basename="user_groups")

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', include(router.urls))
]