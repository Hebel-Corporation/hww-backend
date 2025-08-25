from django.core.management.base import BaseCommand
from members.models import Account


class Command(BaseCommand):
    help = "Reconcilie tous les equilibres des comptes"

    def handle(self, *args, **options):
        from django.utils import timezone
        now = timezone.now()
        self.stdout.write(f"🚀 Traitement lancé à {now}")

        for account in Account.objects.filter(is_active=True):
            account._tree_manager.rebuild()
            if account.get_children().count() > 1:
                direct_account_downlines = account.get_children().order_by('created_at')
                left_downline, right_downline = direct_account_downlines
                
                left_downline_leg = left_downline.get_descendants(include_self=True).order_by('created_at')
                right_downline_leg = right_downline.get_descendants(include_self=True).order_by('created_at')

                left_count = left_downline_leg.count()
                right_count = right_downline_leg.count()
                min_count = min(left_count, right_count)

                from prices.models import Matching
                
                # Vérifier s'il y a de nouveaux matchings possibles
                if min_count > account.get_matching_count and account.get_referral_count > 0:
                    # Déterminer quelle branche a le minimum
                    if left_count <= right_count:
                        minimal_branch = left_downline_leg
                        opposite_branch = right_downline_leg
                        branch_name = "gauche"
                    else:
                        minimal_branch = right_downline_leg
                        opposite_branch = left_downline_leg
                        branch_name = "droite"
                    
                    # Calculer le nombre de nouveaux matchings à créer
                    new_matchings_count = min_count - account.get_matching_count
                    
                    self.stdout.write(f"  → Compte {account.company_id}: {new_matchings_count} nouveaux matchings possibles")
                    self.stdout.write(f"    Branche minimale: {branch_name} ({min_count} membres) avec {account.get_matching_count} matchings")
                    
                    # Récupérer tous les IDs des enfants déjà utilisés dans les matchings de ce compte
                    existing_matching_downlines = Matching.objects.filter(
                        grantee=account
                    ).values_list('downlines__id', flat=True)
                    
                    # Filtrer les enfants de la branche minimale en excluant ceux déjà matchés
                    unmatched_children = minimal_branch.filter(
                        is_active=True  # Seulement les comptes actifs
                    ).exclude(
                        id__in=existing_matching_downlines  # Exclure ceux déjà dans des matchings
                    )[:new_matchings_count]

                    opposite_unmatched_children = opposite_branch.filter(
                        is_active=True  # Seulement les comptes actifs
                    ).exclude(
                        id__in=existing_matching_downlines  # Exclure ceux déjà dans des matchings
                    )[:new_matchings_count]
                    
                    # Créer les nouveaux matchings en appariant les enfants des deux branches
                    from config.models import MatchingPrice
                    from members.models import Subscription
                    from django.shortcuts import get_object_or_404
                    from utils.utils_functions import check_all_rewards, check_all_promotions
                    
                    for child_one, child_two in zip(unmatched_children, opposite_unmatched_children):
                        # Déterminer qui est le new_member_account (date supérieure) et pairing_downline (date inférieure)
                        if child_one.created_at > child_two.created_at:
                            new_member_account = child_one
                            pairing_downline = child_two
                        else:
                            new_member_account = child_two
                            pairing_downline = child_one
                        
                        # Calculer le montant du matching
                        try:
                            matchings_count = account.get_matching_count + 1
                            matching_price = MatchingPrice.objects.filter(
                                begin__lte=matchings_count, 
                                end__gte=matchings_count
                            ).first()
                            
                            if matching_price:
                                # Utiliser la subscription du new_member_account pour calculer le montant
                                new_account_subscription = get_object_or_404(Subscription, member_account=new_member_account)
                                amount = new_account_subscription.package.price * matching_price.package_price_percent
                                
                                # Créer le matching bonus
                                matching = Matching.objects.create(
                                    grantee=account,
                                    amount=amount,
                                    office=new_member_account.office,
                                    is_validated = account.get_daily_matching_count(date_value=new_member_account.created_at.date()) < matching_price.daily_max_matching,
                                    created_at=new_member_account.created_at,
                                )
                                
                                matching.downlines.set([new_member_account, pairing_downline])
                                matching.save()
                                
                                self.stdout.write(f"✅ Matching créé: {new_member_account.company_id} (nouveau) ↔ {pairing_downline.company_id} (ancien) - ${amount}")
                                
                                # Vérifier les récompenses et promotions
                                check_all_rewards(account)
                                check_all_promotions(account)
                            else:
                                self.stdout.write(f"⚠️ Aucun prix de matching trouvé pour le count {matchings_count}")
                                
                        except Exception as e:
                            self.stdout.write(f"❌ Erreur lors de la création du matching: {str(e)}")
                    
                    self.stdout.write(f"→ {len(unmatched_children)} enfants traités de la branche {branch_name}")
                elif account.get_referral_count == 0:
                    matchings_to_delete = Matching.objects.filter(grantee=account, is_paid=False)
                    count_to_delete = matchings_to_delete.count()
                    if count_to_delete > 0 :
                        matchings_to_delete.delete()
                        self.stdout.write(f"→ Suppression des {count_to_delete} matchings non payés du compte {account.company_id}")
                    self.stdout.write(f"→ Le compte {account.company_id}: n'a pas le droit de faire de matching (il n'a jamais fait de referral)")
                else:
                    # Pas de nouveaux matchings possibles
                    self.stdout.write(f"→ Compte {account.company_id}: Aucun nouveau matching (min: {min_count}, déjà accordés: {account.get_matching_count})")

        self.stdout.write(self.style.SUCCESS("✅ Equilibres des comptes traités."))
