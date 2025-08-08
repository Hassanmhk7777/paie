# paie/auth_views.py - Nouveau fichier à créer

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils import timezone
import logging
from datetime import date, timedelta

from .models import UserProfile, UserRole, Employee, DemandeConge, PeriodePaie
from .forms import CustomLoginForm, FirstLoginPasswordForm

logger = logging.getLogger(__name__)

@csrf_protect
@require_http_methods(["GET", "POST"])
def custom_login(request):
    """Vue de connexion personnalisée avec redirection selon le rôle"""
    
    # Si déjà connecté, rediriger selon le rôle
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)
    
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Authentification
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Vérifier si l'utilisateur a un profil
                    try:
                        profile = user.profile
                        
                        # Vérifier si le profil est actif
                        if not profile.is_active:
                            messages.error(request, 'Votre compte a été désactivé. Contactez votre administrateur.')
                            logger.warning(f'Tentative de connexion avec compte désactivé: {username}')
                            return render(request, 'auth/login.html', {'form': form})
                        
                        # Connexion réussie
                        login(request, user)
                        
                        # Gérer la session "Remember me"
                        if not remember_me:
                            request.session.set_expiry(0)  # Session expire à la fermeture du navigateur
                        else:
                            request.session.set_expiry(60 * 60 * 24 * 7)  # 7 jours
                        
                        # Log de connexion
                        logger.info(f'Connexion réussie: {username} ({profile.get_role_display()})')
                        
                        # Messages de bienvenue
                        welcome_msg = f"Bienvenue, {user.get_full_name() or user.username} !"
                        if profile.is_first_login:
                            messages.info(request, f"{welcome_msg} Veuillez changer votre mot de passe.")
                            return redirect('paie:first_login_password_change')
                        else:
                            messages.success(request, welcome_msg)
                        
                        # Redirection selon le rôle ou URL next
                        next_url = request.GET.get('next')
                        if next_url:
                            return redirect(next_url)
                        else:
                            return redirect_user_by_role(user)
                    
                    except UserProfile.DoesNotExist:
                        messages.error(request, 'Profil utilisateur non configuré. Contactez votre administrateur.')
                        logger.error(f'Utilisateur sans profil: {username}')
                        
                else:
                    messages.error(request, 'Votre compte est inactif.')
                    logger.warning(f'Tentative de connexion avec compte inactif: {username}')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
                logger.warning(f'Échec d\'authentification: {username}')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'auth/login.html', {
        'form': form,
        'page_title': 'Connexion - PaiePro'
    })


@csrf_protect
@login_required
def custom_logout(request):
    """Vue de déconnexion personnalisée"""
    
    username = request.user.username
    role = getattr(request.user.profile, 'role', 'INCONNU') if hasattr(request.user, 'profile') else 'INCONNU'
    
    # Log de déconnexion
    logger.info(f'Déconnexion: {username} ({role})')
    
    # Déconnexion
    logout(request)
    
    # Message et redirection
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('paie:login')


@csrf_protect
@login_required
def first_login_password_change(request):
    """Changement de mot de passe obligatoire à la première connexion"""
    
    # Vérifier que c'est bien la première connexion
    if not hasattr(request.user, 'profile') or not request.user.profile.is_first_login:
        messages.info(request, 'Changement de mot de passe déjà effectué.')
        return redirect_user_by_role(request.user)
    
    if request.method == 'POST':
        form = FirstLoginPasswordForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            
            # Marquer que ce n'est plus la première connexion
            profile = user.profile
            profile.is_first_login = False
            profile.save()
            
            # Maintenir la session après changement de mot de passe
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Votre mot de passe a été changé avec succès !')
            logger.info(f'Changement mot de passe première connexion: {user.username}')
            
            # Redirection selon le rôle
            return redirect_user_by_role(user)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = FirstLoginPasswordForm(request.user)
    
    return render(request, 'auth/first_login_password.html', {
        'form': form,
        'page_title': 'Changement de mot de passe - PaiePro'
    })


@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    
    profile = request.user.profile
    
    context = {
        'user': request.user,
        'profile': profile,
        'page_title': 'Mon Profil - PaiePro'
    }
    
    # Template différent selon le rôle
    if profile.is_admin:
        template = 'auth/profile_admin.html'
    elif profile.is_rh:
        template = 'auth/profile_rh.html'  
    else:
        template = 'auth/profile_employee.html'
    
    return render(request, template, context)


def redirect_user_by_role(user):
    """Fonction utilitaire pour rediriger selon le rôle"""
    
    if not hasattr(user, 'profile'):
        # Pas de profil = page d'erreur ou création automatique
        return redirect('paie:login')
    
    profile = user.profile
    
    # Redirection selon le rôle
    if profile.is_admin:
        return redirect('paie:admin_dashboard')
    elif profile.is_rh:
        return redirect('paie:rh_dashboard')
    elif profile.is_employe:
        return redirect('paie:employee_dashboard')
    else:
        # Rôle inconnu
        return redirect('paie:login')


# === VUES AJAX POUR SPA ===

@login_required
@require_http_methods(["GET"])
def api_user_info(request):
    """API pour récupérer les informations utilisateur (pour le header SPA)"""
    
    user = request.user
    profile = user.profile
    
    data = {
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'role': profile.role,
        'role_display': profile.get_role_display(),
        'is_admin': profile.is_admin,
        'is_rh': profile.is_rh,
        'is_employe': profile.is_employe,
        'is_manager': profile.is_manager,
        'avatar': profile.avatar.url if profile.avatar else None,
        'phone': profile.phone,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'employee': {
            'nom': profile.employee.nom if profile.employee else None,
            'prenom': profile.employee.prenom if profile.employee else None,
            'matricule': profile.employee.matricule if profile.employee else None,
            'department': profile.employee.department.nom if profile.employee and profile.employee.department else None,
        } if profile.employee else None
    }
    
    return JsonResponse(data)


@login_required  
@require_http_methods(["POST"])
def api_logout(request):
    """API de déconnexion pour SPA"""
    
    username = request.user.username
    logout(request)
    
    return JsonResponse({
        'success': True,
        'message': 'Déconnexion réussie',
        'redirect_url': reverse('paie:login')
    })


# === VUES DE DASHBOARDS SELON LES RÔLES ===

@login_required
def admin_dashboard(request):
    """Dashboard administrateur"""
    
    # Vérifier les permissions 
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin:
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('paie:login')
    
    # Statistiques pour le dashboard
    try:
        total_employees = Employee.objects.filter(is_active=True).count()
        pending_leaves = DemandeConge.objects.filter(statut='SOUMISE').count()
        current_period = PeriodePaie.objects.exclude(statut='CLOTUREE').first()
        
        stats = {
            'total_employees': total_employees,
            'employees_present': total_employees,  # À implémenter avec le système de pointage
            'pending_leaves': pending_leaves,
            'current_period': current_period.nom if current_period else 'Aucune',
        }
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques: {e}")
        stats = {
            'total_employees': 0,
            'employees_present': 0,
            'pending_leaves': 0,
            'current_period': 'N/A',
        }
    
    # Données spécifiques admin
    context = {
        'page_title': 'Administration - PaiePro',
        'dashboard_type': 'admin',
        'user': request.user,
        'profile': request.user.profile,
        'stats': stats,
    }
    
    return render(request, 'auth/dashboard_simple.html', context)


@login_required
def rh_dashboard(request):
    """Dashboard RH"""
    
    if not hasattr(request.user, 'profile') or (not request.user.profile.is_rh and not request.user.profile.is_admin):
        messages.error(request, 'Accès réservé aux ressources humaines.')
        return redirect('paie:login')
    
    context = {
        'page_title': 'Ressources Humaines - PaiePro',
        'dashboard_type': 'rh',
        'user': request.user,
        'profile': request.user.profile,
    }
    
    return render(request, 'auth/dashboard_simple.html', context)


@login_required  
def employee_dashboard(request):
    """Dashboard employé"""
    
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profil utilisateur requis.')
        return redirect('paie:login')
    
    context = {
        'page_title': 'Mon Espace - PaiePro',
        'dashboard_type': 'employee',
        'user': request.user,
        'profile': request.user.profile,
    }
    
    return render(request, 'auth/dashboard_simple.html', context)


# === APIs POUR LE DASHBOARD ===

@login_required
def api_dashboard_stats(request):
    """API pour récupérer les statistiques du dashboard"""
    try:
        # Calculer les statistiques selon le rôle
        if request.user.profile.is_admin or request.user.profile.is_rh:
            # Statistiques globales
            total_employees = Employee.objects.filter(is_active=True).count()
            pending_leaves = DemandeConge.objects.filter(statut='SOUMISE').count()
            current_period = PeriodePaie.objects.exclude(statut='CLOTUREE').first()
            
            # Présences du jour (simulation - à implémenter avec le module pointage)
            employees_present = max(0, total_employees - 5)  # Simulation
            
            stats = {
                'total_employees': total_employees,
                'employees_present': employees_present,
                'pending_leaves': pending_leaves,
                'current_period': current_period.nom if current_period else 'Aucune période active',
            }
        else:
            # Statistiques employé
            employee = request.user.profile.employee
            if employee:
                leaves_this_year = DemandeConge.objects.filter(
                    employe=employee,
                    date_debut__year=date.today().year
                ).count()
                
                stats = {
                    'leaves_taken': leaves_this_year,
                    'leaves_remaining': max(0, 25 - leaves_this_year),  # 25 jours par an
                    'current_period': 'Mois en cours',
                    'last_payslip': 'Disponible',
                }
            else:
                stats = {'error': 'Profil employé non trouvé'}
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Erreur API dashboard stats: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors du calcul des statistiques'
        }, status=500)


@login_required
def api_recent_activities(request):
    """API pour récupérer les activités récentes"""
    try:
        activities = []
        
        if request.user.profile.is_admin or request.user.profile.is_rh:
            # Activités globales
            
            # Dernières demandes de congés
            recent_leaves = DemandeConge.objects.select_related('employe').order_by('-date_creation')[:3]
            for leave in recent_leaves:
                activities.append({
                    'description': f'Demande de congé - {leave.type_conge.nom}',
                    'user': f'{leave.employe.first_name} {leave.employe.last_name}',
                    'type': 'Congé',
                    'time': leave.date_creation.strftime('%H:%M'),
                    'date': leave.date_creation.strftime('%d/%m/%Y')
                })
            
            # Activités système simulées
            activities.extend([
                {
                    'description': 'Calcul de paie effectué',
                    'user': 'Système',
                    'type': 'Paie',
                    'time': '14:30',
                    'date': date.today().strftime('%d/%m/%Y')
                },
                {
                    'description': 'Nouveau collaborateur ajouté',
                    'user': request.user.get_full_name() or request.user.username,
                    'type': 'RH',
                    'time': '10:15',
                    'date': date.today().strftime('%d/%m/%Y')
                }
            ])
        else:
            # Activités employé
            employee = request.user.profile.employee
            if employee:
                my_leaves = DemandeConge.objects.filter(employe=employee).order_by('-date_creation')[:3]
                for leave in my_leaves:
                    activities.append({
                        'description': f'Votre demande de {leave.type_conge.nom}',
                        'user': 'Vous',
                        'type': f'Statut: {leave.get_statut_display()}',
                        'time': leave.date_creation.strftime('%H:%M'),
                        'date': leave.date_creation.strftime('%d/%m/%Y')
                    })
        
        return JsonResponse({
            'success': True,
            'activities': activities[:5]  # Limiter à 5 activités
        })
        
    except Exception as e:
        logger.error(f"Erreur API recent activities: {e}")
        return JsonResponse({
            'success': False,
            'activities': []
        })