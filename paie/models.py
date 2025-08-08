# paie/models.py - Version corrigée et complète
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date
from django.utils import timezone
from datetime import time, timedelta
import uuid
from django.core.exceptions import ValidationError

class Site(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom du site")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Adresse")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")
    postal_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Code postal")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    website = models.URLField(blank=True, null=True, verbose_name="Site web")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def employee_count(self):
        """Retourne le nombre d'employés sur ce site"""
        return self.employee_set.filter(is_active=True).count()

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom du département")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def employee_count(self):
        """Retourne le nombre d'employés dans ce département"""
        return self.employee_set.filter(is_active=True).count()

class Employee(models.Model):
    """Modèle unifié Employé avec toutes les données RH et Paie"""
    
    # ===== INFORMATIONS PERSONNELLES =====
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Téléphone")
    
    # ===== INFORMATIONS PROFESSIONNELLES =====
    position = models.CharField(max_length=100, verbose_name="Poste")
    hire_date = models.DateField(verbose_name="Date d'embauche")
    matricule = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Matricule")
    
    # Relations
    site = models.ForeignKey(
        Site, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Site d'affectation"
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Département"
    )
    # Manager hiérarchique pour workflow congés
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employes_geres')

    # Paramètres congés
    conges_acquis_debut_annee = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    date_derniere_maj_conges = models.DateField(null=True, blank=True)

    # Préférences notifications
    notification_email_conges = models.BooleanField(default=True)
    notification_sms_conges = models.BooleanField(default=False)
    
    # ===== DONNÉES PAIE =====
    salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Salaire de base"
    )
    
    # Numéros administratifs
    numero_cnss = models.CharField(max_length=20, blank=True, verbose_name="N° CNSS")
    numero_amo = models.CharField(max_length=20, blank=True, verbose_name="N° AMO")
    numero_cimr = models.CharField(max_length=20, blank=True, verbose_name="N° CIMR")
    numero_mutuelle = models.CharField(max_length=20, blank=True, verbose_name="N° Mutuelle")
    
    # Situation familiale
    SITUATION_CHOICES = [
        ('CELIBATAIRE', 'Célibataire'),
        ('MARIE', 'Marié(e)'),
        ('DIVORCE', 'Divorcé(e)'),
        ('VEUF', 'Veuf(ve)'),
    ]
    situation_familiale = models.CharField(
        max_length=20, 
        choices=SITUATION_CHOICES, 
        default='CELIBATAIRE',
        verbose_name="Situation familiale"
    )
    nb_enfants_charge = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Nombre d'enfants à charge"
    )
    conjoint_salarie = models.BooleanField(default=False, verbose_name="Conjoint salarié")
    
    # Paramètres horaires
    REGIME_CHOICES = [
        ('TEMPS_PLEIN', 'Temps plein'),
        ('TEMPS_PARTIEL', 'Temps partiel'),
    ]
    regime_horaire = models.CharField(
        max_length=20, 
        choices=REGIME_CHOICES, 
        default='TEMPS_PLEIN',
        verbose_name="Régime horaire"
    )
    nb_heures_semaine = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=44.00,
        verbose_name="Heures par semaine"
    )
    
    # Options paie
    affilie_cimr = models.BooleanField(default=False, verbose_name="Affilié CIMR")
    exonere_ir = models.BooleanField(default=False, verbose_name="Exonéré IR")
    
    # Informations bancaires
    banque_principale = models.CharField(max_length=100, blank=True, verbose_name="Banque")
    rib_principal = models.CharField(max_length=30, blank=True, verbose_name="RIB")
    
    # ===== MÉTADONNÉES =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # Générer matricule automatiquement
        if not self.matricule:
            last_id = Employee.objects.aggregate(models.Max('id'))['id__max'] or 0
            self.matricule = f"EMP{str(last_id + 1).zfill(4)}"
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Nom complet"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def nom(self):
        """Alias pour compatibilité avec templates paie"""
        return self.last_name
    
    @property 
    def prenom(self):
        """Alias pour compatibilité avec templates paie"""
        return self.first_name
    
    @property
    def salaire_base(self):
        """Alias pour compatibilité avec calculs paie"""
        return self.salary
    
    @property
    def date_embauche(self):
        """Alias pour compatibilité avec calculs paie"""
        return self.hire_date
    
    @property
    def actif(self):
        """Alias pour compatibilité avec templates paie"""
        return self.is_active

    @property
    def years_of_service(self):
        """Calcule l'ancienneté en années"""
        if not self.hire_date:
            return 0
        today = date.today()
        return today.year - self.hire_date.year - (
            (today.month, today.day) < (self.hire_date.month, self.hire_date.day)
        )

    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError
        
        if self.hire_date and self.hire_date > date.today():
            raise ValidationError({
                'hire_date': 'La date d\'embauche ne peut pas être dans le futur.'
            })
        
        if self.salary and self.salary <= 0:
            raise ValidationError({
                'salary': 'Le salaire doit être positif.'
            })

# ===== MODÈLES PAIE =====

class AnneePaie(models.Model):
    """Années de paie pour organiser les périodes"""
    
    annee = models.IntegerField(unique=True, verbose_name="Année")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    
    # Paramètres par défaut pour l'année
    nb_jours_travail_annuel = models.IntegerField(default=260)
    nb_heures_travail_annuel = models.DecimalField(max_digits=8, decimal_places=2, default=2288.00)
    
    # Statut
    is_active = models.BooleanField(default=True, verbose_name="Active")
    is_closed = models.BooleanField(default=False, verbose_name="Clôturée")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Année de Paie"
        verbose_name_plural = "Années de Paie"
        ordering = ['-annee']
    
    def __str__(self):
        return f"Année {self.annee}"
    
    @property
    def nb_periodes(self):
        """Nombre de périodes dans cette année"""
        return self.periodes.count() if hasattr(self, 'periodes') else 0

class ParametragePaie(models.Model):
    """Paramètres généraux de la paie - Conformité Maroc"""
    
    # Plafonds légaux
    plafond_cnss = models.DecimalField(max_digits=10, decimal_places=2, default=6000.00)
    plafond_frais_prof = models.DecimalField(max_digits=10, decimal_places=2, default=2500.00)
    deduction_personne = models.DecimalField(max_digits=6, decimal_places=2, default=30.00)
    
    # Taux CNSS
    taux_cnss_salarie = models.DecimalField(max_digits=5, decimal_places=2, default=4.48)
    taux_cnss_patronal = models.DecimalField(max_digits=5, decimal_places=2, default=6.40)
    taux_prestations_sociales = models.DecimalField(max_digits=5, decimal_places=2, default=8.98)
    taux_formation_prof = models.DecimalField(max_digits=5, decimal_places=2, default=1.60)
    
    # Taux AMO
    taux_amo_salarie = models.DecimalField(max_digits=5, decimal_places=2, default=2.26)
    taux_amo_patronal = models.DecimalField(max_digits=5, decimal_places=2, default=2.26)
    taux_participation_amo = models.DecimalField(max_digits=5, decimal_places=2, default=1.85)
    
    # Taux CIMR
    taux_cimr = models.DecimalField(max_digits=5, decimal_places=2, default=6.00)
    taux_frais_prof = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    
    annee = models.IntegerField(unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'paie_parametrage'
        verbose_name = 'Paramétrage Paie'
        verbose_name_plural = 'Paramétrages Paie'
    
    def __str__(self):
        return f"Paramètres Paie {self.annee}"

class BaremeIR(models.Model):
    """Barème Impôt sur le Revenu - Tranches progressives"""
    
    parametrage = models.ForeignKey(ParametragePaie, on_delete=models.CASCADE, related_name='baremes_ir')
    tranche_min = models.DecimalField(max_digits=10, decimal_places=2)
    tranche_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taux = models.DecimalField(max_digits=5, decimal_places=2)
    somme_a_deduire = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ordre = models.IntegerField()
    
    class Meta:
        db_table = 'paie_bareme_ir'
        ordering = ['ordre']
        verbose_name = 'Barème IR'
        verbose_name_plural = 'Barèmes IR'
    
    def __str__(self):
        max_str = self.tranche_max if self.tranche_max else "∞"
        return f"Tranche {self.tranche_min} - {max_str} : {self.taux}%"

class RubriquePersonnalisee(models.Model):
    """Rubriques personnalisées créées par l'entreprise"""
    
    TYPE_CHOICES = [
        ('GAIN', 'Gain/Prime'),
        ('RETENUE', 'Retenue'),
        ('AVANTAGE', 'Avantage en nature'),
        ('INDEMNITE', 'Indemnité'),
    ]
    
    CALCUL_CHOICES = [
        ('FIXE', 'Montant fixe'),
        ('POURCENTAGE', 'Pourcentage du salaire'),
        ('FORMULE', 'Formule personnalisée'),
    ]
    
    PERIODICITE_CHOICES = [
        ('MENSUEL', 'Mensuel'),
        ('UNIQUE', 'Unique'),
        ('CONDITIONNEL', 'Conditionnel'),
    ]
    
    code = models.CharField(max_length=10, unique=True)
    libelle = models.CharField(max_length=100)
    type_rubrique = models.CharField(max_length=10, choices=TYPE_CHOICES)
    mode_calcul = models.CharField(max_length=15, choices=CALCUL_CHOICES)
    periodicite = models.CharField(max_length=15, choices=PERIODICITE_CHOICES)
    
    # Paramètres de calcul
    valeur_fixe = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    formule = models.TextField(null=True, blank=True)
    
    # Impact fiscal et social
    imposable_ir = models.BooleanField(default=True)
    soumis_cnss = models.BooleanField(default=True)
    soumis_amo = models.BooleanField(default=True)
    soumis_cimr = models.BooleanField(default=False)
    
    # Affichage bulletin
    ordre_affichage = models.IntegerField(default=1)
    afficher_bulletin = models.BooleanField(default=True)
    
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'paie_rubrique_personnalisee'
        verbose_name = 'Rubrique Personnalisée'
        verbose_name_plural = 'Rubriques Personnalisées'
        ordering = ['ordre_affichage']
    
    def __str__(self):
        return f"{self.code} - {self.libelle}"

class PeriodePaie(models.Model):
    """Périodes de paie (mensuelle, quinzaine, etc.)"""
    
    TYPE_CHOICES = [
        ('MENSUEL', 'Mensuel'),
        ('QUINZAINE', 'Quinzaine'),
        ('HEBDOMADAIRE', 'Hebdomadaire'),
        ('JOURNALIER', 'Journalier'),
    ]
    
    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('CALCULE', 'Calculée'),
        ('VALIDEE', 'Validée'),
        ('CLOTUREE', 'Clôturée'),
    ]
    
    libelle = models.CharField(max_length=100)
    type_periode = models.CharField(max_length=15, choices=TYPE_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField()
    date_paie = models.DateField()
    
    nb_jours_travailles = models.IntegerField(default=30)
    nb_heures_standard = models.DecimalField(max_digits=6, decimal_places=2, default=191.33)
    
    parametrage = models.ForeignKey(ParametragePaie, on_delete=models.PROTECT)
    annee_paie = models.ForeignKey(AnneePaie, on_delete=models.PROTECT, related_name='periodes', null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='BROUILLON')
    
    # Suivi
    calcule_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='periodes_calculees')
    date_calcul = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='periodes_validees')
    date_validation = models.DateTimeField(null=True, blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'paie_periode'
        verbose_name = 'Période de Paie'
        verbose_name_plural = 'Périodes de Paie'
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.libelle} ({self.date_debut} - {self.date_fin})"

class BulletinPaie(models.Model):
    """Bulletin de paie individuel"""
    
    periode = models.ForeignKey(PeriodePaie, on_delete=models.CASCADE, related_name='bulletins')
    employe = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='bulletins')
    
    # Salaire de base et éléments variables
    salaire_base = models.DecimalField(max_digits=10, decimal_places=2)
    heures_supplementaires = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    taux_heure_sup = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Primes et indemnités
    prime_anciennete = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prime_responsabilite = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    indemnite_transport = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avantages_nature = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Totaux calculés
    total_brut = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_imposable = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cotisable_cnss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Cotisations sociales
    cotisation_cnss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cotisation_amo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cotisation_cimr = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Impôts
    ir_brut = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ir_net = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Retenues diverses
    avances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prets = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    autres_retenues = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Total des retenues et net à payer
    total_retenues = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_a_payer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Charges patronales
    charges_cnss_patronal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charges_amo_patronal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    formation_professionnelle = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prestations_sociales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Métadonnées
    numero_bulletin = models.CharField(max_length=20, unique=True)
    date_generation = models.DateTimeField(auto_now_add=True)
    genere_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Fichier PDF du bulletin
    fichier_pdf = models.FileField(upload_to='bulletins_paie/', null=True, blank=True)
    
    class Meta:
        db_table = 'paie_bulletin'
        verbose_name = 'Bulletin de Paie'
        verbose_name_plural = 'Bulletins de Paie'
        unique_together = ['periode', 'employe']
        ordering = ['-periode__date_debut', 'employe__last_name']
    
    def __str__(self):
        return f"Bulletin {self.employe.full_name} - {self.periode.libelle}"
    
    def save(self, *args, **kwargs):
        if not self.numero_bulletin:
            from datetime import datetime
            date_str = self.periode.date_debut.strftime('%Y%m')
            count = BulletinPaie.objects.filter(periode=self.periode).count() + 1
            self.numero_bulletin = f"{date_str}-{self.employe.id:03d}-{count:03d}"
        super().save(*args, **kwargs)

class LigneBulletin(models.Model):
    """Lignes détaillées du bulletin (rubriques personnalisées)"""
    
    bulletin = models.ForeignKey(BulletinPaie, on_delete=models.CASCADE, related_name='lignes')
    rubrique = models.ForeignKey(RubriquePersonnalisee, on_delete=models.CASCADE)
    
    # Calcul
    base_calcul = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taux_applique = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Affichage
    ordre_affichage = models.IntegerField()
    
    class Meta:
        db_table = 'paie_ligne_bulletin'
        ordering = ['ordre_affichage']
        unique_together = ['bulletin', 'rubrique']


     # ================== MODÈLES MODULE CONGÉS ==================
# À AJOUTER à la fin de paie/models.py

class TypeConge(models.Model):
    """Types de congés configurables"""
    
    CATEGORIE_CHOICES = [
        ('LEGAL', 'Congé légal'),
        ('MALADIE', 'Congé maladie'),
        ('MATERNITE', 'Congé maternité/paternité'),
        ('EXCEPTIONNEL', 'Congé exceptionnel'),
        ('FORMATION', 'Congé formation'),
        ('SANS_SOLDE', 'Congé sans solde'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=100)
    categorie = models.CharField(max_length=15, choices=CATEGORIE_CHOICES)
    
    # Paramètres
    jours_max_annuel = models.IntegerField(default=0)  # 0 = illimité
    cumul_autorise = models.BooleanField(default=True)
    report_autorise = models.BooleanField(default=True)
    justificatif_requis = models.BooleanField(default=False)
    decompte_weekend = models.BooleanField(default=False)
    
    # Impact paie
    remunere = models.BooleanField(default=True)
    taux_remuneration = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)  # %
    
    # Règles d'acquisition
    jours_acquis_par_mois = models.DecimalField(max_digits=4, decimal_places=2, default=0)  # Ex: 2.5 jours/mois
    anciennete_minimum_mois = models.IntegerField(default=0)
    
    # Configuration
    couleur_affichage = models.CharField(max_length=7, default='#007bff')  # Couleur hex
    ordre_affichage = models.IntegerField(default=1)
    actif = models.BooleanField(default=True)
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'paie_type_conge'
        verbose_name = 'Type de Congé'
        verbose_name_plural = 'Types de Congés'
        ordering = ['ordre_affichage', 'libelle']
    
    def __str__(self):
        return f"{self.code} - {self.libelle}"

class RegleConge(models.Model):
    """Règles métier configurables pour les congés"""
    
    TYPE_REGLE_CHOICES = [
        ('ACQUISITION', 'Règle d\'acquisition'),
        ('VALIDATION', 'Règle de validation'),
        ('PLANIFICATION', 'Règle de planification'),
        ('REPORT', 'Règle de report'),
    ]
    
    code = models.CharField(max_length=30, unique=True)
    libelle = models.CharField(max_length=150)
    type_regle = models.CharField(max_length=15, choices=TYPE_REGLE_CHOICES)
    
    # Paramètres de la règle (JSON flexible)
    parametres = models.JSONField(default=dict)
    # Exemple: {"max_consecutifs": 15, "min_jours_entre_demandes": 7}
    
    # Application
    types_conge = models.ManyToManyField(TypeConge, blank=True)
    departements = models.ManyToManyField('Department', blank=True)  # Si modèle existe
    
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'paie_regle_conge'
        verbose_name = 'Règle de Congé'
        verbose_name_plural = 'Règles de Congés'
    
    def __str__(self):
        return f"{self.code} - {self.libelle}"

class SoldeConge(models.Model):
    """Soldes de congés par employé, type et année"""
    
    employe = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='soldes_conges')
    type_conge = models.ForeignKey(TypeConge, on_delete=models.CASCADE)
    annee = models.IntegerField()
    
    # Soldes
    jours_acquis = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    jours_pris = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    jours_reportes = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    jours_anticipes = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Ajustements manuels
    ajustement_manuel = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    motif_ajustement = models.TextField(blank=True)
    ajuste_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_ajustement = models.DateTimeField(null=True, blank=True)
    
    # Calculs automatiques
    date_derniere_maj = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'paie_solde_conge'
        verbose_name = 'Solde de Congé'
        verbose_name_plural = 'Soldes de Congés'
        unique_together = ['employe', 'type_conge', 'annee']
        ordering = ['-annee', 'employe__last_name']
    
    def __str__(self):
        return f"{self.employe} - {self.type_conge} ({self.annee})"
    
    @property
    def jours_disponibles(self):
        """Calcule les jours disponibles"""
        return self.jours_acquis + self.jours_reportes + self.ajustement_manuel - self.jours_pris
    
    @property
    def jours_restants(self):
        """Alias pour jours_disponibles"""
        return max(self.jours_disponibles, 0)

class DemandeConge(models.Model):
    """Demandes de congés avec workflow d'approbation"""
    
    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('SOUMISE', 'Soumise'),
        ('EN_ATTENTE_MANAGER', 'En attente Manager'),
        ('EN_ATTENTE_RH', 'En attente RH'),
        ('APPROUVEE', 'Approuvée'),
        ('REFUSEE', 'Refusée'),
        ('ANNULEE', 'Annulée'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
    ]
    
    PRIORITE_CHOICES = [
        ('NORMALE', 'Normale'),
        ('URGENTE', 'Urgente'),
        ('PLANIFIEE', 'Planifiée'),
    ]
    
    # Identification
    numero_demande = models.CharField(max_length=20, unique=True, blank=True)
    employe = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='demandes_conges')
    type_conge = models.ForeignKey(TypeConge, on_delete=models.PROTECT)
    
    # Période de congé
    date_debut = models.DateField()
    date_fin = models.DateField()
    date_reprise = models.DateField()  # Calculée automatiquement
    
    # Détails
    nb_jours_demandes = models.DecimalField(max_digits=5, decimal_places=2)
    nb_jours_ouvrables = models.DecimalField(max_digits=5, decimal_places=2)
    motif = models.TextField(max_length=500, blank=True)
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='NORMALE')
    
    # Workflow
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='BROUILLON')
    manager_assigne = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes_a_approuver')
    
    # Pièces jointes
    justificatif = models.FileField(upload_to='conges/justificatifs/', null=True, blank=True)
    certificat_medical = models.FileField(upload_to='conges/certificats/', null=True, blank=True)
    
    # Remplacement
    remplacant = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='remplacements')
    note_remplacement = models.TextField(max_length=300, blank=True)
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='demandes_creees')
    
    # Métadonnées
    commentaire_interne = models.TextField(blank=True)
    
    class Meta:
        db_table = 'paie_demande_conge'
        verbose_name = 'Demande de Congé'
        verbose_name_plural = 'Demandes de Congés'
        ordering = ['-date_creation']
        
        # Index pour performance
        indexes = [
            models.Index(fields=['employe', 'statut']),
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['statut', 'date_creation']),
        ]
    
    def __str__(self):
        return f"{self.numero_demande} - {self.employe} ({self.date_debut} → {self.date_fin})"
    
    def save(self, *args, **kwargs):
        # Générer numéro automatique
        if not self.numero_demande:
            from datetime import datetime
            annee = datetime.now().year
            count = DemandeConge.objects.filter(
                date_creation__year=annee
            ).count() + 1
            self.numero_demande = f"CONG{annee}{count:04d}"
        
        # Calculer date de reprise (jour ouvrable suivant)
        if self.date_fin:
            from datetime import timedelta
            self.date_reprise = self.date_fin + timedelta(days=1)
            # TODO: Ajuster pour éviter weekends/jours fériés
        
        super().save(*args, **kwargs)
    
    @property
    def duree_totale(self):
        """Durée totale en jours calendaires"""
        if self.date_debut and self.date_fin:
            return (self.date_fin - self.date_debut).days + 1
        return 0
    
    @property
    def est_modifiable(self):
        """Vérifie si la demande peut être modifiée"""
        return self.statut in ['BROUILLON', 'SOUMISE']
    
    @property
    def est_annulable(self):
        """Vérifie si la demande peut être annulée"""
        return self.statut in ['SOUMISE', 'EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH', 'APPROUVEE']

class ApprobationConge(models.Model):
    """Historique des approbations/refus de congés"""
    
    ACTION_CHOICES = [
        ('SOUMISSION', 'Soumission'),
        ('APPROBATION_MANAGER', 'Approbation Manager'),
        ('REFUS_MANAGER', 'Refus Manager'),
        ('APPROBATION_RH', 'Approbation RH'),
        ('REFUS_RH', 'Refus RH'),
        ('ANNULATION', 'Annulation'),
        ('MODIFICATION', 'Modification'),
    ]
    
    demande = models.ForeignKey(DemandeConge, on_delete=models.CASCADE, related_name='approbations')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Acteur
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    role_utilisateur = models.CharField(max_length=20)  # MANAGER, RH, EMPLOYE, ADMIN
    
    # Détails de l'action
    commentaire = models.TextField(max_length=500, blank=True)
    statut_precedent = models.CharField(max_length=20, blank=True)
    statut_nouveau = models.CharField(max_length=20)
    
    # Modifications (pour traçabilité)
    donnees_avant = models.JSONField(null=True, blank=True)
    donnees_apres = models.JSONField(null=True, blank=True)
    
    # Métadonnées
    date_action = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'paie_approbation_conge'
        verbose_name = 'Approbation de Congé'
        verbose_name_plural = 'Approbations de Congés'
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.demande.numero_demande} - {self.get_action_display()} par {self.utilisateur}"

# ================== EXTENSION MODÈLE EMPLOYEE ==================
# Ajouter ces champs au modèle Employee existant si pas déjà présents

# Dans Employee, ajouter ces champs s'ils n'existent pas :
"""
# Manager hiérarchique pour workflow congés
manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employes_geres')

# Paramètres congés
conges_acquis_debut_annee = models.DecimalField(max_digits=5, decimal_places=2, default=0)
date_derniere_maj_conges = models.DateField(null=True, blank=True)

# Préférences notifications
notification_email_conges = models.BooleanField(default=True)
notification_sms_conges = models.BooleanField(default=False)
"""   


class PlageHoraire(models.Model):
    """Créneaux horaires : matin, après-midi, nuit, etc."""
    
    TYPES_PLAGE = [
        ('STANDARD', 'Horaire Standard'),
        ('FLEXIBLE', 'Horaire Flexible'),
        ('EQUIPE_MATIN', 'Équipe Matin'),
        ('EQUIPE_SOIR', 'Équipe Soir'),
        ('EQUIPE_NUIT', 'Équipe Nuit'),
        ('TEMPS_PARTIEL', 'Temps Partiel'),
        ('CADRE', 'Horaire Cadre'),
    ]
    
    nom = models.CharField(max_length=100)
    type_plage = models.CharField(max_length=20, choices=TYPES_PLAGE, default='STANDARD')
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    duree_pause = models.DurationField(default=timedelta(hours=1))
    heure_debut_pause = models.TimeField(null=True, blank=True)
    heure_fin_pause = models.TimeField(null=True, blank=True)
    tolerance_arrivee = models.DurationField(default=timedelta(minutes=10))
    tolerance_depart = models.DurationField(default=timedelta(minutes=10))
    
    jours_travailles = models.JSONField(default=list)  # [1,2,3,4,5] pour Lun-Ven
    
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plage Horaire"
        verbose_name_plural = "Plages Horaires"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.heure_debut}-{self.heure_fin})"
    
    @property
    def duree_theorique(self):
        """Calcule la durée théorique de travail (sans pause)"""
        debut = timezone.datetime.combine(timezone.now().date(), self.heure_debut)
        fin = timezone.datetime.combine(timezone.now().date(), self.heure_fin)
        if fin < debut:  # Horaire de nuit
            fin += timedelta(days=1)
        return fin - debut - self.duree_pause


class HoraireTravail(models.Model):
    """Horaires théoriques par employé/période"""
    
    employe = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='horaires')
    plage_horaire = models.ForeignKey(PlageHoraire, on_delete=models.CASCADE)
    
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)  # Si null = horaire permanent
    
    # Horaires spécifiques si différents de la plage
    heure_debut_personnalisee = models.TimeField(null=True, blank=True)
    heure_fin_personnalisee = models.TimeField(null=True, blank=True)
    
    # Jours travaillés spécifiques pour cet employé
    jours_travailles_personnalises = models.JSONField(null=True, blank=True)
    
    commentaire = models.TextField(blank=True)
    
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = "Horaire de Travail"
        verbose_name_plural = "Horaires de Travail"
        ordering = ['-date_debut']
        unique_together = ['employe', 'date_debut']
    
    def __str__(self):
        return f"{self.employe.nom} - {self.plage_horaire.nom} ({self.date_debut})"
    
    @property
    def heure_debut_effective(self):
        return self.heure_debut_personnalisee or self.plage_horaire.heure_debut
    
    @property
    def heure_fin_effective(self):
        return self.heure_fin_personnalisee or self.plage_horaire.heure_fin
    
    @property
    def jours_travailles_effectifs(self):
        return self.jours_travailles_personnalises or self.plage_horaire.jours_travailles


class Pointage(models.Model):
    """Enregistrements pointage : arrivée, sortie, pauses"""
    
    TYPES_POINTAGE = [
        ('ARRIVEE', 'Arrivée'),
        ('SORTIE', 'Sortie'),
        ('PAUSE_DEBUT', 'Début Pause'),
        ('PAUSE_FIN', 'Fin Pause'),
    ]
    
    STATUTS = [
        ('NORMAL', 'Normal'),
        ('RETARD', 'Retard'),
        ('AVANCE', 'Avancé'),
        ('CORRIGE', 'Corrigé'),
        ('SUSPECT', 'Suspect'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employe = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='pointages')
    type_pointage = models.CharField(max_length=15, choices=TYPES_POINTAGE)
    
    heure_pointage = models.DateTimeField()
    heure_theorique = models.DateTimeField(null=True, blank=True)
    
    statut = models.CharField(max_length=10, choices=STATUTS, default='NORMAL')
    
    # Métadonnées
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    geolocalisation = models.JSONField(null=True, blank=True)
    
    # Correction et validation
    corrige = models.BooleanField(default=False)
    heure_originale = models.DateTimeField(null=True, blank=True)
    raison_correction = models.TextField(blank=True)
    corrige_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Justification
    justifie = models.BooleanField(default=False)
    justification = models.TextField(blank=True)
    document_justificatif = models.FileField(upload_to='pointages/justificatifs/', null=True, blank=True)
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pointages_crees')
    
    class Meta:
        verbose_name = "Pointage"
        verbose_name_plural = "Pointages"
        ordering = ['-heure_pointage']
        indexes = [
            models.Index(fields=['employe', 'heure_pointage']),
            models.Index(fields=['type_pointage', 'heure_pointage']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"{self.employe.nom} - {self.get_type_pointage_display()} - {self.heure_pointage.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def retard_minutes(self):
        """Calcule le retard en minutes si applicable"""
        if self.type_pointage == 'ARRIVEE' and self.heure_theorique:
            delta = self.heure_pointage - self.heure_theorique
            return max(0, delta.total_seconds() / 60)
        return 0
    
    def save(self, *args, **kwargs):
        # Déterminer automatiquement le statut
        if self.type_pointage == 'ARRIVEE' and self.heure_theorique:
            retard = self.retard_minutes
            if retard > 15:
                self.statut = 'RETARD'
            elif retard < -10:  # Trop tôt
                self.statut = 'AVANCE'
        
        super().save(*args, **kwargs)


class PresenceJournaliere(models.Model):
    """Résumé quotidien par employé : heures, retards, etc."""
    
    STATUTS_JOUR = [
        ('PRESENT', 'Présent'),
        ('ABSENT', 'Absent'),
        ('PARTIEL', 'Présence Partielle'),
        ('CONGE', 'En Congé'),
        ('MALADIE', 'Arrêt Maladie'),
        ('MISSION', 'En Mission'),
        ('TELETRAVAIL', 'Télétravail'),
    ]
    
    employe = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='presences_journalieres')
    date = models.DateField()
    horaire_travail = models.ForeignKey(HoraireTravail, on_delete=models.CASCADE, null=True)
    
    statut_jour = models.CharField(max_length=15, choices=STATUTS_JOUR, default='ABSENT')
    
    # Pointages de la journée
    heure_arrivee = models.DateTimeField(null=True, blank=True)
    heure_sortie = models.DateTimeField(null=True, blank=True)
    pauses = models.JSONField(default=list)  # Liste des pauses [{"debut": "12:00", "fin": "13:00"}]
    
    # Calculs automatiques
    heures_travaillees = models.DurationField(default=timedelta(0))
    heures_theoriques = models.DurationField(default=timedelta(0))
    duree_pauses = models.DurationField(default=timedelta(0))
    
    retard_minutes = models.IntegerField(default=0)
    depart_anticipe_minutes = models.IntegerField(default=0)
    
    # Heures supplémentaires
    heures_supplementaires = models.DurationField(default=timedelta(0))
    heures_sup_25 = models.DurationField(default=timedelta(0))  # Premières 8h sup
    heures_sup_50 = models.DurationField(default=timedelta(0))  # Au-delà de 8h sup
    
    # Validation
    valide = models.BooleanField(default=False)
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    
    # Commentaires
    commentaire_rh = models.TextField(blank=True)
    commentaire_employe = models.TextField(blank=True)
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Présence Journalière"
        verbose_name_plural = "Présences Journalières"
        ordering = ['-date']
        unique_together = ['employe', 'date']
        indexes = [
            models.Index(fields=['employe', 'date']),
            models.Index(fields=['date', 'statut_jour']),
            models.Index(fields=['valide']),
        ]
    
    def __str__(self):
        return f"{self.employe.nom} - {self.date.strftime('%d/%m/%Y')} - {self.get_statut_jour_display()}"
    
    @property
    def est_jour_travaille(self):
        """Vérifie si c'est un jour travaillé selon l'horaire"""
        if self.horaire_travail:
            return self.date.weekday() + 1 in self.horaire_travail.jours_travailles_effectifs
        return False
    
    @property
    def taux_presence(self):
        """Calcule le taux de présence en pourcentage"""
        if self.heures_theoriques.total_seconds() > 0:
            return (self.heures_travaillees.total_seconds() / self.heures_theoriques.total_seconds()) * 100
        return 0


class ReglePointage(models.Model):
    """Règles métier : seuils retard, heures sup, etc."""
    
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    # Tolérances
    tolerance_retard_minutes = models.IntegerField(default=10)
    tolerance_depart_anticipe_minutes = models.IntegerField(default=10)
    
    # Seuils d'alerte
    seuil_retard_alerte_minutes = models.IntegerField(default=15)
    nb_retards_alerte_mois = models.IntegerField(default=3)
    nb_absences_alerte_mois = models.IntegerField(default=2)
    
    # Heures supplémentaires
    seuil_heures_sup_jour = models.DurationField(default=timedelta(hours=8))
    seuil_heures_sup_semaine = models.DurationField(default=timedelta(hours=44))
    taux_majoration_25 = models.DecimalField(max_digits=5, decimal_places=2, default=25.00)
    taux_majoration_50 = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    
    # Pauses
    duree_pause_max_sans_retenue = models.DurationField(default=timedelta(hours=1))
    pause_payee = models.BooleanField(default=False)
    
    # Validation automatique
    validation_auto_seuil_minutes = models.IntegerField(default=15)
    validation_obligatoire_weekend = models.BooleanField(default=True)
    validation_obligatoire_feries = models.BooleanField(default=True)
    
    # Période d'application
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = "Règle de Pointage"
        verbose_name_plural = "Règles de Pointage"
        ordering = ['-date_debut']
    
    def __str__(self):
        return self.nom


class ValidationPresence(models.Model):
    """Workflow validation des présences"""
    
    TYPES_VALIDATION = [
        ('JOURNALIERE', 'Validation Journalière'),
        ('HEBDOMADAIRE', 'Validation Hebdomadaire'),
        ('MENSUELLE', 'Validation Mensuelle'),
        ('PONCTUELLE', 'Validation Ponctuelle'),
    ]
    
    STATUTS_VALIDATION = [
        ('EN_ATTENTE', 'En Attente'),
        ('VALIDEE', 'Validée'),
        ('REJETEE', 'Rejetée'),
        ('EN_COURS', 'En Cours de Validation'),
    ]
    
    type_validation = models.CharField(max_length=15, choices=TYPES_VALIDATION)
    statut = models.CharField(max_length=15, choices=STATUTS_VALIDATION, default='EN_ATTENTE')
    
    # Période concernée
    date_debut = models.DateField()
    date_fin = models.DateField()
    
    # Employés concernés
    employes = models.ManyToManyField('Employee', related_name='validations_presence')
    departement = models.ForeignKey('Department', on_delete=models.CASCADE, null=True, blank=True)
    
    # Validation
    validee_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    
    # Commentaires et justifications
    commentaire = models.TextField(blank=True)
    documents_joint = models.FileField(upload_to='validations/', null=True, blank=True)
    
    # Statistiques de la validation
    nb_presences = models.IntegerField(default=0)
    nb_absences = models.IntegerField(default=0)
    nb_retards = models.IntegerField(default=0)
    total_heures_sup = models.DurationField(default=timedelta(0))
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='validations_creees')
    
    class Meta:
        verbose_name = "Validation de Présence"
        verbose_name_plural = "Validations de Présence"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Validation {self.get_type_validation_display()} - {self.date_debut} à {self.date_fin}"


class AlertePresence(models.Model):
    """Alertes automatiques : retards, absences"""
    
    TYPES_ALERTE = [
        ('RETARD', 'Retard'),
        ('ABSENCE', 'Absence Injustifiée'),
        ('RETARDS_REPETES', 'Retards Répétés'),
        ('ABSENCES_REPETEES', 'Absences Répétées'),
        ('OUBLI_POINTAGE', 'Oubli de Pointage'),
        ('HEURES_SUP_EXCESSIVES', 'Heures Supplémentaires Excessives'),
        ('PAUSE_PROLONGEE', 'Pause Prolongée'),
        ('POINTAGE_SUSPECT', 'Pointage Suspect'),
    ]
    
    NIVEAUX_GRAVITE = [
        ('INFO', 'Information'),
        ('ATTENTION', 'Attention'),
        ('ALERTE', 'Alerte'),
        ('CRITIQUE', 'Critique'),
    ]
    
    STATUTS_ALERTE = [
        ('NOUVELLE', 'Nouvelle'),
        ('EN_COURS', 'En Cours de Traitement'),
        ('RESOLUE', 'Résolue'),
        ('IGNOREE', 'Ignorée'),
    ]
    
    type_alerte = models.CharField(max_length=25, choices=TYPES_ALERTE)
    niveau_gravite = models.CharField(max_length=15, choices=NIVEAUX_GRAVITE, default='INFO')
    statut = models.CharField(max_length=15, choices=STATUTS_ALERTE, default='NOUVELLE')
    
    employe = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='alertes_presence')
    date_concernee = models.DateField()
    
    titre = models.CharField(max_length=200)
    message = models.TextField()
    details = models.JSONField(default=dict)  # Données supplémentaires spécifiques
    
    # Actions recommandées
    actions_recommandees = models.TextField(blank=True)
    action_prise = models.TextField(blank=True)
    
    # Traitement
    traitee_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    
    # Notification
    notifiee = models.BooleanField(default=False)
    date_notification = models.DateTimeField(null=True, blank=True)
    destinataires = models.JSONField(default=list)  # Liste des emails notifiés
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Alerte de Présence"
        verbose_name_plural = "Alertes de Présence"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['employe', 'statut']),
            models.Index(fields=['type_alerte', 'niveau_gravite']),
            models.Index(fields=['date_concernee']),
        ]
    
    def __str__(self):
        return f"{self.get_type_alerte_display()} - {self.employe.nom} - {self.date_concernee}"
    
    @property
    def est_critique(self):
        return self.niveau_gravite == 'CRITIQUE'
    
    @property
    def age_heures(self):
        """Retourne l'âge de l'alerte en heures"""
        return (timezone.now() - self.date_creation).total_seconds() / 3600



class UserRole(models.TextChoices):
    """Définition des rôles utilisateur"""
    ADMIN = 'ADMIN', 'Administrateur'
    RH = 'RH', 'Ressources Humaines' 
    EMPLOYE = 'EMPLOYE', 'Employé'

class UserProfile(models.Model):
    """Extension du modèle User Django avec gestion des rôles et permissions"""
    
    # Relation OneToOne avec User Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Relation avec Employee existant (optionnelle pour ADMIN)
    employee = models.OneToOneField(
        'Employee', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='user_profile'
    )
    
    # Rôle utilisateur
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.EMPLOYE,
        verbose_name='Rôle'
    )
    
    # Informations complémentaires
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='Téléphone'
    )
    
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar'
    )
    
    # Préférences utilisateur (JSON)
    preferences = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Préférences'
    )
    
    # Métadonnées
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_profiles',
        verbose_name='Créé par'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    # Gestion première connexion
    is_first_login = models.BooleanField(
        default=True,
        verbose_name='Première connexion'
    )
    
    # Compte actif/inactif
    is_active = models.BooleanField(
        default=True,
        verbose_name='Compte actif'
    )
    
    class Meta:
        verbose_name = 'Profil Utilisateur'
        verbose_name_plural = 'Profils Utilisateurs'
        db_table = 'paie_userprofile'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"
    
    def clean(self):
        """Validation métier"""
        super().clean()
        
        # Un employé doit avoir un profil Employee lié
        if self.role == UserRole.EMPLOYE and not self.employee:
            raise ValidationError({
                'employee': 'Un employé doit être lié à une fiche employé existante.'
            })
        
        # Les ADMIN peuvent ne pas avoir d'Employee lié
        if self.role == UserRole.ADMIN and self.employee:
            # Optionnel : les admins peuvent avoir un Employee ou pas
            pass
    
    def save(self, *args, **kwargs):
        """Override save pour validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    # === MÉTHODES DE PERMISSIONS ===
    
    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_rh(self):
        """Vérifie si l'utilisateur est RH"""
        return self.role == UserRole.RH
    
    @property
    def is_employe(self):
        """Vérifie si l'utilisateur est employé"""
        return self.role == UserRole.EMPLOYE
    
    @property
    def is_manager(self):
        """Vérifie si l'utilisateur peut gérer (ADMIN ou RH)"""
        return self.role in [UserRole.ADMIN, UserRole.RH]
    
    def can_manage_users(self):
        """Peut gérer les utilisateurs"""
        return self.is_admin or self.is_rh
    
    def can_create_admin(self):
        """Peut créer des comptes admin (seuls les ADMIN)"""
        return self.is_admin
    
    def can_access_employee_data(self, target_employee):
        """Peut accéder aux données d'un employé"""
        if self.is_admin or self.is_rh:
            return True
        if self.is_employe and self.employee == target_employee:
            return True
        return False
    
    def can_approve_leaves(self):
        """Peut approuver les congés"""
        return self.is_admin or self.is_rh
    
    def get_accessible_employees(self):
        """Retourne les employés accessibles selon les permissions"""
        from .models import Employee  # Import local pour éviter les cycles
        
        if self.is_admin or self.is_rh:
            return Employee.objects.all()
        elif self.is_employe and self.employee:
            return Employee.objects.filter(id=self.employee.id)
        else:
            return Employee.objects.none()


# Signal pour créer automatiquement un UserProfile
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un UserProfile quand un User est créé"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le UserProfile quand le User est sauvé"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


# === HELPER FUNCTIONS ===

def get_user_role(user):
    """Fonction utilitaire pour récupérer le rôle d'un utilisateur"""
    if hasattr(user, 'profile'):
        return user.profile.role
    return UserRole.EMPLOYE

def user_has_permission(user, permission_name):
    """Vérifie si un utilisateur a une permission spécifique"""
    if not hasattr(user, 'profile'):
        return False
    
    profile = user.profile
    
    permissions_map = {
        'manage_users': profile.can_manage_users(),
        'create_admin': profile.can_create_admin(),
        'approve_leaves': profile.can_approve_leaves(),
        'access_all_data': profile.is_admin or profile.is_rh,
        'manage_paie': profile.is_admin or profile.is_rh,
        'view_reports': profile.is_admin or profile.is_rh,
    }
    
    return permissions_map.get(permission_name, False)