from django.urls import path
from .views import signup, CustomTokenObtainPairView, token_refresh, create_post, like_post, comment_on_post, GoogleLoginView, logout

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('logout/', logout, name='logout'),
    path('token/refresh/', token_refresh, name='token-refresh'),
     path('post/', create_post, name='create_post'),
    path('post/<int:post_id>/like/', like_post, name='like_post'),
    path('post/<int:post_id>/comment/', comment_on_post, name='comment_on_post'),
]
