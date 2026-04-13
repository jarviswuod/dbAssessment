import csv
import io
import json
import os
from datetime import datetime, timezone

from django.conf import settings
from django.http import FileResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connections.models import ConnectionConfig
from .models import ProcessedDataRecord, ExportedFile
from .serializers import (
    SubmitDataSerializer,
    ProcessedDataRecordSerializer,
    ExportedFileSerializer,
)


class SubmitDataView(APIView):
    """Accept edited data, store in DB, and export as file."""

    def post(self, request):
        serializer = SubmitDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        connection_id = serializer.validated_data["connection_id"]
        table_name = serializer.validated_data["table_name"]
        data = serializer.validated_data["data"]
        export_format = serializer.validated_data["export_format"]

        try:
            config = ConnectionConfig.objects.get(id=connection_id)
        except ConnectionConfig.DoesNotExist:
            return Response(
                {"error": "Connection not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 1. Store in DB
        record = ProcessedDataRecord.objects.create(
            user=request.user,
            source_connection=config,
            source_db_type=config.db_type,
            source_table=table_name,
            data=data,
            row_count=len(data),
        )

        # 2. Export as file
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_name = f"{table_name}_{config.db_type}_{timestamp}.{export_format}"

        exports_dir = settings.EXPORTS_DIR
        os.makedirs(exports_dir, exist_ok=True)
        file_path = os.path.join(exports_dir, file_name)

        metadata = {
            "source_db_type": config.db_type,
            "source_table": table_name,
            "connection_name": config.name,
            "exported_by": request.user.username,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "row_count": len(data),
        }

        if export_format == "json":
            output = {"metadata": metadata, "data": data}
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, default=str)
        else:  # csv
            if data:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

        exported_file = ExportedFile.objects.create(
            user=request.user,
            processed_record=record,
            file_format=export_format,
            file_path=file_path,
            file_name=file_name,
            source_db_type=config.db_type,
            source_table=table_name,
        )

        return Response(
            {
                "record_id": record.id,
                "file_id": exported_file.id,
                "file_name": file_name,
                "row_count": len(data),
                "message": "Data stored and exported successfully",
            },
            status=status.HTTP_201_CREATED,
        )


class ProcessedRecordsView(APIView):
    """List processed data records with RBAC."""

    def get(self, request):
        if request.user.is_admin:
            records = ProcessedDataRecord.objects.all()
        else:
            records = ProcessedDataRecord.objects.filter(user=request.user)

        serializer = ProcessedDataRecordSerializer(records, many=True)
        return Response(serializer.data)


class ExportedFilesView(APIView):
    """List exported files with RBAC."""

    def get(self, request):
        if request.user.is_admin:
            files = ExportedFile.objects.all()
        else:
            files = ExportedFile.objects.filter(
                user=request.user
            ) | ExportedFile.objects.filter(is_shared=True)

        serializer = ExportedFileSerializer(files.distinct(), many=True)
        return Response(serializer.data)


class DownloadFileView(APIView):
    """Download an exported file with RBAC check."""

    def get(self, request, file_id):
        try:
            exported_file = ExportedFile.objects.get(id=file_id)
        except ExportedFile.DoesNotExist:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # RBAC: admin sees all, user sees own or shared
        if not request.user.is_admin:
            if exported_file.user != request.user and not exported_file.is_shared:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if not os.path.exists(exported_file.file_path):
            return Response(
                {"error": "File no longer exists on disk"},
                status=status.HTTP_404_NOT_FOUND,
            )

        content_type = (
            "application/json"
            if exported_file.file_format == "json"
            else "text/csv"
        )
        return FileResponse(
            open(exported_file.file_path, "rb"),
            content_type=content_type,
            as_attachment=True,
            filename=exported_file.file_name,
        )


class ShareFileView(APIView):
    """Toggle sharing of an exported file."""

    def post(self, request, file_id):
        try:
            exported_file = ExportedFile.objects.get(id=file_id)
        except ExportedFile.DoesNotExist:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if exported_file.user != request.user and not request.user.is_admin:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        exported_file.is_shared = not exported_file.is_shared
        exported_file.save()
        return Response({"is_shared": exported_file.is_shared})
