from django.urls import path
from .apis import CreateDonationView, ActiveDonationsView, UpdateDonationView, DeleteDonationView, PublishDonationView, DonationDetailView, ReserveDonationView, MyReservedDonationsView, SelfPickupView, RequestVolunteerView, AcceptVolunteerRequestView, AvailableVolunteerRequestsView, MyVolunteerAssignmentsView, MarkDonationInTransitView

urlpatterns = [
    path('donations/create/', CreateDonationView.as_view(), name='create_donation'),
    path('donations/active/', ActiveDonationsView.as_view(),
         name='active_donations'),
    path('donations/<int:donation_id>/',
         DonationDetailView.as_view(), name='donation_detail'),

]

urlpatterns += [
    path('donations/my-reserved/', MyReservedDonationsView.as_view(),
         name='my_reserved_donations'),
    path('donations/<int:donation_id>/reserve/',
         ReserveDonationView.as_view(), name='reserve_donation'),
    path('donations/<int:donation_id>/update/',
         UpdateDonationView.as_view(), name='update_donation'),
    path('donations/<int:donation_id>/delete/',
         DeleteDonationView.as_view(), name='delete_donation'),
    path('donations/<int:donation_id>/publish/',
         PublishDonationView.as_view(), name='publish_donation'),
    path('donations/<int:donation_id>/self-pickup/',
         SelfPickupView.as_view(), name='donation_self_pickup'),
    path('donations/<int:donation_id>/request-volunteer/',
         RequestVolunteerView.as_view(), name='donation_request_volunteer'),
    path('donations/<int:donation_id>/accept-volunteer/',
         AcceptVolunteerRequestView.as_view(), name='accept_volunteer_request'),
]


urlpatterns += [
    path('volunteer/requests/', AvailableVolunteerRequestsView.as_view(),
         name='available_volunteer_requests'),
    path('volunteer/my-assignments/', MyVolunteerAssignmentsView.as_view(),
         name='my_volunteer_assignments'),
    path('volunteer/donations/<int:donation_id>/in-transit/',
         MarkDonationInTransitView.as_view(), name='mark_donation_in_transit'),
]
