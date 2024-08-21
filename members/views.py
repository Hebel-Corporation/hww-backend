from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from members.models import *
from .serializers import *
from authentication.serializers import CustomUserSerializer
from authentication.models import CustomUser
from django.contrib.auth.models import Group


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
        staff_data = request.data.get('staff')


        office_serializer = OfficeSerializer(data=office_data)
        if not office_serializer.is_valid():
            return Response(office_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        staff_serializer = CustomUserSerializer(data=staff_data)
        if not staff_serializer.is_valid():
            return Response(staff_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if not staff_data.get("user_type")=="staff":
            return Response({"error:":"L'utilisateur doit etre un staff"}, status=status.HTTP_400_BAD_REQUEST)
        
        staff_groups = Group.objects.filter(id__in=staff_data.get("groups"))
        if len(staff_groups) != len(staff_data.get("groups")):
            return Response({'error': 'Présence d\'un groupe d\'utilisateur invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        
        staff_data.pop("groups")


        office = office_serializer.save()

        staff = CustomUser.objects.create_user(**staff_data)
        staff.groups.set(staff_groups)
        staff.office=office
        staff.save

        return Response({"office":office_serializer.data,"staff":CustomUserSerializer(staff).data},
                         status=status.HTTP_201_CREATED)
    
    
    
    @action(detail=False, methods=['post'], url_path='assign_staff')
    def assign_staff():

        return Response()



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