from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Donation, CustomUser
from .serializers import DonationSerializer, RegisterUserSerializer, UserSerializer
from .utils import find_closest_recipient
from rest_framework.permissions import IsAuthenticated
from geopy.distance import geodesic



class CreateDonationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = DonationSerializer(data=request.data)
        if serializer.is_valid():
            donation = serializer.save(donor=request.user)
            recipients = CustomUser.objects.filter(user_type='recipient')
            donation_location = tuple(map(float, donation.location.split(',')))
            closest_recipient = find_closest_recipient(donation_location, recipients)

            # Notify the recipient (using Firebase later)
            return Response({
                'message': 'Donation created successfully',
                'closest_recipient': closest_recipient.username if closest_recipient else None
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ActiveDonationsView(APIView):
    def get(self, request):
        donations = Donation.objects.filter(is_claimed=False)
        serializer = DonationSerializer(donations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    

class ActiveDonationsView(APIView):
    def get(self, request):
        user_location_param = request.query_params.get('location')  # e.g., "40.7128,-74.0060"
        
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
        
        donations = Donation.objects.filter(is_claimed=False)

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