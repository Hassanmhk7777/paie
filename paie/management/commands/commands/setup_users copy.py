# paie/management/commands/setup_users.py
# Créez les dossiers : paie/management/ et paie/management/commands/

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from paie.models import UserProfile, UserRole, Employee

class Command(BaseCommand):
    help = 'Initialise le système d\'authentification PaiePro'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Crée un compte administrateur',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Nom d\'utilisateur pour l\'admin',
            default='admin'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email pour l\'admin',
            default='admin@paiepro.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Mot de passe pour l\'admin',
            default='PaiePro2025!'
        )
        parser.add_argument(
            '--link-employees',
            action='store_true',
            help='Lie les employés existants aux utilisateurs',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Initialisation du système d\'authentification PaiePro')
        )

        try:
            with transaction.atomic():
                # 1. Créer des profils pour les utilisateurs existants
                self.create_missing_profiles()
                
                # 2. Créer un admin si demandé
                if options['create_admin']:
                    self.create_admin_user(
                        options['username'],
                        options['email'], 
                        options['password']
                    )
                
                # 3. Lier les employés existants
                if options['link_employees']:
                    self.link_existing_employees()
                
                # 4. Statistiques finales
                self.show_stats()

        except Exception as e:
            raise CommandError(f'Erreur lors de l\'initialisation: {str(e)}')

    def create_missing_profiles(self):
        """Crée des profils pour tous les utilisateurs qui n'en ont pas"""
        users_without_profile = User.objects.filter(profile__isnull=True)
        created_count = 0
        
        for user in users_without_profile:
            profile = UserProfile.objects.create(
                user=user,
                role=UserRole.EMPLOYE,  # Par défaut
                is_first_login=True
            )
            created_count += 1
            self.stdout.write(f'  ✓ Profil créé pour: {user.username}')
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'📋 {created_count} profils créés pour les utilisateurs existants')
            )
        else:
            self.stdout.write('📋 Tous les utilisateurs ont déjà un profil')

    def create_admin_user(self, username, email, password):
        """Crée un utilisateur administrateur"""
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'👑 L\'utilisateur {username} existe déjà')
            )
            user = User.objects.get(username=username)
            # Mettre à jour le profil comme admin
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = UserRole.ADMIN
            profile.is_first_login = False
            profile.save()
            self.stdout.write(f'  ✓ Profil mis à jour en ADMIN pour {username}')
        else:
            # Créer le nouvel utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Administrateur',
                last_name='PaiePro',
                is_staff=True,
                is_superuser=True
            )
            
            # Le signal va créer le profil, on le met à jour
            profile = user.profile
            profile.role = UserRole.ADMIN
            profile.is_first_login = False
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'👑 Compte administrateur créé: {username}')
            )
            self.stdout.write(f'  📧 Email: {email}')
            self.stdout.write(f'  🔑 Mot de passe: {password}')

    def link_existing_employees(self):
        """Lie les employés existants aux utilisateurs selon l'email"""
        employees = Employee.objects.filter(user_profile__isnull=True)
        linked_count = 0
        
        for employee in employees:
            if employee.email:
                # Chercher un utilisateur avec le même email
                try:
                    user = User.objects.get(email=employee.email)
                    if hasattr(user, 'profile'):
                        profile = user.profile
                        if not profile.employee:  # Pas déjà lié
                            profile.employee = employee
                            profile.role = UserRole.EMPLOYE
                            profile.save()
                            linked_count += 1
                            self.stdout.write(f'  ✓ {employee.nom} lié à {user.username}')
                except User.DoesNotExist:
                    self.stdout.write(f'  ⚠️ Aucun utilisateur trouvé pour {employee.email}')
                except User.MultipleObjectsReturned:
                    self.stdout.write(f'  ⚠️ Plusieurs utilisateurs trouvés pour {employee.email}')
        
        if linked_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'🔗 {linked_count} employés liés aux utilisateurs')
            )
        else:
            self.stdout.write('🔗 Aucun employé à lier automatiquement')

    def show_stats(self):
        """Affiche les statistiques du système"""
        total_users = User.objects.count()
        admin_count = UserProfile.objects.filter(role=UserRole.ADMIN).count()
        rh_count = UserProfile.objects.filter(role=UserRole.RH).count()
        employee_count = UserProfile.objects.filter(role=UserRole.EMPLOYE).count()
        linked_count = UserProfile.objects.filter(employee__isnull=False).count()
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 STATISTIQUES SYSTÈME'))
        self.stdout.write('='*50)
        self.stdout.write(f'👥 Total utilisateurs: {total_users}')
        self.stdout.write(f'👑 Administrateurs: {admin_count}')
        self.stdout.write(f'🏢 RH: {rh_count}')
        self.stdout.write(f'👨‍💼 Employés: {employee_count}')
        self.stdout.write(f'🔗 Profils liés à des employés: {linked_count}')
        self.stdout.write('='*50)
        
        # Conseils
        self.stdout.write('\n💡 PROCHAINES ÉTAPES:')
        self.stdout.write('1. Connectez-vous avec le compte admin créé')
        self.stdout.write('2. Créez des comptes RH depuis l\'interface admin')
        self.stdout.write('3. Liez manuellement les employés non liés automatiquement')
        self.stdout.write('4. Configurez les permissions selon vos besoins')


# Créez aussi ce fichier: paie/management/__init__.py (vide)
# Et ce fichier: paie/management/commands/__init__.py (vide)