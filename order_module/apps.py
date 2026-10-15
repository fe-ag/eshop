from django.apps import AppConfig


class OrderModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order_module'

    def ready(self):
        from . import signals  # noqa: F401  (registers the guest-cart merge on login)
