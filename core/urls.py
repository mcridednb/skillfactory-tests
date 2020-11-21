from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.views import RegistrationView, ProfileView, ChangePasswordView, EmailConfirmView

urlpatterns = [
    path("auth/registration/", RegistrationView.as_view(), name="registration"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("email/confirm/", EmailConfirmView.as_view(), name="email-confirm"),
]
