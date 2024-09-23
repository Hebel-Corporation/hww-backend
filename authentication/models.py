import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext as _


from django.conf import settings


class CustomUserManager(BaseUserManager):
   
    def create_user(self, username, password, **extra_fields):
        
        if not username:
            raise ValueError(_('The username must be set'))
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, username, password, **extra_fields):
        """
        Create and save a SuperUser with the given username and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')
        admin_count = self.model.objects.filter(user_type='admin').count()
        extra_fields.setdefault('company_id', f'{settings.COMPANY_INITIAL}-{settings.SUPERUSER_COMPANY_ID_INITIAL}{admin_count+1}')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(username, password, **extra_fields)
    
    
    
class CustomUser(AbstractUser):

    USER_TYPE_CHOICES = (
        ('admin', 'Administrator'),
        ('staff', 'Staff'),
        ('member', 'Member'),
    )

    USER_GENDER_TYPE = (
        ('F', 'Féminin'),
        ('M', 'Masculin'),
    )

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    company_id = models.CharField(_("Company ID"), max_length=50, unique=True, editable=False)
    phone = models.CharField(max_length=14, blank=True, null=True)
    user_type = models.TextField(max_length=10, choices=USER_TYPE_CHOICES, default='member')
    birthday = models.DateField(null=True, blank=True)
    gender = models.TextField(max_length=5, choices=USER_GENDER_TYPE, blank=True, null=True)
    office = models.ForeignKey('members.Office', verbose_name=_("Office Recorder"), related_name="offices_set", blank=True, null=True, on_delete=models.SET_NULL)

    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

