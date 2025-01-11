from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import User
from rest_framework.exceptions import AuthenticationFailed

class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return None

        try:
            validated_token = AccessToken(access_token)
            user = User.objects.get(id=validated_token['user_id'])
            return user, validated_token
        except User.DoesNotExist:
            raise AuthenticationFailed('No user found for this token')
        except Exception:
            raise AuthenticationFailed('Invalid or expired token')

    def authenticate_header(self, request):
        return 'Bearer'
