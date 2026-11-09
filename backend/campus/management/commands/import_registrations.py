"""Import unit registrations exported from the KCA portal.

    python manage.py import_registrations registrations.csv

The CSV needs the columns: email, unit_code, trimester. An optional ``action``
column may hold ``register`` (default) or ``drop``.
"""
import csv
from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from campus.sync import apply_registration


class Command(BaseCommand):
    help = "Import portal unit registrations from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        try:
            handle = open(options["csv_path"], newline="", encoding="utf-8-sig")
        except OSError as exc:
            raise CommandError(str(exc))
        with handle:
            reader = csv.DictReader(handle)
            required = {"email", "unit_code", "trimester"}
            if not reader.fieldnames or not required.issubset({f.strip().lower() for f in reader.fieldnames}):
                raise CommandError("CSV must have the columns: email, unit_code, trimester")
            totals = Counter()
            for row in reader:
                row = {k.strip().lower(): v for k, v in row.items() if k}
                status = apply_registration(
                    row.get("email"), row.get("unit_code"), row.get("trimester"), (row.get("action") or "register").strip().lower()
                )
                totals[status] += 1
        for status, count in sorted(totals.items()):
            self.stdout.write(f"{status}: {count}")
