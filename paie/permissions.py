# paie/permissions.py - Nouveau fichier à créer

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import View
import logging

from .models import UserRole, Employee, UserProfile

logger = logging.getLogger(__name__)

class PermissionManager:
    """Gestionnaire central des permissions"""
    
    @staticmethod
    def check_permission(user, permission_name, target_object=None):
        """
        Vérification centralisée des permissions
        
        Args:
            user: Utilisateur Django
            permission_name: Nom de la permission (string)
            target_object: Objet cible optionnel (Employee, etc.)
        
        Returns:
            bool: True si autorisé, False sinon
        """
        if not user.is_authenticated:
            return False
            
        if not hasattr(user, 'profile'):
            return False
            
        profile = user.profile
        
        # Permissions de base
        base_permissions = {
            # Gestion des utilisateurs
            'manage_users': profile.is_admin or profile.is_rh,
            'create_users': profile.is_admin or profile.is_rh,
            'create_admin': profile.is_admin,
            'deactivate_users': profile.is_admin,
            
            # Gestion des employés
            'view_all_employees': profile.is_admin or profile.is_rh,
            'edit_employees': profile.is_admin or profile.is_rh,
            'delete_employees': profile.is_admin,
            
            # Gestion de la paie
            'calculate_payroll': profile.is_admin or profile.is_rh,
            'validate_payroll': profile.is_admin,
            'view_all_payroll': profile.is_admin or profile.is_rh,
            'export_payroll': profile.is_admin or profile.is_rh,
            'edit_payroll_settings': profile.is_admin,
            
            # Gestion des congés
            'approve_leaves': profile.is_admin or profile.is_rh,
            'view_all_leaves': profile.is_admin or profile.is_rh,
            'override_leave_rules': profile.is_admin,
            
            # Gestion du pointage
            'validate_timesheet': profile.is_admin or profile.is_rh,
            'edit_timesheet': profile.is_admin or profile.is_rh,
            'view_all_timesheet': profile.is_admin or profile.is_rh,
            
            # Paramètres système
            'edit_system_settings': profile.is_admin,
            'manage_departments': profile.is_admin or profile.is_rh,
            'manage_pay_scales': profile.is_admin,
            
            # Rapports
            'view_global_reports': profile.is_admin or profile.is_rh,
            'export_reports': profile.is_admin or profile.is_rh,
            'view_financial_reports': profile.is_admin,
        }
        
        # Permissions avec objet cible
        if target_object:
            if isinstance(target_object, Employee):
                # Un employé peut voir ses propres données
                if profile.is_employe and profile.employee == target_object:
                    object_permissions = {
                        'view_employee': True,
                        'view_own_payroll': True,
                        'view_own_leaves': True,
                        'request_leaves': True,
                        'view_own_timesheet': True,
                    }
                else:
                    object_permissions = {
                        'view_employee': profile.is_admin or profile.is_rh,
                        'view_own_payroll': False,
                        'view_own_leaves': False,
                        'request_leaves': False,
                        'view_own_timesheet': False,
                    }
                
                base_permissions.update(object_permissions)
        
        return base_permissions.get(permission_name, False)
    
    @staticmethod
    def get_accessible_employees(user):
        """Retourne les employés accessibles selon les permissions"""
        if not user.is_authenticated or not hasattr(user, 'profile'):
            return Employee.objects.none()
        
        profile = user.profile
        
        if profile.is_admin or profile.is_rh:
            return Employee.objects.all()
        elif profile.is_employe and profile.employee:
            return Employee.objects.filter(id=profile.employee.id)
        else:
            return Employee.objects.none()


def permission_required(permission_name, target_object_param=None, redirect_url=None):
    """
    Décorateur pour vérifier des permissions spécifiques
    
    Args:
        permission_name (str): Nom de la permission
        target_object_param (str): Nom du paramètre URL contenant l'ID de l'objet cible
        redirect_url (str): URL de redirection en cas de refus
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            target_object = None
            
            # Récupérer l'objet cible si spécifié
            if target_object_param and target_object_param in kwargs:
                object_id = kwargs[target_object_param]
                try:
                    if permission_name.endswith('_employee') or 'employee' in permission_name:
                        target_object = get_object_or_404(Employee, id=object_id)
                except:
                    logger.warning(f'Objet cible introuvable: {target_object_param}={object_id}')
            
            # Vérifier la permission
            if not PermissionManager.check_permission(request.user, permission_name, target_object):
                logger.warning(f'Permission refusée: {request.user.username} -> {permission_name}')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'Permission refusée',
                        'message': f'Vous n\'avez pas la permission "{permission_name}"',
                        'required_permission': permission_name
                    }, status=403)
                else:
                    messages.error(request, f'Permission refusée : {permission_name}')
                    
                    if redirect_url:
                        return redirect(redirect_url)
                    else:
                        # Redirection par défaut selon le rôle
                        profile = request.user.profile
                        if profile.is_admin:
                            return redirect('paie:admin_dashboard')
                        elif profile.is_rh:
                            return redirect('paie:rh_dashboard')
                        else:
                            return redirect('paie:employee_dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def role_or_own_data(allowed_roles=None, object_param='employee_id'):
    """
    Décorateur permettant l'accès aux managers OU aux données personnelles
    
    Args:
        allowed_roles (list): Rôles ayant accès complet
        object_param (str): Paramètre contenant l'ID de l'employé
    """
    if allowed_roles is None:
        allowed_roles = [UserRole.ADMIN, UserRole.RH]
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'profile'):
                return redirect('paie:login')
            
            profile = request.user.profile
            
            # Accès manager
            if profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # Accès aux données personnelles
            if profile.is_employe and profile.employee:
                employee_id = kwargs.get(object_param)
                if employee_id and str(profile.employee.id) == str(employee_id):
                    return view_func(request, *args, **kwargs)
            
            # Accès refusé
            logger.warning(f'Accès refusé: {request.user.username} vers {request.path}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Accès refusé',
                    'message': 'Vous ne pouvez accéder qu\'à vos propres données'
                }, status=403)
            else:
                messages.error(request, 'Vous ne pouvez accéder qu\'à vos propres données.')
                return redirect('paie:employee_dashboard')
        
        return _wrapped_view
    return decorator


def ajax_permission_required(permission_name):
    """Décorateur spécialisé pour les vues AJAX"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not PermissionManager.check_permission(request.user, permission_name):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission refusée',
                    'message': f'Permission "{permission_name}" requise',
                    'required_permission': permission_name,
                    'user_role': request.user.profile.role if hasattr(request.user, 'profile') else None
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class PermissionRequiredMixin:
    """Mixin pour les vues basées sur les classes"""
    
    permission_required = None
    permission_denied_message = "Vous n'avez pas les permissions nécessaires."
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('paie:login')
        
        if self.permission_required:
            if not PermissionManager.check_permission(request.user, self.permission_required):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'Permission refusée',
                        'message': self.permission_denied_message
                    }, status=403)
                else:
                    messages.error(request, self.permission_denied_message)
                    return redirect('paie:employee_dashboard')
        
        return super().dispatch(request, *args, **kwargs)


# === DÉCORATEURS SPÉCIALISÉS PAR FONCTIONNALITÉ ===

def payroll_permission(action='view'):
    """Permissions spécifiques à la paie"""
    permissions_map = {
        'view': 'view_all_payroll',
        'calculate': 'calculate_payroll',
        'validate': 'validate_payroll',
        'export': 'export_payroll'
    }
    
    permission = permissions_map.get(action, 'view_all_payroll')
    return permission_required(permission)


def employee_management_permission(action='view'):
    """Permissions spécifiques à la gestion des employés"""
    permissions_map = {
        'view': 'view_all_employees',
        'edit': 'edit_employees',
        'delete': 'delete_employees'
    }
    
    permission = permissions_map.get(action, 'view_all_employees')
    return permission_required(permission)


def leave_management_permission(action='view'):
    """Permissions spécifiques aux congés"""
    permissions_map = {
        'view': 'view_all_leaves',
        'approve': 'approve_leaves',
        'override': 'override_leave_rules'
    }
    
    permission = permissions_map.get(action, 'view_all_leaves')
    return permission_required(permission)


def system_admin_required(view_func):
    """Décorateur pour les actions d'administration système"""
    return permission_required('edit_system_settings')(view_func)


# === HELPERS POUR LES TEMPLATES ===

def get_user_permissions(user):
    """Retourne toutes les permissions d'un utilisateur pour les templates"""
    if not user.is_authenticated or not hasattr(user, 'profile'):
        return {}
    
    permissions = {}
    permission_list = [
        'manage_users', 'create_users', 'create_admin', 'deactivate_users',
        'view_all_employees', 'edit_employees', 'delete_employees',
        'calculate_payroll', 'validate_payroll', 'view_all_payroll',
        'approve_leaves', 'view_all_leaves', 'override_leave_rules',
        'validate_timesheet', 'edit_timesheet', 'view_all_timesheet',
        'edit_system_settings', 'manage_departments', 'manage_pay_scales',
        'view_global_reports', 'export_reports', 'view_financial_reports'
    ]
    
    for perm in permission_list:
        permissions[perm] = PermissionManager.check_permission(user, perm)
    
    return permissions


# === GESTION DES ERREURS DE PERMISSION ===

def permission_denied_view(request, exception=None):
    """Vue personnalisée pour les erreurs de permission"""
    
    context = {
        'error_title': 'Accès refusé',
        'error_message': 'Vous n\'avez pas les permissions nécessaires pour accéder à cette page.',
        'user_role': request.user.profile.role if hasattr(request.user, 'profile') else None,
        'suggestions': []
    }
    
    # Suggestions selon le rôle
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        if profile.is_employe:
            context['suggestions'] = [
                {'label': 'Mon Espace', 'url': reverse('paie:employee_dashboard')},
                {'label': 'Mon Profil', 'url': reverse('paie:profile')},
                {'label': 'Mes Congés', 'url': '#'},
            ]
        elif profile.is_rh:
            context['suggestions'] = [
                {'label': 'Dashboard RH', 'url': reverse('paie:rh_dashboard')},
                {'label': 'Gestion Employés', 'url': '#'},
                {'label': 'Validation Congés', 'url': '#'},
            ]
        elif profile.is_admin:
            context['suggestions'] = [
                {'label': 'Administration', 'url': reverse('paie:admin_dashboard')},
                {'label': 'Gestion Utilisateurs', 'url': '#'},
                {'label': 'Paramètres', 'url': '#'},
            ]
    
    return render_to_string('errors/permission_denied.html', context)


# === LOGGING DES PERMISSIONS ===

class PermissionLogger:
    """Classe pour logger les accès et refus de permissions"""
    
    @staticmethod
    def log_permission_check(user, permission, granted, target_object=None):
        """Log une vérification de permission"""
        status = "GRANTED" if granted else "DENIED"
        user_info = f"{user.username} ({user.profile.role})" if hasattr(user, 'profile') else user.username
        target_info = f" on {target_object}" if target_object else ""
        
        logger.info(f"PERMISSION {status}: {user_info} -> {permission}{target_info}")
    
    @staticmethod
    def log_access_attempt(user, url, method="GET"):
        """Log une tentative d'accès à une URL"""
        user_info = f"{user.username} ({user.profile.role})" if hasattr(user, 'profile') else user.username
        logger.info(f"ACCESS: {user_info} {method} {url}")


# === DÉCORATEURS AVEC LOGGING ===

def logged_permission_required(permission_name):
    """Version avec logging du décorateur de permission"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            PermissionLogger.log_access_attempt(request.user, request.path, request.method)
            
            granted = PermissionManager.check_permission(request.user, permission_name)
            PermissionLogger.log_permission_check(request.user, permission_name, granted)
            
            if not granted:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'Permission refusée',
                        'message': f'Permission "{permission_name}" requise'
                    }, status=403)
                else:
                    messages.error(request, f'Permission refusée : {permission_name}')
                    return redirect('paie:employee_dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator