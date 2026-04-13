from django.db import models
from django.conf import settings


class ProcessedDataRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="processed_records",
    )
    source_connection = models.ForeignKey(
        "connections.ConnectionConfig",
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_records",
    )
    source_db_type = models.CharField(max_length=20)
    source_table = models.CharField(max_length=200)
    data = models.JSONField()
    row_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "processed_data_records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_table} ({self.row_count} rows) by {self.user}"


class ExportedFile(models.Model):
    FORMAT_CHOICES = [
        ("json", "JSON"),
        ("csv", "CSV"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exported_files",
    )
    processed_record = models.ForeignKey(
        ProcessedDataRecord,
        on_delete=models.CASCADE,
        related_name="exported_files",
    )
    file_format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=300)
    source_db_type = models.CharField(max_length=20)
    source_table = models.CharField(max_length=200)
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "exported_files"
        ordering = ["-created_at"]

    def __str__(self):
        return self.file_name
