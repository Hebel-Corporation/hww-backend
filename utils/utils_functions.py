import random


def generate_subcription_code() -> str :

    leters = "abcdefghijklmnopkrstuvwxyz"
    numbers = "0123456789"

    use_for = leters + leters.upper() + numbers
    length_for_pass = 10

    return "".join(random.sample(use_for, length_for_pass))



# TODO : A EXECUTER AVANT D'ENREGISTRER LE COMPTE
def create_pairing_bonuses(new_member_account, upline, position:str):

    print("======================", new_member_account, upline, position)
   
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


