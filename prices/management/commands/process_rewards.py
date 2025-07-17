from django.core.management.base import BaseCommand
from members.models import Account
from utils.utils_functions import check_all_rewards, check_all_promotions


class Command(BaseCommand):
    help = "Traite toutes les récompenses et promotions (matching et referral)"

    def handle(self, *args, **options):
        from django.utils import timezone
        now = timezone.now()
        self.stdout.write(f"🚀 Traitement lancé à {now}")

        for account in Account.objects.filter(is_active=True):
            check_all_rewards(account)
            check_all_promotions(account)

        self.stdout.write(self.style.SUCCESS("✅ Récompenses et promotions traitées."))
