import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()
logger = logging.getLogger("apps.accounts")


@extend_schema(tags=["Auth"])
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register new user",
        description="Create a new user account with a specified role (admin or user).",
        responses={201: UserSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("action=register user_id=%s role=%s", user.id, user.role)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Auth"])
class ProfileView(APIView):
    @extend_schema(
        summary="Get current user profile",
        responses={200: UserSerializer},
    )
    def get(self, request):
        logger.info("action=profile_view user_id=%s", request.user.id)
        return Response(UserSerializer(request.user).data)


@extend_schema(tags=["Auth"], summary="Login (get JWT tokens)")
class LoggedTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # If we got here, login succeeded (failures raise exceptions caught by the handler)
        username = request.data.get("username", "unknown")
        try:
            user = User.objects.get(username=username)
            logger.info("action=login user_id=%s result=success", user.id)
        except User.DoesNotExist:
            logger.info("action=login username_provided=true result=success")
        return response


@extend_schema(tags=["Auth"], summary="Refresh JWT token")
class LoggedTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        logger.info("action=token_refresh result=success")
        return response
