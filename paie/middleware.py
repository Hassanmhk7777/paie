# paie/middleware.py - Nouveau fichier à créer

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class AuthenticationMiddleware:
    """
    Middleware pour gérer l'authentification et les redirections automatiques
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs qui ne nécessitent pas d'authentification
        self.public_urls = [
            '/paie/auth/login/',
            '/admin/login/',
            '/admin/logout/',
            '/static/',
            '/media/',
        ]
        
        # URLs qui nécessitent une authentification mais pas de vérification de rôle
        self.auth_only_urls = [
            '/paie/auth/logout/',
            '/paie/auth/first-login-password/',
            '/paie/auth/profile/',
            '/paie/api/user-info/',
            '/paie/api/logout/',
        ]
    
    def __call__(self, request):
        # Traitement avant la vue
        response = self.process_request(request)
        if response:
            return response
        
        # Traitement de la vue
        response = self.get_response(request)
        
        # Traitement après la vue (si nécessaire)
        return response
    
    def process_request(self, request):
        """Traitement des requêtes avant qu'elles atteignent les vues"""
        
        path = request.path
        
        # Ignorer les URLs publiques
        if any(path.startswith(url) for url in self.public_urls):
            return None
        
        # Ignorer les URLs admin (Django s'en occupe)
        if path.startswith('/admin/'):
            return None
        
        # Vérifier l'authentification pour toutes les autres URLs
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Authentification requise',
                    'redirect': reverse('paie:login')
                }, status=401)
            else:
                messages.info(request, 'Veuillez vous connecter pour accéder à cette page.')
                return redirect('paie:login')
        
        # URLs qui nécessitent seulement une authentification
        if any(path.startswith(url) for url in self.auth_only_urls):
            return None
        
        # Vérifier que l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Profil utilisateur non configuré. Contactez l\'administrateur.')
            logger.error(f'Utilisateur sans profil: {request.user.username}')
            return redirect('paie:login')
        
        profile = request.user.profile
        
        # Vérifier que le profil est actif
        if not profile.is_active:
            messages.warning(request, 'Votre compte a été désactivé. Contactez votre administrateur.')
            logger.warning(f'Tentative d\'accès avec compte désactivé: {request.user.username}')
            return redirect('paie:logout')
        
        # Redirection première connexion
        if profile.is_first_login and path != '/paie/auth/first-login-password/':
            return redirect('paie:first_login_password_change')
        
        # Ajouter le profil au request pour un accès facile
        request.user_profile = profile
        
        return None


class RoleBasedAccessMiddleware:
    """
    Middleware pour contrôler l'accès selon les rôles
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Configuration des accès par pattern d'URL
        self.role_patterns = {
            # URLs Admin seulement
            '/paie/dashboard/admin/': ['ADMIN'],
            '/paie/spa/users/': ['ADMIN'],
            '/paie/spa/settings/': ['ADMIN'],
            
            # URLs Manager (Admin + RH)
            '/paie/dashboard/rh/': ['ADMIN', 'RH'],
            '/paie/spa/employees/': ['ADMIN', 'RH'],
            '/paie/spa/paie/': ['ADMIN', 'RH'],
            '/paie/spa/leaves/manage/': ['ADMIN', 'RH'],
            '/paie/spa/timesheet/manage/': ['ADMIN', 'RH'],
            
            # URLs Employé seulement
            '/paie/dashboard/employee/': ['EMPLOYE'],
            '/paie/spa/my-paie/': ['EMPLOYE'],
            '/paie/spa/my-leaves/': ['EMPLOYE'],
            '/paie/spa/my-timesheet/': ['EMPLOYE'],
        }
    
    def __call__(self, request):
        response = self.process_request(request)
        if response:
            return response
        
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """Vérifier les permissions selon l'URL"""
        
        if not request.user.is_authenticated:
            return None
        
        if not hasattr(request.user, 'profile'):
            return None
        
        path = request.path
        user_role = request.user.profile.role
        
        # Vérifier les patterns de rôles
        for pattern, allowed_roles in self.role_patterns.items():
            if path.startswith(pattern):
                if user_role not in allowed_roles:
                    logger.warning(f'Accès refusé: {request.user.username} ({user_role}) vers {path}')
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'error': 'Accès refusé',
                            'message': f'Cette page est réservée aux rôles : {", ".join(allowed_roles)}'
                        }, status=403)
                    else:
                        messages.error(
                            request, 
                            f'Accès refusé. Cette page est réservée aux : {", ".join(allowed_roles)}'
                        )
                        # Rediriger vers le dashboard approprié
                        return self._redirect_to_appropriate_dashboard(user_role)
        
        return None
    
    def _redirect_to_appropriate_dashboard(self, role):
        """Rediriger vers le dashboard approprié selon le rôle"""
        if role == 'ADMIN':
            return redirect('paie:admin_dashboard')
        elif role == 'RH':
            return redirect('paie:rh_dashboard')
        else:
            return redirect('paie:employee_dashboard')


class SecurityHeadersMiddleware:
    """
    Middleware pour ajouter des en-têtes de sécurité
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Ajouter des en-têtes de sécurité
        if request.user.is_authenticated:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


# ===== CONFIGURATION SETTINGS.PY =====

"""
# Ajoutez ces configurations dans votre settings.py

# MIDDLEWARE - Ajoutez ces middleware dans l'ordre
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # VOS NOUVEAUX MIDDLEWARE D'AUTHENTIFICATION
    'paie.middleware.AuthenticationMiddleware',
    'paie.middleware.RoleBasedAccessMiddleware',
    'paie.middleware.SecurityHeadersMiddleware',
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# AUTHENTIFICATION
LOGIN_URL = '/paie/auth/login/'
LOGIN_REDIRECT_URL = '/paie/'
LOGOUT_REDIRECT_URL = '/paie/auth/login/'

# SESSIONS
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 heures par défaut
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS en production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True

# CONTEXT PROCESSORS - Ajoutez le vôtre
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # VOTRE CONTEXT PROCESSOR
                'paie.context_processors.user_role_context',
            ],
        },
    },
]

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'paie_auth.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'paie.auth_views': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'paie.middleware': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# MEDIA FILES (pour les avatars)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# SÉCURITÉ
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSRF
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
"""


# ===== CONTEXT PROCESSORS =====
# paie/context_processors.py - Nouveau fichier

def user_role_context(request):
    """Context processor pour avoir les infos utilisateur dans tous les templates"""
    context = {
        'user_role': None,
        'is_admin': False,
        'is_rh': False,
        'is_employe': False,
        'is_manager': False,
        'user_profile': None,
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
            'user_employee': profile.employee,
        })
    
    return context