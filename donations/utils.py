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
        token=donation.user.token,  # Assume this token is stored in the User model
    )
    print('sending the message')
    messaging.send(message)

def send_notification(token, title, body):
    """Send a notification to a specific user."""
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
        )
        response = messaging.send(message)
        print(f"Notification sent: {response}")
    except Exception as e:
        print(f"Error sending notification: {e}")

