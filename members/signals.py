from django.db.models.signals import post_delete
from django.dispatch import receiver
from prices.models import Matching
from members.models import Account


@receiver(post_delete, sender=Account)
def account_deleted_cleanup(sender, instance, **kwargs):
    """
    Signal qui s'exécute APRÈS la suppression d'un compte.
    ATTENTION: L'objet Account est déjà supprimé de la DB !
    """
    print(f"✅ POST-DELETE: Compte {instance.company_id} supprimé avec succès")
    
    try:
        from django.db.models import Count
        
        # Trouver tous les matchings qui n'ont pas 2 éléments dans downlines
        # Ces matchings sont "cassés" car un matching doit avoir 2 downlines
        orphaned_matchings = Matching.objects.annotate(
            downlines_count=Count('downlines')
        ).filter(
            downlines_count__lt=2  # Matchings avec moins de 2 downlines = orphelins
        )
        
        if orphaned_matchings.exists():
            count = orphaned_matchings.count()
            for matching in orphaned_matchings:
                if matching.is_paid :
                    equivalent_matching = Matching.objects.filter(
                        grantee=matching.grantee, 
                        amount=matching.amount, 
                        is_paid=False
                    ).exclude(id=matching.id).first()
                    
                    if equivalent_matching :
                        equivalent_matching.is_paid = True
                        equivalent_matching.save()
                    else :
                        equivalent_matching = Matching.objects.filter(
                            grantee=matching.grantee, 
                            is_paid=False
                        ).exclude(id=matching.id).first()
                        if equivalent_matching :
                            equivalent_matching.is_paid = True
                            equivalent_matching.save()
            
            orphaned_matchings.delete()
            print(f"🧹 POST-DELETE: {count} matching(s) orphelins supprimés (avec moins de 2 downlines)")
        else:
            print(f"ℹ️ POST-DELETE: Aucun matching orphelin détecté")
            
    except Exception as e:
        print(f"❌ POST-DELETE ERROR: {str(e)}")