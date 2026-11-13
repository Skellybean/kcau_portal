"""Sample fee statuses, CATs, assignments and exam timetable. Run after seed_demo.

    python manage.py seed_coursework

demo.student1 and demo.student2 have cleared fees. demo.student3 does not, so you can
see the locked screen. Do not run this against a production database.
"""
from datetime import date, time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from campus.models_coursework import Assessment, ExamSlot, FeeStatus
from campus.models import Unit

STUDENT_DOMAIN = "students.kcau.ac.ke"


class Command(BaseCommand):
    help = "Load sample coursework, fee statuses and exam slots."

    @transaction.atomic
    def handle(self, *args, **options):
        units = {u.code: u for u in Unit.objects.all()}
        if "DIT 201" not in units:
            raise CommandError("Run `python manage.py seed_demo` first.")

        for local, cleared, balance in [("demo.student1", True, "0.00"), ("demo.student2", True, "0.00"), ("demo.student3", False, "18500.00")]:
            FeeStatus.objects.update_or_create(
                email=f"{local}@{STUDENT_DOMAIN}", defaults={"cleared": cleared, "balance": balance}
            )

        now = timezone.now()
        admin = User.objects.filter(email="demo.admin@kcau.ac.ke").first()
        work = [
            ("DIT 201", "cat", "CAT 1: Normalisation", "Answer all questions. Typed answers or a PDF are fine.", now + timedelta(days=5), 30, True, True),
            ("DIT 205", "assignment", "Assignment 1: Class design", "Design and explain a class hierarchy for a library system.", now + timedelta(days=10), 20, True, True),
            ("DIT 210", "assignment", "Assignment 1: Subnetting", "Attach your working as a file.", now + timedelta(days=3), 20, False, True),
            ("DIT 214", "cat", "CAT 1 (closed example)", "This one is past its deadline.", now - timedelta(days=2), 30, True, True),
        ]
        for code, kind, title, instructions, due, max_marks, text, file in work:
            Assessment.objects.update_or_create(
                unit=units[code], title=title,
                defaults={"kind": kind, "instructions": instructions, "due_at": due, "max_marks": max_marks,
                          "allow_text": text, "allow_file": file, "created_by": admin},
            )

        first_exam_day = date.today() + timedelta(days=30)
        for index, code in enumerate(["DIT 201", "DIT 205", "DIT 210", "DIT 214", "STU 701"]):
            ExamSlot.objects.update_or_create(
                unit=units[code], trimester=settings.CURRENT_TRIMESTER,
                defaults={"date": first_exam_day + timedelta(days=index), "start_time": time(9, 0), "end_time": time(12, 0),
                          "venue": "Main Hall" if index % 2 == 0 else "Lecture Hall 3"},
            )

        self.stdout.write(self.style.SUCCESS("Coursework demo data loaded. demo.student3 has outstanding fees."))
