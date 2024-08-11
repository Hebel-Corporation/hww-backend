from django.urls import path, include


urlpatterns = [
    path('', include('members.urls')),
    path('auth/', include('authentication.urls')),
]