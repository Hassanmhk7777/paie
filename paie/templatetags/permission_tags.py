# paie/templatetags/__init__.py - Créer ce dossier et fichier vide

# paie/templatetags/permission_tags.py - Nouveau fichier à créer

from django import template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.urls import reverse, NoReverseMatch
import json

from ..permissions import PermissionManager, get_user_permissions
from ..models import UserRole

register = template.Library()


# === TAGS DE VÉRIFICATION DE PERMISSIONS ===

@register.simple_tag
def has_permission(user, permission_name, target_object=None):
    """
    Vérifie si l'utilisateur a une permission spécifique
    Usage: {% has_permission user 'manage_users' as can_manage %}
    """
    return PermissionManager.check_permission(user, permission_name, target_object)


@register.simple_tag
def user_can(user, permission_name):
    """
    Version courte pour les permissions simples
    Usage: {% user_can user 'edit_employees' %}
    """
    return PermissionManager.check_permission(user, permission_name)


@register.filter
def can_access_employee(user, employee):
    """
    Filtre pour vérifier l'accès à un employé spécifique
    Usage: {% if user|can_access_employee:employee %}
    """
    return PermissionManager.check_permission(user, 'view_employee', employee)


@register.inclusion_tag('partials/permission_check.html', takes_context=True)
def check_permission(context, permission_name, target_object=None):
    """
    Tag d'inclusion pour afficher du contenu selon les permissions
    Usage: {% check_permission 'manage_users' %}...{% endcheck_permission %}
    """
    request = context['request']
    user = request.user
    
    has_perm = PermissionManager.check_permission(user, permission_name, target_object)
    
    return {
        'has_permission': has_perm,
        'permission_name': permission_name,
        'user': user,
        'user_role': user.profile.role if hasattr(user, 'profile') else None
    }


# === TAGS DE RÔLES ===

@register.simple_tag
def is_role(user, role_name):
    """
    Vérifie si l'utilisateur a un rôle spécifique
    Usage: {% is_role user 'ADMIN' %}
    """
    if not hasattr(user, 'profile'):
        return False
    return user.profile.role == role_name


@register.filter
def is_admin(user):
    """Vérifie si l'utilisateur est admin"""
    return hasattr(user, 'profile') and user.profile.is_admin


@register.filter
def is_rh(user):
    """Vérifie si l'utilisateur est RH"""
    return hasattr(user, 'profile') and user.profile.is_rh


@register.filter
def is_employee(user):
    """Vérifie si l'utilisateur est employé"""
    return hasattr(user, 'profile') and user.profile.is_employe


@register.filter
def is_manager(user):
    """Vérifie si l'utilisateur est manager (Admin ou RH)"""
    return hasattr(user, 'profile') and user.profile.is_manager


# === MENU ET SIDEBAR ADAPTATIFS ===

@register.inclusion_tag('partials/sidebar_menu.html', takes_context=True)
def render_sidebar(context):
    """
    Rendu du menu sidebar selon les permissions
    Usage: {% render_sidebar %}
    """
    request = context['request']
    user = request.user
    
    if not user.is_authenticated or not hasattr(user, 'profile'):
        return {'menu_items': []}
    
    profile = user.profile
    menu_items = []
    
    # Dashboard
    if profile.is_admin:
        menu_items.append({
            'icon': 'fas fa-tachometer-alt',
            'label': 'Dashboard Admin',
            'url': reverse('paie:admin_dashboard'),
            'active': request.resolver_match.url_name == 'admin_dashboard',
            'badge': None
        })
    elif profile.is_rh:
        menu_items.append({
            'icon': 'fas fa-chart-line',
            'label': 'Dashboard RH',
            'url': reverse('paie:rh_dashboard'),
            'active': request.resolver_match.url_name == 'rh_dashboard',
            'badge': None
        })
    else:
        menu_items.append({
            'icon': 'fas fa-home',
            'label': 'Mon Espace',
            'url': reverse('paie:employee_dashboard'),
            'active': request.resolver_match.url_name == 'employee_dashboard',
            'badge': None
        })
    
    # Gestion des utilisateurs (Admin + RH)
    if PermissionManager.check_permission(user, 'manage_users'):
        menu_items.append({
            'icon': 'fas fa-users-cog',
            'label': 'Utilisateurs',
            'url': reverse('paie:users_management') if profile.is_admin else '#',
            'active': 'users' in request.path,
            'badge': 'Admin' if profile.is_admin else None,
            'submenu': [
                {
                    'label': 'Liste des utilisateurs',
                    'url': reverse('paie:users_list'),
                    'permission': 'view_users'
                },
                {
                    'label': 'Créer utilisateur',
                    'url': reverse('paie:user_create'),
                    'permission': 'create_users'
                }
            ] if profile.is_admin else []
        })
    
    # Employés
    if PermissionManager.check_permission(user, 'view_all_employees'):
        menu_items.append({
            'icon': 'fas fa-id-badge',
            'label': 'Employés',
            'url': reverse('paie:spa_employees_list'),
            'active': 'employees' in request.path,
            'badge': 'Tous' if profile.is_manager else None
        })
    elif profile.is_employe:
        menu_items.append({
            'icon': 'fas fa-user',
            'label': 'Mon Profil',
            'url': reverse('paie:profile'),
            'active': 'profile' in request.path,
            'badge': None
        })
    
    # Paie
    if PermissionManager.check_permission(user, 'view_all_payroll'):
        menu_items.append({
            'icon': 'fas fa-calculator',
            'label': 'Paie',
            'url': reverse('paie:payroll_management'),
            'active': 'payroll' in request.path or 'paie' in request.path,
            'badge': 'Gestion',
            'submenu': [
                {
                    'label': 'Calculer paies',
                    'url': '#',
                    'permission': 'calculate_payroll'
                },
                {
                    'label': 'Valider paies',
                    'url': '#',
                    'permission': 'validate_payroll'
                },
                {
                    'label': 'Paramètres',
                    'url': '#',
                    'permission': 'edit_system_settings'
                }
            ]
        })
    elif profile.is_employe:
        menu_items.append({
            'icon': 'fas fa-file-invoice-dollar',
            'label': 'Mes Paies',
            'url': reverse('paie:my_payroll'),
            'active': 'my-payroll' in request.path,
            'badge': None
        })
    
    # Congés
    if PermissionManager.check_permission(user, 'view_all_leaves'):
        # Compter les demandes en attente (simulation)
        pending_count = 5  # TODO: Calculer réellement
        menu_items.append({
            'icon': 'fas fa-calendar-alt',
            'label': 'Congés',
            'url': reverse('paie:leaves_management'),
            'active': 'leaves' in request.path or 'congé' in request.path,
            'badge': f'{pending_count}' if pending_count > 0 else None,
            'badge_class': 'bg-warning' if pending_count > 0 else None
        })
    elif profile.is_employe:
        menu_items.append({
            'icon': 'fas fa-umbrella-beach',
            'label': 'Mes Congés',
            'url': reverse('paie:my_leaves'),
            'active': 'my-leaves' in request.path,
            'badge': None
        })
    
    # Pointages
    if PermissionManager.check_permission(user, 'view_all_timesheet'):
        menu_items.append({
            'icon': 'fas fa-clock',
            'label': 'Pointages',
            'url': reverse('paie:timesheet_management'),
            'active': 'timesheet' in request.path or 'pointage' in request.path,
            'badge': 'Validation'
        })
    elif profile.is_employe:
        menu_items.append({
            'icon': 'fas fa-stopwatch',
            'label': 'Mes Pointages',
            'url': reverse('paie:my_timesheet'),
            'active': 'my-timesheet' in request.path,
            'badge': None
        })
    
    # Rapports (Admin + RH)
    if PermissionManager.check_permission(user, 'view_global_reports'):
        menu_items.append({
            'icon': 'fas fa-chart-bar',
            'label': 'Rapports',
            'url': reverse('paie:reports'),
            'active': 'reports' in request.path,
            'badge': 'Pro' if profile.is_admin else 'RH',
            'submenu': [
                {
                    'label': 'Rapports RH',
                    'url': reverse('paie:hr_reports'),
                    'permission': 'view_global_reports'
                },
                {
                    'label': 'Rapports Financiers',
                    'url': reverse('paie:financial_reports'),
                    'permission': 'view_financial_reports'
                }
            ]
        })
    
    # Documents (Employés)
    if profile.is_employe:
        menu_items.append({
            'icon': 'fas fa-file-alt',
            'label': 'Mes Documents',
            'url': reverse('paie:my_documents'),
            'active': 'documents' in request.path,
            'badge': None
        })
    
    # Paramètres (Admin seulement)
    if PermissionManager.check_permission(user, 'edit_system_settings'):
        menu_items.append({
            'icon': 'fas fa-cogs',
            'label': 'Paramètres',
            'url': reverse('paie:system_settings'),
            'active': 'settings' in request.path,
            'badge': 'Admin',
            'submenu': [
                {
                    'label': 'Paramètres généraux',
                    'url': reverse('paie:general_settings'),
                    'permission': 'edit_system_settings'
                },
                {
                    'label': 'Barèmes et taux',
                    'url': reverse('paie:pay_scales'),
                    'permission': 'manage_pay_scales'
                },
                {
                    'label': 'Départements',
                    'url': reverse('paie:departments'),
                    'permission': 'manage_departments'
                }
            ]
        })
    
    return {
        'menu_items': menu_items,
        'user_profile': profile,
        'current_path': request.path
    }


@register.inclusion_tag('partials/user_header.html', takes_context=True)
def render_user_header(context):
    """
    Rendu de l'en-tête utilisateur avec avatar et infos
    Usage: {% render_user_header %}
    """
    request = context['request']
    user = request.user
    
    if not user.is_authenticated or not hasattr(user, 'profile'):
        return {}
    
    profile = user.profile
    
    return {
        'user': user,
        'profile': profile,
        'avatar_url': profile.avatar.url if profile.avatar else '/static/img/default-avatar.png',
        'full_name': user.get_full_name() or user.username,
        'role_display': profile.get_role_display(),
        'role_class': {
            'ADMIN': 'badge-danger',
            'RH': 'badge-warning', 
            'EMPLOYE': 'badge-info'
        }.get(profile.role, 'badge-secondary'),
        'employee': profile.employee,
        'notifications_count': 3,  # TODO: Calculer réellement
        'has_unread_messages': True  # TODO: Vérifier réellement
    }


# === TAGS D'ACTIONS CONDITIONNELLES ===

@register.inclusion_tag('partials/action_button.html', takes_context=True)
def action_button(context, permission, label, url, icon=None, css_class="btn-primary", confirm=None):
    """
    Bouton d'action avec vérification de permission
    Usage: {% action_button 'edit_employees' 'Modifier' employee_url 'fas fa-edit' %}
    """
    request = context['request']
    user = request.user
    
    has_perm = PermissionManager.check_permission(user, permission)
    
    return {
        'has_permission': has_perm,
        'label': label,
        'url': url,
        'icon': icon,
        'css_class': css_class,
        'confirm': confirm,
        'permission': permission
    }


@register.simple_tag(takes_context=True)
def permission_url(context, permission, url_name, *args, **kwargs):
    """
    Génère une URL seulement si l'utilisateur a la permission
    Usage: {% permission_url 'edit_employees' 'employee_edit' employee.id %}
    """
    request = context['request']
    user = request.user
    
    if not PermissionManager.check_permission(user, permission):
        return '#'
    
    try:
        return reverse(url_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return '#'


# === TAGS DE FILTRAGE DE DONNÉES ===

@register.filter
def filter_by_permission(queryset, user):
    """
    Filtre un queryset selon les permissions de l'utilisateur
    Usage: {{ employees|filter_by_permission:user }}
    """
    if not hasattr(user, 'profile'):
        return queryset.none()
    
    return PermissionManager.get_accessible_employees(user)


@register.simple_tag
def get_accessible_employees(user):
    """
    Retourne les employés accessibles selon les permissions
    Usage: {% get_accessible_employees user as employees %}
    """
    return PermissionManager.get_accessible_employees(user)


# === TAGS D'INTERFACE CONDITIONNELLE ===

@register.inclusion_tag('partials/conditional_content.html', takes_context=True)
def show_if_permission(context, permission, content_template, target_object=None):
    """
    Affiche un contenu seulement si l'utilisateur a la permission
    Usage: {% show_if_permission 'edit_employees' 'partials/edit_form.html' %}
    """
    request = context['request']
    user = request.user
    
    has_perm = PermissionManager.check_permission(user, permission, target_object)
    
    return {
        'has_permission': has_perm,
        'content_template': content_template,
        'context': context
    }


@register.simple_tag
def permission_json(user):
    """
    Retourne les permissions de l'utilisateur en JSON (pour JavaScript)
    Usage: {% permission_json user %}
    """
    permissions = get_user_permissions(user)
    return mark_safe(json.dumps(permissions))


@register.filter
def has_any_permission(user, permissions_string):
    """
    Vérifie si l'utilisateur a au moins une des permissions listées
    Usage: {{ user|has_any_permission:"edit_employees,delete_employees" }}
    """
    permissions_list = [p.strip() for p in permissions_string.split(',')]
    
    for permission in permissions_list:
        if PermissionManager.check_permission(user, permission):
            return True
    
    return False


@register.filter
def has_all_permissions(user, permissions_string):
    """
    Vérifie si l'utilisateur a toutes les permissions listées
    Usage: {{ user|has_all_permissions:"edit_employees,view_all_employees" }}
    """
    permissions_list = [p.strip() for p in permissions_string.split(',')]
    
    for permission in permissions_list:
        if not PermissionManager.check_permission(user, permission):
            return False
    
    return True


# === TAGS DE STATISTIQUES ET BADGES ===

@register.simple_tag
def count_pending_approvals(user):
    """
    Compte les éléments en attente d'approbation pour l'utilisateur
    Usage: {% count_pending_approvals user as pending_count %}
    """
    if not PermissionManager.check_permission(user, 'approve_leaves'):
        return 0
    
    # TODO: Implémenter le comptage réel
    from ..models import DemandeConge
    try:
        return DemandeConge.objects.filter(statut='EN_ATTENTE').count()
    except:
        return 0


@register.simple_tag
def get_user_stats(user):
    """
    Retourne les statistiques de l'utilisateur selon son rôle
    Usage: {% get_user_stats user as stats %}
    """
    if not hasattr(user, 'profile'):
        return {}
    
    profile = user.profile
    stats = {}
    
    if profile.is_admin or profile.is_rh:
        # Statistiques manager
        stats.update({
            'total_employees': PermissionManager.get_accessible_employees(user).count(),
            'pending_leaves': count_pending_approvals(user),
            'active_payrolls': 0,  # TODO: Calculer
        })
    elif profile.is_employe:
        # Statistiques employé
        if profile.employee:
            stats.update({
                'remaining_leaves': 25,  # TODO: Calculer réellement
                'worked_hours_month': 152,  # TODO: Calculer
                'last_payroll_date': None,  # TODO: Récupérer
            })
    
    return stats