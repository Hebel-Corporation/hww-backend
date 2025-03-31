from django.db.models import F
from prices.models import PurchaseBonus

def run():
    # Met à jour tous les PurchaseBonus où amount_to_be_paid est 0 ou null
    PurchaseBonus.objects.filter(amount_to_be_paid=0, is_paid=False).update(amount_to_be_paid=F('amount'))
    print("Mise à jour terminée")
