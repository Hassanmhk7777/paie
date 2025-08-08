# paie/management/commands/init_attendance_module.py
# Script Django pour initialiser le module Pointage & Présence avec des données de test

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.utils import timezone
from datetime import datetime, date, time, timedelta
import random
from decimal import Decimal

from paie.models import (
    # Modèles existants (supposés)
    Employee, Departement,
    # Nouveaux modèles du module pointage
    PlageHoraire, HoraireTravail, ReglePointage, Pointage, 
    PresenceJournaliere, ValidationPresence, AlertePresence
)


class Command(BaseCommand):
    help = 'Initialise le module Pointage & Présence avec des données de test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full-demo',
            action='store_true',
            help='Créer un jeu de données complet avec historique (30 jours)',
        )
        parser.add_argument(
            '--employees-count',
            type=int,
            default=20,
            help='Nombre d\'employés à créer (défaut: 20)',
        )
        parser.add_argument(
            '--days-history',
            type=int,
            default=7,
            help='Nombre de jours d\'historique à générer (défaut: 7)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Initialisation du Module Pointage & Présence PAIEPRO')
        )

        try:
            # 1. Créer les groupes et permissions
            self.create_groups_and_permissions()

            # 2. Créer les départements si ils n'existent pas
            self.create_departments()

            # 3. Créer les employés de test si ils n'existent pas
            employees_count = options['employees_count']
            self.create_test_employees(employees_count)

            # 4. Créer les plages horaires standard
            self.create_time_slots()

            # 5. Créer les règles de pointage
            self.create_attendance_rules()

            # 6. Assigner des horaires aux employés
            self.assign_employee_schedules()

            # 7. Générer un historique de pointages
            days_history = options['days_history']
            if options['full_demo']:
                days_history = 30
            self.generate_attendance_history(days_history)

            # 8. Créer quelques alertes exemples
            self.create_sample_alerts()

            # 9. Afficher le récapitulatif
            self.display_summary()

            self.stdout.write(
                self.style.SUCCESS('✅ Module Pointage & Présence initialisé avec succès!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de l\'initialisation: {str(e)}')
            )
            raise

    def create_groups_and_permissions(self):
        """Créer les groupes et permissions pour le module pointage"""
        self.stdout.write('📋 Création des groupes et permissions...')

        # Créer les permissions personnalisées
        permissions_data = [
            ('can_manage_attendance', 'Peut gérer les présences'),
            ('can_point_for_others', 'Peut pointer pour d\'autres employés'),
            ('can_validate_attendance', 'Peut valider les présences'),
            ('can_correct_pointage', 'Peut corriger les pointages'),
            ('can_export_attendance', 'Peut exporter les données'),
            ('can_manage_schedules', 'Peut gérer les horaires'),
            ('can_view_reports', 'Peut voir les rapports'),
            ('can_admin_attendance', 'Administration du pointage'),
        ]

        # Créer les groupes
        groups_data = [
            ('RH Pointage', ['can_manage_attendance', 'can_validate_attendance', 
                           'can_export_attendance', 'can_view_reports']),
            ('Manager Pointage', ['can_validate_attendance', 'can_view_reports']),
            ('Operateur Pointage', ['can_point_for_others']),
            ('Admin Pointage', ['can_admin_attendance', 'can_manage_schedules']),
        ]

        for group_name, group_permissions in groups_data:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'  ✓ Groupe créé: {group_name}')

        self.stdout.write('  ✓ Groupes et permissions configurés')

    def create_departments(self):
        """Créer les départements de test"""
        self.stdout.write('🏢 Création des départements...')

        departments = [
            {'nom': 'Direction Générale', 'code': 'DG'},
            {'nom': 'Ressources Humaines', 'code': 'RH'},
            {'nom': 'Informatique', 'code': 'IT'},
            {'nom': 'Commercial', 'code': 'COM'},
            {'nom': 'Production', 'code': 'PROD'},
            {'nom': 'Logistique', 'code': 'LOG'},
            {'nom': 'Comptabilité', 'code': 'COMPTA'},
            {'nom': 'Marketing', 'code': 'MKT'},
        ]

        for dept_data in departments:
            dept, created = Departement.objects.get_or_create(
                code=dept_data['code'],
                defaults={
                    'nom': dept_data['nom'],
                    'actif': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Département créé: {dept.nom}')

    def create_test_employees(self, count):
        """Créer des employés de test"""
        self.stdout.write(f'👥 Création de {count} employés de test...')

        # Données de test pour les employés
        first_names = [
            'Ahmed', 'Fatima', 'Mohammed', 'Aisha', 'Omar', 'Khadija', 'Ali', 'Zahra',
            'Hassan', 'Layla', 'Youssef', 'Nadia', 'Khalid', 'Samira', 'Rachid', 'Amina',
            'Karim', 'Malika', 'Abdelkader', 'Zohra', 'Said', 'Aicha', 'Mustapha', 'Latifa'
        ]
        
        last_names = [
            'Alami', 'Benali', 'Cherkaoui', 'Darif', 'El Fassi', 'Ghazi', 'Hajji', 'Idrissi',
            'Jabbari', 'Kadiri', 'Lamrani', 'Mansouri', 'Naciri', 'Ouali', 'Qadiri', 'Rifai',
            'Semlali', 'Tazi', 'Umayyad', 'Wahabi', 'Yachaoui', 'Zaidi', 'Alaoui', 'Berberi'
        ]

        departements = list(Departement.objects.all())
        
        for i in range(count):
            if Employee.objects.filter(matricule=f'EMP{i+1:03d}').exists():
                continue

            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            employee = Employee.objects.create(
                matricule=f'EMP{i+1:03d}',
                nom=last_name,
                prenom=first_name,
                email=f'{first_name.lower()}.{last_name.lower()}@paiepro.ma',
                telephone=f'06{random.randint(10000000, 99999999)}',
                date_naissance=date(1980 + random.randint(0, 25), random.randint(1, 12), random.randint(1, 28)),
                date_embauche=date(2020 + random.randint(0, 3), random.randint(1, 12), random.randint(1, 28)),
                departement=random.choice(departements),
                poste=random.choice(['Employé', 'Technicien', 'Cadre', 'Responsable']),
                salaire_base=Decimal(str(random.randint(4000, 15000))),
                actif=True
            )
            
            if i == 0:  # Premier employé créé
                self.stdout.write(f'  ✓ Employé créé: {employee.prenom} {employee.nom}')

        self.stdout.write(f'  ✓ {count} employés créés')

    def create_time_slots(self):
        """Créer les plages horaires standard"""
        self.stdout.write('⏰ Création des plages horaires...')

        time_slots = [
            {
                'nom': 'Horaire Standard',
                'type_plage': 'STANDARD',
                'heure_debut': time(8, 0),
                'heure_fin': time(17, 0),
                'heure_debut_pause': time(12, 0),
                'heure_fin_pause': time(13, 0),
                'duree_pause': timedelta(hours=1),
                'jours_travailles': [1, 2, 3, 4, 5],  # Lun-Ven
            },
            {
                'nom': 'Horaire Flexible',
                'type_plage': 'FLEXIBLE',
                'heure_debut': time(8, 0),
                'heure_fin': time(17, 0),
                'duree_pause': timedelta(hours=1),
                'tolerance_arrivee': timedelta(hours=1),
                'tolerance_depart': timedelta(hours=1),
                'jours_travailles': [1, 2, 3, 4, 5],
            },
            {
                'nom': 'Équipe Matin',
                'type_plage': 'EQUIPE_MATIN',
                'heure_debut': time(6, 0),
                'heure_fin': time(14, 0),
                'heure_debut_pause': time(10, 0),
                'heure_fin_pause': time(10, 30),
                'duree_pause': timedelta(minutes=30),
                'jours_travailles': [1, 2, 3, 4, 5, 6],  # Lun-Sam
            },
            {
                'nom': 'Équipe Soir',
                'type_plage': 'EQUIPE_SOIR',
                'heure_debut': time(14, 0),
                'heure_fin': time(22, 0),
                'heure_debut_pause': time(18, 0),
                'heure_fin_pause': time(18, 30),
                'duree_pause': timedelta(minutes=30),
                'jours_travailles': [1, 2, 3, 4, 5, 6],
            },
            {
                'nom': 'Temps Partiel Matin',
                'type_plage': 'TEMPS_PARTIEL',
                'heure_debut': time(8, 0),
                'heure_fin': time(12, 0),
                'duree_pause': timedelta(minutes=15),
                'jours_travailles': [1, 2, 3, 4, 5],
            },
            {
                'nom': 'Horaire Cadre',
                'type_plage': 'CADRE',
                'heure_debut': time(9, 0),
                'heure_fin': time(18, 0),
                'duree_pause': timedelta(hours=1, minutes=30),
                'tolerance_arrivee': timedelta(hours=2),
                'tolerance_depart': timedelta(hours=2),
                'jours_travailles': [1, 2, 3, 4, 5],
            }
        ]

        for slot_data in time_slots:
            plage, created = PlageHoraire.objects.get_or_create(
                nom=slot_data['nom'],
                defaults=slot_data
            )
            if created:
                self.stdout.write(f'  ✓ Plage horaire créée: {plage.nom}')

        self.stdout.write('  ✓ Plages horaires créées')

    def create_attendance_rules(self):
        """Créer les règles de pointage"""
        self.stdout.write('📋 Création des règles de pointage...')

        # Règle standard marocaine
        regle, created = ReglePointage.objects.get_or_create(
            nom='Règles Standard Maroc 2024',
            defaults={
                'description': 'Règles de pointage conformes à la législation marocaine',
                'tolerance_retard_minutes': 10,
                'tolerance_depart_anticipe_minutes': 10,
                'seuil_retard_alerte_minutes': 15,
                'nb_retards_alerte_mois': 3,
                'nb_absences_alerte_mois': 2,
                'seuil_heures_sup_jour': timedelta(hours=8),
                'seuil_heures_sup_semaine': timedelta(hours=44),
                'taux_majoration_25': Decimal('25.00'),
                'taux_majoration_50': Decimal('50.00'),
                'duree_pause_max_sans_retenue': timedelta(hours=1),
                'pause_payee': True,
                'validation_auto_seuil_minutes': 15,
                'validation_obligatoire_weekend': True,
                'validation_obligatoire_feries': True,
                'date_debut': date.today(),
                'actif': True,
            }
        )

        if created:
            self.stdout.write('  ✓ Règle de pointage créée')
        else:
            self.stdout.write('  ✓ Règle de pointage existe déjà')

    def assign_employee_schedules(self):
        """Assigner des horaires aux employés"""
        self.stdout.write('📅 Attribution des horaires aux employés...')

        employees = Employee.objects.filter(actif=True)
        plages = list(PlageHoraire.objects.filter(actif=True))

        for employee in employees:
            # Éviter les doublons
            if HoraireTravail.objects.filter(employe=employee, actif=True).exists():
                continue

            # Attribution selon le département
            if employee.departement:
                if 'Direction' in employee.departement.nom:
                    plage = PlageHoraire.objects.get(nom='Horaire Cadre')
                elif 'Production' in employee.departement.nom:
                    plage = random.choice([
                        PlageHoraire.objects.get(nom='Équipe Matin'),
                        PlageHoraire.objects.get(nom='Équipe Soir')
                    ])
                elif 'RH' in employee.departement.nom or 'IT' in employee.departement.nom:
                    plage = PlageHoraire.objects.get(nom='Horaire Flexible')
                else:
                    plage = PlageHoraire.objects.get(nom='Horaire Standard')
            else:
                plage = random.choice(plages)

            HoraireTravail.objects.create(
                employe=employee,
                plage_horaire=plage,
                date_debut=employee.date_embauche or date.today() - timedelta(days=30),
                actif=True
            )

        self.stdout.write('  ✓ Horaires attribués à tous les employés')

    def generate_attendance_history(self, days):
        """Générer un historique de pointages"""
        self.stdout.write(f'📊 Génération de {days} jours d\'historique...')

        employees = Employee.objects.filter(actif=True)
        today = date.today()

        for day_offset in range(days):
            current_date = today - timedelta(days=day_offset)
            
            # Ignorer les dimanches (jour de repos au Maroc)
            if current_date.weekday() == 6:
                continue

            for employee in employees:
                horaire = HoraireTravail.objects.filter(
                    employe=employee,
                    actif=True,
                    date_debut__lte=current_date
                ).first()

                if not horaire:
                    continue

                # Vérifier si c'est un jour travaillé
                jour_semaine = current_date.weekday() + 1
                if jour_semaine not in horaire.jours_travailles_effectifs:
                    continue

                # Probabilité de présence (90% de chance d'être présent)
                if random.random() < 0.1:  # 10% d'absence
                    # Créer une entrée d'absence
                    PresenceJournaliere.objects.get_or_create(
                        employe=employee,
                        date=current_date,
                        defaults={
                            'horaire_travail': horaire,
                            'statut_jour': 'ABSENT',
                            'heures_theoriques': horaire.plage_horaire.duree_theorique,
                        }
                    )
                    continue

                # Générer les pointages pour cet employé
                self.generate_employee_day_attendance(employee, horaire, current_date)

        self.stdout.write('  ✓ Historique de pointages généré')

    def generate_employee_day_attendance(self, employee, horaire, date_pointage):
        """Générer les pointages d'un employé pour une journée"""
        base_datetime = datetime.combine(date_pointage, time(0, 0))
        
        # Heure d'arrivée (avec variation aléatoire)
        heure_theorique_arrivee = datetime.combine(date_pointage, horaire.heure_debut_effective)
        variation_arrivee = random.randint(-15, 30)  # Entre 15 min d'avance et 30 min de retard
        heure_arrivee = heure_theorique_arrivee + timedelta(minutes=variation_arrivee)

        # Pointage arrivée
        pointage_arrivee = Pointage.objects.create(
            employe=employee,
            type_pointage='ARRIVEE',
            heure_pointage=heure_arrivee,
            heure_theorique=heure_theorique_arrivee,
            statut='RETARD' if variation_arrivee > 15 else 'NORMAL'
        )

        # Pause déjeuner (si définie)
        if horaire.plage_horaire.heure_debut_pause:
            pause_debut = datetime.combine(
                date_pointage, 
                horaire.plage_horaire.heure_debut_pause
            ) + timedelta(minutes=random.randint(-10, 15))

            pause_fin = datetime.combine(
                date_pointage,
                horaire.plage_horaire.heure_fin_pause
            ) + timedelta(minutes=random.randint(-5, 10))

            Pointage.objects.create(
                employe=employee,
                type_pointage='PAUSE_DEBUT',
                heure_pointage=pause_debut,
            )

            Pointage.objects.create(
                employe=employee,
                type_pointage='PAUSE_FIN',
                heure_pointage=pause_fin,
            )

        # Heure de sortie (avec variation aléatoire)
        heure_theorique_sortie = datetime.combine(date_pointage, horaire.heure_fin_effective)
        variation_sortie = random.randint(-30, 60)  # Entre 30 min plus tôt et 1h plus tard
        heure_sortie = heure_theorique_sortie + timedelta(minutes=variation_sortie)

        # 20% de chance de ne pas pointer la sortie (oubli)
        if random.random() < 0.8:
            Pointage.objects.create(
                employe=employee,
                type_pointage='SORTIE',
                heure_pointage=heure_sortie,
                heure_theorique=heure_theorique_sortie,
            )

        # Calculer et créer la présence journalière
        from paie.services.gestionnaire_pointage import GestionnairePointage
        gestionnaire = GestionnairePointage()
        gestionnaire._mettre_a_jour_presence_journaliere(employee, date_pointage)

    def create_sample_alerts(self):
        """Créer quelques alertes d'exemple"""
        self.stdout.write('🚨 Création d\'alertes d\'exemple...')

        employees = list(Employee.objects.filter(actif=True)[:5])
        
        alert_types = [
            ('RETARD', 'ATTENTION', 'Retard de plus de 20 minutes'),
            ('ABSENCE', 'ALERTE', 'Absence injustifiée détectée'),
            ('RETARDS_REPETES', 'CRITIQUE', '3 retards cette semaine'),
            ('OUBLI_POINTAGE', 'ATTENTION', 'Oubli de pointage de sortie'),
        ]

        for i, (type_alerte, gravite, titre) in enumerate(alert_types):
            if i < len(employees):
                AlertePresence.objects.create(
                    type_alerte=type_alerte,
                    niveau_gravite=gravite,
                    employe=employees[i],
                    date_concernee=date.today() - timedelta(days=random.randint(0, 3)),
                    titre=titre,
                    message=f'Alerte automatique générée pour {employees[i].prenom} {employees[i].nom}',
                    details={'generated': True, 'demo': True}
                )

        self.stdout.write('  ✓ Alertes d\'exemple créées')

    def display_summary(self):
        """Afficher un résumé de l'initialisation"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📈 RÉSUMÉ DE L\'INITIALISATION'))
        self.stdout.write('='*60)

        # Compter les éléments créés
        stats = {
            'Départements': Departement.objects.count(),
            'Employés': Employee.objects.filter(actif=True).count(),
            'Plages horaires': PlageHoraire.objects.filter(actif=True).count(),
            'Règles de pointage': ReglePointage.objects.filter(actif=True).count(),
            'Horaires assignés': HoraireTravail.objects.filter(actif=True).count(),
            'Pointages générés': Pointage.objects.count(),
            'Présences journalières': PresenceJournaliere.objects.count(),
            'Alertes': AlertePresence.objects.filter(statut='NOUVELLE').count(),
        }

        for label, count in stats.items():
            self.stdout.write(f'{label:.<30} {count:>5}')

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎯 ACCÈS AU SYSTÈME'))
        self.stdout.write('='*60)

        self.stdout.write('Interface de pointage: /spa/attendance/timeclock/')
        self.stdout.write('Dashboard temps réel: /spa/attendance/dashboard/')
        self.stdout.write('Validation présences: /spa/attendance/validation/')
        self.stdout.write('Rapports: /spa/attendance/reports/')
        self.stdout.write('Configuration: /spa/attendance/settings/')

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🔑 COMPTES DE TEST'))
        self.stdout.write('='*60)

        # Suggestions pour les comptes admin
        if User.objects.filter(is_superuser=True).exists():
            admin_user = User.objects.filter(is_superuser=True).first()
            self.stdout.write(f'Admin existant: {admin_user.username}')
        else:
            self.stdout.write('Créez un superuser avec: python manage.py createsuperuser')

        self.stdout.write('\n' + self.style.WARNING('💡 PROCHAINES ÉTAPES:'))
        self.stdout.write('1. Configurez les groupes utilisateurs dans l\'admin')
        self.stdout.write('2. Testez l\'interface de pointage')
        self.stdout.write('3. Personnalisez les règles de pointage')
        self.stdout.write('4. Configurez les notifications')
        self.stdout.write('5. Formez vos utilisateurs')

    def create_superuser_if_needed(self):
        """Créer un superuser pour les tests si nécessaire"""
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@paiepro.ma',
                password='admin123',
                first_name='Administrator',
                last_name='PAIEPRO'
            )
            self.stdout.write('  ✓ Superuser créé: admin / admin123')

# ============================================================================
# SCRIPT ADDITIONNEL : Nettoyage des données de test
# ============================================================================

class CleanupCommand(BaseCommand):
    """Commande pour nettoyer les données de test"""
    help = 'Nettoie les données de test du module pointage'

    def handle(self, *args, **options):
        self.stdout.write('🧹 Nettoyage des données de test...')
        
        # Supprimer dans l'ordre inverse des dépendances
        AlertePresence.objects.filter(details__demo=True).delete()
        PresenceJournaliere.objects.all().delete()
        Pointage.objects.all().delete()
        ValidationPresence.objects.all().delete()
        HoraireTravail.objects.all().delete()
        ReglePointage.objects.all().delete()
        PlageHoraire.objects.all().delete()
        
        # Optionnel: supprimer les employés de test
        Employee.objects.filter(matricule__startswith='EMP').delete()
        
        self.stdout.write(self.style.SUCCESS('✅ Données de test supprimées'))

# ============================================================================
# UTILITAIRES POUR LES DÉVELOPPEURS
# ============================================================================

def create_dev_data():
    """Fonction utilitaire pour créer des données de développement"""
    from django.core.management import call_command
    
    print("🔧 Création des données de développement...")
    call_command('init_attendance_module', '--full-demo', '--employees-count', '50')
    print("✅ Données de développement créées")

def reset_attendance_module():
    """Fonction utilitaire pour réinitialiser complètement le module"""
    print("🔄 Réinitialisation du module pointage...")
    
    # Nettoyer les données existantes
    AlertePresence.objects.all().delete()
    PresenceJournaliere.objects.all().delete()
    Pointage.objects.all().delete()
    ValidationPresence.objects.all().delete()
    HoraireTravail.objects.all().delete()
    ReglePointage.objects.all().delete()
    PlageHoraire.objects.all().delete()
    
    # Recréer les données
    create_dev_data()
    print("✅ Module réinitialisé")