import datetime

import jwt
import requests
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.utils import timezone

from groupflix import settings

from .models import *

User=CustomUser

def create_jwt(payload, expires_in=3600):
    payload_copy = payload.copy()
    payload_copy['exp'] = timezone.now() + datetime.timedelta(seconds=expires_in)
    payload_copy['iat'] = timezone.now()

    token = jwt.encode(payload_copy, settings.SECRET_KEY, algorithm='HS256')
    return token


def get_tokens_from_refresh_token(refresh_token):
    refresh = RefreshToken(refresh_token)
    access =str(refresh.access_token)
    return {
        "access": access,
        "refresh": str(refresh),
    }

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_user_from_token(token_str):
    token = AccessToken(token_str)  # Automatically verifies and decodes the token
    user_id = token['user_id']
    return User.objects.get(id=user_id)

def send_verification_email(curr_user: User):
    email_tracker=EmailTracker.objects.get_or_create(user=curr_user)[0]
    if timezone.now()-email_tracker.updated_at<datetime.timedelta(minutes=5) and email_tracker.count !=0:
        return "Email Already Sent"
    else:
        url = "https://api.brevo.com/v3/smtp/email"
        print(url)
        jwt_token = create_jwt({"email": curr_user.email}, expires_in=10 * 60)
        verification_url = settings.GOOGLE_FRONTEND_REDIRECT_URL + "success?token=" + jwt_token
        headers = {
            "accept": "application/json",
            "api-key": settings.EMAIL_API_KEY,
            "content-type": "application/json"
        }

        data = {
            "to": [
                {
                    "email": curr_user.email,
                    "name": curr_user.name,
                }
            ],
            "templateId": 1,
            "params": {
                "name": curr_user.name,
                "verification_link":verification_url
            },
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        email_tracker.count = email_tracker.count + 1
        email_tracker.save()
        return "Email Sent Successfully"

def send_email_to_url(curr_user: User,template_id:int,params):
    email_tracker=EmailTracker.objects.get_or_create(user=curr_user)[0]
    if timezone.now()-email_tracker.updated_at<datetime.timedelta(minutes=2) and email_tracker.count !=0:
        return "Please Wait 2 minutes"
    else:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": settings.EMAIL_API_KEY,
            "content-type": "application/json"
        }

        data = {
            "to": [
                {
                    "email": curr_user.email,
                    "name": curr_user.name,
                }
            ],
            "templateId": template_id,
            "params":params,
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        email_tracker.count = email_tracker.count + 1
        email_tracker.save()
        return "Email Sent Successfully"


