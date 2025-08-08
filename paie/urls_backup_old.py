from django.urls import path, include
from . import views, auth_views

app_name = 'paie'

urlpatterns = [
    # ==============================================================================
    # AUTHENTIFICATION
    # ==============================================================================
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
    
    # Dashboards selon les rôles
    path('dashboard/admin/', auth_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/rh/', auth_views.rh_dashboard, name='rh_dashboard'),
    path('dashboard/employee/', auth_views.employee_dashboard, name='employee_dashboard'),
    
    # ==============================================================================
    # MAIN SPA ENTRY POINT
    # ==============================================================================
    path('', auth_views.redirect_user_by_role, name='home'),
    
    # ==============================================================================
    # SPA CONTENT ROUTES
    # ==============================================================================
    
    # Dashboard
    path('spa/dashboard/', views.spa_dashboard, name='spa_dashboard'),
    
    # Employees
    path('spa/employees/list/', views.spa_employees_list, name='spa_employees_list'),
    path('spa/employees/organigramme/', views.spa_organigramme, name='spa_organigramme'),
    
    # Payroll
    path('spa/payroll/calculation/', views.spa_payroll_calculation, name='spa_payroll_calculation'),
    path('spa/payroll/bulletins/', views.spa_payroll_bulletins, name='spa_payroll_bulletins'),
    path('spa/payroll/history/', views.spa_payroll_history, name='spa_payroll_history'),
    path('spa/payroll/settings/', views.spa_payroll_settings, name='spa_payroll_settings'),
    path('spa/payroll/statistics/', views.spa_payroll_statistics, name='spa_payroll_statistics'),
    
    # Leave Management
    path('spa/leave/requests/', views.spa_leave_requests, name='spa_leave_requests'),
    path('spa/leave/planning/', views.spa_leave_planning, name='spa_leave_planning'),
    path('spa/leave/approvals/', views.spa_leave_approvals, name='spa_leave_approvals'),
    path('spa/leave/calendar/', views.spa_leave_calendar, name='spa_leave_calendar'),
    
    # Attendance
    path('spa/attendance/live/', views.spa_attendance_live, name='spa_attendance_live'),
    path('spa/attendance/history/', views.spa_attendance_history, name='spa_attendance_history'),
    path('spa/attendance/absences/', views.spa_attendance_absences, name='spa_attendance_absences'),
    path('spa/attendance/reports/', views.spa_attendance_reports, name='spa_attendance_reports'),
    
    # Configuration
    path('spa/config/sites/', views.spa_config_sites, name='spa_config_sites'),
    path('spa/config/users/', views.spa_config_users, name='spa_config_users'),
    path('spa/config/settings/', views.spa_config_settings, name='spa_config_settings'),
    
    # Reports
    path('spa/reports/dashboard/', views.spa_reports_dashboard, name='spa_reports_dashboard'),
    path('spa/reports/hr/', views.spa_reports_hr, name='spa_reports_hr'),
    path('spa/reports/exports/', views.spa_reports_exports, name='spa_reports_exports'),
    
    # ==============================================================================
    # EMPLOYEE CRUD (AJAX)
    # ==============================================================================
    path('employees/create/', views.employee_create, name='employee_create'),
    # Alias for SPA AJAX compatibility
    path('api/employees/create/', views.employee_create, name='api_employee_create'),
    path('employees/<int:pk>/update/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    
    # ==============================================================================
    # API ENDPOINTS
    # ==============================================================================
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/recent-employees/', views.api_recent_employees, name='api_recent_employees'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('paie/api/user-permissions/', views.api_user_permissions, name='api_user_permissions'),
    
    # ==============================================================================
    # LEGACY REDIRECTS (Pour compatibilité)
    # ==============================================================================
    path('dashboard/', views.dashboard, name='dashboard'),
    path('payroll/', views.payroll, name='payroll'),
    path('leave/', views.leave, name='leave'),
    path('attendance/', views.attendance, name='attendance'),
    path('employees/', views.employees, name='employees'),
]

# ================== CONTENU SPA - MODULE PAIE ==================
urlpatterns += [
    # Contenu SPA Paie
    path('spa/payroll/calculation/', views.payroll_calculation_content, name='payroll_calculation_content'),
    path('spa/payroll/bulletins/', views.payroll_bulletins_content, name='payroll_bulletins_content'),
    path('spa/payroll/parametrage/', views.payroll_parametrage_content, name='spa_payroll_parametrage'),
    path('spa/payroll/periodes/', views.payroll_periodes_content, name='spa_payroll_periodes'),
    path('spa/payroll/statistics/', views.payroll_statistics_content, name='spa_payroll_statistics'),
]

# ================== API PAIE ==================
urlpatterns += [
    # API Calcul et Génération
    path('api/paie/calculer-bulletin-test/', views.api_calculer_bulletin_test, name='api_calculer_bulletin_test'),
    path('api/paie/calculer-test/', views.api_calculer_bulletin_test, name='api_calculer_bulletin_test_alt'),
    path('api/bulletin/calculer/', views.api_calculer_bulletin_test, name='api_bulletin_calculer'),
    path('api/paie/generer-bulletin/', views.api_generer_bulletin, name='api_generer_bulletin'),
    path('api/paie/calculer-periode/', views.api_calculer_periode, name='api_calculer_periode'),
    
    # Debug page (temporaire)
    path('debug/calcul-paie/', views.debug_calcul_paie, name='debug_calcul_paie'),
    
    # API Bulletins
    path('api/paie/bulletin/<int:bulletin_id>/', views.api_bulletin_detail, name='api_bulletin_detail'),
    path('api/paie/bulletin/<int:bulletin_id>/pdf/', views.api_bulletin_pdf, name='api_bulletin_pdf'),
    path('api/paie/bulletin/<int:bulletin_id>/excel/', views.api_bulletin_excel, name='api_bulletin_excel'),
    path('api/paie/bulletin/<int:bulletin_id>/delete/', views.api_bulletin_delete, name='api_bulletin_delete'),
    path('api/paie/bulletins/export/', views.api_bulletins_export, name='api_bulletins_export'),
    
    # API Statistiques
    path('api/paie/statistiques/', views.api_statistiques_paie, name='api_statistiques_paie'),
    path('api/statistiques/paie/', views.api_statistiques_paie, name='api_statistiques_paie_alt'),
    path('api/paie/statistiques/export/', views.api_export_statistiques_paie, name='api_export_statistiques_paie'),
    path('api/paie/statistiques/data/', views.api_statistiques_paie_data, name='api_statistiques_paie_data'),
    
    # API Rubriques Personnalisées
    path('api/paie/rubrique/create/', views.api_rubrique_create, name='api_rubrique_create'),
    path('api/paie/rubrique/<int:rubrique_id>/', views.api_rubrique_detail, name='api_rubrique_detail'),
    path('api/paie/rubrique/<int:rubrique_id>/update/', views.api_rubrique_update, name='api_rubrique_update'),
    path('api/paie/rubrique/<int:rubrique_id>/delete/', views.api_rubrique_delete, name='api_rubrique_delete'),
    
    # API Paramétrage
    path('api/paie/parametrages/', views.api_parametrages_list, name='api_parametrages_list'),
    path('api/parametrages/', views.api_parametrages_list, name='api_parametrages_list_short'),
    path('api/paie/parametrage/<int:parametrage_id>/update/', views.api_parametrage_update, name='api_parametrage_update'),
    path('api/paie/parametrage/create/', views.api_parametrage_create, name='api_parametrage_create'),
    path('api/paie/bareme-ir/<int:bareme_id>/update/', views.api_bareme_ir_update, name='api_bareme_ir_update'),
    path('api/paie/bareme-ir/create/', views.api_bareme_ir_create, name='api_bareme_ir_create'),
    path('api/paie/bareme-ir/<int:bareme_id>/delete/', views.api_bareme_ir_delete, name='api_bareme_ir_delete'),
    
    # API Périodes  
    path('api/paie/periode/create/', views.api_periode_create, name='api_periode_create'),
    path('api/periode/create/', views.api_periode_create, name='api_periode_create_short'),
    path('api/paie/periode/<int:periode_id>/', views.api_periode_detail, name='api_periode_detail'),
    path('api/paie/periode/<int:periode_id>/update/', views.api_periode_update, name='api_periode_update'),
    path('api/paie/periode/<int:periode_id>/delete/', views.api_periode_delete, name='api_periode_delete'),
    path('api/paie/periode/<int:periode_id>/valider/', views.api_periode_valider, name='api_periode_valider'),
    path('api/paie/periode/<int:periode_id>/cloturer/', views.api_periode_cloturer, name='api_periode_cloturer'),
    
    # API Export/Import
    path('api/paie/export/periode/<int:periode_id>/', views.api_export_periode, name='api_export_periode'),
    path('api/paie/export/bulletin/<int:bulletin_id>/', views.api_export_bulletin, name='api_export_bulletin'),
    path('api/paie/export/bulletins/', views.api_export_bulletins, name='api_export_bulletins'),
    path('api/paie/export/declarations/', views.api_export_declarations, name='api_export_declarations'),
]

# ================== URLS ADMIN/GESTION (Optionnel) ==================
urlpatterns += [
    # PDF Bulletins
    path('bulletins/<int:bulletin_id>/pdf/', views.bulletin_pdf, name='bulletin_pdf'),
    path('bulletins/<int:bulletin_id>/download/', views.bulletin_download, name='bulletin_download'),
    
    # Impressions groupées  
    path('periodes/<int:periode_id>/bulletins-pdf/', views.periode_bulletins_pdf, name='periode_bulletins_pdf'),
    path('periodes/<int:periode_id>/livre-paie/', views.periode_livre_paie, name='periode_livre_paie'),
    
    # Déclarations sociales
    path('declarations/cnss/<int:periode_id>/', views.declaration_cnss, name='declaration_cnss'),
    path('declarations/amo/<int:periode_id>/', views.declaration_amo, name='declaration_amo'),
    path('declarations/ir/<int:periode_id>/', views.declaration_ir, name='declaration_ir'),
    
    # API Déclarations
    path('api/paie/declaration/cnss/<int:periode_id>/', views.declaration_cnss, name='api_declaration_cnss'),
    path('api/paie/declaration/amo/<int:periode_id>/', views.declaration_amo, name='api_declaration_amo'),
    path('api/paie/declaration/ir/<int:periode_id>/', views.declaration_ir, name='api_declaration_ir'),
]
# ================== CONTENU SPA - MODULE CONGÉS ==================
urlpatterns += [
    # Contenu SPA Congés
    path('spa/leave/requests/', views.leave_requests_content, name='leave_requests_content'),
    path('spa/leave/planning/', views.leave_planning_content, name='leave_planning_content'),
    path('spa/leave/approvals/', views.leave_approvals_content, name='leave_approvals_content'),
    path('spa/leave/calendar/', views.leave_calendar_content, name='leave_calendar_content'),
    path('spa/leave/balances/', views.leave_balances_content, name='leave_balances_content'),
    path('spa/leave/settings/', views.leave_settings_content, name='leave_settings_content'),
]

# ================== API CONGÉS ==================
urlpatterns += [
    # API Demandes de Congés
    path('api/leave/create/', views.api_create_leave_request, name='api_create_leave_request'),
    path('api/leave/<int:demande_id>/approve/', views.api_approve_leave_request, name='api_approve_leave_request'),
    path('api/leave/<int:demande_id>/cancel/', views.api_cancel_leave_request, name='api_cancel_leave_request'),
    
    # API Validation et Calculs
    path('api/leave/validate-dates/', views.api_validate_leave_dates, name='api_validate_leave_dates'),
    path('api/leave/employee/<int:employe_id>/balances/', views.api_employee_balances, name='api_employee_balances'),
    
    # API Données Calendrier et Statistiques
    path('api/leave/calendar-data/', views.api_leave_calendar_data, name='api_leave_calendar_data'),
    path('api/leave/statistics/', views.api_leave_statistics, name='api_leave_statistics'),
    
    # API Gestion Types de Congés (pour RH)
    # path('api/leave/types/', views.api_leave_types_list, name='api_leave_types_list'),  # TODO: implement view
    path('api/leave/types/create/', views.api_leave_type_create, name='api_leave_type_create'),
    path('api/leave/types/<int:type_id>/update/', views.api_leave_type_update, name='api_leave_type_update'),
    path('api/leave/types/<int:type_id>/delete/', views.api_leave_type_delete, name='api_leave_type_delete'),
    
    # API Export/Import
    path('api/leave/export/planning/', views.api_export_leave_planning, name='api_export_leave_planning'),
    path('api/leave/export/balances/', views.api_export_leave_balances, name='api_export_leave_balances'),
    path('api/leave/import/balances/', views.api_import_leave_balances, name='api_import_leave_balances'),
]

# ================== URLS OPTIONNELLES (Fonctionnalités avancées) ==================
urlpatterns += [
    # Workflow Avancé
    path('api/leave/<int:demande_id>/history/', views.api_leave_request_history, name='api_leave_request_history'),
    path('api/leave/workflow/rules/', views.api_leave_workflow_rules, name='api_leave_workflow_rules'),
    
    # Notifications
    path('api/leave/notifications/', views.api_leave_notifications, name='api_leave_notifications'),
    path('api/leave/notifications/<int:notif_id>/mark-read/', views.api_mark_notification_read, name='api_mark_notification_read'),
    
    # Rapports
    path('api/leave/reports/usage/', views.api_leave_usage_report, name='api_leave_usage_report'),
    path('api/leave/reports/trends/', views.api_leave_trends_report, name='api_leave_trends_report'),
    
    # Paramétrage avancé
    path('api/leave/settings/', views.api_leave_settings, name='api_leave_settings'),
    path('api/leave/settings/update/', views.api_update_leave_settings, name='api_update_leave_settings'),
]

urlpatterns += [
    # ============================================================================
    # VUES SPA CONTENT - Interface utilisateur
    # ============================================================================
    
    # Interface Pointage Principal
    path('spa/attendance/timeclock/', 
         views.attendance_timeclock_content, 
         name='attendance_timeclock_content'),
    
    # Dashboard Temps Réel
    path('spa/attendance/dashboard/', 
         views.attendance_dashboard_content, 
         name='attendance_dashboard_content'),
    
    # Rapports de Présence
    path('spa/attendance/reports/', 
         views.attendance_reports_content, 
         name='attendance_reports_content'),
    
    # Gestion Horaires et Plannings
    path('spa/attendance/schedules/', 
         views.attendance_schedules_content, 
         name='attendance_schedules_content'),
    
    # Validation et Correction Pointages
    path('spa/attendance/validation/', 
         views.attendance_validation_content, 
         name='attendance_validation_content'),
    
    # Configuration Règles et Paramètres
    path('spa/attendance/settings/', 
         views.attendance_settings_content, 
         name='attendance_settings_content'),

    # ============================================================================
    # APIs REST POINTAGE - Fonctionnalités backend
    # ============================================================================
    
    # API Pointage Principal
    path('api/attendance/create-pointage/', 
         views.api_create_pointage, 
         name='api_create_pointage'),
    
    # API Statut Présence Temps Réel
    path('api/attendance/presence-status/', 
         views.api_get_presence_status, 
         name='api_get_presence_status'),
    
    # API Calcul Heures Journalières
    path('api/attendance/calculate-daily-hours/', 
         views.api_calculate_daily_hours, 
         name='api_calculate_daily_hours'),
    
    # API Données Rapports
    # path('api/attendance/reports-data/', 
    #      views.api_attendance_reports_data,  # TODO: implement view
    #      name='api_attendance_reports_data'),
    
    # API Validation Présences
    path('api/attendance/validate-attendance/', 
         views.api_validate_attendance, 
         name='api_validate_attendance'),
    
    # API Export Données Paie
    path('api/attendance/export-payroll-data/', 
         views.api_export_payroll_data, 
         name='api_export_payroll_data'),

    # ============================================================================
    # APIs UTILITAIRES - Actions spéciales
    # ============================================================================
    
    # API Correction Pointage
    path('api/attendance/correct-pointage/', 
         views.api_correct_pointage, 
         name='api_correct_pointage'),
    
    # API Horaire Employé
    path('api/attendance/employee-schedule/<int:employe_id>/', 
         views.api_get_employee_schedule, 
         name='api_get_employee_schedule'),

    # ============================================================================
    # EXPORTS PDF ET EXCEL
    # ============================================================================
    
    # Export PDF Feuille de Présence
    path('attendance/export-pdf/', 
         views.export_attendance_pdf, 
         name='export_attendance_pdf'),
    
    # Export Excel Feuille de Présence
    path('attendance/export-excel/', 
         views.export_attendance_excel, 
         name='export_attendance_excel'),

    # ============================================================================
    # GESTION DES PLAGES HORAIRES (CRUD)
    # ============================================================================
    
    # Créer une plage horaire
    path('api/attendance/plages-horaires/create/', 
         views.api_create_plage_horaire, 
         name='api_create_plage_horaire'),
    
    # Modifier une plage horaire
    path('api/attendance/plages-horaires/<int:plage_id>/update/', 
         views.api_update_plage_horaire, 
         name='api_update_plage_horaire'),
    
    # Supprimer une plage horaire
    path('api/attendance/plages-horaires/<int:plage_id>/delete/', 
         views.api_delete_plage_horaire, 
         name='api_delete_plage_horaire'),
    
    # Dupliquer une plage horaire
    path('api/attendance/plages-horaires/<int:plage_id>/duplicate/', 
         views.api_duplicate_plage_horaire, 
         name='api_duplicate_plage_horaire'),

    # ============================================================================
    # GESTION DES HORAIRES EMPLOYÉS (CRUD)
    # ============================================================================
    
    # Assigner un horaire à un employé
    path('api/attendance/horaires-employes/assign/', 
         views.api_assign_horaire_employe, 
         name='api_assign_horaire_employe'),
    
    # Modifier l'horaire d'un employé
    path('api/attendance/horaires-employes/<int:horaire_id>/update/', 
         views.api_update_horaire_employe, 
         name='api_update_horaire_employe'),
    
    # Terminer l'horaire d'un employé
    path('api/attendance/horaires-employes/<int:horaire_id>/end/', 
         views.api_end_horaire_employe, 
         name='api_end_horaire_employe'),
    
    # Historique des horaires d'un employé
    path('api/attendance/horaires-employes/history/<int:employe_id>/', 
         views.api_get_horaire_history, 
         name='api_get_horaire_history'),

    # ============================================================================
    # GESTION DES RÈGLES DE POINTAGE (CRUD)
    # ============================================================================
    
    # Créer une règle de pointage
    path('api/attendance/regles-pointage/create/', 
         views.api_create_regle_pointage, 
         name='api_create_regle_pointage'),
    
    # Modifier une règle de pointage
    path('api/attendance/regles-pointage/<int:regle_id>/update/', 
         views.api_update_regle_pointage, 
         name='api_update_regle_pointage'),
    
    # Activer/Désactiver une règle
    path('api/attendance/regles-pointage/<int:regle_id>/toggle/', 
         views.api_toggle_regle_pointage, 
         name='api_toggle_regle_pointage'),

    # ============================================================================
    # GESTION DES ALERTES
    # ============================================================================
    
    # Marquer une alerte comme traitée
    path('api/attendance/alertes/<int:alerte_id>/resolve/', 
         views.api_resolve_alerte, 
         name='api_resolve_alerte'),
    
    # Créer une alerte manuelle
    path('api/attendance/alertes/create/', 
         views.api_create_alerte, 
         name='api_create_alerte'),
    
    # Liste des alertes avec filtres
    path('api/attendance/alertes/', 
         views.api_list_alertes, 
         name='api_list_alertes'),

    # ============================================================================
    # STATISTIQUES ET ANALYTICS
    # ============================================================================
    
    # Statistiques globales du jour
    path('api/attendance/stats/daily/', 
         views.api_daily_stats, 
         name='api_daily_stats'),
    
    # Statistiques d'un employé
    path('api/attendance/stats/employee/<int:employe_id>/', 
         views.api_employee_stats, 
         name='api_employee_stats'),
    
    # Statistiques d'un département
    path('api/attendance/stats/department/<int:departement_id>/', 
         views.api_department_stats, 
         name='api_department_stats'),
    
    # Tendances sur période
    path('api/attendance/stats/trends/', 
         views.api_attendance_trends, 
         name='api_attendance_trends'),

    # ============================================================================
    # OUTILS D'ADMINISTRATION
    # ============================================================================
    
    # Recalculer les présences d'une période
    path('api/attendance/admin/recalculate/', 
         views.api_recalculate_attendances, 
         name='api_recalculate_attendances'),
    
    # Import en masse de pointages
    path('api/attendance/admin/bulk-import/', 
         views.api_bulk_import_pointages, 
         name='api_bulk_import_pointages'),
    
    # Nettoyage des données anciennes
    path('api/attendance/admin/cleanup/', 
         views.api_cleanup_old_data, 
         name='api_cleanup_old_data'),
    
    # Test des notifications
    path('api/attendance/admin/test-notification/', 
         views.api_test_notification, 
         name='api_test_notification'),

    # ============================================================================
    # INTÉGRATIONS EXTERNES
    # ============================================================================
    
    # Webhook pour réception de pointages externes
    path('api/attendance/webhook/pointage/', 
         views.webhook_receive_pointage, 
         name='webhook_receive_pointage'),
    
    # API pour intégration tierce (format standardisé)
    path('api/attendance/external/sync/', 
         views.api_external_sync, 
         name='api_external_sync'),

    # ============================================================================
    # RAPPORTS AVANCÉS
    # ============================================================================
    
    # Rapport détaillé personnalisé
    path('api/attendance/reports/custom/', 
         views.api_custom_report, 
         name='api_custom_report'),
    
    # Export CSV personnalisé
    path('attendance/export-csv/', 
         views.export_attendance_csv, 
         name='export_attendance_csv'),
    
    # Rapport de performance employé
    path('attendance/report-performance/<int:employe_id>/', 
         views.employee_performance_report, 
         name='employee_performance_report'),

    # ============================================================================
    # PLANIFICATION ET PRÉVISIONS
    # ============================================================================
    
    # Planificateur d'horaires
    path('api/attendance/planning/schedule/', 
         views.api_schedule_planning, 
         name='api_schedule_planning'),
    
    # Prévisions de présence
    path('api/attendance/planning/forecast/', 
         views.api_attendance_forecast, 
         name='api_attendance_forecast'),
    
    # Optimisation des plannings
    path('api/attendance/planning/optimize/', 
         views.api_optimize_schedules, 
         name='api_optimize_schedules'),
]

# ============================================================================
# PATTERNS DE NAVIGATION SPA - À ajouter dans le template principal
# ============================================================================

"""
Patterns JavaScript pour la navigation SPA à ajouter dans base_spa.html :

// Navigation vers les modules de pointage
function navigateToAttendance(module) {
    const routes = {
        'timeclock': '/spa/attendance/timeclock/',
        'dashboard': '/spa/attendance/dashboard/',
        'reports': '/spa/attendance/reports/',
        'schedules': '/spa/attendance/schedules/',
        'validation': '/spa/attendance/validation/',
        'settings': '/spa/attendance/settings/'
    };
    
    if (routes[module]) {
        loadSPAContent(routes[module]);
        updateActiveMenu('attendance-' + module);
    }
}

// Exemple d'appels depuis le menu
<li class="nav-item">
    <a class="nav-link" href="#" onclick="navigateToAttendance('timeclock')">
        <i class="fas fa-fingerprint me-2"></i>Pointage
    </a>
</li>
"""

# ============================================================================
# PERMISSIONS RECOMMANDÉES
# ============================================================================

"""
Permissions Django à créer pour le module pointage :

# Dans votre modèle Permission ou via les migrations
permissions_pointage = [
    ('can_manage_attendance', 'Peut gérer les présences'),
    ('can_point_for_others', 'Peut pointer pour d\'autres employés'),
    ('can_validate_attendance', 'Peut valider les présences'),
    ('can_correct_pointage', 'Peut corriger les pointages'),
    ('can_export_attendance', 'Peut exporter les données'),
    ('can_manage_schedules', 'Peut gérer les horaires'),
    ('can_view_reports', 'Peut voir les rapports'),
    ('can_admin_attendance', 'Administration du pointage'),
]

# Utilisation dans les vues avec @permission_required
@permission_required('paie.can_validate_attendance')
def api_validate_attendance(request):
    # ...
"""

# ============================================================================
# MIDDLEWARE RECOMMANDÉ
# ============================================================================

"""
Middleware pour logging automatique des actions de pointage :

class AttendanceLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Avant la requête
        if request.path.startswith('/api/attendance/'):
            # Logger l'action
            pass
            
        response = self.get_response(request)
        
        # Après la requête
        if request.path.startswith('/api/attendance/') and response.status_code == 200:
            # Logger le succès
            pass
            
        return response
"""

# ============================================================================
# TÂCHES CELERY RECOMMANDÉES
# ============================================================================

"""
Tâches asynchrones pour le module pointage :

# Dans tasks.py
from celery import shared_task
from .services.gestionnaire_pointage import GestionnairePointage

@shared_task
def calculate_daily_attendances():
    '''Calcule les présences journalières automatiquement'''
    gestionnaire = GestionnairePointage()
    return gestionnaire.calculer_presences_journalieres_auto()

@shared_task
def send_daily_attendance_report():
    '''Envoie le rapport quotidien par email'''
    # Implémentation...

@shared_task
def detect_attendance_anomalies():
    '''Détecte les anomalies de pointage'''
    # Implémentation...

@shared_task
def cleanup_old_pointages():
    '''Nettoie les anciens pointages (>2 ans)'''
    # Implémentation...

# Configuration CELERY BEAT dans settings.py
CELERY_BEAT_SCHEDULE = {
    'calculate-daily-attendances': {
        'task': 'paie.tasks.calculate_daily_attendances',
        'schedule': crontab(hour=23, minute=30),  # 23:30 chaque jour
    },
    'send-daily-report': {
        'task': 'paie.tasks.send_daily_attendance_report',
        'schedule': crontab(hour=18, minute=0),   # 18:00 chaque jour
    },
    'detect-anomalies': {
        'task': 'paie.tasks.detect_attendance_anomalies',
        'schedule': crontab(minute='*/30'),       # Toutes les 30 minutes
    },
}
"""

# ============================================================================
# CONFIGURATION RECOMMANDÉE
# ============================================================================

"""
Settings spécifiques au module pointage à ajouter dans settings.py :

# Configuration Pointage & Présence
ATTENDANCE_SETTINGS = {
    # Règles par défaut
    'DEFAULT_TOLERANCE_MINUTES': 10,
    'DEFAULT_LATE_THRESHOLD_MINUTES': 15,
    'DEFAULT_OVERTIME_THRESHOLD_HOURS': 44,  # Maroc : 44h/semaine
    
    # Notifications
    'ENABLE_EMAIL_NOTIFICATIONS': True,
    'ENABLE_SMS_NOTIFICATIONS': False,
    'NOTIFICATION_EMAILS': ['rh@entreprise.com'],
    
    # Exports
    'EXPORT_FORMATS': ['pdf', 'excel', 'csv'],
    'MAX_EXPORT_RECORDS': 10000,
    
    # Sécurité
    'ENABLE_GEOLOCATION_CHECK': False,
    'ENABLE_IP_RESTRICTION': False,
    'ALLOWED_CORRECTION_DAYS': 7,
    
    # Performance
    'CACHE_STATS_MINUTES': 15,
    'CLEANUP_OLD_DATA_MONTHS': 24,
    'BATCH_SIZE': 1000,
}

# Cache spécifique
CACHES['attendance'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/2',
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
    'KEY_PREFIX': 'attendance',
    'TIMEOUT': 900,  # 15 minutes
}
"""


# URLs d'authentification
auth_urlpatterns = [
    # path('login/', auth_views.custom_login, name='login'),  # TODO: implement view
    # path('logout/', auth_views.custom_logout, name='logout'),  # TODO: implement view
    # path('first-login-password/', auth_views.first_login_password_change, name='first_login_password_change'),  # TODO: implement view
    # path('profile/', auth_views.profile_view, name='profile'),  # TODO: implement view
    
    # APIs pour l'authentification
    # path('api/user-info/', auth_views.api_user_info, name='api_user_info'),  # TODO: implement view
    # path('api/logout/', auth_views.api_logout, name='api_logout'),  # TODO: implement view
]

# URLs des dashboards selon les rôles
dashboard_urlpatterns = [
    # path('dashboard/admin/', auth_views.admin_dashboard, name='admin_dashboard'),  # TODO: implement view
    # path('dashboard/rh/', auth_views.rh_dashboard, name='rh_dashboard'),  # TODO: implement view
    # path('dashboard/employee/', auth_views.employee_dashboard, name='employee_dashboard'),  # TODO: implement view
]

# URLs SPA existantes (vos URLs actuelles)
spa_urlpatterns = [
    path('spa/', views.spa_dashboard, name='spa_dashboard'),
    path('spa/employees/', views.spa_employees_list, name='spa_employees_list'),
    # ... ajoutez vos autres URLs SPA existantes ...
]

# URLs API existantes (vos APIs actuelles)
api_urlpatterns = [
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    # ... ajoutez vos autres APIs existantes ...
]

# URLs principales - Ajout des URLs d'auth manquantes
urlpatterns = [
    # ==============================================================================
    # MAIN SPA ENTRY POINT
    # ==============================================================================
    path('', views.home, name='home'),
    
    # ==============================================================================
    # SPA CONTENT ROUTES
    # ==============================================================================
    
    # Dashboard
    path('spa/dashboard/', views.spa_dashboard, name='spa_dashboard'),
    
    # Employees
    path('spa/employees/list/', views.spa_employees_list, name='spa_employees_list'),
    path('spa/employees/organigramme/', views.spa_organigramme, name='spa_organigramme'),
    
    # Payroll
    path('spa/payroll/calculation/', views.spa_payroll_calculation, name='spa_payroll_calculation'),
    path('spa/payroll/bulletins/', views.spa_payroll_bulletins, name='spa_payroll_bulletins'),
    path('spa/payroll/history/', views.spa_payroll_history, name='spa_payroll_history'),
    path('spa/payroll/settings/', views.spa_payroll_settings, name='spa_payroll_settings'),
    path('spa/payroll/statistics/', views.spa_payroll_statistics, name='spa_payroll_statistics'),
    
    # Leave Management
    path('spa/leaves/request/', views.spa_leave_requests, name='spa_leaves_request'),
    path('spa/leaves/calendar/', views.spa_leave_calendar, name='spa_leave_calendar'),
    path('spa/leaves/approval/', views.spa_leave_approvals, name='spa_leave_approvals'),
    # path('spa/leaves/history/', views.spa_leave_history, name='spa_leave_history'),  # TODO: implement view
    # path('spa/leaves/balance/', views.spa_leave_balance, name='spa_leave_balance'),  # TODO: implement view
    
    # Attendance
    # path('spa/attendance/clock/', views.spa_attendance_clock, name='spa_attendance_clock'),  # TODO: implement view
    # path('spa/attendance/management/', views.spa_attendance_management, name='spa_attendance_management'),  # TODO: implement view  
    path('spa/attendance/reports/', views.spa_attendance_reports, name='spa_attendance_reports'),
    # path('spa/attendance/rules/', views.spa_attendance_rules, name='spa_attendance_rules'),  # TODO: implement view
    
    # Reports
    # path('spa/reports/payroll/', views.spa_reports_payroll, name='spa_reports_payroll'),  # TODO: implement view
    # path('spa/reports/attendance/', views.spa_reports_attendance, name='spa_reports_attendance'),  # TODO: implement view
    # path('spa/reports/leaves/', views.spa_reports_leaves, name='spa_reports_leaves'),  # TODO: implement view
    # path('spa/reports/analytics/', views.spa_reports_analytics, name='spa_reports_analytics'),  # TODO: implement view
    
    # Admin
    # path('spa/admin/users/', views.spa_admin_users, name='spa_admin_users'),  # TODO: implement view
    # path('spa/admin/settings/', views.spa_admin_settings, name='spa_admin_settings'),  # TODO: implement view
    # path('spa/admin/backup/', views.spa_admin_backup, name='spa_admin_backup'),  # TODO: implement view
    # path('spa/admin/logs/', views.spa_admin_logs, name='spa_admin_logs'),  # TODO: implement view
    
    # ==============================================================================
    # API ENDPOINTS
    # ==============================================================================
    
    # Dashboard API
    path('api/dashboard/stats/', auth_views.api_dashboard_stats, name='api_dashboard_stats'),
    # path('api/dashboard/recent-activities/', auth_views.api_recent_activities, name='api_recent_activities'),  # TODO: implement view
    path('api/dashboard/employee-stats/', views.api_employee_stats, name='api_employee_stats'),
    
    # Employee APIs - TODO: implement missing views
    # path('api/employees/', views.api_employees_list, name='api_employees_list'),
    # path('api/employees/create/', views.api_employee_create, name='api_employee_create'),
    # path('api/employees/<int:employee_id>/', views.api_employee_detail, name='api_employee_detail'),
    # path('api/employees/<int:employee_id>/update/', views.api_employee_update, name='api_employee_update'),
    # path('api/employees/<int:employee_id>/delete/', views.api_employee_delete, name='api_employee_delete'),
    # path('api/employees/import/', views.api_employees_import, name='api_employees_import'),
    # path('api/employees/export/', views.api_employees_export, name='api_employees_export'),
    
    # Payroll APIs
    # path('api/payroll/calculate/', views.api_payroll_calculate, name='api_payroll_calculate'),  # TODO: implement view
    # path('api/payroll/periods/', views.api_payroll_periods, name='api_payroll_periods'),  # TODO: implement view
    # path('api/payroll/bulletins/', views.api_payroll_bulletins, name='api_payroll_bulletins'),  # TODO: implement view
    # path('api/payroll/bulletin/<int:bulletin_id>/', views.api_payroll_bulletin_detail, name='api_payroll_bulletin_detail'),  # TODO: implement view
    # path('api/payroll/bulletin/<int:bulletin_id>/pdf/', views.api_payroll_bulletin_pdf, name='api_payroll_bulletin_pdf'),  # TODO: implement view
    # path('api/payroll/settings/', views.api_payroll_settings, name='api_payroll_settings'),  # TODO: implement view
    # path('api/payroll/preview/', views.api_payroll_preview, name='api_payroll_preview'),  # TODO: implement view
    # path('api/payroll/batch-calculate/', views.api_payroll_batch_calculate, name='api_payroll_batch_calculate'),  # TODO: implement view
    
    # Leave Management APIs
    # path('api/leaves/requests/', views.api_leaves_requests, name='api_leaves_requests'),  # TODO: implement view
    # path('api/leaves/request/', views.api_leave_request_create, name='api_leave_request_create'),  # TODO: implement view
    # path('api/leaves/request/<int:request_id>/', views.api_leave_request_detail, name='api_leave_request_detail'),  # TODO: implement view
    # path('api/leaves/request/<int:request_id>/approve/', views.api_leave_request_approve, name='api_leave_request_approve'),  # TODO: implement view
    # path('api/leaves/request/<int:request_id>/reject/', views.api_leave_request_reject, name='api_leave_request_reject'),  # TODO: implement view
    # path('api/leaves/balance/<int:employee_id>/', views.api_leave_balance, name='api_leave_balance'),  # TODO: implement view
    # path('api/leaves/calendar/', views.api_leaves_calendar, name='api_leaves_calendar'),  # TODO: implement view
    # path('api/leaves/types/', views.api_leave_types, name='api_leave_types'),  # TODO: implement view
    
    # Attendance APIs - utilisant views général
    # path('api/attendance/clock-in/', views.api_clock_in, name='api_clock_in'),  # TODO: implement view
    # path('api/attendance/clock-out/', views.api_clock_out, name='api_clock_out'),  # TODO: implement view
    # path('api/attendance/status/', views.api_attendance_status, name='api_attendance_status'),  # TODO: implement view
    # path('api/attendance/history/', views.api_attendance_history, name='api_attendance_history'),  # TODO: implement view
    # path('api/attendance/summary/', views.api_attendance_summary, name='api_attendance_summary'),  # TODO: implement view
    # path('api/attendance/employees/', views.api_attendance_employees, name='api_attendance_employees'),  # TODO: implement view
    path('api/attendance/validate/', views.api_validate_attendance, name='api_validate_attendance'),
    # path('api/attendance/report/', views.api_attendance_report, name='api_attendance_report'),  # TODO: implement view
    
    # Reports APIs
    # path('api/reports/payroll/', views.api_reports_payroll, name='api_reports_payroll'),  # TODO: implement view
    # path('api/reports/attendance/', views.api_reports_attendance, name='api_reports_attendance'),  # TODO: implement view
    # path('api/reports/leaves/', views.api_reports_leaves, name='api_reports_leaves'),  # TODO: implement view
    # path('api/reports/analytics/', views.api_reports_analytics, name='api_reports_analytics'),  # TODO: implement view
    
    # Admin APIs
    # path('api/admin/users/', views.api_admin_users, name='api_admin_users'),  # TODO: implement view
    # path('api/admin/user/create/', views.api_admin_user_create, name='api_admin_user_create'),  # TODO: implement view
    # path('api/admin/user/<int:user_id>/', views.api_admin_user_detail, name='api_admin_user_detail'),  # TODO: implement view
    # path('api/admin/settings/', views.api_admin_settings, name='api_admin_settings'),  # TODO: implement view
    # path('api/admin/backup/', views.api_admin_backup, name='api_admin_backup'),  # TODO: implement view
    # path('api/admin/logs/', views.api_admin_logs, name='api_admin_logs'),  # TODO: implement view
    
    # ==============================================================================
    # AUTHENTIFICATION - Ajout des URLs manquantes
    # ==============================================================================
    # path('login/', auth_views.custom_login, name='login'),  # TODO: implement view
    # path('logout/', auth_views.custom_logout, name='logout'),  # TODO: implement view
    # path('first-login-password/', auth_views.first_login_password_change, name='first_login_password_change'),  # TODO: implement view
    # path('profile/', auth_views.profile_view, name='profile'),  # TODO: implement view
    
    # APIs pour l'authentification
    # path('api/user-info/', auth_views.api_user_info, name='api_user_info'),  # TODO: implement view
    # path('api/logout/', auth_views.api_logout, name='api_logout'),  # TODO: implement view
    
    # ==============================================================================
    # DASHBOARDS SELON LES RÔLES
    # ==============================================================================
    # path('dashboard/admin/', auth_views.admin_dashboard, name='admin_dashboard'),  # TODO: implement view
    # path('dashboard/rh/', auth_views.rh_dashboard, name='rh_dashboard'),  # TODO: implement view
    # path('dashboard/employee/', auth_views.employee_dashboard, name='employee_dashboard'),  # TODO: implement view
]


# ===== URLs PRINCIPALES DU PROJET =====
# Dans votre paie_project/urls.py (le fichier principal)

"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    # Redirection vers l'authentification ou dashboard selon l'état
    if request.user.is_authenticated:
        from paie.auth_views import redirect_user_by_role
        return redirect_user_by_role(request.user)
    else:
        return redirect('paie:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('paie/', include('paie.urls')),
    path('', home_redirect, name='home'),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""
