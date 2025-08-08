# paie/urls_auth_test.py - URLs simplifiées pour le test d'auth

from django.urls import path
from . import auth_views, views

app_name = 'paie'

urlpatterns = [
    # Authentification uniquement
    path('login/', auth_views.custom_login, name='login'),
    path('logout/', auth_views.custom_logout, name='logout'),
    path('first-login-password/', auth_views.first_login_password_change, name='first_login_password_change'),
    path('profile/', auth_views.profile_view, name='profile'),
    
    # APIs pour l'authentification
    path('api/user-info/', auth_views.api_user_info, name='api_user_info'),
    path('api/logout/', auth_views.api_logout, name='api_logout'),
    path('paie/api/user-permissions/', views.api_user_permissions, name='api_user_permissions'),
    
    # APIs essentielles pour le dashboard
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/recent-employees/', views.api_recent_employees, name='api_recent_employees'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/attendance/presence-status/', views.api_get_presence_status, name='api_get_presence_status'),
    path('api/attendance/alertes/', views.api_list_alertes, name='api_alertes_pointage'),
    
    # SPA Content Routes essentielles (only existing views)
    path('spa/dashboard/', views.spa_dashboard, name='spa_dashboard'),
    path('spa/employees/list/', views.spa_employees_list, name='spa_employees_list'),
    path('spa/employees/organigramme/', views.spa_organigramme, name='spa_organigramme'),
    path('spa/payroll/calculation/', views.spa_payroll_calculation, name='spa_payroll_calculation'),
    path('spa/payroll/bulletins/', views.spa_payroll_bulletins, name='spa_payroll_bulletins'),
    path('spa/payroll/statistics/', views.spa_payroll_statistics, name='spa_payroll_statistics'),
    path('spa/payroll/history/', views.spa_payroll_history, name='spa_payroll_history'),
    path('spa/leave/approvals/', views.spa_leave_approvals, name='spa_leave_approvals'),
    path('spa/attendance/reports/', views.spa_attendance_reports, name='spa_attendance_reports'),
    path('spa/config/users/', views.spa_config_users, name='spa_config_users'),
    path('spa/config/sites/', views.spa_config_sites, name='spa_config_sites'),
    path('spa/config/settings/', views.spa_config_settings, name='spa_config_settings'),
    
    # Dashboards selon les rôles
    path('dashboard/admin/', auth_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/rh/', auth_views.rh_dashboard, name='rh_dashboard'),
    path('dashboard/employee/', auth_views.employee_dashboard, name='employee_dashboard'),
    
    # Redirection racine
    path('', auth_views.redirect_user_by_role, name='home'),
]