from django.apps import AppConfig


class VaultConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Vault'

    def ready(self):
        import Vault.signals