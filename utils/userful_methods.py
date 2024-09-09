from enum import Enum
import re
from decimal import Decimal

def instance_exists(instance):
    return instance.__class__.objects.filter(pk=instance.pk).exists()

class IdType(Enum):
    OFFICE = 1
    STAFF = 2
    MEMBER = 3
    ACCOUNT = 4

def get_new_company_id(new_instance,id_type:IdType):

    last_instance = None
    new_instance_id = ''
    new_company_id =''

    if id_type==IdType.ACCOUNT:
        last_instance = new_instance.__class__.objects.filter(member=new_instance.member).order_by('-created_at').first()
    elif id_type == IdType.OFFICE:
        last_instance = new_instance.__class__.objects.filter(location=new_instance.location).order_by('-created_at').first()
    else:
        last_instance = new_instance.__class__.objects.filter(user_type="staff" if id_type==IdType.STAFF else "member").exclude(is_superuser=True).order_by('-date_joined').first()

    if last_instance:
        last_instance_id = int(re.findall(r'[0-9]+',last_instance.company_id.split('-').pop()).pop())
        new_instance_id = str(last_instance_id+1)
    else :
        new_instance_id = "1"

    user_initial = "S" if id_type==IdType.STAFF else "M"  
        
    if id_type==IdType.ACCOUNT:
        new_company_id = new_instance.member.company_id+"-"+new_instance_id.zfill(2)
    elif id_type == IdType.OFFICE:
        new_company_id = new_instance.location.code+new_instance_id.zfill(3)
    else:
        new_company_id = new_instance.office.company_id+"-"+user_initial+new_instance_id.zfill(2 if id_type==IdType.STAFF else 5)

    return new_company_id


# TODO : A EXECUTER AVANT D'ENREGISTRER LE COMPTE
def create_pairing_bonuses(new_member_account, upline, position:str):
   
    if upline :
        from prices.models import Matching
        from config.models import MatchingPrice

        upline_direct_downlines = upline.get_children()

        new_downline_side_direct_downline = upline_direct_downlines.filter(position=position).first()
        opposite_direct_downline = upline_direct_downlines.filter(position="left" if position=="right" else "right").first()

        new_downline_leg_length = new_downline_side_direct_downline.get_descendants(include_self=True).count() if new_downline_side_direct_downline else 0 #new_downline_side_direct_downline.get_descendant_count() + 1 
        opposite_leg_lenght = opposite_direct_downline.get_descendants(include_self=True).count() if opposite_direct_downline else 0 #opposite_direct_downline.get_descendant_count() + 1
    
        if new_downline_leg_length < opposite_leg_lenght:
            pairing_downline = list(opposite_direct_downline.get_descendants(include_self=True))[new_downline_leg_length]

            matchings_count = upline.matchings_count + 1
            # matchings_count = Matching.objects.filter(grantee=upline).count() + 1
            matching_price = MatchingPrice.objects.filter(begin__lte=matchings_count,end__gte=matchings_count).first()
            amount = new_member_account.package.price * matching_price.package_price_percent

            matching =  Matching.objects.create(
                grantee = upline,
                amount = amount 
            )

            matching.downlines.set([new_member_account,pairing_downline])
            upline.matchings_count = matchings_count
            upline.save()
    
        create_pairing_bonuses(new_member_account,upline=upline.parent,position=upline.position)



def on_office_save(instance):

    if instance.company_id == '' and instance.location:
        instance.company_id = get_new_company_id(instance,IdType.OFFICE)
        

def on_user_save(instance):

    if instance.company_id == '' and instance.office:
        instance.company_id = get_new_company_id(instance,IdType.STAFF if instance.user_type=="staff" else IdType.MEMBER)


def on_account_save(instance):

    if instance.company_id == '' and instance.member:
        instance.company_id =  get_new_company_id(instance, IdType.ACCOUNT)

    if not instance_exists(instance):

        if instance.referral_account and instance.parent:

            from prices.models import Referral

            Referral.objects.create(
            grantee = instance.referral_account,
                downline=instance,
                amount=instance.package.price*Decimal('0.2') # 20% du prix du package
            )

            if instance.parent.get_children().filter(position="left").exists():
                instance.position = "right"

        create_pairing_bonuses(instance,instance.parent,instance.position)



    