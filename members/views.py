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
        staff.save()

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


    def get_account_by_company_id(self, request):

        company_id = request.query_params.get('company_id', None)

        if company_id is None:
            return Response({'error': 'ID de la compangie requis.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = Account.objects.get(company_id=company_id)
        except Account.DoesNotExist:
            return Response({'error': 'Le compte associé a l\'ID renseigné n\'a pas été trouvé.'}, status=status.HTTP_404_NOT_FOUND)
        
        return instance
    

    @action(detail=False, methods=['get'])
    def get_by_company_id(self,request):
        
        instance = self.get_account_by_company_id(request=request)

        if type(instance) is Response:
            return instance

        return Response({"account_id":instance.id},status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['get'])
    def sponsor_is_valid(self,request):
        
        referral_id = request.query_params.get('referral_id', None)

        instance = self.get_account_by_company_id(request=request)
        if type(instance) is Response:
            return instance
        

        sponsor_account = instance

        if(sponsor_account.get_children().count()>1):
            return Response({'error': 'Le sponsor a déjà deux downlines.'}, status=status.HTTP_400_BAD_REQUEST)
        

        referral_account = Account.objects.get(id=referral_id)
        if not referral_account.get_descendants(include_self=True).filter(id=sponsor_account.id).exists():
           return Response({'error': 'Le sponsor et le parrain sont dans des réseaux differents.'}, status=status.HTTP_400_BAD_REQUEST) 

        return Response({"sponsor_account_id":sponsor_account.id},status=status.HTTP_200_OK)
    

    @action(detail=False,methods=['post'])
    def create_member(self,request):

        member_data = request.data.get('member')
        sponsor_account_id = request.data.get('sponsor_account')
        referral_account_id = request.data.get('referral_account')
        package_id = request.data.get('package')

        member_serialiser = CustomUserSerializer(data=member_data)
        if not member_serialiser.is_valid():
            return Response(member_serialiser.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # member = CustomUser.objects.create_user(**member_data)
        office = request.user.office
        # member.office = office
        # member.save()


        sponsor_account = Account.objects.get(id=sponsor_account_id)
        referral_account = Account.objects.get(id=referral_account_id)
        package = Package.objects.get(id=package_id)

        # account = Account.objects.create(
        #     member=member,
        #     # company_id = "",
        #     package = package,
        #     referral_account = referral_account,
        #     parent = sponsor_account,

        # )

        # return Response({"data":AccountSerializer(account).data},status=status.HTTP_201_CREATED)
        return Response()
    
    @action(detail=False,methods=["get"])
    def test(self,request):

        import re
        from enum import Enum

        class IdType(Enum):
            OFFICE = 1
            STAFF = 2
            MEMBER = 3
            ACCOUNT = 4

        def get_new_company_id(id_type:IdType,office=None,member=None):

            last_instance = None
            new_company_id =''

            if(id_type==IdType.ACCOUNT):
                last_instance = Account.objects.filter(member=member).order_by('-created_at').first()
            else:
                last_instance = CustomUser.objects.filter(user_type="staff" if id_type==IdType.STAFF else "member").order_by('-date_joined').first()
            
            user_initial = "S" if id_type==IdType.STAFF else "M"  

            if last_instance:
            
                last_instance_id = int(re.findall(r'[0-9]+',last_instance.company_id.split('-').pop()).pop())
                
                if id_type==IdType.ACCOUNT:
                    new_company_id = member.company_id+"-"+str(last_instance_id+1).zfill(2)
                else:
                    new_company_id = office.company_id+"-"+user_initial+str(last_instance_id+1).zfill(5)
            else:

                if id_type==IdType.ACCOUNT:
                    new_company_id = member.company_id+"-"+"1".zfill(2)
                else:
                    new_company_id = office.company_id+"-"+user_initial+"1".zfill(5)

            return new_company_id


        member = CustomUser.objects.filter(user_type="member").first()
        print("=======>",get_new_company_id(IdType.ACCOUNT,member=member))

        return Response()



class SubscriptionViewSet(viewsets.ModelViewSet) :
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]