# paie/api_views.py - Nouveau fichier pour les APIs protégées

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
import json
import logging

from .permissions import PermissionManager, ajax_permission_required
from .models import Employee, UserProfile, UserRole

logger = logging.getLogger(__name__)

# === APIS DE GESTION DES UTILISATEURS ===

@ajax_permission_required('manage_users')
@require_http_methods(["GET"])
def api_users_list(request):
    """API pour lister les utilisateurs selon les permissions"""
    
    profile = request.user.profile
    
    # Filtrage selon les permissions
    if profile.is_admin:
        users = UserProfile.objects.all()
    elif profile.is_rh:
        # RH peut voir tous sauf les admins
        users = UserProfile.objects.exclude(role=UserRole.ADMIN)
    else:
        # Cas d'erreur normalement bloqué par le décorateur
        return JsonResponse({'error': 'Permission insuffisante'}, status=403)
    
    # Filtres optionnels
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '')
    active_filter = request.GET.get('active', '')
    
    if search:
        users = users.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if active_filter:
        users = users.filter(is_active=active_filter.lower() == 'true')
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    paginator = Paginator(users, per_page)
    page_obj = paginator.get_page(page)
    
    # Sérialisation
    users_data = []
    for profile in page_obj:
        user_data = {
            'id': profile.id,
            'user_id': profile.user.id,
            'username': profile.user.username,
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'email': profile.user.email,
            'role': profile.role,
            'role_display': profile.get_role_display(),
            'is_active': profile.is_active,
            'is_first_login': profile.is_first_login,
            'created_at': profile.created_at.isoformat() if profile.created_at else None,
            'last_login': profile.user.last_login.isoformat() if profile.user.last_login else None,
            'employee': {
                'id': profile.employee.id,
                'nom': profile.employee.nom,
                'prenom': profile.employee.prenom,
                'matricule': profile.employee.matricule,
                'department': profile.employee.department.nom if profile.employee.department else None
            } if profile.employee else None,
            'can_edit': PermissionManager.check_permission(request.user, 'edit_employees'),
            'can_delete': PermissionManager.check_permission(request.user, 'delete_employees') and not profile.is_admin
        }
        users_data.append(user_data)
    
    return JsonResponse({
        'success': True,
        'data': users_data,
        'pagination': {
            'page': page_obj.number,
            'per_page': per_page,
            'total': paginator.count,
            'pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        },
        'filters': {
            'search': search,
            'role': role_filter,
            'active': active_filter
        }
    })


@ajax_permission_required('create_users')
@require_http_methods(["POST"])
def api_user_create(request):
    """API pour créer un utilisateur"""
    
    try:
        data = json.loads(request.body)
        
        # Vérification des permissions pour le rôle demandé
        requested_role = data.get('role', UserRole.EMPLOYE)
        if requested_role == UserRole.ADMIN and not request.user.profile.is_admin:
            return JsonResponse({
                'success': False,
                'error': 'Seuls les administrateurs peuvent créer des comptes admin'
            }, status=403)
        
        # Création de l'utilisateur
        from .forms import UserCreationFormWithRole
        form = UserCreationFormWithRole(data, created_by=request.user)
        
        if form.is_valid():
            user = form.save()
            
            logger.info(f'Utilisateur créé: {user.username} par {request.user.username}')
            
            return JsonResponse({
                'success': True,
                'message': 'Utilisateur créé avec succès',
                'user': {
                    'id': user.profile.id,
                    'username': user.username,
                    'full_name': user.get_full_name(),
                    'role': user.profile.role,
                    'role_display': user.profile.get_role_display()
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        logger.error(f'Erreur création utilisateur: {str(e)}')
        return JsonResponse({'success': False, 'error': 'Erreur serveur'}, status=500)


@ajax_permission_required('edit_employees')
@require_http_methods(["PUT"])
def api_user_update(request, user_id):
    """API pour modifier un utilisateur"""
    
    try:
        user_profile = get_object_or_404(UserProfile, id=user_id)
        data = json.loads(request.body)
        
        # Vérification des permissions spéciales
        if user_profile.is_admin and not request.user.profile.is_admin:
            return JsonResponse({
                'success': False,
                'error': 'Seuls les administrateurs peuvent modifier des comptes admin'
            }, status=403)
        
        # Mise à jour des champs autorisés
        allowed_fields = ['first_name', 'last_name', 'email', 'is_active']
        user = user_profile.user
        
        for field in allowed_fields:
            if field in data:
                if field == 'is_active':
                    user_profile.is_active = data[field]
                else:
                    setattr(user, field, data[field])
        
        # Mise à jour du rôle (avec vérification)
        if 'role' in data:
            new_role = data['role']
            if new_role == UserRole.ADMIN and not request.user.profile.is_admin:
                return JsonResponse({
                    'success': False,
                    'error': 'Seuls les administrateurs peuvent assigner le rôle admin'
                }, status=403)
            user_profile.role = new_role
        
        user.save()
        user_profile.save()
        
        logger.info(f'Utilisateur modifié: {user.username} par {request.user.username}')
        
        return JsonResponse({
            'success': True,
            'message': 'Utilisateur modifié avec succès'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        logger.error(f'Erreur modification utilisateur: {str(e)}')
        return JsonResponse({'success': False, 'error': 'Erreur serveur'}, status=500)


# === APIS EMPLOYÉS ===

@ajax_permission_required('view_all_employees')
@require_http_methods(["GET"])
def api_employees_list(request):
    """API pour lister les employés selon les permissions"""
    
    employees = PermissionManager.get_accessible_employees(request.user)
    
    # Filtres
    search = request.GET.get('search', '').strip()
    department_filter = request.GET.get('department', '')
    
    if search:
        employees = employees.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(matricule__icontains=search)
        )
    
    if department_filter:
        employees = employees.filter(department_id=department_filter)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    paginator = Paginator(employees, per_page)
    page_obj = paginator.get_page(page)
    
    # Sérialisation
    employees_data = []
    for employee in page_obj:
        employee_data = {
            'id': employee.id,
            'matricule': employee.matricule,
            'nom': employee.nom,
            'prenom': employee.prenom,
            'email': employee.email,
            'phone': employee.phone,
            'date_embauche': employee.date_embauche.isoformat() if employee.date_embauche else None,
            'department': {
                'id': employee.department.id,
                'nom': employee.department.nom
            } if employee.department else None,
            'has_user_account': hasattr(employee, 'user_profile') and employee.user_profile is not None,
            'user_role': employee.user_profile.role if hasattr(employee, 'user_profile') and employee.user_profile else None,
            'can_edit': PermissionManager.check_permission(request.user, 'edit_employees'),
            'can_delete': PermissionManager.check_permission(request.user, 'delete_employees')
        }
        employees_data.append(employee_data)
    
    return JsonResponse({
        'success': True,
        'data': employees_data,
        'pagination': {
            'page': page_obj.number,
            'per_page': per_page,
            'total': paginator.count,
            'pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        }
    })


# === APIS DE PERMISSIONS ===

@login_required
@require_http_methods(["GET"])
def api_user_permissions(request):
    """API pour récupérer les permissions de l'utilisateur actuel"""
    
    if not hasattr(request.user, 'profile'):
        return JsonResponse({'error': 'Profil utilisateur non configuré'}, status=400)
    
    from .permissions import get_user_permissions
    permissions = get_user_permissions(request.user)
    
    profile = request.user.profile
    
    return JsonResponse({
        'success': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
            'role': profile.role,
            'role_display': profile.get_role_display(),
            'is_admin': profile.is_admin,
            'is_rh': profile.is_rh,
            'is_employe': profile.is_employe,
            'is_manager': profile.is_manager
        },
        'permissions': permissions
    })


@login_required
@require_http_methods(["POST"])
def api_check_permission(request):
    """API pour vérifier une permission spécifique"""
    
    try:
        data = json.loads(request.body)
        permission_name = data.get('permission')
        target_object_id = data.get('target_object_id')
        target_object_type = data.get('target_object_type')
        
        if not permission_name:
            return JsonResponse({'error': 'Permission name required'}, status=400)
        
        target_object = None
        if target_object_id and target_object_type:
            if target_object_type == 'employee':
                try:
                    target_object = Employee.objects.get(id=target_object_id)
                except Employee.DoesNotExist:
                    return JsonResponse({'error': 'Target object not found'}, status=404)
        
        has_permission = PermissionManager.check_permission(
            request.user, 
            permission_name, 
            target_object
        )
        
        return JsonResponse({
            'success': True,
            'has_permission': has_permission,
            'permission': permission_name,
            'user_role': request.user.profile.role
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        logger.error(f'Erreur vérification permission: {str(e)}')
        return JsonResponse({'error': 'Erreur serveur'}, status=500)


# === APIS STATISTIQUES ===

@ajax_permission_required('view_global_reports')
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """API pour les statistiques du dashboard"""
    
    profile = request.user.profile
    stats = {}
    
    try:
        if profile.is_admin or profile.is_rh:
            # Statistiques globales
            from django.contrib.auth.models import User
            
            stats['users'] = {
                'total': User.objects.count(),
                'admin': UserProfile.objects.filter(role=UserRole.ADMIN).count(),
                'rh': UserProfile.objects.filter(role=UserRole.RH).count(),
                'employee': UserProfile.objects.filter(role=UserRole.EMPLOYE).count(),
                'active': UserProfile.objects.filter(is_active=True).count()
            }
            
            stats['employees'] = {
                'total': Employee.objects.count(),
                'with_accounts': Employee.objects.filter(user_profile__isnull=False).count(),
                'without_accounts': Employee.objects.filter(user_profile__isnull=True).count()
            }
            
            # TODO: Ajouter stats paie, congés, pointages
            
        elif profile.is_employe and profile.employee:
            # Statistiques personnelles
            stats['personal'] = {
                'remaining_leaves': 25,  # TODO: Calculer réellement
                'used_leaves': 5,  # TODO: Calculer
                'hours_this_month': 152,  # TODO: Calculer
                'last_payroll': None  # TODO: Récupérer
            }
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'user_role': profile.role
        })
        
    except Exception as e:
        logger.error(f'Erreur récupération stats: {str(e)}')
        return JsonResponse({'error': 'Erreur serveur'}, status=500)


# === MIDDLEWARE API DE PERMISSIONS ===

class APIPermissionMiddleware:
    """
    Middleware spécialisé pour les APIs
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs API nécessitant une authentification
        self.api_patterns = [
            '/paie/api/',
        ]
    
    def __call__(self, request):
        # Vérifier si c'est une requête API
        is_api_request = any(request.path.startswith(pattern) for pattern in self.api_patterns)
        
        if is_api_request:
            # Forcer l'authentification pour toutes les APIs
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'Authentification requise',
                    'code': 'AUTHENTICATION_REQUIRED'
                }, status=401)
            
            # Vérifier que l'utilisateur a un profil
            if not hasattr(request.user, 'profile'):
                return JsonResponse({
                    'success': False,
                    'error': 'Profil utilisateur non configuré',
                    'code': 'PROFILE_NOT_CONFIGURED'
                }, status=400)
            
            # Vérifier que le profil est actif
            if not request.user.profile.is_active:
                return JsonResponse({
                    'success': False,
                    'error': 'Compte désactivé',
                    'code': 'ACCOUNT_DISABLED'
                }, status=403)
        
        response = self.get_response(request)
        
        # Ajouter des headers de sécurité aux réponses API
        if is_api_request:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return response