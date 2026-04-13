import logging

from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import viewsets, status, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.permissions import IsOwnerOrAdmin
from .models import ConnectionConfig
from .serializers import ConnectionConfigSerializer
from .connectors.factory import ConnectorFactory

logger = logging.getLogger("apps.connections")


@extend_schema_view(
    list=extend_schema(tags=["Connections"], summary="List connections"),
    create=extend_schema(tags=["Connections"], summary="Create connection"),
    retrieve=extend_schema(tags=["Connections"], summary="Get connection details"),
    update=extend_schema(tags=["Connections"], summary="Update connection"),
    partial_update=extend_schema(tags=["Connections"], summary="Partial update connection"),
    destroy=extend_schema(tags=["Connections"], summary="Delete connection"),
)
class ConnectionConfigViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectionConfigSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ConnectionConfig.objects.none()
        user = self.request.user
        if user.is_admin:
            return ConnectionConfig.objects.select_related("owner").all()
        return ConnectionConfig.objects.select_related("owner").filter(owner=user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        count = len(response.data.get("results", response.data)) if isinstance(response.data, (dict, list)) else 0
        logger.info("action=list_connections user_id=%s count=%d", request.user.id, count)
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        logger.info("action=retrieve_connection user_id=%s connection_id=%s", request.user.id, kwargs.get("pk"))
        return response

    def perform_create(self, serializer):
        instance = serializer.save()
        logger.info(
            "action=create_connection user_id=%s connection_id=%s db_type=%s",
            self.request.user.id, instance.id, instance.db_type,
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        logger.info(
            "action=update_connection user_id=%s connection_id=%s db_type=%s",
            self.request.user.id, instance.id, instance.db_type,
        )

    def perform_destroy(self, instance):
        logger.info(
            "action=delete_connection user_id=%s connection_id=%s db_type=%s",
            self.request.user.id, instance.id, instance.db_type,
        )
        instance.delete()

    @extend_schema(
        tags=["Connections"],
        request=None,
        responses={200: inline_serializer("TestResult", {"success": drf_serializers.BooleanField()})},
        summary="Test connection",
        description="Attempt to connect to the external database and report success/failure.",
    )
    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        config = self.get_object()
        connector = ConnectorFactory.from_config(config)
        success = connector.test_connection()
        if success:
            logger.info(
                "action=test_connection user_id=%s connection_id=%s result=success",
                request.user.id, config.id,
            )
        else:
            logger.warning(
                "action=test_connection user_id=%s connection_id=%s result=failed",
                request.user.id, config.id,
            )
        return Response({"success": success})

    @extend_schema(
        tags=["Connections"],
        responses={200: inline_serializer("TableList", {"tables": drf_serializers.ListField(child=drf_serializers.CharField())})},
        summary="List tables",
        description="List all tables/collections in the connected database.",
    )
    @action(detail=True, methods=["get"])
    def tables(self, request, pk=None):
        config = self.get_object()
        connector = ConnectorFactory.from_config(config)
        try:
            with connector:
                tables = connector.list_tables()
            logger.info(
                "action=list_tables user_id=%s connection_id=%s table_count=%d",
                request.user.id, config.id, len(tables),
            )
            return Response({"tables": tables})
        except Exception as e:
            raise ValidationError(str(e))

    @extend_schema(
        tags=["Connections"],
        responses={200: inline_serializer("ColumnList", {"columns": drf_serializers.ListField(child=drf_serializers.CharField())})},
        summary="List columns",
        description="List column names for a specific table.",
    )
    @action(detail=True, methods=["get"], url_path="tables/(?P<table_name>[^/.]+)/columns")
    def columns(self, request, pk=None, table_name=None):
        config = self.get_object()
        connector = ConnectorFactory.from_config(config)
        try:
            with connector:
                columns = connector.get_columns(table_name)
            logger.info(
                "action=list_columns user_id=%s connection_id=%s table=%s column_count=%d",
                request.user.id, config.id, table_name, len(columns),
            )
            return Response({"columns": columns})
        except Exception as e:
            raise ValidationError(str(e))
