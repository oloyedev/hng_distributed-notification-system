from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
#from django.utils.translation import gettext_lazy as _

class User(AbstractBaseUser, PermissionsMixin):
    email = models.CharField(max_length=255, unique=True, blank=False, null=False)
    user_name = models.CharField(max_length=255)
    push_token = models.CharField(max_length=500, blank=True, null=True)
    preferences = models.JSONField(default=dict, blank=False, null=False)
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']
    
    def __str__(self):
        return self.email
    
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }