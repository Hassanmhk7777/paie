from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver

from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create UserProfile automatically when a new User is created.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
    
@receiver(post_migrate)
def create_profiles_for_existing_users(sender, **kwargs):
    """
    Create UserProfile for existing users after migrations.
    """
    # Only run for this app
    if sender.name == 'paie':
        from django.contrib.auth.models import User
        for user in User.objects.all():
            UserProfile.objects.get_or_create(user=user)
