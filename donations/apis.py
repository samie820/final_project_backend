from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Donation, CustomUser, VolunteerRequest
from .serializers import DonationSerializer, RegisterUserSerializer, UserSerializer, VolunteerDonationSerializer
from .utils import find_closest_recipient
from rest_framework.permissions import IsAuthenticated
from geopy.distance import geodesic
from .utils import send_notification_to_recipient, send_notification


class CreateDonationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DonationSerializer(data=request.data)
        if serializer.is_valid():
            donation = serializer.save(donor=request.user)
            recipients = CustomUser.objects.filter(user_type='recipient')
            donation_location = tuple(map(float, donation.location.split(',')))
            closest_recipient = find_closest_recipient(
                donation_location, recipients)

            send_notification_to_recipient(donation)

            # Notify the recipient (using Firebase later)
            return Response({
                'id': donation.id,
                'message': 'Donation created successfully',
                'closest_recipient': closest_recipient.username if closest_recipient else None
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DonationDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, donation_id):
        try:
            donation = Donation.objects.get(
                id=donation_id, deleted_at__isnull=True)
            serializer = DonationSerializer(
                donation, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Donation.DoesNotExist:
            return Response({"error": "Donation not found"}, status=status.HTTP_404_NOT_FOUND)


class ActiveDonationsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user_location_param = request.query_params.get(
            'location')  # e.g., "40.7128,-74.0060"

        if not user_location_param:
            return Response(
                {"error": "Location query parameter is required in the format 'latitude,longitude'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_location = tuple(map(float, user_location_param.split(',')))
        except ValueError:
            return Response(
                {"error": "Invalid location format. Use 'latitude,longitude'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        donations = Donation.objects.filter(
            is_claimed=False, status='published')

        # Calculate distances
        donations_with_distances = []
        for donation in donations:
            donation_location = tuple(map(float, donation.location.split(',')))
            distance = geodesic(user_location, donation_location).kilometers
            donations_with_distances.append((donation, distance))

        # Sort by distance
        donations_with_distances.sort(key=lambda x: x[1])

        # Serialize and include the distance in the response
        serializer = DonationSerializer(
            [donation for donation, _ in donations_with_distances],
            many=True,
            context={'user_location': user_location}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UpdateDonationView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, donation_id):
        try:
            donation = Donation.objects.get(id=donation_id, donor=request.user)
            serializer = DonationSerializer(
                donation, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Donation updated successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Donation not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)


class PublishDonationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, donation_id):
        try:
            donation = Donation.objects.get(id=donation_id, donor=request.user)
            if donation.status == 'draft':
                donation.status = 'published'
                donation.save()
                return Response({"message": "Donation published successfully"}, status=status.HTTP_200_OK)
            return Response({"error": "Donation is already published"}, status=status.HTTP_400_BAD_REQUEST)
        except Donation.DoesNotExist:
            return Response({"error": "Donation not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)


class DeleteDonationView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, donation_id):
        try:
            donation = Donation.objects.get(id=donation_id, donor=request.user)
            donation.delete()  # Soft delete
            return Response({"message": "Donation soft deleted successfully"}, status=status.HTTP_200_OK)
        except Donation.DoesNotExist:
            return Response({"error": "Donation not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)


class RestoreDonationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, donation_id):
        try:
            donation = Donation.all_objects.get(
                id=donation_id, donor=request.user, deleted_at__isnull=False)
            donation.restore()
            return Response({"message": "Donation restored successfully"}, status=status.HTTP_200_OK)
        except Donation.DoesNotExist:
            return Response({"error": "Donation not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)


class ReserveDonationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, donation_id):
        try:
            print('we are here')
            donation = Donation.objects.get(id=donation_id, is_claimed=False)
            donation.reserved_by = request.user
            donation.save()

            # Notify the donor
            if donation.donor and donation.donor.fcm_token:
                send_notification(
                    token=donation.donor.fcm_token,
                    title="Donation Reserved",
                    body=f"{request.user.username} has reserved your donation of {donation.food_type}."
                )

            return Response({"message": "Donation reserved successfully"}, status=200)
        except Donation.DoesNotExist:
            return Response({"error": "Donation not available or already reserved"}, status=400)


class MyReservedDonationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        donations = Donation.objects.filter(
            reserved_by=request.user, deleted_at__isnull=True)
        serializer = DonationSerializer(
            donations, many=True, context={'request': request})
        return Response(serializer.data)


class SelfPickupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, donation_id):
        try:
            donation = Donation.objects.get(
                id=donation_id, reserved_by=request.user)
            if donation.volunteer or donation.self_pickup:
                return Response({"error": "This donation already has an assigned pickup"}, status=400)

            donation.self_pickup = True
            donation.save()

            return Response({"message": "You are now picking up the donation yourself"}, status=200)
        except Donation.DoesNotExist:
            return Response({"error": "Donation not found"}, status=404)


class RequestVolunteerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, donation_id):
        try:
            donation = Donation.objects.get(
                id=donation_id, reserved_by=request.user)
            if donation.volunteer or donation.self_pickup:
                return Response({"error": "Donation already has a pickup arrangement"}, status=400)

            volunteer_request, created = VolunteerRequest.objects.get_or_create(
                donation=donation,
                defaults={'requested_by': request.user}
            )

            if not created:
                return Response({"message": "Volunteer request already exists"}, status=200)

            return Response({"message": "Volunteer request created"}, status=201)
        except Donation.DoesNotExist:
            return Response({"error": "Donation not found"}, status=404)


class AcceptVolunteerRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, donation_id):
        try:
            volunteer_request = VolunteerRequest.objects.get(
                donation__id=donation_id, accepted_by__isnull=True)

            donation = volunteer_request.donation
            donation.volunteer = request.user
            donation.save()

            volunteer_request.accepted_by = request.user
            volunteer_request.accepted_at = now()
            volunteer_request.save()

            return Response({"message": "You have accepted the volunteer request"}, status=200)
        except VolunteerRequest.DoesNotExist:
            return Response({"error": "No volunteer request found or already accepted"}, status=404)


class AvailableVolunteerRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        location_param = request.query_params.get('location')
        if not location_param:
            return Response({"error": "location query param is required (format: lat,long)"}, status=400)

        try:
            user_location = tuple(map(float, location_param.split(',')))
        except ValueError:
            return Response({"error": "Invalid location format. Use lat,long."}, status=400)

        # Get all volunteer requests that have not been accepted
        requests = VolunteerRequest.objects.filter(
            accepted_by__isnull=True, donation__deleted_at__isnull=True)

        results = []
        for req in requests:
            donation = req.donation
            try:
                donation_location = tuple(
                    map(float, donation.location.split(',')))
                distance_km = geodesic(user_location, donation_location).km
                results.append((donation, round(distance_km, 2)))
            except Exception as e:
                continue  # Skip invalid locations

        # Sort by distance
        results.sort(key=lambda x: x[1])
        donations_sorted = [item[0] for item in results]

        serializer = DonationSerializer(
            donations_sorted, many=True, context={'request': request})
        data = serializer.data

        # Attach the distance in the response
        for i, (_, distance) in enumerate(results):
            data[i]['distance'] = distance

        return Response(data)


class MyVolunteerAssignmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        donations = Donation.objects.filter(
            volunteer=request.user, deleted_at__isnull=True)
        serializer = VolunteerDonationSerializer(donations, many=True)
        return Response(serializer.data)


class MarkDonationInTransitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, donation_id):
        try:
            donation = Donation.objects.get(
                id=donation_id, volunteer=request.user)

            if donation.is_in_transit:
                return Response({"message": "Donation is already in transit."}, status=200)

            donation.is_in_transit = True
            donation.save()

            return Response({"message": "Donation marked as in transit."}, status=200)
        except Donation.DoesNotExist:
            return Response({"error": "Donation not found or unauthorized"}, status=404)
