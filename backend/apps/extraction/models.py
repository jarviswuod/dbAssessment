from django.db import models
from django.conf import settings


class ExtractionJob(models.Model):
    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="extraction_jobs"
    )
    connection = models.ForeignKey(
        "connections.ConnectionConfig", on_delete=models.CASCADE, related_name="extraction_jobs"
    )
    table_name = models.CharField(max_length=200)
    batch_size = models.PositiveIntegerField(default=100)
    total_rows = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "extraction_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Extract {self.table_name} from {self.connection.name}"
