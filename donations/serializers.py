from rest_framework import serializers
from .models import Donation, CustomUser
from geopy.distance import geodesic


class DonationSerializer(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()  # Read-only field
    is_reserved_by_me = serializers.SerializerMethodField()
    is_reserved = serializers.SerializerMethodField()
    collection_status = serializers.SerializerMethodField() 
    
    class Meta:
        model = Donation
        fields = ['id', 'food_type', 'quantity', 'location', 'image', 'expires_at', 'distance', 'status', 'is_reserved_by_me', 'is_reserved', 'collection_status']
        
        read_only_fields = ['created_at', 'is_claimed', 'is_reserved_by_me', 'is_reserved', 'collection_status']

    def get_distance(self, obj):
        user_location = self.context.get('user_location')
        if user_location:
            donation_location = tuple(map(float, obj.location.split(',')))
            return geodesic(user_location, donation_location).kilometers
        return None
    
    def get_is_reserved_by_me(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.reserved_by == request.user
        return False
    def get_is_reserved(self, obj):
        request = self.context.get('request')
        print('we are here ======?')
        if request and hasattr(request, 'user'):
            return obj.reserved_by is not None
        return False
    
    def get_collection_status(self, obj):
        if obj.is_claimed:
            return "RECIPIENT_RESERVATION"
        if obj.self_pickup:
            return "RECIPIENT_SELF_PICKUP"
        if obj.volunteer:
            return "TO_BE_COLLECTED_BY_VOLUNTEER"
        if hasattr(obj, 'volunteer_request') and not obj.volunteer_request.is_accepted():
            return "VONTEER_REQUEST_PENDING"
        return "PENDING_COLLECTION"
        


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