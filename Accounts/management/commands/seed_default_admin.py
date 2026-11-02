"""
Bootstrap a usable admin account on fresh databases.

The free-tier deployment runs on the in-container sqlite file, so every
deploy/restart starts from an empty database and no one can log in.
This command runs after `migrate` in the Docker CMD and creates one
superuser — but only when the database has none, so a user-created
admin (or a persistent Postgres) is never touched.

Credentials come from the ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL
environment variables. The built-in defaults exist so a demo deployment
works out of the box; production should always set ADMIN_PASSWORD.
"""
import os
import sys

from django.core.management.base import BaseCommand

from Accounts.models import UserAccounts

DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'Admin@12345'
DEFAULT_EMAIL = 'admin@example.com'


class Command(BaseCommand):
    help = (
        'Create the initial superuser from ADMIN_USERNAME/ADMIN_PASSWORD/'
        'ADMIN_EMAIL when the database has no superuser yet.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--username', default=os.environ.get('ADMIN_USERNAME', DEFAULT_USERNAME))
        parser.add_argument('--password', default=os.environ.get('ADMIN_PASSWORD', DEFAULT_PASSWORD))
        parser.add_argument('--email', default=os.environ.get('ADMIN_EMAIL', DEFAULT_EMAIL))

    def handle(self, *args, **options):
        username = (options['username'] or DEFAULT_USERNAME).strip()
        password = options['password'] or DEFAULT_PASSWORD
        email = (options['email'] or DEFAULT_EMAIL).strip()

        if UserAccounts.objects.filter(is_superuser=True).exists():
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
