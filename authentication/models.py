import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext as _


# class CustomUserManager(BaseUserManager):
#     """
#     Custom user model manager for authentication using usernames and password.
#     """
#     def create_user(self, username, password, **extra_fields):
#         """
#         Create and save a User with the given email and password.
#         """
#         if not username:
#             raise ValueError(_('The username must be set'))
        
#         user = self.model(username=username, **extra_fields)
#         user.set_password(password)
#         user.save()

#         return user
    
#     def create_superuser(self, username, password, **extra_fields):
#         """
#         Create and save a SuperUser with the given username and password.
#         """
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('is_active', True)

#         if extra_fields.get('is_staff') is not True:
#             raise ValueError(_('Superuser must have is_staff=True.'))
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError(_('Superuser must have is_superuser=True.'))
        
#         return self.create_user(username, password, **extra_fields)
    
class CustomUser(AbstractUser):
    id = models.UUIDField(_("Unique ID"), primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateField(_("Date"), auto_now=False, auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username
