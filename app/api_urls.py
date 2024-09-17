from django.urls import path, include


urlpatterns = [
    path('members/', include('members.urls')),
    path('auth/', include('authentication.urls')),
]