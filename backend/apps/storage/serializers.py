from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import SubmitJob, ProcessedDataRecord, ExportedFile


class SubmitDataSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField(help_text="ID of the source database connection")
    table_name = serializers.CharField(max_length=200, help_text="Source table name")
    data = serializers.ListField(child=serializers.DictField(), help_text="Edited row data")
    original_data = serializers.ListField(child=serializers.DictField(), required=False, default=list, help_text="Original rows (for diff-based updates)")
    export_format = serializers.ChoiceField(choices=["json", "csv"], default="json", help_text="File export format")


class SubmitJobSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()
    record_id = serializers.IntegerField(source="record.id", read_only=True, allow_null=True)
    file_id = serializers.IntegerField(source="exported_file.id", read_only=True, allow_null=True)

    class Meta:
        model = SubmitJob
        fields = [
            "id", "status", "table_name", "export_format",
            "row_count", "rows_updated_in_source", "source_update_error",
            "error_message", "record_id", "file_id", "file_name",
            "created_at", "completed_at",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_file_name(self, obj):
        return obj.exported_file.file_name if obj.exported_file else None


class ShareFileResponseSerializer(serializers.Serializer):
    is_shared = serializers.BooleanField()


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

    @extend_schema_field(serializers.CharField(allow_null=True))
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
