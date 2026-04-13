from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    ADMIN = "admin"
    USER = "user"
    ROLE_CHOICES = [
        (ADMIN, "Admin"),
        (USER, "User"),
    ]

    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="users"
    )

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role and self.role.name == Role.ADMIN
