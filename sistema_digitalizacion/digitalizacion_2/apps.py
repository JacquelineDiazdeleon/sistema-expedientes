from django.apps import AppConfig


class Digitalizacion2Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "digitalizacion_2"
    verbose_name = "Digitalización 2"
    
    def ready(self):
        # Importar señales para que se registren
        import digitalizacion_2.signals  # noqa
