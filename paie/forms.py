from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
        labels = {
            'first_name': "Prénom",
            'last_name': "Nom",
            'email': "Email",
            'position': "Poste",
            'salary': "Salaire",
            'hire_date': "Date d'embauche",
            'site': "Site d'affectation",
            'department': "Département",
        }
