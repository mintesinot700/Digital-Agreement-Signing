"""
Bootstrap a usable demo state on fresh databases.

The free-tier deployment runs on the in-container sqlite file, so every
deploy/restart starts from an empty database and no one can log in.
This command runs after `migrate` in the Docker CMD and:

1. Creates one superuser — but only when the database has none, so a
   user-created admin (or a persistent Postgres) is never touched.
2. Creates `Pdf_agreement` template rows for the PDFs bundled in
   agreement/files/, so a fresh install has something to submit
   against. Matching rows are never overwritten; set
   SEED_SAMPLE_TEMPLATES=0 to disable.

Credentials come from the ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL
environment variables. The built-in defaults exist so a demo deployment
works out of the box; production should always set ADMIN_PASSWORD.
"""
import os
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from Accounts.models import UserAccounts
from agreement.models import Pdf_agreement

DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'Admin@12345'
DEFAULT_EMAIL = 'admin@example.com'

# accounts/management/commands/ -> repo root is three levels up.
SAMPLE_FILES_DIR = Path(__file__).resolve().parents[3] / 'agreement' / 'files'

_FALSEY = {'0', 'false', 'no', 'off', ''}


def _sample_templates_disabled():
    return os.environ.get('SEED_SAMPLE_TEMPLATES', '1').strip().lower() in _FALSEY


def _template_name(pdf_path):
    """sample_rental_agreement.pdf -> 'Sample Rental Agreement'"""
    stem = pdf_path.stem.replace('-', '_').replace('_', ' ').strip()
    return ' '.join(word.capitalize() for word in stem.split())


class Command(BaseCommand):
    help = (
        'Create the initial superuser and the bundled sample agreement '
        'templates when the database is fresh.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--username', default=os.environ.get('ADMIN_USERNAME', DEFAULT_USERNAME))
        parser.add_argument('--password', default=os.environ.get('ADMIN_PASSWORD', DEFAULT_PASSWORD))
        parser.add_argument('--email', default=os.environ.get('ADMIN_EMAIL', DEFAULT_EMAIL))

    def handle(self, *args, **options):
        username = (options['username'] or DEFAULT_USERNAME).strip()
        password = options['password'] or DEFAULT_PASSWORD
        email = (options['email'] or DEFAULT_EMAIL).strip()

        self._seed_admin(username, password, email)
        self._seed_sample_templates()

    def _seed_admin(self, username, password, email):
        if UserAccounts.objects.filter(is_superuser=True).exists():
            # An ADMIN_PASSWORD set explicitly in the environment is treated
            # as an operator instruction: rotate the bootstrap admin's
            # password to match it (only that account, only when the env
            # var is present — default-password boots never clobber it).
            env_password = os.environ.get('ADMIN_PASSWORD', '').strip()
            bootstrap_user = UserAccounts.objects.filter(
                username__iexact=username, is_superuser=True
            ).first()
            if env_password and bootstrap_user and not bootstrap_user.check_password(env_password):
                bootstrap_user.set_password(env_password)
                bootstrap_user.save(update_fields=['password'])
                self.stdout.write(self.style.SUCCESS(
                    f'Rotated password of bootstrap admin "{bootstrap_user.username}" '
                    'to match the ADMIN_PASSWORD environment variable.'
                ))
            self.stdout.write('Superuser already exists — leaving it untouched.')
            return

        if UserAccounts.objects.filter(username__iexact=username).exists():
            # Deploy must not fail over a naming clash; the existing user
            # simply is not promoted automatically.
            self.stdout.write(
                f'Username "{username}" is already taken and the database has '
                'no superuser — set ADMIN_USERNAME to a free username.'
            )
            return

        if password == DEFAULT_PASSWORD:
            self.stdout.write(
                'WARNING: using the built-in default admin password. '
                'Set ADMIN_PASSWORD in the environment before going public.',
                self.style.WARNING,
            )

        UserAccounts.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f'Bootstrap admin "{username}" created '
            f'{"(default password — change it)" if password == DEFAULT_PASSWORD else ""}'
        ))

    def _seed_sample_templates(self):
        if _sample_templates_disabled():
            self.stdout.write('SEED_SAMPLE_TEMPLATES disabled — skipping sample templates.')
            return

        for pdf_path in sorted(SAMPLE_FILES_DIR.glob('*.pdf')):
            name = _template_name(pdf_path)
            if Pdf_agreement.objects.filter(type_of_agreement__iexact=name).exists():
                continue
            try:
                template = Pdf_agreement(type_of_agreement=name)
                template.pdf_file.save(pdf_path.name, ContentFile(pdf_path.read_bytes()), save=True)
            except Exception as exc:  # a bad bundled file must never block boot
                self.stdout.write(self.style.WARNING(
                    f'Could not seed sample template "{name}": {exc}'
                ))
                continue
            self.stdout.write(self.style.SUCCESS(
                f'Seeded sample template "{name}" ({template.pdf_file.name}).'
            ))
