from datetime import datetime, timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connections.models import ConnectionConfig
from apps.connections.connectors.factory import ConnectorFactory
from .models import ExtractionJob
from .serializers import ExtractionRequestSerializer, ExtractionJobSerializer


def _serialize_value(val):
    """Convert non-JSON-serializable values to strings."""
    if isinstance(val, (datetime,)):
        return val.isoformat()
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if hasattr(val, "__str__") and not isinstance(val, (str, int, float, bool, list, dict, type(None))):
        return str(val)
    return val


class ExtractDataView(APIView):
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
                    return Response(
                        {"error": "Connection not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {"error": "Connection not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        connector = ConnectorFactory.from_config(config)
        try:
            with connector:
                total_rows = connector.get_row_count(table_name)
                raw_data = connector.fetch_batch(table_name, offset, batch_size)
                columns = connector.get_columns(table_name)
        except Exception as e:
            return Response(
                {"error": f"Extraction failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize data for JSON serialization
        data = []
        for row in raw_data:
            data.append({k: _serialize_value(v) for k, v in row.items()})

        # Log extraction job
        ExtractionJob.objects.create(
            user=request.user,
            connection=config,
            table_name=table_name,
            batch_size=batch_size,
            total_rows=total_rows,
            status="completed",
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


class ExtractionJobListView(APIView):
    def get(self, request):
        if request.user.is_admin:
            jobs = ExtractionJob.objects.all()
        else:
            jobs = ExtractionJob.objects.filter(user=request.user)
        serializer = ExtractionJobSerializer(jobs, many=True)
        return Response(serializer.data)
