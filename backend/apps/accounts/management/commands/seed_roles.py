from django.core.management.base import BaseCommand
from apps.accounts.models import Role


class Command(BaseCommand):
    help = "Seed initial roles"

    def handle(self, *args, **options):
        for name in [Role.ADMIN, Role.USER]:
            Role.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS(f"Role '{name}' ready"))
