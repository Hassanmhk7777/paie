# paie/services/calculateur_paie.py
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class CalculateurPaieMaroc:
    """
    Service de calcul de paie conforme à la législation marocaine
    Gère CNSS, AMO, CIMR, IR et rubriques personnalisées
    """
    
    def __init__(self, parametrage_paie):
        self.parametrage = parametrage_paie
        self.baremes_ir = parametrage_paie.baremes_ir.all().order_by('ordre')
        
    def calculer_bulletin(self, employe, periode, donnees_variables=None):
        """
        Calcule un bulletin de paie complet
        
        Args:
            employe: Instance Employee
            periode: Instance PeriodePaie  
            donnees_variables: Dict avec heures sup, primes, etc.
        
        Returns:
            Dict avec tous les éléments calculés
        """
        try:
            # Initialisation des données
            donnees_variables = donnees_variables or {}
            calcul = self._initialiser_calcul(employe, periode, donnees_variables)
            
            # 1. Calcul du brut
            calcul = self._calculer_elements_brut(calcul)
            
            # 2. Application des rubriques personnalisées
            calcul = self._appliquer_rubriques_personnalisees(calcul)
            
            # 3. Calcul des cotisations sociales
            calcul = self._calculer_cotisations_sociales(calcul)
            
            # 4. Calcul de l'impôt sur le revenu
            calcul = self._calculer_impot_revenu(calcul)
            
            # 5. Calcul des retenues diverses
            calcul = self._calculer_retenues_diverses(calcul)
            
            # 6. Calcul du net à payer
            calcul = self._calculer_net_a_payer(calcul)
            
            # 7. Calcul des charges patronales
            calcul = self._calculer_charges_patronales(calcul)
            
            logger.info(f"Calcul paie terminé pour {employe} - Net: {calcul['net_a_payer']}")
            return calcul
            
        except Exception as e:
            logger.error(f"Erreur calcul paie {employe}: {e}")
            raise
    
    def _initialiser_calcul(self, employe, periode, donnees_variables):
        """Initialise la structure de calcul"""
        return {
            'employe': employe,
            'periode': periode,
            'parametrage': self.parametrage,
            
            # Éléments de base
            'salaire_base': employe.salaire_base,
            'heures_supplementaires': Decimal(str(donnees_variables.get('heures_sup', 0))),
            'taux_heure_sup': Decimal(str(donnees_variables.get('taux_heure_sup', 0))),
            'jours_travailles': donnees_variables.get('jours_travailles', periode.nb_jours_travailles),
            
            # Primes et indemnités standards
            'prime_anciennete': Decimal(str(donnees_variables.get('prime_anciennete', 0))),
            'prime_responsabilite': Decimal(str(donnees_variables.get('prime_responsabilite', 0))),
            'indemnite_transport': Decimal(str(donnees_variables.get('indemnite_transport', 0))),
            'avantages_nature': Decimal(str(donnees_variables.get('avantages_nature', 0))),
            
            # Retenues
            'avances': Decimal(str(donnees_variables.get('avances', 0))),
            'prets': Decimal(str(donnees_variables.get('prets', 0))),
            'autres_retenues': Decimal(str(donnees_variables.get('autres_retenues', 0))),
            
            # Rubriques personnalisées
            'rubriques_gains': [],
            'rubriques_retenues': [],
            
            # Totaux (seront calculés)
            'total_brut': Decimal('0'),
            'total_imposable': Decimal('0'),
            'total_cotisable_cnss': Decimal('0'),
            'cotisation_cnss': Decimal('0'),
            'cotisation_amo': Decimal('0'),
            'cotisation_cimr': Decimal('0'),
            'ir_brut': Decimal('0'),
            'ir_net': Decimal('0'),
            'total_retenues': Decimal('0'),
            'net_a_payer': Decimal('0'),
            
            # Charges patronales
            'charges_cnss_patronal': Decimal('0'),
            'charges_amo_patronal': Decimal('0'),
            'formation_professionnelle': Decimal('0'),
            'prestations_sociales': Decimal('0'),
        }
    
    def _calculer_elements_brut(self, calcul):
        """Calcule tous les éléments du salaire brut"""
        
        # Salaire de base (au prorata si nécessaire)
        salaire_base_period = calcul['salaire_base']
        if calcul['jours_travailles'] != calcul['periode'].nb_jours_travailles:
            salaire_base_period = (
                calcul['salaire_base'] * 
                Decimal(str(calcul['jours_travailles'])) / 
                Decimal(str(calcul['periode'].nb_jours_travailles))
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        calcul['salaire_base_period'] = salaire_base_period
        
        # Heures supplémentaires
        montant_heures_sup = (
            calcul['heures_supplementaires'] * calcul['taux_heure_sup']
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        calcul['montant_heures_sup'] = montant_heures_sup
        
        # Total brut initial
        calcul['total_brut'] = (
            salaire_base_period + 
            montant_heures_sup +
            calcul['prime_anciennete'] +
            calcul['prime_responsabilite'] +
            calcul['indemnite_transport'] +
            calcul['avantages_nature']
        )
        
        return calcul
    
    def _appliquer_rubriques_personnalisees(self, calcul):
        """Applique les rubriques personnalisées de l'entreprise"""
        from paie.models import RubriquePersonnalisee
        
        rubriques = RubriquePersonnalisee.objects.filter(actif=True)
        
        for rubrique in rubriques:
            montant = self._calculer_rubrique_personnalisee(rubrique, calcul)
            
            ligne_rubrique = {
                'rubrique': rubrique,
                'montant': montant,
                'base_calcul': calcul['total_brut'],
            }
            
            if rubrique.type_rubrique in ['GAIN', 'AVANTAGE', 'INDEMNITE']:
                calcul['rubriques_gains'].append(ligne_rubrique)
                calcul['total_brut'] += montant
            else:  # RETENUE
                calcul['rubriques_retenues'].append(ligne_rubrique)
        
        return calcul
    
    def _calculer_rubrique_personnalisee(self, rubrique, calcul):
        """Calcule le montant d'une rubrique personnalisée"""
        
        if rubrique.mode_calcul == 'FIXE':
            return rubrique.valeur_fixe or Decimal('0')
            
        elif rubrique.mode_calcul == 'POURCENTAGE':
            base = calcul['total_brut']
            return (base * (rubrique.pourcentage or Decimal('0')) / 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
        elif rubrique.mode_calcul == 'FORMULE':
            # Évaluation sécurisée de formules simples
            try:
                # Variables disponibles dans les formules
                variables = {
                    'salaire_base': float(calcul['salaire_base']),
                    'total_brut': float(calcul['total_brut']),
                    'anciennete_annees': self._calculer_anciennete_annees(calcul['employe']),
                }
                
                # Évaluation simple (à sécuriser en production)
                resultat = eval(rubrique.formule, {"__builtins__": {}}, variables)
                return Decimal(str(resultat)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
            except Exception as e:
                logger.warning(f"Erreur formule rubrique {rubrique.code}: {e}")
                return Decimal('0')
        
        return Decimal('0')
    
    def _calculer_cotisations_sociales(self, calcul):
        """Calcule CNSS, AMO et CIMR"""
        
        # Base cotisable CNSS (avec plafond)
        base_cnss = min(calcul['total_brut'], self.parametrage.plafond_cnss)
        calcul['total_cotisable_cnss'] = base_cnss
        
        # Cotisation CNSS salarié 
        calcul['cotisation_cnss'] = (
            base_cnss * self.parametrage.taux_cnss_salarie / 100
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Cotisation AMO salarié
        calcul['cotisation_amo'] = (
            calcul['total_brut'] * self.parametrage.taux_amo_salarie / 100
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Cotisation CIMR (si affilié)
        if calcul['employe'].affilie_cimr:
            calcul['cotisation_cimr'] = (
                calcul['total_brut'] * self.parametrage.taux_cimr / 100
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return calcul
    
    def _calculer_impot_revenu(self, calcul):
        """Calcule l'impôt sur le revenu selon barème progressif marocain"""
        
        # Base imposable
        base_imposable = calcul['total_brut']
        
        # Déduction frais professionnels (20% plafonné)
        frais_prof = min(
            base_imposable * self.parametrage.taux_frais_prof / 100,
            self.parametrage.plafond_frais_prof
        )
        
        # Déduction cotisations sociales
        total_cotisations = (
            calcul['cotisation_cnss'] + 
            calcul['cotisation_amo'] + 
            calcul['cotisation_cimr']
        )
        
        # Revenu net imposable
        revenu_imposable = base_imposable - frais_prof - total_cotisations
        calcul['total_imposable'] = revenu_imposable
        
        # Application du barème progressif
        if revenu_imposable <= 0 or calcul['employe'].exonere_ir:
            calcul['ir_brut'] = Decimal('0')
        else:
            calcul['ir_brut'] = self._appliquer_bareme_ir(revenu_imposable)
        
        # Déductions pour charges de famille
        deductions_famille = self._calculer_deductions_famille(calcul['employe'])
        
        # IR net
        calcul['ir_net'] = max(
            calcul['ir_brut'] - deductions_famille, 
            Decimal('0')
        )
        
        return calcul
    
    def _appliquer_bareme_ir(self, revenu_mensuel):
        """Applique le barème progressif de l'IR"""
        
        # Calcul sur base annuelle
        revenu_annuel = revenu_mensuel * 12
        ir_annuel = Decimal('0')
        
        for bareme in self.baremes_ir:
            if revenu_annuel <= bareme.tranche_min:
                break
                
            tranche_max = bareme.tranche_max or revenu_annuel
            assiette_tranche = min(revenu_annuel, tranche_max) - bareme.tranche_min
            
            if assiette_tranche > 0:
                ir_tranche = (assiette_tranche * bareme.taux / 100) - bareme.somme_a_deduire
                ir_annuel += max(ir_tranche, Decimal('0'))
        
        # Retour au mensuel
        ir_mensuel = (ir_annuel / 12).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return ir_mensuel
    
    def _calculer_deductions_famille(self, employe):
        """Calcule les déductions familiales"""
        
        deduction = Decimal('0')
        
        # Déduction par personne à charge
        deduction += self.parametrage.deduction_personne * employe.nb_enfants_charge
        
        # Déduction conjoint (si non salarié)
        if employe.situation_familiale == 'MARIE' and not employe.conjoint_salarie:
            deduction += self.parametrage.deduction_personne
        
        return deduction
    
    def _calculer_retenues_diverses(self, calcul):
        """Calcule toutes les retenues"""
        
        retenues_rubriques = sum(
            ligne['montant'] for ligne in calcul['rubriques_retenues']
        )
        
        calcul['total_retenues'] = (
            calcul['cotisation_cnss'] +
            calcul['cotisation_amo'] +
            calcul['cotisation_cimr'] +
            calcul['ir_net'] +
            calcul['avances'] +
            calcul['prets'] +
            calcul['autres_retenues'] +
            retenues_rubriques
        )
        
        return calcul
    
    def _calculer_net_a_payer(self, calcul):
        """Calcule le net à payer"""
        
        calcul['net_a_payer'] = calcul['total_brut'] - calcul['total_retenues']
        return calcul
    
    def _calculer_charges_patronales(self, calcul):
        """Calcule les charges patronales"""
        
        base_cnss = calcul['total_cotisable_cnss']
        
        # CNSS patronal
        calcul['charges_cnss_patronal'] = (
            base_cnss * self.parametrage.taux_cnss_patronal / 100
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # AMO patronal
        calcul['charges_amo_patronal'] = (
            calcul['total_brut'] * self.parametrage.taux_amo_patronal / 100
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Formation professionnelle
        calcul['formation_professionnelle'] = (
            calcul['total_brut'] * self.parametrage.taux_formation_prof / 100
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Prestations sociales
        calcul['prestations_sociales'] = (
            base_cnss * self.parametrage.taux_prestations_sociales / 100
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return calcul
    
    def _calculer_anciennete_annees(self, employe):
        """Calcule l'ancienneté en années"""
        from datetime import date
        
        today = date.today()
        anciennete = today - employe.date_embauche
        return anciennete.days // 365
    
    @transaction.atomic
    def generer_bulletin_db(self, employe, periode, donnees_variables=None):
        """
        Génère et sauvegarde un bulletin en base
        
        Returns:
            Instance BulletinPaie créée
        """
        from paie.models import BulletinPaie, LigneBulletin
        
        # Calcul
        calcul = self.calculer_bulletin(employe, periode, donnees_variables)
        
        # Création du bulletin
        bulletin = BulletinPaie.objects.create(
            periode=periode,
            employe=employe,
            salaire_base=calcul['salaire_base_period'],
            heures_supplementaires=calcul['heures_supplementaires'],
            taux_heure_sup=calcul['taux_heure_sup'],
            prime_anciennete=calcul['prime_anciennete'],
            prime_responsabilite=calcul['prime_responsabilite'],
            indemnite_transport=calcul['indemnite_transport'],
            avantages_nature=calcul['avantages_nature'],
            total_brut=calcul['total_brut'],
            total_imposable=calcul['total_imposable'],
            total_cotisable_cnss=calcul['total_cotisable_cnss'],
            cotisation_cnss=calcul['cotisation_cnss'],
            cotisation_amo=calcul['cotisation_amo'],
            cotisation_cimr=calcul['cotisation_cimr'],
            ir_brut=calcul['ir_brut'],
            ir_net=calcul['ir_net'],
            avances=calcul['avances'],
            prets=calcul['prets'],
            autres_retenues=calcul['autres_retenues'],
            total_retenues=calcul['total_retenues'],
            net_a_payer=calcul['net_a_payer'],
            charges_cnss_patronal=calcul['charges_cnss_patronal'],
            charges_amo_patronal=calcul['charges_amo_patronal'],
            formation_professionnelle=calcul['formation_professionnelle'],
            prestations_sociales=calcul['prestations_sociales'],
        )
        
        # Création des lignes pour rubriques personnalisées
        for ordre, ligne in enumerate(calcul['rubriques_gains'] + calcul['rubriques_retenues'], 1):
            LigneBulletin.objects.create(
                bulletin=bulletin,
                rubrique=ligne['rubrique'],
                base_calcul=ligne.get('base_calcul', Decimal('0')),
                montant=ligne['montant'],
                ordre_affichage=ordre
            )
        
        logger.info(f"Bulletin généré: {bulletin.numero_bulletin}")
        return bulletin

class CalculateurPeriode:
    """Service pour calculer une période complète"""
    
    @transaction.atomic
    def calculer_periode_complete(self, periode, employes_ids=None, force_recreate=False):
        """
        Calcule tous les bulletins d'une période
        
        Args:
            periode: Instance PeriodePaie
            employes_ids: Liste des IDs employés (None = tous)
            force_recreate: Recréer les bulletins existants
        
        Returns:
            Dict avec statistiques de traitement
        """
        from paie.models import Employee, BulletinPaie
        
        if periode.statut == 'CLOTUREE':
            raise ValueError("Impossible de modifier une période clôturée")
        
        # Sélection des employés
        if employes_ids:
            employes = Employee.objects.filter(id__in=employes_ids, is_active=True)
        else:
            employes = Employee.objects.filter(is_active=True)
        
        calculateur = CalculateurPaieMaroc(periode.parametrage)
        stats = {
            'total_employes': employes.count(),
            'bulletins_crees': 0,
            'bulletins_modifies': 0,
            'erreurs': []
        }
        
        for employe in employes:
            try:
                # Vérifier si bulletin existe
                bulletin_existant = BulletinPaie.objects.filter(
                    periode=periode, employe=employe
                ).first()
                
                if bulletin_existant and not force_recreate:
                    continue
                    
                if bulletin_existant:
                    bulletin_existant.delete()
                    stats['bulletins_modifies'] += 1
                
                # Générer nouveau bulletin
                bulletin = calculateur.generer_bulletin_db(employe, periode)
                stats['bulletins_crees'] += 1
                
            except Exception as e:
                error_msg = f"Erreur {employe}: {str(e)}"
                stats['erreurs'].append(error_msg)
                logger.error(error_msg)
        
        # Mise à jour statut période
        if not stats['erreurs']:
            periode.statut = 'CALCULE'
            periode.save()
        
        return stats