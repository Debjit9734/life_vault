from django.db import models
from django.contrib.auth.models import User
from django_otp.models import Device
from django.contrib.auth import get_user_model
import os
from django.utils import timezone
# Create your models here.

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=50)
    file_size = models.CharField(max_length=20)
    nominees = models.ManyToManyField('Nominee', blank=True, related_name='accessible_uploaded_files')


    def name(self):
        return os.path.basename(self.file.name)
    
    #def get_file_url(self):
        #return self.file.url
    
# models.py

    
User = get_user_model()

class EmailOTPDevice(Device):
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)

    def generate_otp(self):
        import random
        code = "%06d" % random.randint(0, 999999)
        self.otp_code = code
        self.save()
        return code

    def verify_token(self, token):
        return str(token) == self.otp_code
    
class SecureVaultItem(models.Model):
    ITEM_TYPES = (
        ('id', 'IDs & Passport'),
        ('password', 'Passwords'),
        ('crypto', 'Crypto Wallet'),
        ('bank', 'Bank Details'),
        ('atm', 'ATM Card'),
        ('other', 'Others'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    name = models.CharField(max_length=255)
    data = models.JSONField()  # Store flexible data structure
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_item_type_display()}: {self.name}"
    

class LoginActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    device = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.timestamp} from {self.ip_address}"
    


class Nominee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    notifications = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    accessible_files = models.ManyToManyField(UploadedFile, blank=True, related_name='accessible_nominees_files')
    accessible_vault_items = models.ManyToManyField(SecureVaultItem, blank=True, related_name='accessible_nominees_vault_items')

    def __str__(self):
        return self.name
    
# models.py (add this at the bottom)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    account_timeout_minutes = models.PositiveIntegerField(default=43200)  # Default 30 days in minutes
    last_activity = models.DateTimeField(auto_now_add=True)


    inactivity_email_count = models.PositiveIntegerField(default=0)
    last_inactivity_email = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.username}'s Profile"
    



