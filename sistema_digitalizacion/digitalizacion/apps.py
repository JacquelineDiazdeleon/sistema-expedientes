from django.apps import AppConfig


class DigitalizacionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "digitalizacion"
    
    def ready(self):
        # Importar señales para que se registren
        import digitalizacion.signals  # noqa
