# paie/migrations/0002_userprofile_system.py
# Créez ce fichier après avoir lancé : python manage.py makemigrations paie

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('paie', '0001_initial'),  # Votre migration existante
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[('ADMIN', 'Administrateur'), ('RH', 'Ressources Humaines'), ('EMPLOYE', 'Employé')], 
                    default='EMPLOYE', 
                    max_length=10, 
                    verbose_name='Rôle'
                )),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Téléphone')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar')),
                ('preferences', models.JSONField(blank=True, default=dict, verbose_name='Préférences')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Modifié le')),
                ('is_first_login', models.BooleanField(default=True, verbose_name='Première connexion')),
                ('is_active', models.BooleanField(default=True, verbose_name='Compte actif')),
                ('created_by', models.ForeignKey(
                    blank=True, 
                    null=True, 
                    on_delete=django.db.models.deletion.SET_NULL, 
                    related_name='created_profiles', 
                    to=settings.AUTH_USER_MODEL, 
                    verbose_name='Créé par'
                )),
                ('employee', models.OneToOneField(
                    blank=True, 
                    null=True, 
                    on_delete=django.db.models.deletion.SET_NULL, 
                    related_name='user_profile', 
                    to='paie.employee', 
                    verbose_name='Employé'
                )),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE, 
                    related_name='profile', 
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Profil Utilisateur',
                'verbose_name_plural': 'Profils Utilisateurs',
                'db_table': 'paie_userprofile',
            },
        ),
    ]