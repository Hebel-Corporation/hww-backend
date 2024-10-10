import random
from django.conf import settings


def generate_subcription_code() -> str :

    leters = "abcdefghijklmnopkrstuvwxyz"
    numbers = "0123456789"

    use_for = leters + leters.upper() + numbers
    length_for_pass = 10

    return "".join(random.sample(use_for, length_for_pass))




"""
    This method is an utility function that help creating an Account instance
    related to referral, sponsor and the owner member.

    It takes 3 params [referral, sponsor and member]
"""
def create_account(referral, sponsor, member, office, package_id):
    from members.models import Account, Package
    from config.models import SubscriptionCode
    account_position = None
    if sponsor :
        account_position = 'left' if sponsor.get_children().count() < 1 else 'right'

    package = None
    if package_id :
        try :
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist :
            raise ValueError(f"Il n'existe pas de paquet avec l'ID {package_id}.")
    else :
        package = Package.objects.filter(is_default=True).first() 

    try :
        subscription_code = SubscriptionCode.objects.filter(office=office, package=package, is_valid=True).order_by('created_at').first()
    except SubscriptionCode.DoesNotExist :
        raise ValueError(f"Vous avez pas de codes d'enregistrement valides pour ce paquet enfin d'enregistrer ce compte.")

    account = Account(
        member=member,
        office = office,
        company_id = f"{member.company_id}-{settings.ACCOUNT_COMPANY_ID_INITIAL}{member.accounts.count()+1}",
        referral_account = referral,
        parent = sponsor,
        position = account_position,
        pvs=subscription_code.package.price
    )
    account.save(subscription_code=subscription_code) # Transfer [package] instance in account save method

    return account





# TODO : A EXECUTER AVANT D'ENREGISTRER LE COMPTE
def create_pairing_bonuses(new_member_account, upline, position:str):
   
    if upline :
        from prices.models import Matching
        from config.models import MatchingPrice

        # Increase upline PVs
        upline.pvs += new_member_account.pvs
        upline.save()

        # Get upline direct children
        upline_direct_downlines = upline.get_children()

        new_downline_side_direct_downline = upline_direct_downlines.filter(position=position).first()
        opposite_direct_downline = upline_direct_downlines.filter(position="left" if position=="right" else "right").first()

        new_downline_leg_length = new_downline_side_direct_downline.get_descendants(include_self=True).count() if new_downline_side_direct_downline else 0 #new_downline_side_direct_downline.get_descendant_count() + 1 
        opposite_leg_lenght = opposite_direct_downline.get_descendants(include_self=True).count() if opposite_direct_downline else 0 #opposite_direct_downline.get_descendant_count() + 1
    
        if new_downline_leg_length - 1 < opposite_leg_lenght:

            pairing_downline = list(opposite_direct_downline.get_descendants(include_self=True)).order_by('created_at')[new_downline_leg_length-1]

            if not upline.has_already_a_matched(new_member_account) and not upline.has_already_a_matched(pairing_downline) :
                from django.shortcuts import get_object_or_404
                from members.models import Subscription

                matchings_count = upline.get_matching_count + 1
                matching_price = MatchingPrice.objects.filter(begin__lte=matchings_count,end__gte=matchings_count).first()
                new_account_subscription = get_object_or_404(Subscription, member_account=new_member_account)
                amount = new_account_subscription.package.price * matching_price.package_price_percent

                matching =  Matching.objects.create(
                    grantee = upline,
                    amount = amount 
                )

                matching.downlines.set([new_member_account,pairing_downline])
                matching.save()
    
        create_pairing_bonuses(new_member_account,upline=upline.parent,position=upline.position)


