from django.urls import path
from .apis import CreateDonationView, ActiveDonationsView

urlpatterns = [
    path('donations/create/', CreateDonationView.as_view(), name='create_donation'),
    path('donations/active/', ActiveDonationsView.as_view(), name='active_donations'),
]