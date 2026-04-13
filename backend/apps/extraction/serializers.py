from rest_framework import serializers
from .models import ExtractionJob


class ExtractionRequestSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField()
    table_name = serializers.CharField(max_length=200)
    batch_size = serializers.IntegerField(default=100, min_value=1, max_value=10000)
    offset = serializers.IntegerField(default=0, min_value=0)


class ExtractionJobSerializer(serializers.ModelSerializer):
    connection_name = serializers.CharField(source="connection.name", read_only=True)
    db_type = serializers.CharField(source="connection.db_type", read_only=True)

    class Meta:
        model = ExtractionJob
        fields = [
            "id", "connection", "connection_name", "db_type",
            "table_name", "batch_size", "total_rows",
            "status", "created_at",
        ]
