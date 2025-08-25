import random
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


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
        if sponsor.get_children().count() == 2 :
            raise ValueError(f"Le membre {sponsor.company_id} a deja 2 enfants.")

    package = None
    if package_id :
        try :
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist :
            raise ValueError(f"Il n'existe pas de paquet avec l'ID {package_id}.")
    else :
        package = Package.objects.filter(is_default=True).first() 

    subscription_code = None
    try :
        subscription_code = SubscriptionCode.objects.filter(office=office, package=package, is_valid=True).order_by('created_at').first()
    except SubscriptionCode.DoesNotExist :
        raise ValueError(f"Vous avez pas de codes d'enregistrement valides pour ce paquet enfin d'enregistrer ce compte.")

    account = Account(
        office = office,
        referral_account = referral,
        parent = sponsor,
        member = member,
        company_id = f"{member.company_id}-{settings.ACCOUNT_COMPANY_ID_INITIAL}{member.accounts.count()+1}",
        position = account_position
    )
    
    account.save(subscription_code=subscription_code) # Transfer [package] instance in account save method
    
    return account






# A EXECUTER AVANT D'ENREGISTRER LE COMPTE
def create_pairing_bonuses(new_member_account, upline, position:str):
   
    if upline :
        from prices.models import Matching
        from config.models import MatchingPrice

        # Get upline direct children
        upline_direct_downlines = upline.get_children()

        new_downline_side_direct_downline = upline_direct_downlines.filter(position=position).first()
        opposite_direct_downline = upline_direct_downlines.filter(position="left" if position=="right" else "right").first()

        new_downline_leg_length = new_downline_side_direct_downline.get_descendants(include_self=True).count() if new_downline_side_direct_downline else 0 #new_downline_side_direct_downline.get_descendant_count() + 1 
        opposite_leg_lenght = opposite_direct_downline.get_descendants(include_self=True).count() if opposite_direct_downline else 0 #opposite_direct_downline.get_descendant_count() + 1
    
        if new_downline_leg_length - 1 < opposite_leg_lenght and upline.get_referral_count > 0:

            pairing_downline = list(opposite_direct_downline.get_descendants(include_self=True).order_by('created_at'))[new_downline_leg_length-1]

            if not upline.has_already_a_matched(new_member_account) and not upline.has_already_a_matched(pairing_downline) :
                from django.shortcuts import get_object_or_404
                from members.models import Subscription

                matchings_count = upline.get_matching_count + 1
                matching_price = MatchingPrice.objects.filter(begin__lte=matchings_count,end__gte=matchings_count).first()
                new_account_subscription = get_object_or_404(Subscription, member_account=new_member_account)
                amount = new_account_subscription.package.price * matching_price.package_price_percent

                matching =  Matching.objects.create(
                    grantee = upline,
                    amount = amount,
                    office = new_member_account.office,
                    is_validated = upline.get_daily_matching_count() < matching_price.daily_max_matching
                )

                matching.downlines.set([new_member_account,pairing_downline])
                matching.save()

                # Check if the member qualifies for a reward after creating a matching for him.
                check_all_rewards(upline)
                check_all_promotions(upline)
    
        create_pairing_bonuses(new_member_account,upline=upline.parent,position=upline.position)





def has_paid_maintenance(account_instance) :
    return account_instance.payments.filter(type='maintenance').exists()




def get_period_filtered_bonus_queryset(queryset, period_filter):
    now = timezone.now()

    if period_filter == 'all' :
        queryset = queryset.all().order_by('-created_at')
    elif period_filter == 'daily' :
        queryset = queryset.filter(created_at__date=now.date()).order_by('-created_at')
    elif period_filter == 'weekly' :
        start_of_week = now - timedelta(days=now.weekday())
        queryset = queryset.filter(created_at__date__gte=start_of_week.date()).order_by('-created_at')
    elif period_filter == 'monthly' :
        queryset = queryset.filter(created_at__year=now.year, created_at__month=now.month).order_by('-created_at')

    return queryset




def check_all_rewards(account):
    """
    Attribue les récompenses permanentes à un membre (équilibres ou referrals)
    """
    from prices.models import Reward

    rewards = Reward.objects.filter(is_active=True).order_by('unit_number')

    for reward in rewards:
        if reward.unit_type == 'matching':
            count = account.get_matching_count
        elif reward.unit_type == 'referral':
            count = account.get_referral_count


        if count >= reward.unit_number:
            if reward not in account.rewards.all():
                account.rewards.add(reward)




def check_all_promotions(account):
    """
    Vérifie le palier de promotion atteint et assigne UNIQUEMENT le plus haut niveau.
    """
    from prices.models import Promotion, Matching, Referral

    now = timezone.now()
    promotion = Promotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).first()

    best_promo = None

    if promotion :
        for promoItem in promotion.promotionitem_set.all() :
            if promoItem.unit_type == 'matching':
                count = Matching.objects.filter(
                    grantee=account,
                    is_validated=True,
                    created_at__range=(promoItem.promotion.start_date, promoItem.promotion.end_date)
            ).count()
            elif promoItem.unit_type == 'referral':
                count = Referral.objects.filter(
                    grantee=account,
                    created_at__range=(promoItem.promotion.start_date, promoItem.promotion.end_date)
                ).count()
            else:
                continue

            if count >= promoItem.unit_number:
                best_promo = promoItem
                break  # Le premier qu’on trouve (car trié du plus haut au plus bas)

        if best_promo:
            # Enlever les anciennes promotions de cette période
            active_promos = account.promotions.filter(
                promotion__start_date__lte=now,
                promotion__end_date__gte=now,
                unit_type=best_promo.unit_type
            )

            for old in active_promos:
                if old != best_promo:
                    account.promotions.remove(old)

            # Ajouter seulement le palier le plus haut s’il n’y est pas
            if best_promo not in account.promotions.all():
                account.promotions.add(best_promo)