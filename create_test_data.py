#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paie_project.settings')
django.setup()

from paie.models import Site, Department, Employee

def create_test_data():
    """Créer des données de test pour tester les vues"""
    print("Création des données de test...")
    
    # Créer des sites
    site1, created = Site.objects.get_or_create(
        name="Siège Social",
        defaults={
            'address': '123 Rue Mohammed V',
            'city': 'Casablanca',
            'postal_code': '20000',
            'phone': '+212 522 123 456',
            'email': 'siege@company.ma',
            'is_active': True
        }
    )
    
    site2, created = Site.objects.get_or_create(
        name="Filiale Rabat",
        defaults={
            'address': '456 Avenue Hassan II',
            'city': 'Rabat',
            'postal_code': '10000',
            'phone': '+212 537 123 456',
            'email': 'rabat@company.ma',
            'is_active': True
        }
    )
    
    # Créer des départements
    dept_rh, created = Department.objects.get_or_create(
        name="Ressources Humaines",
        defaults={
            'description': 'Gestion du personnel et des ressources humaines',
            'is_active': True
        }
    )
    
    dept_it, created = Department.objects.get_or_create(
        name="Informatique",
        defaults={
            'description': 'Service informatique et développement',
            'is_active': True
        }
    )
    
    dept_finance, created = Department.objects.get_or_create(
        name="Finance",
        defaults={
            'description': 'Comptabilité et gestion financière',
            'is_active': True
        }
    )
    
    dept_marketing, created = Department.objects.get_or_create(
        name="Marketing",
        defaults={
            'description': 'Marketing et communication',
            'is_active': True
        }
    )
    
    # Créer des employés
    employees_data = [
        {
            'first_name': 'Ahmed',
            'last_name': 'Benali',
            'email': 'ahmed.benali@company.ma',
            'position': 'Directeur RH',
            'site': site1,
            'department': dept_rh,
            'salary': 15000,
            'hire_date': date(2020, 1, 15)
        },
        {
            'first_name': 'Fatima',
            'last_name': 'Alaoui',
            'email': 'fatima.alaoui@company.ma',
            'position': 'Développeuse Senior',
            'site': site1,
            'department': dept_it,
            'salary': 12000,
            'hire_date': date(2019, 6, 10)
        },
        {
            'first_name': 'Hassan',
            'last_name': 'Mouhcine',
            'email': 'hassan.mouhcine@company.ma',
            'position': 'Comptable',
            'site': site2,
            'department': dept_finance,
            'salary': 9000,
            'hire_date': date(2021, 3, 20)
        },
        {
            'first_name': 'Aicha',
            'last_name': 'Zohri',
            'email': 'aicha.zohri@company.ma',
            'position': 'Chef Marketing',
            'site': site1,
            'department': dept_marketing,
            'salary': 11000,
            'hire_date': date(2020, 9, 5)
        },
        {
            'first_name': 'Omar',
            'last_name': 'Berrada',
            'email': 'omar.berrada@company.ma',
            'position': 'Administrateur Système',
            'site': site2,
            'department': dept_it,
            'salary': 10000,
            'hire_date': date(2022, 1, 10)
        },
        {
            'first_name': 'Khadija',
            'last_name': 'Filali',
            'email': 'khadija.filali@company.ma',
            'position': 'Assistante RH',
            'site': site1,
            'department': dept_rh,
            'salary': 6000,
            'hire_date': date(2023, 4, 15)
        },
        {
            'first_name': 'Youssef',
            'last_name': 'Idrissi',
            'email': 'youssef.idrissi@company.ma',
            'position': 'Analyste Financier',
            'site': site2,
            'department': dept_finance,
            'salary': 8500,
            'hire_date': date(2021, 11, 30)
        },
        {
            'first_name': 'Nadia',
            'last_name': 'Lahlou',
            'email': 'nadia.lahlou@company.ma',
            'position': 'Designer',
            'site': site1,
            'department': dept_marketing,
            'salary': 7500,
            'hire_date': date(2022, 8, 12)
        }
    ]
    
    # Créer les employés
    for emp_data in employees_data:
        employee, created = Employee.objects.get_or_create(
            email=emp_data['email'],
            defaults={
                'first_name': emp_data['first_name'],
                'last_name': emp_data['last_name'],
                'position': emp_data['position'],
                'site': emp_data['site'],
                'department': emp_data['department'],
                'salary': emp_data['salary'],
                'hire_date': emp_data['hire_date'],
                'phone': f'+212 6{str(hash(emp_data["email"]))[-8:]}',
                'is_active': True,
                'situation_familiale': 'MARIE',
                'nb_enfants_charge': 1 if emp_data['first_name'] in ['Ahmed', 'Hassan', 'Omar'] else 0,
                'regime_horaire': 'TEMPS_PLEIN',
                'nb_heures_semaine': 44.00,
                'affilie_cimr': True,
            }
        )
        
        if created:
            print(f"✓ Employé créé: {employee.full_name} - {employee.position}")
        else:
            print(f"• Employé existant: {employee.full_name}")
    
    # Afficher les statistiques
    print(f"\n=== STATISTIQUES ===")
    print(f"Sites: {Site.objects.filter(is_active=True).count()}")
    print(f"Départements: {Department.objects.filter(is_active=True).count()}")
    print(f"Employés: {Employee.objects.filter(is_active=True).count()}")
    
    print(f"\n=== RÉPARTITION PAR SITE ===")
    for site in Site.objects.filter(is_active=True):
        count = Employee.objects.filter(is_active=True, site=site).count()
        print(f"{site.name}: {count} employés")
    
    print(f"\n=== RÉPARTITION PAR DÉPARTEMENT ===")
    for dept in Department.objects.filter(is_active=True):
        count = Employee.objects.filter(is_active=True, department=dept).count()
        print(f"{dept.name}: {count} employés")
    
    print("\nDonnées de test créées avec succès! 🎉")

if __name__ == '__main__':
    create_test_data()
