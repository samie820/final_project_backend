from django.contrib import admin
from .models import Donation, CustomUser


# Register your models here.
@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('food_type', 'quantity', 'donor', 'created_at', 'is_claimed')
    list_filter = ('is_claimed', 'created_at')
    search_fields = ('food_type', 'donor__username')
    readonly_fields = ('created_at',)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'user_type', 'location')
    list_filter = ('user_type',)
    search_fields = ('username',)