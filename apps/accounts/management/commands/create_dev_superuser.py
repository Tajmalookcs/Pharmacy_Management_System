from django.core.management.base import BaseCommand
from apps.accounts.models import User

# ─────────────────────────────────────────────
# Developer superuser credentials
# To change: edit DEVELOPER_USERNAME and DEVELOPER_PASSWORD below
# ─────────────────────────────────────────────
DEVELOPER_USERNAME = "tajmalookcs"
DEVELOPER_EMAIL    = "tajmalookcs@gmail.com"
DEVELOPER_PASSWORD = "Alamgir@786"
DEVELOPER_NAME     = "Taj Malook"
# ─────────────────────────────────────────────


class Command(BaseCommand):
    help = "Create the developer superuser (run once after fresh setup)"

    def handle(self, *args, **options):
        if User.objects.filter(username=DEVELOPER_USERNAME).exists():
            self.stdout.write(f'[SKIP] Superuser "{DEVELOPER_USERNAME}" already exists.')
            return

        User.objects.create_superuser(
            username=DEVELOPER_USERNAME,
            email=DEVELOPER_EMAIL,
            password=DEVELOPER_PASSWORD,
            first_name="Taj",
            last_name="Malook",
        )
        User.objects.filter(username=DEVELOPER_USERNAME).update(role='superuser')
        self.stdout.write(f'[OK] Superuser "{DEVELOPER_USERNAME}" created.')
