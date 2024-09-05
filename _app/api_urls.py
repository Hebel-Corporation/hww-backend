from django.urls import path, include


urlpatterns = [
    path('prices/',include('prices.urls')),
    path('members/', include('members.urls')),
    path('auth/', include('authentication.urls')),
]