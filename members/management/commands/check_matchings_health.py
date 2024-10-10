from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from prices.models import Matching
from members.models import Account, Subscription
from config.models import MatchingPrice


class Command(BaseCommand):
    help = 'Affiche un message de bienvenue'

    def handle(self, *args, **kwargs):
        
        accounts = Account.objects.all()

        for upline_account in accounts :
            children = upline_account.get_children().order_by('created_at')
            if children.count() == 2 :
                left_account, right_account = children

                left_network = left_account.get_descendants(include_self=True).order_by('created_at')
                right_network = right_account.get_descendants(include_self=True).order_by('created_at')

                for left_downline, right_downline in zip(left_network, right_network):
                    if not upline_account.has_already_a_matched(left_downline) and not upline_account.has_already_a_matched(right_downline) :

                        matchings_count = upline_account.get_matching_count + 1
                        matching_price = MatchingPrice.objects.filter(begin__lte=matchings_count,end__gte=matchings_count).first()
                        new_account_subscription = get_object_or_404(Subscription, member_account=left_downline)
                        amount = new_account_subscription.package.price * matching_price.package_price_percent

                        matching =  Matching.objects.create(
                            grantee = upline_account,
                            amount = amount 
                        )

                        matching.downlines.set([left_downline,right_downline])
                        matching.save()

        self.stdout.write("vérification terminée !")
