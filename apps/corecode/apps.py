from django.apps import AppConfig

class CorecodeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.corecode'

    def ready(self):
        # Import and connect the signals
        from . import models