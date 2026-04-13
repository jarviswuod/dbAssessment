from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Role
from apps.connections.models import ConnectionConfig

User = get_user_model()

# Pre-configured connections matching docker-compose test databases
DEMO_CONNECTIONS = [
    {
        "name": "Demo PostgreSQL",
        "db_type": "postgres",
        "host": "postgres_test",
        "port": 5432,
        "username": "testuser",
        "password": "testpass",
        "database": "testdb",
    },
    {
        "name": "Demo MySQL",
        "db_type": "mysql",
        "host": "mysql_test",
        "port": 3306,
        "username": "testuser",
        "password": "testpass",
        "database": "testdb",
    },
    {
        "name": "Demo MongoDB",
        "db_type": "mongodb",
        "host": "mongo_test",
        "port": 27017,
        "username": "testuser",
        "password": "testpass",
        "database": "testdb",
    },
    {
        "name": "Demo ClickHouse",
        "db_type": "clickhouse",
        "host": "clickhouse_test",
        "port": 8123,
        "username": "testuser",
        "password": "testpass",
        "database": "testdb",
    },
]


class Command(BaseCommand):
    help = "Seed demo user and pre-configured database connections for evaluation"

    def handle(self, *args, **options):
        admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        user_role, _ = Role.objects.get_or_create(name=Role.USER)

        # Create demo admin
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@demo.com",
                "first_name": "Admin",
                "last_name": "User",
                "role": admin_role,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created demo admin: admin / admin123"))
        else:
            self.stdout.write("Demo admin already exists")

        # Create demo regular user
        demo_user, created = User.objects.get_or_create(
            username="demo",
            defaults={
                "email": "demo@demo.com",
                "first_name": "Demo",
                "last_name": "User",
                "role": user_role,
            },
        )
        if created:
            demo_user.set_password("demo1234")
            demo_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo user:  demo / demo1234"))
        else:
            self.stdout.write("Demo user already exists")

        # Create connections for admin (visible to all via admin role)
        for conn_data in DEMO_CONNECTIONS:
            obj, created = ConnectionConfig.objects.get_or_create(
                owner=admin,
                name=conn_data["name"],
                defaults=conn_data,
            )
            status = "created" if created else "exists"
            self.stdout.write(
                self.style.SUCCESS(f"  Connection '{conn_data['name']}' — {status}")
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("  DEMO READY"))
        self.stdout.write(self.style.SUCCESS("  Admin login:  admin / admin123"))
        self.stdout.write(self.style.SUCCESS("  User login:   demo / demo1234"))
        self.stdout.write(self.style.SUCCESS("  Frontend:     http://localhost:3000"))
        self.stdout.write(self.style.SUCCESS("  API:          http://localhost:8000/api/v1/"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
