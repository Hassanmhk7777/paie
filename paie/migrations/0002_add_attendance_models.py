# paie/migrations/0002_add_attendance_models.py
# Migration Django pour créer les tables du Module Pointage & Présence

from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings
import datetime

class Migration(migrations.Migration):

    dependencies = [
        ('paie', '0001_initial'),  # Dépend de la migration initiale avec Employee, Departement, etc.
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ============================================================================
        # 1. PLAGE HORAIRE - Créneaux horaires de base
        # ============================================================================
        migrations.CreateModel(
            name='PlageHoraire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('type_plage', models.CharField(
                    choices=[
                        ('STANDARD', 'Horaire Standard'),
                        ('FLEXIBLE', 'Horaire Flexible'),
                        ('EQUIPE_MATIN', 'Équipe Matin'),
                        ('EQUIPE_SOIR', 'Équipe Soir'),
                        ('EQUIPE_NUIT', 'Équipe Nuit'),
                        ('TEMPS_PARTIEL', 'Temps Partiel'),
                        ('CADRE', 'Horaire Cadre'),
                    ],
                    default='STANDARD',
                    max_length=20
                )),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
                ('duree_pause', models.DurationField(default=datetime.timedelta(hours=1))),
                ('heure_debut_pause', models.TimeField(blank=True, null=True)),
                ('heure_fin_pause', models.TimeField(blank=True, null=True)),
                ('tolerance_arrivee', models.DurationField(default=datetime.timedelta(minutes=10))),
                ('tolerance_depart', models.DurationField(default=datetime.timedelta(minutes=10))),
                ('jours_travailles', models.JSONField(default=list)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Plage Horaire',
                'verbose_name_plural': 'Plages Horaires',
                'ordering': ['nom'],
            },
        ),

        # ============================================================================
        # 2. HORAIRE TRAVAIL - Horaires assignés aux employés
        # ============================================================================
        migrations.CreateModel(
            name='HoraireTravail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_debut', models.DateField()),
                ('date_fin', models.DateField(blank=True, null=True)),
                ('heure_debut_personnalisee', models.TimeField(blank=True, null=True)),
                ('heure_fin_personnalisee', models.TimeField(blank=True, null=True)),
                ('jours_travailles_personnalises', models.JSONField(blank=True, null=True)),
                ('commentaire', models.TextField(blank=True)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('cree_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('employe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='horaires', to='paie.employee')),
                ('plage_horaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='paie.plagehoraire')),
            ],
            options={
                'verbose_name': 'Horaire de Travail',
                'verbose_name_plural': 'Horaires de Travail',
                'ordering': ['-date_debut'],
            },
        ),

        # ============================================================================
        # 3. REGLE POINTAGE - Règles métier du système
        # ============================================================================
        migrations.CreateModel(
            name='ReglePointage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('tolerance_retard_minutes', models.IntegerField(default=10)),
                ('tolerance_depart_anticipe_minutes', models.IntegerField(default=10)),
                ('seuil_retard_alerte_minutes', models.IntegerField(default=15)),
                ('nb_retards_alerte_mois', models.IntegerField(default=3)),
                ('nb_absences_alerte_mois', models.IntegerField(default=2)),
                ('seuil_heures_sup_jour', models.DurationField(default=datetime.timedelta(hours=8))),
                ('seuil_heures_sup_semaine', models.DurationField(default=datetime.timedelta(hours=44))),
                ('taux_majoration_25', models.DecimalField(decimal_places=2, default=25.00, max_digits=5)),
                ('taux_majoration_50', models.DecimalField(decimal_places=2, default=50.00, max_digits=5)),
                ('duree_pause_max_sans_retenue', models.DurationField(default=datetime.timedelta(hours=1))),
                ('pause_payee', models.BooleanField(default=False)),
                ('validation_auto_seuil_minutes', models.IntegerField(default=15)),
                ('validation_obligatoire_weekend', models.BooleanField(default=True)),
                ('validation_obligatoire_feries', models.BooleanField(default=True)),
                ('date_debut', models.DateField()),
                ('date_fin', models.DateField(blank=True, null=True)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('cree_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Règle de Pointage',
                'verbose_name_plural': 'Règles de Pointage',
                'ordering': ['-date_debut'],
            },
        ),

        # ============================================================================
        # 4. POINTAGE - Enregistrements individuels de pointage
        # ============================================================================
        migrations.CreateModel(
            name='Pointage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('type_pointage', models.CharField(
                    choices=[
                        ('ARRIVEE', 'Arrivée'),
                        ('SORTIE', 'Sortie'),
                        ('PAUSE_DEBUT', 'Début Pause'),
                        ('PAUSE_FIN', 'Fin Pause'),
                    ],
                    max_length=15
                )),
                ('heure_pointage', models.DateTimeField()),
                ('heure_theorique', models.DateTimeField(blank=True, null=True)),
                ('statut', models.CharField(
                    choices=[
                        ('NORMAL', 'Normal'),
                        ('RETARD', 'Retard'),
                        ('AVANCE', 'Avancé'),
                        ('CORRIGE', 'Corrigé'),
                        ('SUSPECT', 'Suspect'),
                    ],
                    default='NORMAL',
                    max_length=10
                )),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('geolocalisation', models.JSONField(blank=True, null=True)),
                ('corrige', models.BooleanField(default=False)),
                ('heure_originale', models.DateTimeField(blank=True, null=True)),
                ('raison_correction', models.TextField(blank=True)),
                ('justifie', models.BooleanField(default=False)),
                ('justification', models.TextField(blank=True)),
                ('document_justificatif', models.FileField(blank=True, null=True, upload_to='pointages/justificatifs/')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('corrige_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pointages_corriges', to=settings.AUTH_USER_MODEL)),
                ('cree_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pointages_crees', to=settings.AUTH_USER_MODEL)),
                ('employe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pointages', to='paie.employee')),
            ],
            options={
                'verbose_name': 'Pointage',
                'verbose_name_plural': 'Pointages',
                'ordering': ['-heure_pointage'],
            },
        ),

        # ============================================================================
        # 5. PRESENCE JOURNALIERE - Résumé quotidien par employé
        # ============================================================================
        migrations.CreateModel(
            name='PresenceJournaliere',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('statut_jour', models.CharField(
                    choices=[
                        ('PRESENT', 'Présent'),
                        ('ABSENT', 'Absent'),
                        ('PARTIEL', 'Présence Partielle'),
                        ('CONGE', 'En Congé'),
                        ('MALADIE', 'Arrêt Maladie'),
                        ('MISSION', 'En Mission'),
                        ('TELETRAVAIL', 'Télétravail'),
                    ],
                    default='ABSENT',
                    max_length=15
                )),
                ('heure_arrivee', models.DateTimeField(blank=True, null=True)),
                ('heure_sortie', models.DateTimeField(blank=True, null=True)),
                ('pauses', models.JSONField(default=list)),
                ('heures_travaillees', models.DurationField(default=datetime.timedelta(0))),
                ('heures_theoriques', models.DurationField(default=datetime.timedelta(0))),
                ('duree_pauses', models.DurationField(default=datetime.timedelta(0))),
                ('retard_minutes', models.IntegerField(default=0)),
                ('depart_anticipe_minutes', models.IntegerField(default=0)),
                ('heures_supplementaires', models.DurationField(default=datetime.timedelta(0))),
                ('heures_sup_25', models.DurationField(default=datetime.timedelta(0))),
                ('heures_sup_50', models.DurationField(default=datetime.timedelta(0))),
                ('valide', models.BooleanField(default=False)),
                ('date_validation', models.DateTimeField(blank=True, null=True)),
                ('commentaire_rh', models.TextField(blank=True)),
                ('commentaire_employe', models.TextField(blank=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('employe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='presences_journalieres', to='paie.employee')),
                ('horaire_travail', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='paie.horairetravail')),
                ('valide_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Présence Journalière',
                'verbose_name_plural': 'Présences Journalières',
                'ordering': ['-date'],
            },
        ),

        # ============================================================================
        # 6. VALIDATION PRESENCE - Workflow de validation
        # ============================================================================
        migrations.CreateModel(
            name='ValidationPresence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_validation', models.CharField(
                    choices=[
                        ('JOURNALIERE', 'Validation Journalière'),
                        ('HEBDOMADAIRE', 'Validation Hebdomadaire'),
                        ('MENSUELLE', 'Validation Mensuelle'),
                        ('PONCTUELLE', 'Validation Ponctuelle'),
                    ],
                    max_length=15
                )),
                ('statut', models.CharField(
                    choices=[
                        ('EN_ATTENTE', 'En Attente'),
                        ('VALIDEE', 'Validée'),
                        ('REJETEE', 'Rejetée'),
                        ('EN_COURS', 'En Cours de Validation'),
                    ],
                    default='EN_ATTENTE',
                    max_length=15
                )),
                ('date_debut', models.DateField()),
                ('date_fin', models.DateField()),
                ('date_validation', models.DateTimeField(blank=True, null=True)),
                ('commentaire', models.TextField(blank=True)),
                ('documents_joint', models.FileField(blank=True, null=True, upload_to='validations/')),
                ('nb_presences', models.IntegerField(default=0)),
                ('nb_absences', models.IntegerField(default=0)),
                ('nb_retards', models.IntegerField(default=0)),
                ('total_heures_sup', models.DurationField(default=datetime.timedelta(0))),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('cree_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='validations_creees', to=settings.AUTH_USER_MODEL)),
                ('departement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='paie.department')),
                ('validee_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Validation de Présence',
                'verbose_name_plural': 'Validations de Présence',
                'ordering': ['-date_creation'],
            },
        ),

        # ============================================================================
        # 7. ALERTE PRESENCE - Système d'alertes automatiques
        # ============================================================================
        migrations.CreateModel(
            name='AlertePresence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_alerte', models.CharField(
                    choices=[
                        ('RETARD', 'Retard'),
                        ('ABSENCE', 'Absence Injustifiée'),
                        ('RETARDS_REPETES', 'Retards Répétés'),
                        ('ABSENCES_REPETEES', 'Absences Répétées'),
                        ('OUBLI_POINTAGE', 'Oubli de Pointage'),
                        ('HEURES_SUP_EXCESSIVES', 'Heures Supplémentaires Excessives'),
                        ('PAUSE_PROLONGEE', 'Pause Prolongée'),
                        ('POINTAGE_SUSPECT', 'Pointage Suspect'),
                    ],
                    max_length=25
                )),
                ('niveau_gravite', models.CharField(
                    choices=[
                        ('INFO', 'Information'),
                        ('ATTENTION', 'Attention'),
                        ('ALERTE', 'Alerte'),
                        ('CRITIQUE', 'Critique'),
                    ],
                    default='INFO',
                    max_length=15
                )),
                ('statut', models.CharField(
                    choices=[
                        ('NOUVELLE', 'Nouvelle'),
                        ('EN_COURS', 'En Cours de Traitement'),
                        ('RESOLUE', 'Résolue'),
                        ('IGNOREE', 'Ignorée'),
                    ],
                    default='NOUVELLE',
                    max_length=15
                )),
                ('date_concernee', models.DateField()),
                ('titre', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('details', models.JSONField(default=dict)),
                ('actions_recommandees', models.TextField(blank=True)),
                ('action_prise', models.TextField(blank=True)),
                ('date_traitement', models.DateTimeField(blank=True, null=True)),
                ('notifiee', models.BooleanField(default=False)),
                ('date_notification', models.DateTimeField(blank=True, null=True)),
                ('destinataires', models.JSONField(default=list)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('employe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertes_presence', to='paie.employee')),
                ('traitee_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Alerte de Présence',
                'verbose_name_plural': 'Alertes de Présence',
                'ordering': ['-date_creation'],
            },
        ),

        # ============================================================================
        # RELATIONS MANY-TO-MANY
        # ============================================================================
        migrations.AddField(
            model_name='validationpresence',
            name='employes',
            field=models.ManyToManyField(related_name='validations_presence', to='paie.employee'),
        ),

        # ============================================================================
        # CONTRAINTES D'UNICITÉ ET INDEX
        # ============================================================================
        migrations.AddConstraint(
            model_name='horairetravail',
            constraint=models.UniqueConstraint(fields=['employe', 'date_debut'], name='unique_horaire_employe_date'),
        ),
        migrations.AddConstraint(
            model_name='presencejournaliere',
            constraint=models.UniqueConstraint(fields=['employe', 'date'], name='unique_presence_employe_date'),
        ),

        # ============================================================================
        # INDEX POUR PERFORMANCE
        # ============================================================================
        migrations.AddIndex(
            model_name='pointage',
            index=models.Index(fields=['employe', 'heure_pointage'], name='paie_pointage_emp_heure_idx'),
        ),
        migrations.AddIndex(
            model_name='pointage',
            index=models.Index(fields=['type_pointage', 'heure_pointage'], name='paie_pointage_type_heure_idx'),
        ),
        migrations.AddIndex(
            model_name='pointage',
            index=models.Index(fields=['statut'], name='paie_pointage_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='presencejournaliere',
            index=models.Index(fields=['employe', 'date'], name='paie_presence_emp_date_idx'),
        ),
        migrations.AddIndex(
            model_name='presencejournaliere',
            index=models.Index(fields=['date', 'statut_jour'], name='paie_presence_date_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='presencejournaliere',
            index=models.Index(fields=['valide'], name='paie_presence_valide_idx'),
        ),
        migrations.AddIndex(
            model_name='alertepresence',
            index=models.Index(fields=['employe', 'statut'], name='paie_alerte_emp_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='alertepresence',
            index=models.Index(fields=['type_alerte', 'niveau_gravite'], name='paie_alerte_type_gravite_idx'),
        ),
        migrations.AddIndex(
            model_name='alertepresence',
            index=models.Index(fields=['date_concernee'], name='paie_alerte_date_idx'),
        ),
    ]