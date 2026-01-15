from django.apps import AppConfig

class CorecodeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.corecode'

    def ready(self):
        # Import models and signals so receivers are registered
        from . import models  # noqa: F401
        from . import signals  # noqa: F401