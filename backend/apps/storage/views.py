import csv
import json
import logging
import os
from datetime import datetime, timezone

from django.conf import settings
from django.http import FileResponse
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connections.models import ConnectionConfig
from apps.connections.connectors.factory import ConnectorFactory
from .models import SubmitJob, ProcessedDataRecord, ExportedFile
from .tasks import process_submit_job
from .serializers import (
    SubmitDataSerializer,
    SubmitJobSerializer,
    ShareFileResponseSerializer,
    ProcessedDataRecordSerializer,
    ExportedFileSerializer,
)

logger = logging.getLogger("apps.storage")


class SubmitDataView(APIView):
    """Accept edited data, dispatch background processing job."""

    @extend_schema(
        tags=["Storage"],
        request=SubmitDataSerializer,
        responses={202: SubmitJobSerializer},
        summary="Submit edited data",
        description="Validates and stores data, then dispatches a background job to write back "
                    "to the source database and export a file. Returns the job ID for polling.",
    )
    def post(self, request):
        serializer = SubmitDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        connection_id = serializer.validated_data["connection_id"]
        table_name = serializer.validated_data["table_name"]
        data = serializer.validated_data["data"]
        original_data = serializer.validated_data.get("original_data", [])
        export_format = serializer.validated_data["export_format"]

        try:
            config = ConnectionConfig.objects.get(id=connection_id)
            if config.owner != request.user and not request.user.is_admin:
                raise PermissionDenied("Permission denied")
        except ConnectionConfig.DoesNotExist:
            raise NotFound("Connection not found")

        # Store data immediately (synchronous — lightweight)
        record = ProcessedDataRecord.objects.create(
            user=request.user,
            source_connection=config,
            source_db_type=config.db_type,
            source_table=table_name,
            data=data,
            row_count=len(data),
        )
        # Stash original_data for the task (stored transiently on the record)
        record._original_data = original_data

        # Create job and dispatch to Celery
        job = SubmitJob.objects.create(
            user=request.user,
            connection=config,
            table_name=table_name,
            export_format=export_format,
            row_count=len(data),
            record=record,
        )
        process_submit_job.delay(job.id)

        logger.info(
            "action=submit_data user_id=%s job_id=%s connection_id=%s table=%s rows=%d",
            request.user.id, job.id, config.id, table_name, len(data),
        )

        return Response(
            SubmitJobSerializer(job).data,
            status=status.HTTP_202_ACCEPTED,
        )


class SubmitJobStatusView(APIView):
    """Poll for submit job completion."""

    @extend_schema(
        tags=["Storage"],
        responses={200: SubmitJobSerializer},
        summary="Get submit job status",
        description="Poll for the status of a background submit job.",
    )
    def get(self, request, job_id):
        try:
            job = SubmitJob.objects.select_related("exported_file").get(id=job_id)
        except SubmitJob.DoesNotExist:
            raise NotFound("Job not found")

        # RBAC: owner or admin
        if job.user != request.user and not request.user.is_admin:
            raise PermissionDenied("Permission denied")

        return Response(SubmitJobSerializer(job).data)


class ProcessedRecordsView(generics.ListAPIView):
    """List processed data records with RBAC."""
    serializer_class = ProcessedDataRecordSerializer

    @extend_schema(
        tags=["Storage"],
        summary="List processed records",
        description="Returns all processed data records. Admins see all; users see only their own.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_admin:
            return ProcessedDataRecord.objects.select_related("user", "source_connection").all()
        return ProcessedDataRecord.objects.select_related("user", "source_connection").filter(user=self.request.user)


class ExportedFilesView(generics.ListAPIView):
    """List exported files with RBAC."""
    serializer_class = ExportedFileSerializer

    @extend_schema(
        tags=["Storage"],
        summary="List exported files",
        description="Returns all exported files. Admins see all; users see own files and shared files.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_admin:
            return ExportedFile.objects.select_related("user").all()
        return (
            ExportedFile.objects.select_related("user").filter(user=self.request.user)
            | ExportedFile.objects.select_related("user").filter(is_shared=True)
        ).distinct()


class DownloadFileView(APIView):
    """Download an exported file with RBAC check."""

    @extend_schema(
        tags=["Storage"],
        responses={(200, "application/octet-stream"): bytes},
        summary="Download exported file",
        description="Download a JSON or CSV export. Admins can download any file; users can download their own or shared files.",
    )
    def get(self, request, file_id):
        try:
            exported_file = ExportedFile.objects.get(id=file_id)
        except ExportedFile.DoesNotExist:
            raise NotFound("File not found")

        # RBAC: admin sees all, user sees own or shared
        if not request.user.is_admin:
            if exported_file.user != request.user and not exported_file.is_shared:
                raise PermissionDenied("Permission denied")

        if not os.path.exists(exported_file.file_path):
            raise NotFound("File no longer exists on disk")

        # Prevent path traversal: ensure file is within the exports directory
        real_path = os.path.realpath(exported_file.file_path)
        exports_dir = os.path.realpath(str(settings.EXPORTS_DIR))
        if not real_path.startswith(exports_dir):
            raise PermissionDenied("Invalid file path")

        logger.info("action=download_file user_id=%s file_id=%s format=%s", request.user.id, file_id, exported_file.file_format)

        content_type = (
            "application/json"
            if exported_file.file_format == "json"
            else "text/csv"
        )
        fh = open(exported_file.file_path, "rb")
        response = FileResponse(
            fh,
            content_type=content_type,
            as_attachment=True,
            filename=exported_file.file_name,
        )
        response["X-Content-Length"] = os.path.getsize(exported_file.file_path)
        return response


class ShareFileView(APIView):
    """Toggle sharing of an exported file."""

    @extend_schema(
        tags=["Storage"],
        request=None,
        responses={200: ShareFileResponseSerializer},
        summary="Toggle file sharing",
        description="Toggle the shared status of an exported file. Only the file owner or an admin can change sharing.",
    )
    def post(self, request, file_id):
        try:
            exported_file = ExportedFile.objects.get(id=file_id)
        except ExportedFile.DoesNotExist:
            raise NotFound("File not found")

        if exported_file.user != request.user and not request.user.is_admin:
            raise PermissionDenied("Permission denied")

        exported_file.is_shared = not exported_file.is_shared
        exported_file.save()
        logger.info(
            "action=share_file user_id=%s file_id=%s is_shared=%s",
            request.user.id, file_id, exported_file.is_shared,
        )
        return Response({"is_shared": exported_file.is_shared})
