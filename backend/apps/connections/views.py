from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ConnectionConfig
from .serializers import ConnectionConfigSerializer
from .connectors.factory import ConnectorFactory


class ConnectionConfigViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectionConfigSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return ConnectionConfig.objects.all()
        return ConnectionConfig.objects.filter(owner=user)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        config = self.get_object()
        connector = ConnectorFactory.from_config(config)
        success = connector.test_connection()
        return Response({"success": success})

    @action(detail=True, methods=["get"])
    def tables(self, request, pk=None):
        config = self.get_object()
        connector = ConnectorFactory.from_config(config)
        try:
            with connector:
                tables = connector.list_tables()
            return Response({"tables": tables})
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["get"], url_path="tables/(?P<table_name>[^/.]+)/columns")
    def columns(self, request, pk=None, table_name=None):
        config = self.get_object()
        connector = ConnectorFactory.from_config(config)
        try:
            with connector:
                columns = connector.get_columns(table_name)
            return Response({"columns": columns})
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
