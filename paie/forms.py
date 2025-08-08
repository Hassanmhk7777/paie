# paie/forms.py - CORRECTION URGENTE
from django import forms
from .models import Employee, Site, Department
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from .models import UserRole

class EmployeeSearchForm(forms.Form):
    """Formulaire de recherche et filtrage des employés"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, email ou poste...',
            'autocomplete': 'off'
        }),
        label='Recherche'
    )
    
    site = forms.ModelChoiceField(
        queryset=Site.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les sites",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Site'
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les départements",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Département'
    )

class EmployeeForm(forms.ModelForm):
    """Formulaire de création/modification employé"""
    
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'position', 'hire_date', 'site', 'department', 
            'salary', 'situation_familiale', 'nb_enfants_charge',
            'regime_horaire', 'nb_heures_semaine', 'affilie_cimr',
            'numero_cnss', 'numero_amo', 'numero_cimr'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nom'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemple.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+212 6XX XX XX XX'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Intitulé du poste'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'site': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'situation_familiale': forms.Select(attrs={'class': 'form-select'}),
            'nb_enfants_charge': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10'
            }),
            'regime_horaire': forms.Select(attrs={'class': 'form-select'}),
            'nb_heures_semaine': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.5'
            }),
            'affilie_cimr': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'numero_cnss': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° CNSS'
            }),
            'numero_amo': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'N° AMO'
            }),
            'numero_cimr': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° CIMR'
            }),
        }
        
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Email',
            'phone': 'Téléphone',
            'position': 'Poste',
            'hire_date': 'Date d\'embauche',
            'site': 'Site',
            'department': 'Département',
            'salary': 'Salaire (MAD)',
            'situation_familiale': 'Situation familiale',
            'nb_enfants_charge': 'Enfants à charge',
            'regime_horaire': 'Régime horaire',
            'nb_heures_semaine': 'Heures/semaine',
            'affilie_cimr': 'Affilié CIMR',
            'numero_cnss': 'N° CNSS',
            'numero_amo': 'N° AMO',
            'numero_cimr': 'N° CIMR',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Charger les sites et départements actifs
        self.fields['site'].queryset = Site.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        
        # Rendre certains champs optionnels
        self.fields['site'].required = False
        self.fields['department'].required = False
        self.fields['phone'].required = False
        self.fields['numero_cnss'].required = False
        self.fields['numero_amo'].required = False
        self.fields['numero_cimr'].required = False

    def clean_email(self):
        """Validation email unique"""
        email = self.cleaned_data.get('email')
        if email:
            employee_id = self.instance.pk if self.instance else None
            if Employee.objects.filter(email=email).exclude(pk=employee_id).exists():
                raise forms.ValidationError('Un employé avec cet email existe déjà.')
        return email

    def clean_salary(self):
        """Validation salaire positif"""
        salary = self.cleaned_data.get('salary')
        if salary is not None and salary <= 0:
            raise forms.ValidationError('Le salaire doit être positif.')
        return salary
    

class CustomLoginForm(forms.Form):
    """Formulaire de connexion personnalisé"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Nom d\'utilisateur',
            'autofocus': True,
            'autocomplete': 'username',
            'style': 'color: #1a202c !important; background-color: #ffffff !important;'
        }),
        label='Nom d\'utilisateur'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Mot de passe',
            'autocomplete': 'current-password',
            'style': 'color: #1a202c !important; background-color: #ffffff !important;'
        }),
        label='Mot de passe'
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Se souvenir de moi'
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip().lower()
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if not username:
            raise ValidationError('Le nom d\'utilisateur est requis.')
        
        if not password:
            raise ValidationError('Le mot de passe est requis.')
        
        return cleaned_data


class FirstLoginPasswordForm(PasswordChangeForm):
    """Formulaire pour le changement de mot de passe à la première connexion"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnalisation des champs
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe actuel'
        })
        
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        })
        
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le nouveau mot de passe'
        })
        
        # Labels français
        self.fields['old_password'].label = 'Mot de passe actuel'
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmer le mot de passe'
        
        # Messages d'aide
        self.fields['new_password1'].help_text = """
        <small class="form-text text-muted">
            <ul class="mb-0 ps-3">
                <li>Au moins 8 caractères</li>
                <li>Au moins une lettre majuscule</li>
                <li>Au moins une lettre minuscule</li>
                <li>Au moins un chiffre</li>
            </ul>
        </small>
        """
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        
        if password:
            # Validation personnalisée du mot de passe
            if len(password) < 8:
                raise ValidationError('Le mot de passe doit contenir au moins 8 caractères.')
            
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une lettre majuscule.')
            
            if not re.search(r'[a-z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une lettre minuscule.')
            
            if not re.search(r'\d', password):
                raise ValidationError('Le mot de passe doit contenir au moins un chiffre.')
        
        return password

class UserCreationFormWithRole(UserCreationForm):
    """Formulaire de création d'utilisateur avec rôle (pour les admins)"""
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        }),
        label='Prénom'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom'
        }),
        label='Nom'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.com'
        }),
        label='Email'
    )
    
    role = forms.ChoiceField(
        choices=UserRole.choices,
        initial=UserRole.EMPLOYE,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Rôle'
    )
    
    employee = forms.ModelChoiceField(
        queryset=None,  # Sera défini dans __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Employé associé',
        help_text='Optionnel - pour lier ce compte à un employé existant'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+212 6XX XXXXXX'
        }),
        label='Téléphone'
    )
    
    def __init__(self, *args, **kwargs):
        self.created_by = kwargs.pop('created_by', None)
        super().__init__(*args, **kwargs)
        
        # Personnaliser les champs de base
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur'
        })
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
        
        # Charger les employés sans compte utilisateur
        from .models import Employee, UserProfile
        self.fields['employee'].queryset = Employee.objects.filter(
            user_profile__isnull=True
        ).order_by('nom', 'prenom')
        
        # Si l'utilisateur qui crée n'est pas admin, limiter les rôles
        if self.created_by and hasattr(self.created_by, 'profile'):
            if not self.created_by.profile.is_admin:
                # Les RH ne peuvent pas créer d'admin
                role_choices = [
                    (UserRole.RH, 'Ressources Humaines'),
                    (UserRole.EMPLOYE, 'Employé')
                ]
                self.fields['role'].choices = role_choices
                self.initial['role'] = UserRole.EMPLOYE
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Un utilisateur avec cet email existe déjà.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        employee = cleaned_data.get('employee')
        
        # Un employé doit avoir un Employee lié
        if role == 'EMPLOYE' and not employee:
            raise ValidationError({
                'employee': 'Un employé doit être lié à une fiche employé existante.'
            })
        
        # Vérifier que l'employé n'est pas déjà lié
        if employee:
            from .models import UserProfile
            if UserProfile.objects.filter(employee=employee).exists():
                raise ValidationError({
                    'employee': 'Cet employé est déjà lié à un compte utilisateur.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            
            # Créer le profil utilisateur
            from .models import UserProfile
            profile = UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                employee=self.cleaned_data.get('employee'),
                phone=self.cleaned_data.get('phone'),
                created_by=self.created_by,
                is_first_login=True,
                is_active=True
            )
        
        return user


class UserProfileForm(forms.ModelForm):
    """Formulaire pour modifier un profil utilisateur"""
    
    class Meta:
        from .models import UserProfile
        model = UserProfile
        fields = ['phone', 'avatar', 'preferences']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+212 6XX XXXXXX'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'preferences': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Préférences au format JSON'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Labels en français
        self.fields['phone'].label = 'Téléphone'
        self.fields['avatar'].label = 'Photo de profil'
        self.fields['preferences'].label = 'Préférences'
        
        # Aide pour les préférences
        self.fields['preferences'].help_text = """
        <small class="form-text text-muted">
            Format JSON, exemple: {"theme": "dark", "notifications": true}
        </small>
        """


class PasswordChangeFormCustom(PasswordChangeForm):
    """Formulaire personnalisé pour changer le mot de passe"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Styling Bootstrap
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Labels français
        self.fields['old_password'].label = 'Mot de passe actuel'
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmer le nouveau mot de passe'