# paie/services/gestionnaire_pointage.py
# Service métier pour la gestion complète du pointage et des présences

from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import logging
from typing import Dict, List, Optional, Tuple

from ..models import (
    Employee, Pointage, PresenceJournaliere, HoraireTravail, 
    PlageHoraire, ReglePointage, ValidationPresence, AlertePresence,
    TypeConge, DemandeConge
)

logger = logging.getLogger(__name__)


class GestionnairePointage:
    """Service principal pour la gestion du pointage et des présences"""
    
    def __init__(self):
        self.regle_active = self._get_regle_active()
    
    def _get_regle_active(self) -> Optional[ReglePointage]:
        """Récupère la règle de pointage active"""
        return ReglePointage.objects.filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=date.today()),
            actif=True,
            date_debut__lte=date.today()
        ).first()
    
    @transaction.atomic
    def enregistrer_pointage(self, employe_id: int, type_pointage: str, 
                           heure: datetime = None, cree_par_id: int = None,
                           ip_address: str = None, justification: str = "") -> Dict:
        """
        Enregistre un nouveau pointage pour un employé
        
        Args:
            employe_id: ID de l'employé
            type_pointage: ARRIVEE, SORTIE, PAUSE_DEBUT, PAUSE_FIN
            heure: Heure du pointage (défaut: maintenant)
            cree_par_id: ID de l'utilisateur qui enregistre
            ip_address: Adresse IP pour traçabilité
            justification: Justification éventuelle
            
        Returns:
            Dict avec le résultat et les détails
        """
        try:
            employe = Employee.objects.get(id=employe_id)
            heure = heure or timezone.now()
            
            # Vérifier les règles métier
            validation_result = self._valider_pointage(employe, type_pointage, heure)
            if not validation_result['valide']:
                return {
                    'success': False,
                    'message': validation_result['message'],
                    'warnings': validation_result.get('warnings', [])
                }
            
            # Récupérer l'horaire théorique
            horaire_travail = self._get_horaire_employe(employe, heure.date())
            heure_theorique = self._calculer_heure_theorique(horaire_travail, type_pointage, heure.date())
            
            # Créer le pointage
            pointage = Pointage.objects.create(
                employe=employe,
                type_pointage=type_pointage,
                heure_pointage=heure,
                heure_theorique=heure_theorique,
                ip_address=ip_address,
                justification=justification,
                cree_par_id=cree_par_id
            )
            
            # Mettre à jour la présence journalière
            self._mettre_a_jour_presence_journaliere(employe, heure.date())
            
            # Vérifier les alertes
            self._verifier_alertes_pointage(employe, pointage)
            
            logger.info(f"Pointage enregistré: {employe.last_name} - {type_pointage} - {heure}")
            
            return {
                'success': True,
                'pointage_id': str(pointage.id),
                'message': 'Pointage enregistré avec succès',
                'retard_minutes': pointage.retard_minutes if type_pointage == 'ARRIVEE' else 0,
                'statut': pointage.statut
            }
            
        except Employee.DoesNotExist:
            return {'success': False, 'message': 'Employé non trouvé'}
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du pointage: {e}")
            return {'success': False, 'message': f'Erreur technique: {str(e)}'}
    
    def _valider_pointage(self, employe: Employee, type_pointage: str, heure: datetime) -> Dict:
        """Valide les règles métier avant enregistrement"""
        warnings = []
        
        # Vérifier les pointages existants du jour
        pointages_jour = Pointage.objects.filter(
            employe=employe,
            heure_pointage__date=heure.date()
        ).order_by('heure_pointage')
        
        derniers_pointages = list(pointages_jour.values_list('type_pointage', flat=True))
        
        # Règles de cohérence
        if type_pointage == 'ARRIVEE':
            if 'ARRIVEE' in derniers_pointages and 'SORTIE' not in derniers_pointages:
                return {
                    'valide': False,
                    'message': 'Employé déjà arrivé aujourd\'hui sans pointage de sortie'
                }
        
        elif type_pointage == 'SORTIE':
            if 'ARRIVEE' not in derniers_pointages:
                warnings.append('Aucun pointage d\'arrivée trouvé pour aujourd\'hui')
                
        elif type_pointage == 'PAUSE_DEBUT':
            if 'ARRIVEE' not in derniers_pointages:
                return {
                    'valide': False,
                    'message': 'Impossible de commencer une pause sans pointage d\'arrivée'
                }
            if derniers_pointages and derniers_pointages[-1] == 'PAUSE_DEBUT':
                return {
                    'valide': False,
                    'message': 'Une pause est déjà en cours'
                }
                
        elif type_pointage == 'PAUSE_FIN':
            if 'PAUSE_DEBUT' not in derniers_pointages:
                return {
                    'valide': False,
                    'message': 'Aucune pause en cours à terminer'
                }
            # Vérifier qu'on termine bien la dernière pause
            if derniers_pointages and derniers_pointages[-1] != 'PAUSE_DEBUT':
                return {
                    'valide': False,
                    'message': 'Aucune pause en cours à terminer'
                }
        
        # Vérifier l'heure (pas dans le futur, pas trop ancien)
        if heure > timezone.now() + timedelta(minutes=5):
            return {
                'valide': False,
                'message': 'Impossible de pointer dans le futur'
            }
        
        if heure < timezone.now() - timedelta(days=7):
            warnings.append('Pointage de plus de 7 jours, validation manuelle requise')
        
        return {
            'valide': True,
            'message': 'Validation OK',
            'warnings': warnings
        }
    
    def _get_horaire_employe(self, employe: Employee, date_pointage: date) -> Optional[HoraireTravail]:
        """Récupère l'horaire de travail effectif pour un employé à une date donnée"""
        return HoraireTravail.objects.filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=date_pointage),
            employe=employe,
            actif=True,
            date_debut__lte=date_pointage
        ).first()
    
    def _calculer_heure_theorique(self, horaire_travail: HoraireTravail, 
                                type_pointage: str, date_pointage: date) -> Optional[datetime]:
        """Calcule l'heure théorique selon l'horaire de travail"""
        if not horaire_travail:
            return None
        
        # Vérifier si c'est un jour travaillé
        jour_semaine = date_pointage.weekday() + 1  # 1=Lundi, 7=Dimanche
        if jour_semaine not in horaire_travail.jours_travailles_effectifs:
            return None
        
        if type_pointage == 'ARRIVEE':
            heure_theo = horaire_travail.heure_debut_effective
        elif type_pointage == 'SORTIE':
            heure_theo = horaire_travail.heure_fin_effective
        elif type_pointage == 'PAUSE_DEBUT':
            heure_theo = horaire_travail.plage_horaire.heure_debut_pause
        elif type_pointage == 'PAUSE_FIN':
            heure_theo = horaire_travail.plage_horaire.heure_fin_pause
        else:
            return None
        
        if heure_theo:
            return timezone.datetime.combine(date_pointage, heure_theo)
        return None
    
    @transaction.atomic
    def _mettre_a_jour_presence_journaliere(self, employe: Employee, date_pointage: date):
        """Met à jour le résumé de présence journalière"""
        try:
            # Récupérer ou créer la présence journalière
            presence, created = PresenceJournaliere.objects.get_or_create(
                employe=employe,
                date=date_pointage,
                defaults={
                    'horaire_travail': self._get_horaire_employe(employe, date_pointage)
                }
            )
            
            # Récupérer tous les pointages du jour
            pointages = Pointage.objects.filter(
                employe=employe,
                heure_pointage__date=date_pointage
            ).order_by('heure_pointage')
            
            if not pointages.exists():
                return
            
            # Calculer les heures et statut
            calcul_result = self.calculer_heures_travaillees(employe, date_pointage)
            
            # Mettre à jour la présence
            presence.heure_arrivee = calcul_result.get('heure_arrivee')
            presence.heure_sortie = calcul_result.get('heure_sortie')
            presence.pauses = calcul_result.get('pauses', [])
            presence.heures_travaillees = calcul_result.get('heures_travaillees', timedelta(0))
            presence.heures_theoriques = calcul_result.get('heures_theoriques', timedelta(0))
            presence.duree_pauses = calcul_result.get('duree_pauses', timedelta(0))
            presence.retard_minutes = calcul_result.get('retard_minutes', 0)
            presence.depart_anticipe_minutes = calcul_result.get('depart_anticipe_minutes', 0)
            
            # Déterminer le statut du jour
            if presence.heure_arrivee and presence.heure_sortie:
                presence.statut_jour = 'PRESENT'
            elif presence.heure_arrivee:
                presence.statut_jour = 'PARTIEL'
            else:
                # Vérifier si c'est un congé approuvé
                conge = self._verifier_conge_approuve(employe, date_pointage)
                if conge:
                    presence.statut_jour = 'CONGE'
                else:
                    presence.statut_jour = 'ABSENT'
            
            presence.save()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour présence journalière: {e}")
    
    def calculer_heures_travaillees(self, employe: Employee, date_calc: date) -> Dict:
        """
        Calcule les heures travaillées pour un employé à une date donnée
        
        Returns:
            Dict avec tous les détails des calculs
        """
        pointages = Pointage.objects.filter(
            employe=employe,
            heure_pointage__date=date_calc
        ).order_by('heure_pointage')
        
        if not pointages.exists():
            return {
                'heures_travaillees': timedelta(0),
                'heures_theoriques': timedelta(0),
                'duree_pauses': timedelta(0),
                'retard_minutes': 0,
                'depart_anticipe_minutes': 0
            }
        
        # Organiser les pointages
        pointages_dict = {}
        for p in pointages:
            pointages_dict[p.type_pointage] = p.heure_pointage
        
        # Calculer les heures travaillées
        heure_arrivee = pointages_dict.get('ARRIVEE')
        heure_sortie = pointages_dict.get('SORTIE')
        
        heures_travaillees = timedelta(0)
        duree_pauses = timedelta(0)
        
        if heure_arrivee:
            fin_calcul = heure_sortie or timezone.now()
            heures_brutes = fin_calcul - heure_arrivee
            
            # Calculer les pauses
            pauses = self._calculer_pauses(pointages, date_calc)
            duree_pauses = sum([p['duree'] for p in pauses], timedelta(0))
            
            # Heures nettes = heures brutes - pauses
            heures_travaillees = max(timedelta(0), heures_brutes - duree_pauses)
        
        # Récupérer les heures théoriques
        horaire_travail = self._get_horaire_employe(employe, date_calc)
        heures_theoriques = timedelta(0)
        if horaire_travail:
            heures_theoriques = horaire_travail.plage_horaire.duree_theorique
        
        # Calculer retards et départs anticipés
        retard_minutes = 0
        depart_anticipe_minutes = 0
        
        if heure_arrivee and horaire_travail:
            heure_theo_arrivee = self._calculer_heure_theorique(horaire_travail, 'ARRIVEE', date_calc)
            if heure_theo_arrivee and heure_arrivee > heure_theo_arrivee:
                retard_minutes = (heure_arrivee - heure_theo_arrivee).total_seconds() / 60
        
        if heure_sortie and horaire_travail:
            heure_theo_sortie = self._calculer_heure_theorique(horaire_travail, 'SORTIE', date_calc)
            if heure_theo_sortie and heure_sortie < heure_theo_sortie:
                depart_anticipe_minutes = (heure_theo_sortie - heure_sortie).total_seconds() / 60
        
        return {
            'heure_arrivee': heure_arrivee,
            'heure_sortie': heure_sortie,
            'pauses': self._calculer_pauses(pointages, date_calc),
            'heures_travaillees': heures_travaillees,
            'heures_theoriques': heures_theoriques,
            'duree_pauses': duree_pauses,
            'retard_minutes': int(retard_minutes),
            'depart_anticipe_minutes': int(depart_anticipe_minutes)
        }
    
    def _calculer_pauses(self, pointages, date_calc: date) -> List[Dict]:
        """Calcule les périodes de pause à partir des pointages"""
        pauses = []
        pointages_list = list(pointages.values('type_pointage', 'heure_pointage'))
        
        pause_debut = None
        for pointage in pointages_list:
            if pointage['type_pointage'] == 'PAUSE_DEBUT':
                pause_debut = pointage['heure_pointage']
            elif pointage['type_pointage'] == 'PAUSE_FIN' and pause_debut:
                pause_fin = pointage['heure_pointage']
                duree = pause_fin - pause_debut
                pauses.append({
                    'debut': pause_debut.strftime('%H:%M'),
                    'fin': pause_fin.strftime('%H:%M'),
                    'duree': duree
                })
                pause_debut = None
        
        # Si pause en cours (pas de PAUSE_FIN)
        if pause_debut:
            duree = timezone.now() - pause_debut
            pauses.append({
                'debut': pause_debut.strftime('%H:%M'),
                'fin': 'En cours',
                'duree': duree
            })
        
        return pauses
    
    def detecter_retards_absences(self, date_detection: date = None) -> Dict:
        """
        Détecte les retards et absences pour une date donnée
        
        Args:
            date_detection: Date à analyser (défaut: aujourd'hui)
            
        Returns:
            Dict avec les statistiques et listes des retards/absences
        """
        date_detection = date_detection or date.today()
        
        # Récupérer tous les employés actifs avec horaires
        employes_actifs = Employee.objects.filter(
            is_active=True,
            horaires__actif=True,
            horaires__date_debut__lte=date_detection,
            horaires__date_fin__isnull=True
        ).distinct()
        
        retards = []
        absences = []
        presents = []
        
        for employe in employes_actifs:
            horaire = self._get_horaire_employe(employe, date_detection)
            if not horaire:
                continue
            
            # Vérifier si c'est un jour travaillé
            jour_semaine = date_detection.weekday() + 1
            if jour_semaine not in horaire.jours_travailles_effectifs:
                continue
            
            # Vérifier les pointages du jour
            pointage_arrivee = Pointage.objects.filter(
                employe=employe,
                type_pointage='ARRIVEE',
                heure_pointage__date=date_detection
            ).first()
            
            # Vérifier si en congé
            if self._verifier_conge_approuve(employe, date_detection):
                continue
            
            if pointage_arrivee:
                # Calculer le retard
                heure_theo = self._calculer_heure_theorique(horaire, 'ARRIVEE', date_detection)
                if heure_theo:
                    retard_minutes = (pointage_arrivee.heure_pointage - heure_theo).total_seconds() / 60
                    if retard_minutes > (self.regle_active.tolerance_retard_minutes if self.regle_active else 10):
                        retards.append({
                            'employe': employe,
                            'heure_arrivee': pointage_arrivee.heure_pointage,
                            'heure_theorique': heure_theo,
                            'retard_minutes': int(retard_minutes)
                        })
                    else:
                        presents.append(employe)
                else:
                    presents.append(employe)
            else:
                # Absence détectée
                absences.append({
                    'employe': employe,
                    'horaire': horaire
                })
        
        return {
            'date': date_detection,
            'retards': retards,
            'absences': absences,
            'presents': presents,
            'total_employes': len(employes_actifs),
            'nb_retards': len(retards),
            'nb_absences': len(absences),
            'nb_presents': len(presents)
        }
    
    def calculer_heures_supplementaires(self, employe: Employee, date_debut: date, date_fin: date = None) -> Dict:
        """
        Calcule les heures supplémentaires pour un employé sur une période
        
        Args:
            employe: Employé concerné
            date_debut: Date de début (début de semaine pour calcul weekly)
            date_fin: Date de fin (défaut: fin de semaine)
            
        Returns:
            Dict avec détail des heures supplémentaires
        """
        if not date_fin:
            # Calculer la fin de semaine (dimanche)
            date_fin = date_debut + timedelta(days=(6 - date_debut.weekday()))
        
        presences = PresenceJournaliere.objects.filter(
            employe=employe,
            date__range=[date_debut, date_fin],
            statut_jour__in=['PRESENT', 'PARTIEL']
        )
        
        total_heures = sum([p.heures_travaillees for p in presences], timedelta(0))
        total_heures_theoriques = sum([p.heures_theoriques for p in presences], timedelta(0))
        
        # Seuil légal Maroc : 44h/semaine
        seuil_hebdo = self.regle_active.seuil_heures_sup_semaine if self.regle_active else timedelta(hours=44)
        
        heures_sup_total = timedelta(0)
        heures_sup_25 = timedelta(0)
        heures_sup_50 = timedelta(0)
        
        if total_heures > seuil_hebdo:
            heures_sup_total = total_heures - seuil_hebdo
            
            # Répartition 25% / 50% (premières 8h à 25%, reste à 50%)
            if heures_sup_total <= timedelta(hours=8):
                heures_sup_25 = heures_sup_total
            else:
                heures_sup_25 = timedelta(hours=8)
                heures_sup_50 = heures_sup_total - timedelta(hours=8)
        
        return {
            'periode': f"{date_debut.strftime('%d/%m/%Y')} - {date_fin.strftime('%d/%m/%Y')}",
            'total_heures': total_heures,
            'total_heures_theoriques': total_heures_theoriques,
            'seuil_hebdo': seuil_hebdo,
            'heures_sup_total': heures_sup_total,
            'heures_sup_25': heures_sup_25,
            'heures_sup_50': heures_sup_50,
            'montant_25': self._calculer_montant_heures_sup(employe, heures_sup_25, 25),
            'montant_50': self._calculer_montant_heures_sup(employe, heures_sup_50, 50)
        }
    
    def _calculer_montant_heures_sup(self, employe: Employee, duree: timedelta, taux_majoration: int) -> Decimal:
        """Calcule le montant des heures supplémentaires"""
        if duree.total_seconds() == 0:
            return Decimal('0.00')
        
        # Récupérer le salaire horaire (supposé disponible dans Employee)
        salaire_horaire = getattr(employe, 'salaire_horaire', Decimal('0.00'))
        heures = Decimal(str(duree.total_seconds() / 3600))
        majoration = Decimal(str(1 + taux_majoration / 100))
        
        return salaire_horaire * heures * majoration
    
    def _verifier_conge_approuve(self, employe: Employee, date_conge: date) -> bool:
        """Vérifie si l'employé a un congé approuvé pour cette date"""
        return DemandeConge.objects.filter(
            employe=employe,
            date_debut__lte=date_conge,
            date_fin__gte=date_conge,
            statut='APPROUVE'
        ).exists()
    
    def generer_feuille_presence(self, date_debut: date, date_fin: date = None, 
                               departement_id: int = None) -> Dict:
        """
        Génère une feuille de présence pour une période donnée
        
        Args:
            date_debut: Date de début
            date_fin: Date de fin (défaut: même jour)
            departement_id: ID du département (optionnel)
            
        Returns:
            Dict avec les données de la feuille de présence
        """
        date_fin = date_fin or date_debut
        
        # Filtre employés
        employes_query = Employee.objects.filter(is_active=True)
        if departement_id:
            employes_query = employes_query.filter(department_id=departement_id)
        
        employes = employes_query.order_by('nom', 'prenom')
        
        # Récupérer les présences
        presences = PresenceJournaliere.objects.filter(
            employe__in=employes,
            date__range=[date_debut, date_fin]
        ).select_related('employe', 'horaire_travail')
        
        # Organiser les données
        feuille_data = {
            'periode': {
                'debut': date_debut,
                'fin': date_fin,
                'nb_jours': (date_fin - date_debut).days + 1
            },
            'departement': departement_id,
            'employes': [],
            'statistiques': {
                'total_employes': len(employes),
                'total_presences': 0,
                'total_absences': 0,
                'total_retards': 0,
                'total_heures': timedelta(0)
            }
        }
        
        for employe in employes:
            employe_presences = [p for p in presences if p.employe_id == employe.id]
            
            employe_data = {
                'employe': employe,
                'presences': employe_presences,
                'statistiques': {
                    'nb_presences': len([p for p in employe_presences if p.statut_jour == 'PRESENT']),
                    'nb_absences': len([p for p in employe_presences if p.statut_jour == 'ABSENT']),
                    'nb_retards': len([p for p in employe_presences if p.retard_minutes > 0]),
                    'total_heures': sum([p.heures_travaillees for p in employe_presences], timedelta(0)),
                    'total_retard_minutes': sum([p.retard_minutes for p in employe_presences])
                }
            }
            
            feuille_data['employes'].append(employe_data)
            
            # Mise à jour des stats globales
            stats = feuille_data['statistiques']
            stats['total_presences'] += employe_data['statistiques']['nb_presences']
            stats['total_absences'] += employe_data['statistiques']['nb_absences']
            stats['total_retards'] += employe_data['statistiques']['nb_retards']
            stats['total_heures'] += employe_data['statistiques']['total_heures']
        
        return feuille_data
    
    @transaction.atomic
    def valider_presence_journaliere(self, date_validation: date, validee_par_id: int, 
                                   employes_ids: List[int] = None) -> Dict:
        """
        Valide les présences journalières pour une date donnée
        
        Args:
            date_validation: Date à valider
            validee_par_id: ID de l'utilisateur validant
            employes_ids: Liste des IDs employés (optionnel, tous si non spécifié)
            
        Returns:
            Dict avec le résultat de la validation
        """
        try:
            # Filtre des présences à valider
            presences_query = PresenceJournaliere.objects.filter(
                date=date_validation,
                valide=False
            )
            
            if employes_ids:
                presences_query = presences_query.filter(employe_id__in=employes_ids)
            
            presences = list(presences_query.select_related('employe'))
            
            # Valider chaque présence
            validated_count = 0
            errors = []
            
            for presence in presences:
                try:
                    # Recalculer les heures avant validation
                    self._mettre_a_jour_presence_journaliere(presence.employe, date_validation)
                    
                    # Valider
                    presence.valide = True
                    presence.valide_par_id = validee_par_id
                    presence.date_validation = timezone.now()
                    presence.save()
                    
                    validated_count += 1
                    
                except Exception as e:
                    errors.append(f"Erreur pour {presence.employe.last_name}: {str(e)}")
            
            # Créer l'enregistrement de validation
            validation = ValidationPresence.objects.create(
                type_validation='JOURNALIERE',
                statut='VALIDEE',
                date_debut=date_validation,
                date_fin=date_validation,
                validee_par_id=validee_par_id,
                nb_presences=validated_count,
                commentaire=f"Validation automatique de {validated_count} présences"
            )
            
            # Associer les employés validés
            if employes_ids:
                validation.employes.set(employes_ids)
            else:
                validation.employes.set([p.employe_id for p in presences])
            
            return {
                'success': True,
                'validation_id': validation.id,
                'validated_count': validated_count,
                'total_presences': len(presences),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation journalière: {e}")
            return {
                'success': False,
                'message': f"Erreur lors de la validation: {str(e)}"
            }
    
    def exporter_donnees_paie(self, mois: int, annee: int, departement_id: int = None) -> Dict:
        """
        Exporte les données de présence pour intégration dans le calcul de paie
        
        Args:
            mois: Mois à exporter (1-12)
            annee: Année
            departement_id: ID département (optionnel)
            
        Returns:
            Dict avec les données formatées pour la paie
        """
        from calendar import monthrange
        
        # Période du mois
        date_debut = date(annee, mois, 1)
        _, dernier_jour = monthrange(annee, mois)
        date_fin = date(annee, mois, dernier_jour)
        
        # Filtre employés
        employes_query = Employee.objects.filter(is_active=True)
        if departement_id:
            employes_query = employes_query.filter(department_id=departement_id)
        
        employes = employes_query.order_by('matricule')
        
        donnees_paie = {
            'periode': {
                'mois': mois,
                'annee': annee,
                'date_debut': date_debut,
                'date_fin': date_fin
            },
            'employes': [],
            'statistiques_globales': {
                'total_heures_normales': timedelta(0),
                'total_heures_sup': timedelta(0),
                'total_absences': 0,
                'total_retards_minutes': 0
            }
        }
        
        for employe in employes:
            # Récupérer toutes les présences du mois
            presences = PresenceJournaliere.objects.filter(
                employe=employe,
                date__range=[date_debut, date_fin],
                valide=True  # Seulement les présences validées
            )
            
            # Calculer les totaux
            total_heures_travaillees = sum([p.heures_travaillees for p in presences], timedelta(0))
            total_heures_theoriques = sum([p.heures_theoriques for p in presences], timedelta(0))
            total_retard_minutes = sum([p.retard_minutes for p in presences])
            
            # Calculer les heures sup du mois (par semaine)
            heures_sup_details = self._calculer_heures_sup_mensuel(employe, date_debut, date_fin)
            
            # Compter les absences
            nb_absences = presences.filter(statut_jour='ABSENT').count()
            nb_conges = presences.filter(statut_jour='CONGE').count()
            
            # Données employé pour la paie
            employe_data = {
                'employe_id': employe.id,
                'matricule': employe.matricule,
                'nom_complet': f"{employe.last_name} {employe.first_name}",
                'heures_normales': total_heures_travaillees.total_seconds() / 3600,
                'heures_theoriques': total_heures_theoriques.total_seconds() / 3600,
                'heures_supplementaires': {
                    'total': heures_sup_details['total'].total_seconds() / 3600,
                    'taux_25': heures_sup_details['25%'].total_seconds() / 3600,
                    'taux_50': heures_sup_details['50%'].total_seconds() / 3600,
                    'montant_25': heures_sup_details['montant_25'],
                    'montant_50': heures_sup_details['montant_50']
                },
                'absences': {
                    'nb_jours_absences': nb_absences,
                    'nb_jours_conges': nb_conges,
                    'heures_a_decompter': nb_absences * 8  # Estimation 8h/jour
                },
                'retards': {
                    'total_minutes': total_retard_minutes,
                    'montant_retenue': self._calculer_retenue_retards(employe, total_retard_minutes)
                },
                'presences_validees': len(presences),
                'taux_presence': (len(presences) / monthrange(annee, mois)[1]) * 100 if monthrange(annee, mois)[1] > 0 else 0
            }
            
            donnees_paie['employes'].append(employe_data)
            
            # Mise à jour stats globales
            stats = donnees_paie['statistiques_globales']
            stats['total_heures_normales'] += total_heures_travaillees
            stats['total_heures_sup'] += heures_sup_details['total']
            stats['total_absences'] += nb_absences
            stats['total_retards_minutes'] += total_retard_minutes
        
        return donnees_paie
    
    def _calculer_heures_sup_mensuel(self, employe: Employee, date_debut: date, date_fin: date) -> Dict:
        """Calcule les heures supplémentaires sur un mois (semaine par semaine)"""
        heures_sup_total = timedelta(0)
        heures_sup_25 = timedelta(0)
        heures_sup_50 = timedelta(0)
        
        # Parcourir chaque semaine du mois
        current_date = date_debut
        while current_date <= date_fin:
            # Début de semaine (lundi)
            debut_semaine = current_date - timedelta(days=current_date.weekday())
            fin_semaine = debut_semaine + timedelta(days=6)
            
            # Calculer les heures sup de cette semaine
            heures_sup_semaine = self.calculer_heures_supplementaires(employe, debut_semaine, fin_semaine)
            
            heures_sup_total += heures_sup_semaine['heures_sup_total']
            heures_sup_25 += heures_sup_semaine['heures_sup_25']
            heures_sup_50 += heures_sup_semaine['heures_sup_50']
            
            # Semaine suivante
            current_date = fin_semaine + timedelta(days=1)
        
        return {
            'total': heures_sup_total,
            '25%': heures_sup_25,
            '50%': heures_sup_50,
            'montant_25': self._calculer_montant_heures_sup(employe, heures_sup_25, 25),
            'montant_50': self._calculer_montant_heures_sup(employe, heures_sup_50, 50)
        }
    
    def _calculer_retenue_retards(self, employe: Employee, total_retard_minutes: int) -> Decimal:
        """Calcule le montant de retenue pour retards"""
        if total_retard_minutes == 0:
            return Decimal('0.00')
        
        # Appliquer la tolérance
        tolerance = self.regle_active.tolerance_retard_minutes if self.regle_active else 10
        retard_facturable = max(0, total_retard_minutes - tolerance)
        
        if retard_facturable == 0:
            return Decimal('0.00')
        
        # Calculer la retenue (supposé salaire horaire disponible)
        salaire_horaire = getattr(employe, 'salaire_horaire', Decimal('0.00'))
        heures_retard = Decimal(str(retard_facturable / 60))
        
        return salaire_horaire * heures_retard
    
    def _verifier_alertes_pointage(self, employe: Employee, pointage: Pointage):
        """Vérifie et crée les alertes nécessaires après un pointage"""
        try:
            # Alerte retard important
            if pointage.type_pointage == 'ARRIVEE' and pointage.retard_minutes > 30:
                AlertePresence.objects.get_or_create(
                    employe=employe,
                    date_concernee=pointage.heure_pointage.date(),
                    type_alerte='RETARD',
                    defaults={
                        'niveau_gravite': 'ALERTE' if pointage.retard_minutes > 60 else 'ATTENTION',
                        'titre': f'Retard important de {int(pointage.retard_minutes)} minutes',
                        'message': f'Arrivée à {pointage.heure_pointage.strftime("%H:%M")} au lieu de {pointage.heure_theorique.strftime("%H:%M") if pointage.heure_theorique else "N/A"}',
                        'details': {
                            'retard_minutes': pointage.retard_minutes,
                            'heure_pointage': pointage.heure_pointage.isoformat(),
                            'heure_theorique': pointage.heure_theorique.isoformat() if pointage.heure_theorique else None
                        }
                    }
                )
            
            # Vérifier les retards répétés (3 retards dans les 7 derniers jours)
            retards_recents = Pointage.objects.filter(
                employe=employe,
                type_pointage='ARRIVEE',
                statut='RETARD',
                heure_pointage__date__gte=pointage.heure_pointage.date() - timedelta(days=7)
            ).count()
            
            if retards_recents >= 3:
                AlertePresence.objects.get_or_create(
                    employe=employe,
                    date_concernee=pointage.heure_pointage.date(),
                    type_alerte='RETARDS_REPETES',
                    defaults={
                        'niveau_gravite': 'CRITIQUE',
                        'titre': f'{retards_recents} retards dans les 7 derniers jours',
                        'message': 'Retards répétés nécessitant une intervention RH',
                        'actions_recommandees': 'Entretien avec le manager, vérification des horaires'
                    }
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des alertes: {e}")
    
    def get_statut_presence_temps_reel(self) -> Dict:
        """Retourne le statut de présence en temps réel pour tous les employés"""
        aujourd_hui = date.today()
        maintenant = timezone.now()
        
        # Tous les employés actifs
        employes = Employee.objects.filter(is_active=True).select_related('department')
        
        statuts = {
            'presents': [],
            'absents': [],
            'en_pause': [],
            'total_employes': len(employes),
            'timestamp': maintenant.isoformat()
        }
        
        for employe in employes:
            # Vérifier l'horaire de travail aujourd'hui
            horaire = self._get_horaire_employe(employe, aujourd_hui)
            if not horaire:
                continue
            
            # Vérifier si c'est un jour travaillé
            if aujourd_hui.weekday() + 1 not in horaire.jours_travailles_effectifs:
                continue
            
            # Récupérer les pointages du jour
            pointages_jour = Pointage.objects.filter(
                employe=employe,
                heure_pointage__date=aujourd_hui
            ).order_by('heure_pointage')
            
            if not pointages_jour.exists():
                statuts['absents'].append({
                    'employe': employe,
                    'horaire_theorique': horaire.heure_debut_effective.strftime('%H:%M'),
                    'statut': 'ABSENT'
                })
                continue
            
            # Analyser les pointages pour déterminer le statut actuel
            derniers_pointages = list(pointages_jour.values_list('type_pointage', flat=True))
            dernier_pointage = pointages_jour.last()
            
            if 'SORTIE' in derniers_pointages:
                # Employé parti
                continue
            elif derniers_pointages and derniers_pointages[-1] == 'PAUSE_DEBUT':
                # En pause
                statuts['en_pause'].append({
                    'employe': employe,
                    'heure_debut_pause': dernier_pointage.heure_pointage,
                    'duree_pause': maintenant - dernier_pointage.heure_pointage,
                    'statut': 'EN_PAUSE'
                })
            elif 'ARRIVEE' in derniers_pointages:
                # Présent
                pointage_arrivee = pointages_jour.filter(type_pointage='ARRIVEE').first()
                statuts['presents'].append({
                    'employe': employe,
                    'heure_arrivee': pointage_arrivee.heure_pointage,
                    'retard_minutes': pointage_arrivee.retard_minutes,
                    'statut': 'PRESENT'
                })
        
        # Calculer les statistiques
        statuts['statistiques'] = {
            'nb_presents': len(statuts['presents']),
            'nb_absents': len(statuts['absents']),
            'nb_en_pause': len(statuts['en_pause']),
            'taux_presence': (len(statuts['presents']) / statuts['total_employes'] * 100) if statuts['total_employes'] > 0 else 0
        }
        
        return statuts
