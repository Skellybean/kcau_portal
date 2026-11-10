"""Load clearly fictional sample data for demos and marking.

    python manage.py seed_demo
    python manage.py seed_demo --password "Another#Pass1"

Demo accounts are created already verified so they can sign in without an
email code. Do not run this against a production database.
"""
from datetime import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role, User
from campus.models import (
    Announcement,
    Enrollment,
    Facility,
    FacilityCategory,
    Result,
    TimetableSlot,
    Unit,
)

STUDENT_DOMAIN = "students.kcau.ac.ke"
STAFF_DOMAIN = "kcau.ac.ke"

LECTURERS = [
    ("demo.lecturer1", "Demo Lecturer One"),
    ("demo.lecturer2", "Demo Lecturer Two"),
]
STUDENTS = [
    ("demo.student1", "Demo Student One", "DEMO-0001"),
    ("demo.student2", "Demo Student Two", "DEMO-0002"),
    ("demo.student3", "Demo Student Three", "DEMO-0003"),
]

UNITS = [
    ("DIT 201", "Database Systems", 3, 0),
    ("DIT 205", "Object-Oriented Programming", 3, 0),
    ("DIT 210", "Computer Networks", 3, 1),
    ("DIT 214", "Systems Analysis and Design", 3, 1),
    ("STU 701", "Programming Project", 4, 0),
]

# (unit, weekday, start, end, venue, mode, link, note). Links are fictional placeholders.
SLOTS = [
    ("DIT 201", 0, time(8, 0), time(10, 0), "Lecture Hall 3", "in_person", "", ""),
    ("DIT 205", 0, time(11, 0), time(13, 0), "Computer Lab 2", "in_person", "", ""),
    ("DIT 210", 1, time(9, 0), time(11, 0), "", "online", "https://meet.example.com/dit210-demo", "Demo passcode: 2026"),
    ("DIT 214", 2, time(14, 0), time(16, 0), "Room B12", "hybrid", "https://meet.example.com/dit214-demo", ""),
    ("DIT 201", 3, time(8, 0), time(10, 0), "Computer Lab 1", "in_person", "", ""),
    ("STU 701", 4, time(10, 0), time(12, 0), "Project Studio", "in_person", "", ""),
]

# (student index, unit code, cat out of 30, exam out of 70)
RESULTS = [
    (0, "DIT 201", 24, 52), (0, "DIT 205", 21, 47), (0, "DIT 210", 18, 40), (0, "DIT 214", 26, 58),
    (1, "DIT 201", 17, 33), (1, "DIT 205", 22, 49), (1, "DIT 210", 15, 28), (1, "DIT 214", 20, 44),
    (2, "DIT 201", 27, 61), (2, "DIT 205", 25, 55), (2, "DIT 210", 23, 50), (2, "DIT 214", 19, 41),
]

FACILITIES = [
    ("Main Library", FacilityCategory.LIBRARY, "Quiet floors, group study rooms and the e-resources desk.",
     "Library Block, ground to third floor", "Mon-Fri 7:00-21:00, Sat 8:00-17:00", ""),
    ("Computer Labs", FacilityCategory.ACADEMIC, "Open-access machines for coursework and practicals.",
     "ICT Block, first floor", "Mon-Fri 8:00-20:00", ""),
    ("Student Cafeteria", FacilityCategory.FOOD, "Hot meals, snacks and drinks.",
     "Student Centre, ground floor", "Mon-Sat 7:00-19:00", ""),
    ("Medical Clinic", FacilityCategory.HEALTH, "First aid and basic consultations for students and staff.",
     "Near the main gate", "Mon-Fri 8:00-17:00", ""),
    ("Registrar's Office", FacilityCategory.SERVICES, "Records, transcripts and registration queries.",
     "Administration Block, second floor", "Mon-Fri 8:00-17:00", ""),
    ("Sports Ground", FacilityCategory.SPORTS, "Football pitch and open courts.",
     "Behind the Student Centre", "Daily 6:00-18:30", ""),
]


class Command(BaseCommand):
    help = "Create sample users, units, timetable, results, announcements and facilities."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="Campus#Demo2026", help="Password for every demo account")

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]

        lecturers = []
        for local, name in LECTURERS:
            user, _ = User.objects.get_or_create(
                email=f"{local}@{STAFF_DOMAIN}",
                defaults={"full_name": name, "role": Role.LECTURER, "is_verified": True},
            )
            user.set_password(password)
            user.save()
            lecturers.append(user)

        admin, _ = User.objects.get_or_create(
            email=f"demo.admin@{STAFF_DOMAIN}",
            defaults={"full_name": "Demo Administrator", "role": Role.ADMIN, "is_verified": True, "is_staff": True},
        )
        admin.set_password(password)
        admin.save()

        students = []
        for local, name, adm in STUDENTS:
            user, _ = User.objects.get_or_create(
                email=f"{local}@{STUDENT_DOMAIN}",
                defaults={
                    "full_name": name,
                    "role": Role.STUDENT,
                    "is_verified": True,
                    "admission_number": adm,
                    "programme": "Diploma in Information Technology",
                    "year_of_study": 2,
                },
            )
            user.set_password(password)
            user.save()
            students.append(user)

        units = {}
        for code, title, credits, lecturer_index in UNITS:
            unit, _ = Unit.objects.update_or_create(
                code=code,
                defaults={
                    "title": title,
                    "credits": credits,
                    "lecturer": lecturers[lecturer_index],
                    "description": f"Sample description for {title}.",
                },
            )
            units[code] = unit
            for student in students:
                # Stands in for what the KCA portal would send after unit registration.
                Enrollment.objects.get_or_create(
                    student=student, unit=unit, trimester=settings.CURRENT_TRIMESTER
                )

        for code, day, start, end, venue, mode, link, note in SLOTS:
            TimetableSlot.objects.update_or_create(
                unit=units[code], day=day, start_time=start,
                defaults={"end_time": end, "venue": venue, "mode": mode, "meeting_link": link, "meeting_note": note},
            )

        for index, code, cat, exam in RESULTS:
            Result.objects.update_or_create(
                student=students[index], unit=units[code], academic_year="2026/2027",
                defaults={"cat_mark": cat, "exam_mark": exam},
            )

        if not Announcement.objects.exists():
            Announcement.objects.create(
                title="Welcome to the Virtual Campus",
                body="This is sample data. Your timetable, units and results appear here once the registrar loads them.",
                author=admin, pinned=True,
            )
            Announcement.objects.create(
                title="Library hours extended",
                body="The main library stays open until 21:00 on weekdays during the examination period.",
                author=admin,
            )
            Announcement.objects.create(
                title="DIT 201 practical moved",
                body="Thursday's practical will be held in Computer Lab 1 instead of Lecture Hall 3.",
                author=lecturers[0], audience="students",
            )

        if not Facility.objects.exists():
            for name, category, description, location, hours, contact in FACILITIES:
                Facility.objects.create(
                    name=name, category=category, description=description,
                    location=location, opening_hours=hours, contact=contact,
                )

        self.stdout.write(self.style.SUCCESS("Demo data loaded."))
        self.stdout.write(f"  Student:  demo.student1@{STUDENT_DOMAIN}")
        self.stdout.write(f"  Lecturer: demo.lecturer1@{STAFF_DOMAIN}")
        self.stdout.write(f"  Admin:    demo.admin@{STAFF_DOMAIN}")
        self.stdout.write(f"  Password: {password}")
