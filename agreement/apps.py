from django.apps import AppConfig


class AgreementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agreement'

    def ready(self):
       import agreement.signals 