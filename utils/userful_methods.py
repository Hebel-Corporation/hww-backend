from enum import Enum
import re

def instance_exists(instance):
    return instance.__class__.objects.filter(pk=instance.pk).exists()

class IdType(Enum):
    OFFICE = 1
    STAFF = 2
    MEMBER = 3
    ACCOUNT = 4

def get_new_company_id(new_instance,id_type:IdType):

    from members.models import Office,Account
    from authentication.models import CustomUser

    last_instance = None
    new_instance_id = ''
    new_company_id =''

    if id_type==IdType.ACCOUNT:
        last_instance = Account.objects.filter(member=new_instance.member).order_by('-created_at').first()
    elif id_type == IdType.OFFICE:
        last_instance = Office.objects.filter(location=new_instance.location).order_by('-created_at').first()
    else:
        last_instance = CustomUser.objects.filter(user_type="staff" if id_type==IdType.STAFF else "member").order_by('-date_joined').first()


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
# The argument should be the new member's account's sponsor
def create_pairing_bonuses(new_member_account, upline, position:str):

    from prices.models import Matching

    upline_direct_downlines = upline.get_children()
    new_downline_side_direct_downline = upline_direct_downlines.filter(position=position).first()
    opposite_direct_downline = upline_direct_downlines.filter(position="left" if position=="right" else "right").first()
    new_downline_leg_lenght = 0 if new_downline_side_direct_downline==None else new_downline_side_direct_downline.get_descendant_count() + 1
    opposite_leg_lenght = 0 if opposite_direct_downline==None else opposite_direct_downline.get_descendant_count() + 1

    
    if new_downline_leg_lenght < opposite_leg_lenght:
        pairing_downline = list(opposite_direct_downline.get_descendants(include_self=True))[new_downline_leg_lenght]

        matching =  Matching.objects.create(
            grantee = upline,
            amount=8
        )

        matching.downlines.set([new_member_account,pairing_downline])

    
    if upline.parent :
        create_pairing_bonuses(new_member_account,upline=upline.parent,position=upline.position)



def on_office_save(instance):

    if not instance_exists(instance):
        instance.company_id = get_new_company_id(instance,IdType.OFFICE)
        

def on_user_save(instance):

    if not instance_exists(instance):
        instance.company_id = get_new_company_id(instance,IdType.STAFF if instance.user_type=="staff" else IdType.MEMBER)


def on_account_save(instance):

    if not instance_exists(instance):
       
        if instance.parent.get_children().filter(position="left").exists():
            instance.position = "right"

        instance.company_id =  get_new_company_id(instance, IdType.ACCOUNT)

        create_pairing_bonuses(instance,instance.parent,instance.position)



    