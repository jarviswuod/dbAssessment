from django.db import models
from django.conf import settings

from .encryption import encrypt, decrypt


class ConnectionConfig(models.Model):
    DB_TYPE_CHOICES = [
        ("postgres", "PostgreSQL"),
        ("mysql", "MySQL"),
        ("mongodb", "MongoDB"),
        ("clickhouse", "ClickHouse"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connections",
    )
    name = models.CharField(max_length=200)
    db_type = models.CharField(max_length=20, choices=DB_TYPE_CHOICES)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    username = models.CharField(max_length=200)
    encrypted_password = models.TextField(default="")
    database = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "connection_configs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.db_type})"

    @property
    def password(self) -> str:
        """Decrypt password on read."""
        if not self.encrypted_password:
            return ""
        return decrypt(self.encrypted_password)

    @password.setter
    def password(self, value: str):
        """Encrypt password on write."""
        self.encrypted_password = encrypt(value) if value else ""
