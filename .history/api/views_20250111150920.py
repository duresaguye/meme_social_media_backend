from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import UserSerializer, PostSerializer, CommentSerializer, LikeSerializer
from .models import Post, Like
from rest_framework_simplejwt.views import TokenObtainPairView
from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from google.oauth2 import id_token
from google.auth.transport import requests


@api_view(['POST'])
def signup(request):
    """
    Sign up a new user.
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom Token view for JWT login, setting tokens in HttpOnly cookies.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')

        # Create a JsonResponse with success message
        response = JsonResponse({'message': 'Login successful'})

        # Set HttpOnly cookies for the tokens
        if access_token and refresh_token:
            response.set_cookie(
                'access_token', access_token, httponly=True, secure=True, samesite='Strict', max_age=900
            )  # Expires in 15 minutes
            response.set_cookie(
                'refresh_token', refresh_token, httponly=True, secure=True, samesite='Strict', max_age=604800
            )  # Expires in 7 days
        return response
@api_view(['POST'])
def logout(request):
    response = JsonResponse({'message': 'Logged out successfully'})
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


@api_view(['POST'])
def token_refresh(request):
    """
    Refresh the access token using the refresh token stored in cookies.
    """
    refresh_token = request.COOKIES.get('refresh_token')

    if not refresh_token:
        return Response({"error": "Refresh token missing"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh = RefreshToken(refresh_token)
        new_access_token = str(refresh.access_token)

        # Create a response with the new access token
        response = JsonResponse({"access_token": new_access_token})
        response.set_cookie(
            'access_token', new_access_token, httponly=True, secure=True, samesite='Strict', max_age=900
        )  # Expires in 15 minutes
        return response
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
def create_post(request):
    """
    Create a new post.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = PostSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
def like_post(request, post_id):
    """
    Like or unlike a post.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    existing_like = Like.objects.filter(user=request.user, post=post).first()
    if existing_like:
        existing_like.delete()
        return Response({"message": "Post unliked"}, status=status.HTTP_200_OK)

    Like.objects.create(user=request.user, post=post)
    return Response({"message": "Post liked"}, status=status.HTTP_201_CREATED)
@api_view(['POST'])
def comment_on_post(request, post_id):
    """
    Add a comment to a post.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user, post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        access_token = request.data.get('access_token')

        if not access_token:
            return Response({"error": "No access token provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the token with Google
            id_info = id_token.verify_oauth2_token(access_token, requests.Request(), '402861434161-tbprfhgvobro0n3ob0cn0rno2jlv94df.apps.googleusercontent.com')

            # Get or create the user
            user, created = User.objects.get_or_create(email=id_info['email'], defaults={'username': id_info['email']})
            if created:
                user.first_name = id_info.get('given_name', '')
                user.last_name = id_info.get('family_name', '')
                user.save()

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            response = Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })

            # Set tokens in HttpOnly cookies if needed
            response.set_cookie('refresh_token', str(refresh), httponly=True, secure=True, samesite='Strict', max_age=3600*24*7)
            response.set_cookie('access_token', str(refresh.access_token), httponly=True, secure=True, samesite='Strict', max_age=900)

            return response
        except ValueError as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)