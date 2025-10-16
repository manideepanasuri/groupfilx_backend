
import uuid
from django.http import HttpResponseRedirect
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .helpers import *
from .models import *
from groupflix import settings

User=CustomUser

class UserAuthSignupView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        name=request.data.get('name')
        email=request.data.get('email')
        password=request.data.get('password')
        if not name or not email or not password:
            data={
                "success": False,
                "message":"Enter Valid Data"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            data={
                "success": False,
                "message":"User already exists"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        try:
            user=User.objects.create_user(email=email, password=password,name=name)
            tokens=get_tokens_for_user(user)
            data= {
                "success": True,
                "data":{
                    "tokens": tokens,
                    "name": user.name,
                    "email":user.email,
                    "is_verified": user.is_verified,
                },
                "message":"User created successfully"
            }
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            data={
                "success": False,
                "message": "internal server error"
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserAuthLoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        email=request.data.get('email')
        password=request.data.get('password')
        if not email or not password:
            data={
                "success": False,
                "message":"Enter Valid Data"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        if not User.objects.filter(email=email).exists():
            data={
                "success": False,
                "message":"User does not exist"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        try:
            user=User.objects.get(email=email)
            if user.check_password(password):
                tokens=get_tokens_for_user(user)
                data={
                    "success": True,
                    "data":{
                        "tokens": tokens,
                        "name":user.name,
                        "email":user.email,
                        "is_verified":user.is_verified,
                    },
                    "message":"User login successfully"
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                data={
                    "success": False,
                    "message":"Incorrect Password"
                }
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            data={
                "success": False,
                "message": "internal server error"
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RefreshTokenView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        try:
            refresh=request.data.get('refresh')
            tokens=get_tokens_from_refresh_token(refresh)

            user=get_user_from_token(tokens["access"])
            data={
                "success": True,
                "tokens": tokens,
                "is_verified": user.is_verified,
                "message": "Refresh token successfully received"
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            data={
                "success": False,
                "message": "Refresh token Expired"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

class GetUrlForOauthView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request):
        try:
            url=f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.OAUTH_CLIENT_ID}&&redirect_uri={settings.GOOGLE_REDIRECT_URL}&response_type=code&scope=openid%20email%20profile&state={uuid.uuid4()}&access_type=online&prompt=consent"
            url=url.strip()
            data={
                "success": True,
                "url": url,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            data={
                "success": False,
                "message": "internal server error"
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GoogleCallbackView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request):
        try:
            code=request.GET.get('code')
            state=request.GET.get('state')
            if not code or not state:
                redirect_uri=settings.FRONTEND_HOST+"/google-auth/failure"
                return HttpResponseRedirect(redirect_uri)
            token_data = {
                "code": code,
                "client_id": settings.OAUTH_CLIENT_ID,
                "client_secret": settings.OAUTH_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URL,
                "grant_type": "authorization_code"
            }
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data=token_data
            )
            token_response.raise_for_status()
            user_data = token_response.json()
            id_token = user_data['id_token']
            user_data1=jwt.decode(id_token,options={"verify_signature": False})
            name=user_data1['name']
            email=user_data1['email']
            if User.objects.filter(email=email).exists():
                user=User.objects.get(email=email)
                user.is_verified=True
                user.save()
                jwt_token=create_jwt({"email":email},expires_in=180)
                redirect_uri=settings.GOOGLE_FRONTEND_REDIRECT_URL+"success?token="+jwt_token
                return HttpResponseRedirect(redirect_uri)
            else:
                user=User.objects.create_user(email=email,password=f"{uuid.uuid4()}",name=name)
                user.is_verified=True
                user.set_unusable_password()
                user.save()
                jwt_token=create_jwt({"email":email},expires_in=180)
                redirect_uri=settings.GOOGLE_FRONTEND_REDIRECT_URL+"success?token="+jwt_token
                return HttpResponseRedirect(redirect_uri)
        except Exception as e:
            print(e)
            redirect_uri=settings.GOOGLE_FRONTEND_REDIRECT_URL+"/failure"
            return HttpResponseRedirect(redirect_uri)

class VerifyFromGoogleTokenView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        try:
            jwt_token=request.data.get('token')
            data=jwt.decode(jwt=jwt_token,key=settings.SECRET_KEY,algorithms=['HS256'])
            email=data['email']
            user=User.objects.get(email=email)
            user.is_verified=True
            user.save()
            tokens=get_tokens_for_user(user)
            data={
                "success": True,
                "data": {
                    "tokens": tokens,
                    "name": user.name,
                    "email": user.email,
                    "is_verified": user.is_verified,
                },
                "message": "Verification successful"
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            data={
                "success": False,
                "message": "Verification failed"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

class GetVerificationEmailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        try:
            user=request.user
            msg=send_verification_email(user)
            data={
                "success": True,
                "message": msg
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            data={
                "success": False,
                "message": "Failed to send verification email"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        try:
            email=request.data.get('email')
            password=request.data.get('password')
            if not User.objects.filter(email=email).exists():
                data={
                    "success": False,
                    "message": "Email not found"
                }
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            user=User.objects.get(email=email)
            jwt_token=create_jwt({"email":email,"password":password},expires_in=5*60)
            link=settings.FRONTEND_HOST+"change-password?token="+jwt_token
            msg=send_email_to_url(user,2,{"email_heading":"Set New Password","verification_link":link})
            data={
                "success": True,
                "message": msg
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            data={
                "success": False,
                "message": "Failed to send verification email"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordVerifyView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        try:
            jwt_token = request.data.get('token')
            data = jwt.decode(jwt=jwt_token, key=settings.SECRET_KEY, algorithms=['HS256'])
            email = data['email']
            password=data['password']
            user = User.objects.get(email=email)
            user.set_password(password)
            user.is_verified = True
            user.save()
            tokens = get_tokens_for_user(user)
            data = {
                "success": True,
                "data": {
                    "tokens": tokens,
                    "name": user.name,
                    "email": user.email,
                    "is_verified": user.is_verified,
                },
                "message": "Password changed successfully"
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            data = {
                "success": False,
                "message": "Failed to change password"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
