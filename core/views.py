from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.serializers import RegistrationSerializer, ProfileSerializer, ChangePasswordSerializer, EmailConfirmSerializer


class RegistrationView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    authentication_classes = (JWTAuthentication,)

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        return self.request.user


class EmailConfirmView(generics.UpdateAPIView):
    serializer_class = EmailConfirmSerializer

    def get_object(self):
        return self.request.user
