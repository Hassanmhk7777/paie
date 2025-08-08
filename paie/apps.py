from django.apps import AppConfig


class PaieConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paie'
    
    def ready(self):
        # Import signals to auto-create UserProfile on User creation
        import paie.signals
