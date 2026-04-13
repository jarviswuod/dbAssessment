from rest_framework import serializers
from .models import ExtractionJob


class ExtractionRequestSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField(help_text="ID of the database connection to use")
    table_name = serializers.CharField(max_length=200, help_text="Table or collection to extract from")
    batch_size = serializers.IntegerField(default=100, min_value=1, max_value=10000, help_text="Number of rows per batch")
    offset = serializers.IntegerField(default=0, min_value=0, help_text="Row offset for pagination")


class ExtractionSourceSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField()
    connection_name = serializers.CharField()
    db_type = serializers.CharField()
    table_name = serializers.CharField()


class ExtractionResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=serializers.DictField())
    columns = serializers.ListField(child=serializers.CharField())
    total_rows = serializers.IntegerField()
    offset = serializers.IntegerField()
    batch_size = serializers.IntegerField()
    source = ExtractionSourceSerializer()


class ExtractionJobSerializer(serializers.ModelSerializer):
    connection_name = serializers.CharField(source="connection.name", read_only=True)
    db_type = serializers.CharField(source="connection.db_type", read_only=True)

    class Meta:
        model = ExtractionJob
        fields = [
            "id", "connection", "connection_name", "db_type",
            "table_name", "batch_size", "total_rows",
            "status", "error_message", "created_at",
        ]
