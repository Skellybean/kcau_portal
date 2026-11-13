import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("campus", "0003_merge_20261110_1414"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeeStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("cleared", models.BooleanField(default=False)),
                ("balance", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "fee statuses",
                "ordering": ["email"],
            },
        ),
        migrations.CreateModel(
            name="Assessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "kind",
                    models.CharField(
                        choices=[("cat", "CAT"), ("assignment", "Assignment")],
                        default="assignment",
                        max_length=12,
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("instructions", models.TextField(blank=True)),
                ("due_at", models.DateTimeField()),
                ("max_marks", models.DecimalField(decimal_places=2, default=100, max_digits=5)),
                ("allow_text", models.BooleanField(default=True)),
                ("allow_file", models.BooleanField(default=True)),
                ("accept_late", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assessments_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "unit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assessments",
                        to="campus.unit",
                    ),
                ),
            ],
            options={
                "ordering": ["due_at"],
            },
        ),
        migrations.CreateModel(
            name="Submission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text_answer", models.TextField(blank=True)),
                ("file_name", models.CharField(blank=True, max_length=255)),
                ("file_type", models.CharField(blank=True, max_length=100)),
                ("file_size", models.PositiveIntegerField(default=0)),
                ("file_data", models.BinaryField(blank=True, editable=False, null=True)),
                ("submitted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("marks", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("feedback", models.TextField(blank=True)),
                (
                    "assessment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submissions",
                        to="campus.assessment",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        limit_choices_to={"role": "student"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-submitted_at"],
                "unique_together": {("assessment", "student")},
            },
        ),
        migrations.CreateModel(
            name="ExamSlot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("trimester", models.CharField(max_length=40)),
                ("date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("venue", models.CharField(max_length=120)),
                (
                    "unit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exam_slots",
                        to="campus.unit",
                    ),
                ),
            ],
            options={
                "ordering": ["date", "start_time"],
            },
        ),
    ]
