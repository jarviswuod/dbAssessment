from rest_framework import serializers
from .models import ConnectionConfig


class ConnectionConfigSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ConnectionConfig
        fields = [
            "id", "name", "db_type", "host", "port",
            "username", "password", "database",
            "is_active", "created_at", "updated_at",
        ]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        password = validated_data.pop("password", "")
        instance = super().create(validated_data)
        instance.password = password  # triggers encryption via setter
        instance.save(update_fields=["encrypted_password"])
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password is not None:
            instance.password = password  # triggers encryption via setter
            instance.save(update_fields=["encrypted_password"])
        return instance


class ConnectionTestSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField()
