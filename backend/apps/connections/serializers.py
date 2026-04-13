from rest_framework import serializers
from .models import ConnectionConfig


class ConnectionConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectionConfig
        fields = [
            "id", "name", "db_type", "host", "port",
            "username", "password", "database",
            "is_active", "created_at", "updated_at",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class ConnectionTestSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField()
