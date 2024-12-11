from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


# Create your models here.

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('donor', 'Donor'),
        ('recipient', 'Recipient'),
        ('volunteer', 'Volunteer'),
        ('admin', 'Admin'),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    location = models.CharField(max_length=255)  # Can store geolocation as a string (e.g., "latitude,longitude")

    
class Donor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='donor_profile')
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    # Add donor-specific fields

class Recipient(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='recipient_profile')
    # Add recipient-specific fields

class Volunteer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='volunteer_profile')
    availability = models.TextField()
    # Add volunteer-specific fields


class Donation(models.Model):
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    food_type = models.CharField(max_length=255)
    quantity = models.IntegerField()  # Number of meals/items
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='donation_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_claimed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.food_type} ({self.quantity}) by {self.donor.username}"