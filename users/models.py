from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(_("full name"), max_length=255)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class EmailTracker(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    count = models.IntegerField(default=0)
