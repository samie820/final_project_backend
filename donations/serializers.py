from rest_framework import serializers
from .models import Donation, CustomUser
from geopy.distance import geodesic


class DonationSerializer(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()  # Read-only field
    
    class Meta:
        model = Donation
        fields = ['id', 'food_type', 'quantity', 'location', 'image', 'expires_at', 'distance', 'status']
        
        read_only_fields = ['created_at', 'is_claimed']

    def get_distance(self, obj):
        user_location = self.context.get('user_location')
        if user_location:
            donation_location = tuple(map(float, obj.location.split(',')))
            return geodesic(user_location, donation_location).kilometers
        return None
        


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'user_type', 'location']
        read_only_fields = ['id']

class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'email', 'user_type', 'location']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            user_type=validated_data['user_type'],
            location=validated_data['location'],
        )
        return user