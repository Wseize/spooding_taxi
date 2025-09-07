from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer
from rest_framework import serializers
from .models import CustomUser



class CustomRegisterSerializer(RegisterSerializer):
    pass


class CustomLoginSerializer(LoginSerializer):
    pass


class CustomPasswordResetSerializer(PasswordResetSerializer):
    pass


class CustomPasswordResetConfirmSerializer(PasswordResetConfirmSerializer):
    pass


class CustomUserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'is_driver']