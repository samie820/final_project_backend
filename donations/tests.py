# Create your tests here.
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Donation, CustomUser

class DonationAPITests(APITestCase):
    def setUp(self):
        # Create a donor user (the owner of donations)
        self.donor = CustomUser.objects.create_user(
            username='donoruser',
            password='password123',
            email='donor@example.com',
            user_type='donor',
            location='12.9716,77.5946'
        )
        # Create another user to test unauthorized actions
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='password123',
            email='other@example.com',
            user_type='donor',  # or any type you want to test against
            location='13.0827,80.2707'
        )
        # Authenticate as donor by default.
        self.client.force_authenticate(user=self.donor)

    def test_create_donation(self):
        """
        Test that a donation can be created via the create donation endpoint.
        """
        url = reverse('create_donation')
        # Prepare a future expiration date
        expires_at = (timezone.now() + timedelta(days=1)).isoformat()
        payload = {
            'food_type': 'Rice',
            'quantity': 100,
            'location': '12.9716,77.5946',
            'expires_at': expires_at,
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Donation created successfully')
        self.assertEqual(response.data['closest_recipient'], None)

        # Verify that the donation is stored with the correct owner.
        donation = Donation.all_objects.get(id=response.data['id'])
        self.assertEqual(donation.donor, self.donor)

    def test_active_donations(self):
        """
        Test that the active donations endpoint returns only published donations
        and that it computes distance when given a user location.
        """
        # Create a donation with status published.
        published_donation = Donation.objects.create(
            donor=self.donor,
            food_type='Bread',
            quantity=50,
            location='12.9716,77.5946',
            expires_at=timezone.now() + timedelta(days=1),
            status='published'
        )
        # Create a draft donation (which should not be considered “active”)
        Donation.objects.create(
            donor=self.donor,
            food_type='Soup',
            quantity=30,
            location='12.9716,77.5946',
            expires_at=timezone.now() + timedelta(days=1),
            status='draft'
        )
        url = reverse('active_donations')
        # Assuming your view accepts latitude and longitude as query parameters
        response = self.client.get(url, {'location': '12.9716,77.5946'}, format='json')
        print('response', response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Expect only the published donation to be returned.
        self.assertEqual(len(response.data), 1)
        donation_data = response.data[0]
        self.assertEqual(donation_data['food_type'], 'Bread')
        # The serializer’s get_distance should compute a distance (zero if locations match)
        self.assertIn('distance', donation_data)
        self.assertAlmostEqual(donation_data['distance'], 0.0, places=1)

    def test_update_donation(self):
        """
        Test that the donation update endpoint allows the owner to modify donation details.
        """
        donation = Donation.objects.create(
            donor=self.donor,
            food_type='Pizza',
            quantity=20,
            location='12.9716,77.5946',
            expires_at=timezone.now() + timedelta(days=1),
            status='draft'
        )
        url = reverse('update_donation', args=[donation.id])
        payload = {
            'food_type': 'Veg Pizza',
            'quantity': 25,
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        donation.refresh_from_db()
        self.assertEqual(donation.food_type, 'Veg Pizza')
        self.assertEqual(donation.quantity, 25)

    def test_delete_donation(self):
        """
        Test that the donation delete endpoint performs a soft delete.
        (After deletion, the donation should have a non-null deleted_at value
        and be excluded from the default queryset.)
        """
        donation = Donation.objects.create(
            donor=self.donor,
            food_type='Burger',
            quantity=10,
            location='12.9716,77.5946',
            expires_at=timezone.now() + timedelta(days=1),
            status='draft'
        )
        url = reverse('delete_donation', args=[donation.id])
        response = self.client.delete(url, format='json')
        # Depending on your implementation, the status might be 200 or 204.
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        donation.refresh_from_db()
        self.assertIsNotNone(donation.deleted_at)
        # The default manager should now exclude this donation.
        with self.assertRaises(Donation.DoesNotExist):
            Donation.objects.get(id=donation.id)
        # But using the all_objects manager, the donation should still be accessible.
        donation_all = Donation.all_objects.get(id=donation.id)
        self.assertIsNotNone(donation_all.deleted_at)

    def test_publish_donation(self):
        """
        Test that the publish donation endpoint changes the donation's status from 'draft' to 'published'.
        """
        donation = Donation.objects.create(
            donor=self.donor,
            food_type='Sandwich',
            quantity=15,
            location='12.9716,77.5946',
            expires_at=timezone.now() + timedelta(days=1),
            status='draft'
        )
        url = reverse('publish_donation', args=[donation.id])
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'published')

    def test_update_donation_unauthorized(self):
        """
        Test that a user cannot update a donation they do not own.
        (This assumes your UpdateDonationView returns a 404 Forbidden in such cases because there is no matching query.)
        """
        donation = Donation.objects.create(
            donor=self.donor,
            food_type='Pasta',
            quantity=40,
            location='12.9716,77.5946',
            expires_at=timezone.now() + timedelta(days=1),
            status='draft'
        )
        # Switch authentication to another user.
        self.client.force_authenticate(user=self.other_user)
        url = reverse('update_donation', args=[donation.id])
        payload = {
            'food_type': 'Spaghetti',
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)