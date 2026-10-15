from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Customer / manager account. The e-mail address is the login name for customers."""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    street_address = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        full_name = self.get_full_name()
        return full_name or self.email

    @property
    def has_complete_address(self):
        return all([self.country, self.state, self.city, self.street_address, self.postal_code])

    @property
    def is_manager(self):
        return self.is_active and (self.is_staff or self.is_superuser)
