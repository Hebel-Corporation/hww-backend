# from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated
# from members.models import *
# from .serializers import *


class CountryViewSet(viewsets.ModelViewSet) :
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]



class LocationViewSet(viewsets.ModelViewSet) :
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]



class OfficeViewSet(viewsets.ModelViewSet) :
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated]



# class PackageViewSet(viewsets.ModelViewSet) :
#     queryset = Package.objects.all()
#     serializer_class = PackageSerializer
#     permission_classes = [IsAuthenticated]



class AccountViewSet(viewsets.ModelViewSet) :
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]



# class SubscriptionViewSet(viewsets.ModelViewSet) :
#     queryset = Subscription.objects.all()
#     serializer_class = SubscriptionSerializer
#     permission_classes = [IsAuthenticated]