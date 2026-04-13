from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Role

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name"]


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role_name = serializers.ChoiceField(
        choices=[Role.ADMIN, Role.USER], default=Role.USER, write_only=True, required=False,
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name", "role_name"]

    def validate_role_name(self, value):
        if value == Role.ADMIN:
            request = self.context.get("request")
            if not request or not request.user or not request.user.is_authenticated or not request.user.is_admin:
                raise serializers.ValidationError("Only existing admins can create admin accounts.")
        return value

    def create(self, validated_data):
        role_name = validated_data.pop("role_name", Role.USER)
        role = Role.objects.get(name=role_name)
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=role,
        )
        return user
