# paie/decorators.py - Nouveau fichier à créer

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from .models import UserRole

def role_required(allowed_roles=None, redirect_url=None):
    """
    Décorateur pour vérifier les rôles utilisateur
    
    Args:
        allowed_roles (list): Liste des rôles autorisés
        redirect_url (str): URL de redirection si pas autorisé
    """
    if allowed_roles is None:
        allowed_roles = []
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier si l'utilisateur a un profil
            if not hasattr(request.user, 'profile'):
                messages.error(request, "Profil utilisateur non configuré. Contactez l'administrateur.")
                return redirect('paie:login')
            
            user_role = request.user.profile.role
            
            # Vérifier si le rôle est autorisé
            if user_role not in allowed_roles:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # Requête AJAX
                    return JsonResponse({
                        'error': 'Permission refusée',
                        'message': f'Accès réservé aux rôles : {", ".join(allowed_roles)}'
                    }, status=403)
                else:
                    # Requête normale
                    messages.error(
                        request, 
                        f"Accès refusé. Cette page est réservée aux : {', '.join(allowed_roles)}"
                    )
                    if redirect_url:
                        return redirect(redirect_url)
                    else:
                        # Redirection selon le rôle
                        if user_role == UserRole.EMPLOYE:
                            return redirect('paie:employee_dashboard')
                        elif user_role == UserRole.RH:
                            return redirect('paie:rh_dashboard')
                        else:
                            return redirect('paie:admin_dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func=None, *, redirect_url=None):
    """Décorateur pour les vues réservées aux administrateurs"""
    actual_decorator = role_required([UserRole.ADMIN], redirect_url)
    
    if view_func is None:
        return actual_decorator
    else:
        return actual_decorator(view_func)


def rh_required(view_func=None, *, redirect_url=None):
    """Décorateur pour les vues réservées aux RH"""
    actual_decorator = role_required([UserRole.RH], redirect_url)
    
    if view_func is None:
        return actual_decorator
    else:
        return actual_decorator(view_func)


def manager_required(view_func=None, *, redirect_url=None):
    """Décorateur pour les vues réservées aux gestionnaires (ADMIN + RH)"""
    actual_decorator = role_required([UserRole.ADMIN, UserRole.RH], redirect_url)
    
    if view_func is None:
        return actual_decorator
    else:
        return actual_decorator(view_func)


def employee_required(view_func=None, *, redirect_url=None):
    """Décorateur pour les vues réservées aux employés"""
    actual_decorator = role_required([UserRole.EMPLOYE], redirect_url)
    
    if view_func is None:
        return actual_decorator
    else:
        return actual_decorator(view_func)


def permission_required(permission_name):
    """
    Décorateur pour vérifier des permissions spécifiques
    
    Args:
        permission_name (str): Nom de la permission à vérifier
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            from .models import user_has_permission
            
            if not user_has_permission(request.user, permission_name):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'Permission refusée',
                        'message': f'Permission "{permission_name}" requise'
                    }, status=403)
                else:
                    messages.error(request, f"Permission '{permission_name}' requise pour cette action.")
                    return redirect('paie:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def own_data_or_manager(view_func):
    """
    Décorateur pour permettre l'accès aux données personnelles ou si manager
    Utilisé pour les vues qui affichent des données d'employé
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil utilisateur non configuré.")
            return redirect('paie:login')
        
        profile = request.user.profile
        
        # Les managers peuvent tout voir
        if profile.is_manager:
            return view_func(request, *args, **kwargs)
        
        # Pour les employés, vérifier qu'ils accèdent à leurs propres données
        if profile.is_employe:
            # Si la vue prend un employee_id en paramètre
            employee_id = kwargs.get('employee_id') or request.GET.get('employee_id')
            if employee_id and profile.employee:
                if str(profile.employee.id) != str(employee_id):
                    messages.error(request, "Vous ne pouvez accéder qu'à vos propres données.")
                    return redirect('paie:employee_dashboard')
            
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Accès non autorisé.")
        return redirect('paie:dashboard')
    
    return _wrapped_view


# === MIDDLEWARE HELPER ===

class RoleBasedRedirectMiddleware:
    """
    Middleware pour rediriger automatiquement selon le rôle après connexion
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Redirection après login selon le rôle
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            if request.path == reverse('paie:login') or request.path == '/':
                profile = request.user.profile
                
                if profile.is_first_login:
                    return redirect('paie:first_login_password_change')
                
                # Redirection selon le rôle
                if profile.is_admin:
                    return redirect('paie:admin_dashboard')
                elif profile.is_rh:
                    return redirect('paie:rh_dashboard') 
                elif profile.is_employe:
                    return redirect('paie:employee_dashboard')
        
        return None


# === CONTEXT PROCESSORS ===

def user_role_context(request):
    """Context processor pour avoir le rôle dans tous les templates"""
    context = {
        'user_role': None,
        'is_admin': False,
        'is_rh': False,
        'is_employe': False,
        'is_manager': False,
    }
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        context.update({
            'user_role': profile.role,
            'is_admin': profile.is_admin,
            'is_rh': profile.is_rh,
            'is_employe': profile.is_employe,
            'is_manager': profile.is_manager,
            'user_profile': profile,
        })
    
    return context