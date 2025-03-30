from django.contrib import admin
from .models import Donation, CustomUser, VolunteerRequest


# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('user_type', 'is_staff', 'is_superuser')

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('food_type', 'quantity', 'donor', 'created_at', 'expires_at', 'is_claimed')
    search_fields = ('food_type', 'donor__username')
    list_filter = ('is_claimed', 'created_at', 'expires_at')
    readonly_fields = ('created_at',)

@admin.register(VolunteerRequest)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donation', 'requested_by', 'accepted_by', 'created_at', 'accepted_at')