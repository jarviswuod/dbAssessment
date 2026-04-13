from django.urls import path
from .views import RegisterView, ProfileView, LoggedTokenObtainPairView, LoggedTokenRefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoggedTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", LoggedTokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
