from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from members.models import *
from .serializers import *
from authentication.models import CustomUser


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

    def create(self, request):
    
        office_data = request.data.get('office')
        staffs_ids_data = request.data.get('staffs_ids',[])


        office_serializer = OfficeSerializer(data=office_data)
        if not office_serializer.is_valid():
            return Response(office_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        staffs = CustomUser.objects.filter(id__in=staffs_ids_data, user_type='staff')
        if len(staffs) != len(staffs_ids_data):
            return Response({'error': 'Présence d\'un staff invalide ou utilisateur non staff.'}, status=status.HTTP_400_BAD_REQUEST)


        office = office_serializer.save()

        staffs.update(office=office)

        return Response(office_serializer.data, status=status.HTTP_201_CREATED)



class PackageViewSet(viewsets.ModelViewSet) :
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]



class AccountViewSet(viewsets.ModelViewSet) :
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]



class SubscriptionViewSet(viewsets.ModelViewSet) :
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]