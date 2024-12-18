from geopy.distance import geodesic
from .models import CustomUser
import firebase_admin
from firebase_admin import credentials, messaging

def find_closest_recipient(donation_location, recipients):
    closest_recipient = None
    shortest_distance = float('inf')
    for recipient in recipients:
        recipient_location = tuple(map(float, recipient.location.split(',')))
        distance = geodesic(donation_location, recipient_location).kilometers
        if distance < shortest_distance:
            shortest_distance = distance
            closest_recipient = recipient
    return closest_recipient


cred = credentials.Certificate("donations/serviceAccount.json")
firebase_admin.initialize_app(cred)

def send_notification_to_recipient(donation):
    message = messaging.Message(
        notification=messaging.Notification(
            title="New Donation Available!",
            body=f"{donation.food_type} is available near you.",
        ),
        # Hardcoded to simulator
        token="c-ddBdyk2ExMj6fE1gJ2Es:APA91bGIzSEK9PhbL91qohjcIeDFHPaLDuWT_FocQc4ZVEY7ifPrBgc5FIjw_5nvPuW7oGuZwih_MV8QzcCIUND-hkV3JqtvQYp4fdSFRvPFBlV3OPo1JPU",  # Assume this token is stored in the User model
    )
    print('sending the message')
    messaging.send(message)