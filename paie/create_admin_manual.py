# create_admin_manual.py - À placer à la racine du projet (même niveau que manage.py)

import os
import django
from django.contrib.auth.models import User

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paie_project.settings')  # Remplacez par le nom de votre projet
django.setup()

from paie.models import UserProfile, UserRole

def create_admin():
    """Crée un utilisateur admin manuellement"""
    
    print("🚀 Création d'un administrateur PaiePro...")
    
    # Données admin
    username = 'admin'
    email = 'admin@paiepro.com'
    password = 'PaiePro2025!'
    
    try:
        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            print(f"❌ L'utilisateur '{username}' existe déjà")
            user = User.objects.get(username=username)
        else:
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Administrateur',
                last_name='PaiePro',
                is_staff=True,
                is_superuser=True
            )
            print(f"✅ Utilisateur '{username}' créé avec succès")
        
        # Créer ou mettre à jour le profil
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = UserRole.ADMIN
        profile.is_first_login = False
        profile.is_active = True
        profile.save()
        
        if created:
            print("✅ Profil administrateur créé")
        else:
            print("✅ Profil mis à jour en ADMIN")
        
        print("\n" + "="*50)
        print("👑 COMPTE ADMINISTRATEUR CRÉÉ")
        print("="*50)
        print(f"👤 Nom d'utilisateur: {username}")
        print(f"📧 Email: {email}")
        print(f"🔑 Mot de passe: {password}")
        print(f"🎭 Rôle: {profile.get_role_display()}")
        print("="*50)
        print("\n💡 Vous pouvez maintenant vous connecter avec ces identifiants")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {str(e)}")
        return False

def show_stats():
    """Affiche les statistiques"""
    try:
        total_users = User.objects.count()
        total_profiles = UserProfile.objects.count()
        admin_count = UserProfile.objects.filter(role=UserRole.ADMIN).count()
        rh_count = UserProfile.objects.filter(role=UserRole.RH).count()
        employee_count = UserProfile.objects.filter(role=UserRole.EMPLOYE).count()
        
        print("\n📊 STATISTIQUES:")
        print(f"👥 Total utilisateurs: {total_users}")
        print(f"📋 Total profils: {total_profiles}")
        print(f"👑 Administrateurs: {admin_count}")
        print(f"🏢 RH: {rh_count}")
        print(f"👨‍💼 Employés: {employee_count}")
        
    except Exception as e:
        print(f"❌ Erreur statistiques: {str(e)}")

if __name__ == '__main__':
    create_admin()
    show_stats()