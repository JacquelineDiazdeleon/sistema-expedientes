from django.apps import AppConfig


class DigitalizacionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "digitalizacion"
    
    def ready(self):
        # Import signals to register them
        import digitalizacion.signals
