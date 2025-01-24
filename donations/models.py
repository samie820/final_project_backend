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
    # Can store geolocation as a string (e.g., "latitude,longitude")
    location = models.CharField(max_length=255)


class Donor(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='donor_profile')
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    # Add donor-specific fields


class Recipient(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='recipient_profile')
    # Add recipient-specific fields


class Volunteer(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='volunteer_profile')
    availability = models.TextField()
    # Add volunteer-specific fields


class DonationManager(models.Manager):
    def get_queryset(self):
        """Exclude soft-deleted records."""
        return super().get_queryset().filter(deleted_at__isnull=True)

class Donation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    donor = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE)
    food_type = models.CharField(max_length=255)
    quantity = models.IntegerField()  # Number of meals/items
    location = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to='donation_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_claimed = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft')
    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='reserved_donations', null=True, blank=True, on_delete=models.SET_NULL
    )
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='volunteer_donations', null=True, blank=True, on_delete=models.SET_NULL
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = DonationManager()
    all_objects = models.Manager()  # Includes soft-deleted records
    
    
    def delete(self, using=None, keep_parents=False):
        """Override delete to implement soft delete."""
        self.deleted_at = now()
        self.save()

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.save()

    def __str__(self):
        return f"{self.food_type} ({self.quantity}) by {self.donor.username}"
