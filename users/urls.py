from django.urls import path

from users.views import *

urlpatterns = [
    path('signup/', UserAuthSignupView.as_view(), name='signup'),
    path('login/', UserAuthLoginView.as_view(), name='login'),
    path('refresh/',RefreshTokenView.as_view(), name='refresh'),
    path('google-redirect-url/',GetUrlForOauthView.as_view(), name='google-redirect-url'),
    path('google-auth/callback/',GoogleCallbackView.as_view(), name='google-auth-callback'),
    path('verify-google-token/',VerifyFromGoogleTokenView.as_view(), name='verify-google-token'),
    path('get-verification-email/',GetVerificationEmailView.as_view(), name='get-verification-email'),
    path('change-password/',ChangePasswordView.as_view(), name='change-password'),
    path('verify-change-password/',ChangePasswordVerifyView.as_view(), name='verify-change-password'),
]
