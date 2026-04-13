import logging
from datetime import datetime, timezone

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connections.models import ConnectionConfig
from apps.connections.connectors.base import InvalidTableNameError
from apps.connections.connectors.factory import ConnectorFactory
from .models import ExtractionJob
from .serializers import (
    ExtractionRequestSerializer,
    ExtractionResponseSerializer,
    ExtractionJobSerializer,
)
from .utils import serialize_value

logger = logging.getLogger("apps.extraction")


class ExtractDataView(APIView):
    @extend_schema(
        tags=["Extraction"],
        request=ExtractionRequestSerializer,
        responses={200: ExtractionResponseSerializer},
        summary="Extract data batch",
        description="Extract a paginated batch of rows from a table in an external database. "
                    "Returns normalized data, column names, and pagination metadata.",
    )
    def post(self, request):
        serializer = ExtractionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        connection_id = serializer.validated_data["connection_id"]
        table_name = serializer.validated_data["table_name"]
        batch_size = serializer.validated_data["batch_size"]
        offset = serializer.validated_data["offset"]

        try:
            config = ConnectionConfig.objects.get(id=connection_id, owner=request.user)
        except ConnectionConfig.DoesNotExist:
            if request.user.is_admin:
                try:
                    config = ConnectionConfig.objects.get(id=connection_id)
                except ConnectionConfig.DoesNotExist:
                    raise NotFound("Connection not found")
            else:
                raise NotFound("Connection not found")

        connector = ConnectorFactory.from_config(config)
        try:
            with connector:
                total_rows = connector.get_row_count(table_name)
                raw_data = connector.fetch_batch(table_name, offset, batch_size)
                columns = connector.get_columns(table_name)
        except InvalidTableNameError as e:
            ExtractionJob.objects.create(
                user=request.user,
                connection=config,
                table_name=table_name,
                batch_size=batch_size,
                status="failed",
                error_message=str(e),
            )
            raise ValidationError(str(e))
        except Exception as e:
            ExtractionJob.objects.create(
                user=request.user,
                connection=config,
                table_name=table_name,
                batch_size=batch_size,
                status="failed",
                error_message=str(e),
            )
            raise ValidationError(f"Extraction failed: {str(e)}")

        # Normalize data for JSON serialization
        data = []
        for row in raw_data:
            data.append({k: serialize_value(v) for k, v in row.items()})

        # Log extraction job
        ExtractionJob.objects.create(
            user=request.user,
            connection=config,
            table_name=table_name,
            batch_size=batch_size,
            total_rows=total_rows,
            status="completed",
        )

        logger.info(
            "action=extract user_id=%s connection_id=%s table=%s rows=%d offset=%d batch_size=%d",
            request.user.id, config.id, table_name, len(data), offset, batch_size,
        )

        return Response({
            "data": data,
            "columns": columns,
            "total_rows": total_rows,
            "offset": offset,
            "batch_size": batch_size,
            "source": {
                "connection_id": config.id,
                "connection_name": config.name,
                "db_type": config.db_type,
                "table_name": table_name,
            },
        })


class ExtractionJobListView(generics.ListAPIView):
    serializer_class = ExtractionJobSerializer

    @extend_schema(
        tags=["Extraction"],
        summary="List extraction jobs",
        description="Returns extraction job history. Admins see all jobs; users see only their own.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_admin:
            return ExtractionJob.objects.select_related("connection").all()
        return ExtractionJob.objects.select_related("connection").filter(user=self.request.user)
