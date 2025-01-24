from django.urls import path
from .apis import CreateDonationView, ActiveDonationsView, UpdateDonationView, DeleteDonationView, PublishDonationView

urlpatterns = [
    path('donations/create/', CreateDonationView.as_view(), name='create_donation'),
    path('donations/active/', ActiveDonationsView.as_view(),
         name='active_donations'),
]

urlpatterns += [
    path('donations/<int:donation_id>/update/',
         UpdateDonationView.as_view(), name='update_donation'),
    path('donations/<int:donation_id>/delete/',
         DeleteDonationView.as_view(), name='delete_donation'),
    path('donations/<int:donation_id>/publish/',
         PublishDonationView.as_view(), name='publish_donation'),
]
