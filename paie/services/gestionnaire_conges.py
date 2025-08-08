# paie/services/gestionnaire_conges.py
# Service métier pour la gestion des congés

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timedelta
from django.db import transaction
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from typing import Dict, List, Tuple, Optional
import logging
import json

logger = logging.getLogger(__name__)

class GestionnaireConges:
    """
    Service principal pour la gestion des congés
    Gère les règles métier, calculs, et workflow d'approbation
    """
    
    def __init__(self):
        # Import des modèles ici pour éviter les imports circulaires
        from paie.models import (
            TypeConge, SoldeConge, DemandeConge, 
            ApprobationConge, RegleConge, Employee
        )
        self.TypeConge = TypeConge
        self.SoldeConge = SoldeConge
        self.DemandeConge = DemandeConge
        self.ApprobationConge = ApprobationConge
        self.RegleConge = RegleConge
        self.Employee = Employee
    
    # ================== GESTION DES SOLDES ==================
    
    def calculer_soldes_employe(self, employe, annee=None, type_conge=None):
        """
        Calcule les soldes de congés pour un employé
        
        Args:
            employe: Instance Employee
            annee: Année (défaut: année courante)
            type_conge: TypeConge spécifique (défaut: tous)
        
        Returns:
            Dict avec les soldes calculés
        """
        if annee is None:
            annee = datetime.now().year
        
        try:
            soldes = {}
            
            # Types de congés à traiter
            types_conges = [type_conge] if type_conge else self.TypeConge.objects.filter(actif=True)
            
            for type_c in types_conges:
                solde = self._calculer_solde_type_specifique(employe, type_c, annee)
                soldes[type_c.code] = solde
            
            logger.info(f"Soldes calculés pour {employe} - {annee}")
            return soldes
            
        except Exception as e:
            logger.error(f"Erreur calcul soldes {employe}: {e}")
            raise
    
    def _calculer_solde_type_specifique(self, employe, type_conge, annee):
        """Calcule le solde pour un type de congé spécifique"""
        
        # Récupérer ou créer le solde
        solde, created = self.SoldeConge.objects.get_or_create(
            employe=employe,
            type_conge=type_conge,
            annee=annee,
            defaults={
                'jours_acquis': Decimal('0'),
                'jours_pris': Decimal('0'),
                'jours_reportes': Decimal('0'),
                'ajustement_manuel': Decimal('0'),
            }
        )
        
        if created or self._doit_recalculer_solde(solde):
            # Calcul des jours acquis selon les règles
            jours_acquis = self._calculer_jours_acquis(employe, type_conge, annee)
            
            # Calcul des jours pris (demandes approuvées)
            jours_pris = self._calculer_jours_pris(employe, type_conge, annee)
            
            # Calcul des jours reportés de l'année précédente
            jours_reportes = self._calculer_jours_reportes(employe, type_conge, annee)
            
            # Mise à jour du solde
            solde.jours_acquis = jours_acquis
            solde.jours_pris = jours_pris
            solde.jours_reportes = jours_reportes
            solde.save()
        
        return {
            'type_conge': type_conge,
            'jours_acquis': float(solde.jours_acquis),
            'jours_pris': float(solde.jours_pris),
            'jours_reportes': float(solde.jours_reportes),
            'ajustement_manuel': float(solde.ajustement_manuel),
            'jours_disponibles': float(solde.jours_disponibles),
            'jours_restants': float(solde.jours_restants),
        }
    
    def _calculer_jours_acquis(self, employe, type_conge, annee):
        """Calcule les jours acquis selon les règles du type de congé"""
        
        if type_conge.jours_acquis_par_mois <= 0:
            return Decimal('0')
        
        # Date d'embauche et ancienneté
        if not employe.date_embauche:
            return Decimal('0')
        
        date_debut_annee = date(annee, 1, 1)
        date_fin_annee = date(annee, 12, 31)
        
        # Date de début de calcul (embauche ou début d'année)
        date_debut = max(employe.date_embauche, date_debut_annee)
        
        # Vérifier ancienneté minimum
        anciennete_mois = self._calculer_anciennete_mois(employe.date_embauche, date_debut)
        if anciennete_mois < type_conge.anciennete_minimum_mois:
            return Decimal('0')
        
        # Calculer les mois travaillés dans l'année
        if date_debut > date_fin_annee:
            return Decimal('0')
        
        date_fin_calcul = min(date.today(), date_fin_annee)
        if date_fin_calcul < date_debut:
            return Decimal('0')
        
        # Nombre de mois complets + prorata du mois partiel
        mois_complets = 0
        current_date = date_debut
        
        while current_date <= date_fin_calcul:
            if current_date.day == 1:
                # Mois complet
                mois_complets += 1
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            else:
                # Mois partiel - calculer prorata
                jours_dans_mois = self._jours_dans_mois(current_date.year, current_date.month)
                jours_travailles = jours_dans_mois - current_date.day + 1
                
                if date_fin_calcul.month == current_date.month and date_fin_calcul.year == current_date.year:
                    jours_travailles = date_fin_calcul.day - current_date.day + 1
                
                prorata = Decimal(str(jours_travailles)) / Decimal(str(jours_dans_mois))
                mois_complets += float(prorata)
                break
        
        jours_acquis = Decimal(str(mois_complets)) * type_conge.jours_acquis_par_mois
        return jours_acquis.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculer_jours_pris(self, employe, type_conge, annee):
        """Calcule les jours pris (demandes approuvées) pour l'année"""
        
        demandes_approuvees = self.DemandeConge.objects.filter(
            employe=employe,
            type_conge=type_conge,
            statut__in=['APPROUVEE', 'EN_COURS', 'TERMINEE'],
            date_debut__year=annee
        )
        
        total_jours = sum(
            demande.nb_jours_ouvrables for demande in demandes_approuvees
        )
        
        return Decimal(str(total_jours))
    
    def _calculer_jours_reportes(self, employe, type_conge, annee):
        """Calcule les jours reportés de l'année précédente"""
        
        if not type_conge.report_autorise or annee <= employe.date_embauche.year:
            return Decimal('0')
        
        try:
            solde_precedent = self.SoldeConge.objects.get(
                employe=employe,
                type_conge=type_conge,
                annee=annee - 1
            )
            
            jours_restants = solde_precedent.jours_disponibles
            if jours_restants > 0:
                # Appliquer les règles de report (max 5 jours par exemple)
                max_report = getattr(type_conge, 'max_jours_report', 5)
                return min(jours_restants, Decimal(str(max_report)))
            
        except self.SoldeConge.DoesNotExist:
            pass
        
        return Decimal('0')
    
    # ================== VALIDATION DES DEMANDES ==================
    
    def valider_demande_conge(self, demande_data, employe, user=None):
        """
        Valide une demande de congé selon les règles métier
        
        Args:
            demande_data: Dict avec les données de la demande
            employe: Instance Employee
            user: Utilisateur créant la demande
        
        Returns:
            Dict avec résultat validation et erreurs éventuelles
        """
        erreurs = []
        warnings = []
        
        try:
            # Validation des dates
            date_debut = demande_data['date_debut']
            date_fin = demande_data['date_fin']
            type_conge = demande_data['type_conge']
            
            if isinstance(date_debut, str):
                date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
            if isinstance(date_fin, str):
                date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
            
            # 1. Validation des dates de base
            if date_debut > date_fin:
                erreurs.append("La date de fin doit être postérieure à la date de début")
            
            if date_debut < date.today():
                erreurs.append("La date de début ne peut pas être dans le passé")
            
            # 2. Calcul du nombre de jours
            nb_jours_calendaires = (date_fin - date_debut).days + 1
            nb_jours_ouvrables = self.calculer_jours_ouvrables(date_debut, date_fin, type_conge.decompte_weekend)
            
            # 3. Validation des soldes
            if type_conge.categorie in ['LEGAL', 'FORMATION']:
                annee = date_debut.year
                solde = self._calculer_solde_type_specifique(employe, type_conge, annee)
                
                if nb_jours_ouvrables > solde['jours_disponibles']:
                    erreurs.append(f"Solde insuffisant. Disponible: {solde['jours_disponibles']} jours")
            
            # 4. Validation des règles spécifiques
            erreurs_regles = self._valider_regles_metier(demande_data, employe)
            erreurs.extend(erreurs_regles)
            
            # 5. Validation des conflits
            conflits = self._detecter_conflits_planning(employe, date_debut, date_fin)
            if conflits:
                warnings.extend(conflits)
            
            # 6. Validation justificatifs
            if type_conge.justificatif_requis and not demande_data.get('justificatif'):
                erreurs.append(f"Un justificatif est requis pour ce type de congé")
            
            return {
                'valide': len(erreurs) == 0,
                'erreurs': erreurs,
                'warnings': warnings,
                'nb_jours_calendaires': nb_jours_calendaires,
                'nb_jours_ouvrables': nb_jours_ouvrables,
                'solde_apres': solde['jours_disponibles'] - nb_jours_ouvrables if len(erreurs) == 0 else None
            }
            
        except Exception as e:
            logger.error(f"Erreur validation demande: {e}")
            return {
                'valide': False,
                'erreurs': [f"Erreur système: {str(e)}"],
                'warnings': [],
                'nb_jours_calendaires': 0,
                'nb_jours_ouvrables': 0
            }
    
    def _valider_regles_metier(self, demande_data, employe):
        """Valide les règles métier configurables"""
        erreurs = []
        
        regles = self.RegleConge.objects.filter(
            actif=True,
            types_conge=demande_data['type_conge']
        )
        
        for regle in regles:
            if regle.type_regle == 'VALIDATION':
                parametres = regle.parametres
                
                # Exemple de règles configurables
                if 'max_jours_consecutifs' in parametres:
                    nb_jours = (demande_data['date_fin'] - demande_data['date_debut']).days + 1
                    if nb_jours > parametres['max_jours_consecutifs']:
                        erreurs.append(f"Maximum {parametres['max_jours_consecutifs']} jours consécutifs autorisés")
                
                if 'delai_minimum_demande' in parametres:
                    delai = (demande_data['date_debut'] - date.today()).days
                    if delai < parametres['delai_minimum_demande']:
                        erreurs.append(f"Demande doit être faite {parametres['delai_minimum_demande']} jours à l'avance")
        
        return erreurs
    
    def _detecter_conflits_planning(self, employe, date_debut, date_fin):
        """Détecte les conflits de planning"""
        warnings = []
        
        # Vérifier chevauchement avec autres demandes
        demandes_existantes = self.DemandeConge.objects.filter(
            employe=employe,
            statut__in=['SOUMISE', 'EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH', 'APPROUVEE'],
            date_fin__gte=date_debut,
            date_debut__lte=date_fin
        )
        
        if demandes_existantes.exists():
            warnings.append("Chevauchement avec une demande existante")
        
        # Vérifier absence simultanée dans l'équipe (si règle configurée)
        if employe.department:
            demandes_equipe = self.DemandeConge.objects.filter(
                employe__department=employe.department,
                statut='APPROUVEE',
                date_fin__gte=date_debut,
                date_debut__lte=date_fin
            ).exclude(employe=employe)
            
            if demandes_equipe.count() >= 2:  # Plus de 2 personnes absentes
                warnings.append("Plusieurs collègues déjà en congé sur cette période")
        
        return warnings
    
    # ================== WORKFLOW D'APPROBATION ==================
    
    @transaction.atomic
    def soumettre_demande(self, demande_data, employe, user=None):
        """Soumet une nouvelle demande de congé"""
        
        try:
            # Validation préalable
            validation = self.valider_demande_conge(demande_data, employe, user)
            if not validation['valide']:
                return {
                    'success': False,
                    'erreurs': validation['erreurs'],
                    'warnings': validation['warnings']
                }
            
            # Calculer la date de reprise (jour ouvrable suivant la date_fin)
            date_reprise = demande_data['date_fin'] + timedelta(days=1)
            # Ajuster au prochain jour ouvrable si c'est un weekend
            while date_reprise.weekday() >= 5:  # 5=samedi, 6=dimanche
                date_reprise += timedelta(days=1)
            
            # Créer la demande
            demande = self.DemandeConge.objects.create(
                employe=employe,
                type_conge=demande_data['type_conge'],
                date_debut=demande_data['date_debut'],
                date_fin=demande_data['date_fin'],
                date_reprise=date_reprise,
                motif=demande_data.get('motif', ''),
                nb_jours_demandes=validation['nb_jours_calendaires'],
                nb_jours_ouvrables=validation['nb_jours_ouvrables'],
                priorite=demande_data.get('priorite', 'NORMALE'),
                statut='SOUMISE',
                cree_par=user,
                manager_assigne=employe.manager if hasattr(employe, 'manager') else None
            )
            
            # Enregistrer l'action
            self._enregistrer_action(demande, 'SOUMISSION', user, 'EMPLOYE')
            
            # Déterminer le workflow suivant
            self._avancer_workflow(demande)
            
            # Notifications
            self._envoyer_notifications_soumission(demande)
            
            logger.info(f"Demande soumise: {demande.numero_demande}")
            
            return {
                'success': True,
                'demande_id': demande.id,
                'numero_demande': demande.numero_demande,
                'statut': demande.statut,
                'warnings': validation['warnings']
            }
            
        except Exception as e:
            logger.error(f"Erreur soumission demande: {e}")
            return {
                'success': False,
                'erreurs': [f"Erreur système: {str(e)}"]
            }
    
    @transaction.atomic
    def approuver_demande(self, demande_id, user, commentaire="", role=""):
        """Approuve une demande selon le workflow"""
        
        try:
            demande = self.DemandeConge.objects.get(id=demande_id)
            
            # Vérifier les permissions
            if not self._peut_approuver(demande, user, role):
                return {
                    'success': False,
                    'erreur': 'Permissions insuffisantes pour approuver cette demande'
                }
            
            # Déterminer la nouvelle action selon le statut actuel
            ancien_statut = demande.statut
            
            if demande.statut == 'EN_ATTENTE_MANAGER':
                demande.statut = 'EN_ATTENTE_RH'
                action = 'APPROBATION_MANAGER'
            elif demande.statut == 'EN_ATTENTE_RH':
                demande.statut = 'APPROUVEE'
                action = 'APPROBATION_RH'
            else:
                return {
                    'success': False,
                    'erreur': f'Impossible d\'approuver une demande au statut {demande.statut}'
                }
            
            demande.save()
            
            # Enregistrer l'action
            self._enregistrer_action(demande, action, user, role, commentaire, ancien_statut)
            
            # Mettre à jour les soldes si demande complètement approuvée
            if demande.statut == 'APPROUVEE':
                self._mettre_a_jour_soldes(demande)
            
            # Notifications
            self._envoyer_notifications_approbation(demande, action)
            
            logger.info(f"Demande approuvée: {demande.numero_demande} par {user}")
            
            return {
                'success': True,
                'nouveau_statut': demande.statut,
                'action': action
            }
            
        except self.DemandeConge.DoesNotExist:
            return {
                'success': False,
                'erreur': 'Demande introuvable'
            }
        except Exception as e:
            logger.error(f"Erreur approbation demande {demande_id}: {e}")
            return {
                'success': False,
                'erreur': f'Erreur système: {str(e)}'
            }
    
    @transaction.atomic
    def refuser_demande(self, demande_id, user, commentaire="", role=""):
        """Refuse une demande"""
        
        try:
            demande = self.DemandeConge.objects.get(id=demande_id)
            
            if not self._peut_approuver(demande, user, role):
                return {
                    'success': False,
                    'erreur': 'Permissions insuffisantes'
                }
            
            ancien_statut = demande.statut
            demande.statut = 'REFUSEE'
            demande.save()
            
            # Déterminer l'action selon qui refuse
            action = 'REFUS_MANAGER' if 'MANAGER' in ancien_statut else 'REFUS_RH'
            
            self._enregistrer_action(demande, action, user, role, commentaire, ancien_statut)
            
            # Notifications
            self._envoyer_notifications_refus(demande, commentaire)
            
            logger.info(f"Demande refusée: {demande.numero_demande} par {user}")
            
            return {
                'success': True,
                'nouveau_statut': demande.statut
            }
            
        except Exception as e:
            logger.error(f"Erreur refus demande {demande_id}: {e}")
            return {
                'success': False,
                'erreur': f'Erreur système: {str(e)}'
            }
    
    # ================== UTILITAIRES ==================
    
    def calculer_jours_ouvrables(self, date_debut, date_fin, inclure_weekend=False):
        """Calcule le nombre de jours ouvrables entre deux dates"""
        
        if date_debut > date_fin:
            return 0
        
        jours_total = (date_fin - date_debut).days + 1
        
        if inclure_weekend:
            return jours_total
        
        # Exclure weekends
        jours_ouvrables = 0
        current_date = date_debut
        
        while current_date <= date_fin:
            if current_date.weekday() < 5:  # Lundi=0, Vendredi=4
                jours_ouvrables += 1
            current_date += timedelta(days=1)
        
        # TODO: Exclure les jours fériés configurés
        
        return jours_ouvrables
    
    def generer_planning_equipe(self, departement=None, mois=None, annee=None):
        """Génère le planning des congés pour une équipe"""
        
        if mois is None:
            mois = datetime.now().month
        if annee is None:
            annee = datetime.now().year
        
        # Dates du mois
        date_debut = date(annee, mois, 1)
        if mois == 12:
            date_fin = date(annee + 1, 1, 1) - timedelta(days=1)
        else:
            date_fin = date(annee, mois + 1, 1) - timedelta(days=1)
        
        # Employés concernés
        employes = self.Employee.objects.filter(is_active=True)
        if departement:
            employes = employes.filter(department=departement)
        
        # Congés du mois
        conges = self.DemandeConge.objects.filter(
            statut__in=['APPROUVEE', 'EN_COURS'],
            date_fin__gte=date_debut,
            date_debut__lte=date_fin,
            employe__in=employes
        ).select_related('employe', 'type_conge')
        
        # Organiser par employé
        planning = {}
        for employe in employes:
            planning[employe] = {
                'conges': [c for c in conges if c.employe == employe],
                'jours_absents': sum(
                    self.calculer_jours_ouvrables(
                        max(c.date_debut, date_debut),
                        min(c.date_fin, date_fin)
                    ) for c in conges if c.employe == employe
                )
            }
        
        return {
            'periode': f"{mois:02d}/{annee}",
            'date_debut': date_debut,
            'date_fin': date_fin,
            'departement': departement,
            'planning': planning,
            'total_jours_ouvrables': self.calculer_jours_ouvrables(date_debut, date_fin),
        }
    
    # ================== MÉTHODES PRIVÉES ==================
    
    def _doit_recalculer_solde(self, solde):
        """Détermine si un solde doit être recalculé"""
        # Recalculer si dernière MAJ > 24h ou si données manquantes
        if not solde.date_derniere_maj:
            return True
        
        delta = datetime.now() - solde.date_derniere_maj.replace(tzinfo=None)
        return delta.total_seconds() > 86400  # 24h
    
    def _calculer_anciennete_mois(self, date_embauche, date_reference):
        """Calcule l'ancienneté en mois"""
        if not date_embauche:
            return 0
        
        delta = date_reference - date_embauche
        return int(delta.days / 30.44)  # Moyenne de jours par mois
    
    def _jours_dans_mois(self, annee, mois):
        """Retourne le nombre de jours dans un mois"""
        if mois == 12:
            return (date(annee + 1, 1, 1) - date(annee, mois, 1)).days
        else:
            return (date(annee, mois + 1, 1) - date(annee, mois, 1)).days
    
    def _avancer_workflow(self, demande):
        """Avance automatiquement le workflow selon les règles"""
        
        if demande.statut == 'SOUMISE':
            # Si manager assigné, passer en attente manager
            if demande.manager_assigne:
                demande.statut = 'EN_ATTENTE_MANAGER'
            else:
                # Sinon directement en attente RH
                demande.statut = 'EN_ATTENTE_RH'
            demande.save()
    
    def _peut_approuver(self, demande, user, role):
        """Vérifie si l'utilisateur peut approuver la demande"""
        
        if user.is_superuser:
            return True
        
        if demande.statut == 'EN_ATTENTE_MANAGER':
            return (role == 'MANAGER' and demande.manager_assigne == user) or role == 'RH'
        
        if demande.statut == 'EN_ATTENTE_RH':
            return role == 'RH'
        
        return False
    
    def _enregistrer_action(self, demande, action, user, role, commentaire="", statut_precedent=""):
        """Enregistre une action dans l'historique"""
        
        self.ApprobationConge.objects.create(
            demande=demande,
            action=action,
            utilisateur=user,
            role_utilisateur=role,
            commentaire=commentaire,
            statut_precedent=statut_precedent,
            statut_nouveau=demande.statut
        )
    
    def _mettre_a_jour_soldes(self, demande):
        """Met à jour les soldes après approbation"""
        
        # Recalculer le solde pour s'assurer de la cohérence
        self.calculer_soldes_employe(
            demande.employe, 
            demande.date_debut.year, 
            demande.type_conge
        )
    
    def _envoyer_notifications_soumission(self, demande):
        """Envoie les notifications de soumission"""
        
        try:
            if demande.manager_assigne and demande.manager_assigne.email:
                send_mail(
                    subject=f"Nouvelle demande de congé - {demande.employe}",
                    message=f"Une nouvelle demande de congé nécessite votre approbation.\n\n"
                           f"Employé: {demande.employe}\n"
                           f"Période: {demande.date_debut} au {demande.date_fin}\n"
                           f"Type: {demande.type_conge}\n"
                           f"Motif: {demande.motif}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[demande.manager_assigne.email],
                    fail_silently=True
                )
        except Exception as e:
            logger.warning(f"Erreur envoi notification: {e}")
    
    def _envoyer_notifications_approbation(self, demande, action):
        """Envoie les notifications d'approbation"""
        
        try:
            if demande.employe.email:
                statut_readable = demande.get_statut_display()
                send_mail(
                    subject=f"Demande de congé {statut_readable.lower()}",
                    message=f"Votre demande de congé a été mise à jour.\n\n"
                           f"Statut: {statut_readable}\n"
                           f"Période: {demande.date_debut} au {demande.date_fin}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[demande.employe.email],
                    fail_silently=True
                )
        except Exception as e:
            logger.warning(f"Erreur envoi notification: {e}")
    
    def _envoyer_notifications_refus(self, demande, motif):
        """Envoie les notifications de refus"""
        
        try:
            if demande.employe.email:
                send_mail(
                    subject="Demande de congé refusée",
                    message=f"Votre demande de congé a été refusée.\n\n"
                           f"Période: {demande.date_debut} au {demande.date_fin}\n"
                           f"Motif du refus: {motif}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[demande.employe.email],
                    fail_silently=True
                )
        except Exception as e:
            logger.warning(f"Erreur envoi notification: {e}")

# ================== FONCTIONS UTILITAIRES GLOBALES ==================

def initialiser_soldes_employe(employe, annee=None):
    """Fonction utilitaire pour initialiser les soldes d'un nouvel employé"""
    
    if annee is None:
        annee = datetime.now().year
    
    gestionnaire = GestionnaireConges()
    return gestionnaire.calculer_soldes_employe(employe, annee)

def recalculer_tous_soldes(annee=None):
    """Recalcule tous les soldes de congés (tâche planifiée)"""
    
    if annee is None:
        annee = datetime.now().year
    
    from paie.models import Employee
    
    gestionnaire = GestionnaireConges()
    employes = Employee.objects.filter(is_active=True)
    
    results = {
        'traites': 0,
        'erreurs': 0,
        'employes_erreur': []
    }
    
    for employe in employes:
        try:
            gestionnaire.calculer_soldes_employe(employe, annee)
            results['traites'] += 1
        except Exception as e:
            results['erreurs'] += 1
            results['employes_erreur'].append(f"{employe}: {str(e)}")
            logger.error(f"Erreur recalcul solde {employe}: {e}")
    
    logger.info(f"Recalcul soldes terminé - Traités: {results['traites']}, Erreurs: {results['erreurs']}")
    return results