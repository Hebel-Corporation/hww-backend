from enum import Enum
import re

class IdType(Enum):
    OFFICE = 1
    STAFF = 2
    MEMBER = 3
    ACCOUNT = 4

def get_new_company_id(id_type:IdType,location=None,office=None,member=None):

    from members.models import Office,Account
    from authentication.models import CustomUser

    last_instance = None
    new_company_id =''

    if id_type==IdType.ACCOUNT:
        last_instance = Account.objects.filter(member=member).order_by('-created_at').first()
    elif id_type == IdType.OFFICE:
        last_instance = Office.objects.filter(location=location).order_by('-created_at').first()
    else:
        last_instance = CustomUser.objects.filter(user_type="staff" if id_type==IdType.STAFF else "member").order_by('-date_joined').first()
    
    user_initial = "S" if id_type==IdType.STAFF else "M"  

    if last_instance:
    
        last_instance_id = int(re.findall(r'[0-9]+',last_instance.company_id.split('-').pop()).pop())
        
        if id_type==IdType.ACCOUNT:
            new_company_id = member.company_id+"-"+str(last_instance_id+1).zfill(2)
        elif id_type == IdType.OFFICE:
            new_company_id = location.code+str(last_instance_id+1).zfill(3)
        else:
            new_company_id = office.company_id+"-"+user_initial+str(last_instance_id+1).zfill(2 if id_type==IdType.STAFF else 5)
    else:

        if id_type==IdType.ACCOUNT:
            new_company_id = member.company_id+"-"+"1".zfill(2)
        elif id_type == IdType.OFFICE:
            new_company_id = location.code+"1".zfill(3)
        else:
            new_company_id = office.company_id+"-"+user_initial+"1".zfill(5)

    return new_company_id