from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from dj_rest_auth.registration.views import RegisterView, VerifyEmailView
from dj_rest_auth.views import LoginView,LogoutView,PasswordChangeView,PasswordResetView,PasswordResetConfirmView
from accounts.serializers import CustomUserSerializer
from .models import CustomUser



# Create your views here.

class CustomRegisterView(RegisterView):
    pass


class CustomVerifyEmailView(VerifyEmailView):
    pass


class CustomLoginView(LoginView):
    pass
   


class CustomLogoutView(LogoutView):
    pass


class CustomPasswordChangeView(PasswordChangeView):
    pass


class CustomPasswordResetView(PasswordResetView):
    pass

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    pass


class UserProfileView(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]