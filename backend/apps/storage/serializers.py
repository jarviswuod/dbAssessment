from rest_framework import serializers
from .models import ProcessedDataRecord, ExportedFile


class SubmitDataSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField()
    table_name = serializers.CharField(max_length=200)
    data = serializers.ListField(child=serializers.DictField())
    export_format = serializers.ChoiceField(choices=["json", "csv"], default="json")


class ProcessedDataRecordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    connection_name = serializers.SerializerMethodField()

    class Meta:
        model = ProcessedDataRecord
        fields = [
            "id", "username", "connection_name",
            "source_db_type", "source_table", "data",
            "row_count", "created_at",
        ]

    def get_connection_name(self, obj):
        return obj.source_connection.name if obj.source_connection else None


class ExportedFileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ExportedFile
        fields = [
            "id", "username", "file_format", "file_name",
            "source_db_type", "source_table",
            "is_shared", "created_at",
        ]
