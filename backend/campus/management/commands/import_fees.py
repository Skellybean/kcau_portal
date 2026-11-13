"""Import fee clearance exported from the KCA finance system.

    python manage.py import_fees fees.csv

CSV columns: email, cleared, and optionally balance. ``cleared`` accepts
yes/true/1/paid/cleared (anything else counts as outstanding).
"""
import csv
from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from campus.views_coursework import apply_fee_status

YES = {"1", "true", "yes", "y", "paid", "cleared"}


class Command(BaseCommand):
    help = "Import student fee clearance from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        try:
            handle = open(options["csv_path"], newline="", encoding="utf-8-sig")
        except OSError as exc:
            raise CommandError(str(exc))
        with handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or not {"email", "cleared"}.issubset({f.strip().lower() for f in reader.fieldnames}):
                raise CommandError("CSV must have the columns: email, cleared (and optionally balance)")
            totals = Counter()
            for row in reader:
                row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
                status = apply_fee_status(row.get("email", "").lower(), row.get("cleared", "").lower() in YES, row.get("balance"))
                totals[status] += 1
        for status, count in sorted(totals.items()):
            self.stdout.write(f"{status}: {count}")
