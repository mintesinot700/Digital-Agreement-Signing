from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser, PermissionsMixin


class UserAccounts(AbstractUser, PermissionsMixin):
    phone_number = models.CharField(
        max_length=17,
        null=True,
        blank=True,
        help_text="Contact phone number, e.g. '+251912345678'."
    )
    created_at = models.DateTimeField(auto_now_add=True)



    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',
        blank=True,
    )

    def __str__(self):
        return self.username