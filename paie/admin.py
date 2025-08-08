# paie/admin.py - Version corrigée
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import (
    Site, Department, Employee,
    ParametragePaie, BaremeIR, RubriquePersonnalisee, 
    PeriodePaie, BulletinPaie, LigneBulletin
)
from .models import UserProfile, UserRole
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# ==============================================================================
# ADMIN SITE CONFIGURATION
# ==============================================================================

admin.site.site_header = "PaiePro - Administration"
admin.site.site_title = "PaiePro Admin"
admin.site.index_title = "Bienvenue dans l'administration PaiePro"
admin.site.enable_nav_sidebar = True

# ==============================================================================
# ADMIN CLASSES - STRUCTURE ORGANISATIONNELLE
# ==============================================================================

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'email', 'employee_count_display', 'is_active', 'created_at')
    list_filter = ('is_active', 'city', 'created_at')
    search_fields = ('name', 'city', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'employee_count_display')
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'is_active')
        }),
        ('Adresse', {
            'fields': ('address', 'city', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'website'),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': ('created_at', 'updated_at', 'employee_count_display'),
            'classes': ('collapse',)
        })
    )
    
    def employee_count_display(self, obj):
        count = obj.employee_count
        if count > 0:
            url = reverse('admin:paie_employee_changelist') + f'?site__id__exact={obj.id}'
            return format_html(
                '<a href="{}" class="button">{} employé{}</a>',
                url, count, 's' if count > 1 else ''
            )
        return format_html('<span style="color: #999;">Aucun employé</span>')
    
    employee_count_display.short_description = 'Employés'

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'employee_count_display', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'employee_count_display')
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Informations système', {
            'fields': ('created_at', 'updated_at', 'employee_count_display'),
            'classes': ('collapse',)
        })
    )
    
    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return format_html('<span style="color: #999;">Aucune description</span>')
    
    description_short.short_description = 'Description'
    
    def employee_count_display(self, obj):
        count = obj.employee_count
        if count > 0:
            url = reverse('admin:paie_employee_changelist') + f'?department__id__exact={obj.id}'
            return format_html(
                '<a href="{}" class="button">{} employé{}</a>',
                url, count, 's' if count > 1 else ''
            )
        return format_html('<span style="color: #999;">Aucun employé</span>')
    
    employee_count_display.short_description = 'Employés'

# ==============================================================================
# ADMIN EMPLOYEE - UNIFIÉ RH + PAIE
# ==============================================================================

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'full_name_display', 'matricule', 'email', 'position', 'salary_display', 
        'site', 'department', 'hire_date', 'years_of_service_display', 'is_active'
    )
    list_filter = (
        'is_active', 'site', 'department', 'hire_date', 
        'situation_familiale', 'regime_horaire',
        'salary',
        'created_at'
    )
    search_fields = ('first_name', 'last_name', 'email', 'position', 'matricule')
    readonly_fields = ('created_at', 'updated_at', 'years_of_service_display', 'full_name_display', 'matricule')
    list_per_page = 25
    date_hierarchy = 'hire_date'

    
    fieldsets = (
        ('👤 Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('💼 Informations professionnelles', {
            'fields': ('matricule', 'position', 'salary', 'hire_date', 'site', 'department')
        }),
        ('👨‍👩‍👧‍👦 Situation familiale', {
            'fields': ('situation_familiale', 'nb_enfants_charge', 'conjoint_salarie'),
            'classes': ('collapse',)
        }),
        ('🏢 Paramètres administratifs', {
            'fields': (
                'numero_cnss', 'numero_amo', 'numero_cimr', 'numero_mutuelle',
                'regime_horaire', 'nb_heures_semaine', 'affilie_cimr', 'exonere_ir'
            ),
            'classes': ('collapse',)
        }),
        ('🏦 Informations bancaires', {
            'fields': ('banque_principale', 'rib_principal'),
            'classes': ('collapse',)
        }),
        ('⚙️ Statut et système', {
            'fields': ('is_active', 'full_name_display', 'years_of_service_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    # Actions personnalisées
    actions = ['make_active', 'make_inactive', 'export_to_csv', 'generate_bulletins']
    
    def full_name_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color: #666;">Mat: {}</small>',
            obj.full_name, obj.matricule or 'Auto'
        )
    full_name_display.short_description = 'Employé'
    
    def salary_display(self, obj):
        try:
            value = float(obj.salary) if obj.salary is not None else 0.0
        except (ValueError, TypeError):
            value = 0.0
        formatted = '{:,.2f} MAD'.format(value)
        return format_html('<strong style="color: #28a745;">{}</strong>', formatted)
    salary_display.short_description = 'Salaire'
    salary_display.admin_order_field = 'salary'
    
    def years_of_service_display(self, obj):
        years = obj.years_of_service
        if years == 0:
            return format_html('<span style="color: #007bff;">👶 Nouvelle recrue</span>')
        elif years < 2:
            return format_html('<span style="color: #28a745;">🌱 {} an</span>', years)
        elif years < 10:
            return format_html('<span style="color: #ffc107;">⭐ {} ans</span>', years)
        else:
            return format_html('<span style="color: #dc3545;"><strong>🏆 {} ans</strong></span>', years)
    
    years_of_service_display.short_description = 'Ancienneté'
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} employé{"s" if updated > 1 else ""} activé{"s" if updated > 1 else ""}.'
        )
    make_active.short_description = "✅ Activer les employés sélectionnés"
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} employé{"s" if updated > 1 else ""} désactivé{"s" if updated > 1 else ""}.'
        )
    make_inactive.short_description = "❌ Désactiver les employés sélectionnés"
    
    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="employes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Matricule', 'Prénom', 'Nom', 'Email', 'Téléphone', 'Poste', 
            'Salaire', 'Date embauche', 'Site', 'Département', 'CNSS', 'AMO', 'Actif'
        ])
        
        for employee in queryset:
            writer.writerow([
                employee.matricule,
                employee.first_name,
                employee.last_name,
                employee.email,
                employee.phone or '',
                employee.position,
                employee.salary,
                employee.hire_date.strftime('%d/%m/%Y') if employee.hire_date else '',
                employee.site.name if employee.site else '',
                employee.department.name if employee.department else '',
                employee.numero_cnss or '',
                employee.numero_amo or '',
                'Oui' if employee.is_active else 'Non'
            ])
        
        return response
    
    export_to_csv.short_description = "📊 Exporter en CSV"
    
    def generate_bulletins(self, request, queryset):
        """Action pour générer des bulletins en masse"""
        self.message_user(
            request,
            f"Génération de bulletins pour {queryset.count()} employés (fonctionnalité à venir)."
        )
    generate_bulletins.short_description = "💰 Générer bulletins de paie"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('site', 'department')
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Statistiques pour la vue liste
        total_employees = Employee.objects.filter(is_active=True).count()
        total_salary = Employee.objects.filter(is_active=True).aggregate(
            total=models.Sum('salary')
        )['total'] or 0
        
        extra_context.update({
            'total_employees': total_employees,
            'total_salary': total_salary,
            'avg_salary': total_salary / total_employees if total_employees > 0 else 0,
        })
        
        return super().changelist_view(request, extra_context)

# ==============================================================================
# ADMIN CLASSES - MODULE PAIE
# ==============================================================================

@admin.register(ParametragePaie)
class ParametragePaieAdmin(admin.ModelAdmin):
    list_display = ('annee', 'plafond_cnss', 'taux_cnss_salarie', 'taux_amo_salarie', 'actif', 'date_creation')
    list_filter = ('actif', 'annee')
    search_fields = ('annee',)
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('📅 Année et statut', {
            'fields': ('annee', 'actif')
        }),
        ('💰 Plafonds légaux', {
            'fields': ('plafond_cnss', 'plafond_frais_prof', 'deduction_personne', 'taux_frais_prof')
        }),
        ('🛡️ Taux CNSS', {
            'fields': ('taux_cnss_salarie', 'taux_cnss_patronal', 'taux_prestations_sociales', 'taux_formation_prof')
        }),
        ('🏥 Taux AMO', {
            'fields': ('taux_amo_salarie', 'taux_amo_patronal', 'taux_participation_amo')
        }),
        ('🏛️ Taux CIMR', {
            'fields': ('taux_cimr',)
        }),
        ('ℹ️ Informations système', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )

class BaremeIRInline(admin.TabularInline):
    model = BaremeIR
    extra = 1
    ordering = ['ordre']

@admin.register(BaremeIR)
class BaremeIRAdmin(admin.ModelAdmin):
    list_display = ('parametrage', 'ordre', 'tranche_min', 'tranche_max', 'taux', 'somme_a_deduire')
    list_filter = ('parametrage__annee',)
    ordering = ['parametrage', 'ordre']

@admin.register(RubriquePersonnalisee)
class RubriquePersonnaliseeAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'type_rubrique', 'mode_calcul', 'valeur_display', 'actif')
    list_filter = ('type_rubrique', 'mode_calcul', 'actif', 'imposable_ir', 'soumis_cnss')
    search_fields = ('code', 'libelle')
    ordering = ['ordre_affichage']
    
    fieldsets = (
        ('📝 Informations de base', {
            'fields': ('code', 'libelle', 'type_rubrique', 'periodicite', 'actif')
        }),
        ('🧮 Mode de calcul', {
            'fields': ('mode_calcul', 'valeur_fixe', 'pourcentage', 'formule')
        }),
        ('💸 Impact fiscal et social', {
            'fields': ('imposable_ir', 'soumis_cnss', 'soumis_amo', 'soumis_cimr')
        }),
        ('📄 Affichage', {
            'fields': ('ordre_affichage', 'afficher_bulletin')
        })
    )
    
    def valeur_display(self, obj):
        if obj.mode_calcul == 'FIXE' and obj.valeur_fixe:
            return format_html('<strong>{:,.2f} MAD</strong>', obj.valeur_fixe)
        elif obj.mode_calcul == 'POURCENTAGE' and obj.pourcentage:
            return format_html('<strong>{}%</strong>', obj.pourcentage)
        elif obj.mode_calcul == 'FORMULE' and obj.formule:
            return format_html('<code>{}</code>', obj.formule[:30] + '...' if len(obj.formule) > 30 else obj.formule)
        return '-'
    valeur_display.short_description = 'Valeur'

@admin.register(PeriodePaie)
class PeriodePaieAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'type_periode', 'date_debut', 'date_fin', 'statut', 'nb_bulletins', 'total_masse_salariale')
    list_filter = ('type_periode', 'statut', 'date_debut')
    search_fields = ('libelle',)
    readonly_fields = ('date_creation', 'date_modification', 'nb_bulletins', 'total_masse_salariale')
    date_hierarchy = 'date_debut'
    
    fieldsets = (
        ('📅 Période', {
            'fields': ('libelle', 'type_periode', 'date_debut', 'date_fin', 'date_paie')
        }),
        ('⚙️ Paramètres', {
            'fields': ('nb_jours_travailles', 'nb_heures_standard', 'parametrage')
        }),
        ('📊 Statut et suivi', {
            'fields': ('statut', 'calcule_par', 'date_calcul', 'valide_par', 'date_validation')
        }),
        ('📈 Statistiques', {
            'fields': ('nb_bulletins', 'total_masse_salariale'),
            'classes': ('collapse',)
        }),
        ('ℹ️ Informations système', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )
    
    def nb_bulletins(self, obj):
        count = obj.bulletins.count()
        if count > 0:
            url = reverse('admin:paie_bulletinpaie_changelist') + f'?periode__id__exact={obj.id}'
            return format_html('<a href="{}">{} bulletin{}</a>', url, count, 's' if count > 1 else '')
        return '0'
    nb_bulletins.short_description = 'Bulletins'
    
    def total_masse_salariale(self, obj):
        total = obj.bulletins.aggregate(total=models.Sum('net_a_payer'))['total'] or 0
        return format_html('<strong style="color: #28a745;">{:,.2f} MAD</strong>', total)
    total_masse_salariale.short_description = 'Masse salariale'

class LigneBulletinInline(admin.TabularInline):
    model = LigneBulletin
    extra = 0
    readonly_fields = ('rubrique', 'montant')

@admin.register(BulletinPaie)
class BulletinPaieAdmin(admin.ModelAdmin):
    list_display = ('numero_bulletin', 'employe_display', 'periode', 'total_brut', 'net_a_payer', 'date_generation')
    list_filter = ('periode__libelle', 'date_generation', 'employe__department', 'employe__site')
    search_fields = ('numero_bulletin', 'employe__first_name', 'employe__last_name')
    readonly_fields = ('numero_bulletin', 'date_generation', 'genere_par')
    date_hierarchy = 'date_generation'
    inlines = [LigneBulletinInline]
    
    fieldsets = (
        ('👤 Employé et période', {
            'fields': ('employe', 'periode', 'numero_bulletin', 'genere_par', 'date_generation')
        }),
        ('💰 Éléments du brut', {
            'fields': ('salaire_base', 'heures_supplementaires', 'taux_heure_sup', 
                      'prime_anciennete', 'prime_responsabilite', 'indemnite_transport', 'avantages_nature')
        }),
        ('📊 Totaux', {
            'fields': ('total_brut', 'total_imposable', 'total_cotisable_cnss')
        }),
        ('🛡️ Cotisations', {
            'fields': ('cotisation_cnss', 'cotisation_amo', 'cotisation_cimr')
        }),
        ('💸 Impôts et retenues', {
            'fields': ('ir_brut', 'ir_net', 'avances', 'prets', 'autres_retenues', 'total_retenues')
        }),
        ('✅ Net à payer', {
            'fields': ('net_a_payer',)
        }),
        ('🏢 Charges patronales', {
            'fields': ('charges_cnss_patronal', 'charges_amo_patronal', 'formation_professionnelle', 'prestations_sociales'),
            'classes': ('collapse',)
        })
    )
    
    def employe_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.employe.full_name,
            obj.employe.position
        )
    employe_display.short_description = 'Employé'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employe', 'periode', 'genere_par')

# ==============================================================================
# CONFIGURATION AVANCÉE
# ==============================================================================

# Personnalisation du titre admin selon l'environnement
import os
if os.environ.get('DJANGO_ENV') == 'production':
    admin.site.site_header = "🏭 PaiePro PRODUCTION - Administration"
    admin.site.site_title = "PaiePro PROD"
elif os.environ.get('DJANGO_ENV') == 'staging':
    admin.site.site_header = "🧪 PaiePro STAGING - Administration"  
    admin.site.site_title = "PaiePro STAGING"
else:
    admin.site.site_header = "🚧 PaiePro DEV - Administration"
    admin.site.site_title = "PaiePro DEV"
 
# Admin pour UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'role', 
        'employee', 
        'phone', 
        'is_active', 
        'is_first_login',
        'created_at'
    ]
    list_filter = [
        'role', 
        'is_active', 
        'is_first_login', 
        'created_at'
    ]
    search_fields = [
        'user__username', 
        'user__first_name', 
        'user__last_name', 
        'user__email',
        'phone'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'role')
        }),
        ('Informations', {
            'fields': ('employee', 'phone', 'avatar')
        }),
        ('État', {
            'fields': ('is_active', 'is_first_login')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Préférences', {
            'fields': ('preferences',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'employee', 'created_by')


# Extension de l'admin User pour afficher le profil
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Profil'
    verbose_name_plural = 'Profil'
    fields = ['role', 'employee', 'phone', 'avatar', 'is_active']


# Admin User étendu (optionnel - pour voir le profil dans l'admin User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)


# Re-register User admin avec le profil intégré
admin.site.unregister(User)