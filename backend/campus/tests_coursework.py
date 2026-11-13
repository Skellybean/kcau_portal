"""Tests for the fee gate, coursework submissions, exam timetable and exam card.

NOTE: these were written without being run against the real repo. If `make()` below does not
match your User model's create_user signature, adjust that one helper (or swap in make_user
from campus/tests.py).
"""
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Unit
from .models_coursework import Assessment, ExamSlot, FeeStatus, Submission

User = get_user_model()
STUDENT = "jane@students.kcau.ac.ke"


def make(email, role, **extra):
    user = User.objects.create_user(email=email, password="pass12345!", full_name=email.split("@")[0], role=role, **extra)
    return user


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION="Token " + Token.objects.get_or_create(user=user)[0].key)
    return c


class Base(TestCase):
    def setUp(self):
        self.lecturer = make("lec@kcau.ac.ke", "lecturer")
        self.admin = make("adm@kcau.ac.ke", "admin")
        self.student = make(STUDENT, "student")
        self.unit = Unit.objects.create(code="DIT 201", title="Databases", credits=3, lecturer=self.lecturer)
        self.unit.students.add(self.student) if hasattr(self.unit, "students") else None
        FeeStatus.objects.create(email=STUDENT, cleared=True)
        self.cat = Assessment.objects.create(
            unit=self.unit, kind="cat", title="CAT 1", due_at=timezone.now() + timedelta(days=3),
            max_marks=30, created_by=self.lecturer,
        )
        self.s = client_for(self.student)
        self.l = client_for(self.lecturer)
        self.a = client_for(self.admin)


class FeeGateTests(Base):
    def test_cleared_student_has_access(self):
        self.assertEqual(self.s.get("/api/assessments/").status_code, 200)

    def test_unpaid_student_blocked_with_code(self):
        FeeStatus.objects.filter(email=STUDENT).update(cleared=False)
        for path in ["/api/assessments/", "/api/exams/", "/api/exam-card/", "/api/timetable/", "/api/results/"]:
            r = self.s.get(path)
            self.assertEqual(r.status_code, 403, path)
            self.assertEqual(r.json()["code"], "fees_outstanding", path)

    def test_no_fee_row_means_blocked(self):
        FeeStatus.objects.all().delete()
        self.assertEqual(self.s.get("/api/assessments/").status_code, 403)

    def test_me_reports_fees_cleared_and_is_not_gated(self):
        FeeStatus.objects.filter(email=STUDENT).update(cleared=False)
        r = self.s.get("/api/auth/me/")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["fees_cleared"])

    def test_logout_works_when_locked(self):
        FeeStatus.objects.filter(email=STUDENT).update(cleared=False)
        self.assertIn(self.s.post("/api/auth/logout/").status_code, (200, 204))

    def test_staff_not_gated(self):
        self.assertEqual(self.l.get("/api/assessments/").status_code, 200)
        self.assertEqual(self.a.get("/api/exams/").status_code, 200)

    @override_settings(FEE_GATE_ENABLED=False)
    def test_gate_can_be_disabled(self):
        FeeStatus.objects.all().delete()
        self.assertEqual(self.s.get("/api/assessments/").status_code, 200)


class SubmissionTests(Base):
    def url(self):
        return f"/api/assessments/{self.cat.id}/submit/"

    def test_submit_text(self):
        r = self.s.post(self.url(), {"text_answer": "my answer"}, format="multipart")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(Submission.objects.get().text_answer, "my answer")

    def test_submit_file_and_resubmit(self):
        f = SimpleUploadedFile("a.pdf", b"%PDF-1", content_type="application/pdf")
        self.assertEqual(self.s.post(self.url(), {"file": f}, format="multipart").status_code, 200)
        self.assertEqual(self.s.post(self.url(), {"text_answer": "v2"}, format="multipart").status_code, 200)
        self.assertEqual(Submission.objects.count(), 1)

    def test_empty_rejected(self):
        self.assertEqual(self.s.post(self.url(), {}, format="multipart").status_code, 400)

    def test_bad_extension_rejected(self):
        f = SimpleUploadedFile("x.exe", b"MZ", content_type="application/octet-stream")
        self.assertEqual(self.s.post(self.url(), {"file": f}, format="multipart").status_code, 400)

    def test_too_big_rejected(self):
        f = SimpleUploadedFile("x.pdf", b"0" * (5 * 1024 * 1024 + 1), content_type="application/pdf")
        self.assertEqual(self.s.post(self.url(), {"file": f}, format="multipart").status_code, 400)

    def test_closed_after_deadline(self):
        Assessment.objects.filter(pk=self.cat.pk).update(due_at=timezone.now() - timedelta(hours=1))
        self.assertEqual(self.s.post(self.url(), {"text_answer": "late"}, format="multipart").status_code, 400)

    def test_marked_work_locked(self):
        Submission.objects.create(assessment=self.cat, student=self.student, text_answer="x", marks=20)
        self.assertEqual(self.s.post(self.url(), {"text_answer": "y"}, format="multipart").status_code, 400)

    def test_unpaid_cannot_submit(self):
        FeeStatus.objects.filter(email=STUDENT).update(cleared=False)
        self.assertEqual(self.s.post(self.url(), {"text_answer": "x"}, format="multipart").status_code, 403)

    def test_unregistered_unit_is_404(self):
        other = Unit.objects.create(code="DIT 999", title="Other", credits=3, lecturer=self.lecturer)
        a = Assessment.objects.create(unit=other, kind="cat", title="X", due_at=timezone.now() + timedelta(days=1))
        r = self.s.post(f"/api/assessments/{a.id}/submit/", {"text_answer": "x"}, format="multipart")
        self.assertEqual(r.status_code, 404)

    def test_lecturer_marks_within_range(self):
        sub = Submission.objects.create(assessment=self.cat, student=self.student, text_answer="x")
        self.assertEqual(self.l.patch(f"/api/submissions/{sub.id}/", {"marks": 99}, format="json").status_code, 400)
        r = self.l.patch(f"/api/submissions/{sub.id}/", {"marks": 25, "feedback": "Good"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)

    def test_student_cannot_use_submissions_api(self):
        self.assertEqual(self.s.get("/api/submissions/").status_code, 403)


class ExamTests(Base):
    def setUp(self):
        super().setUp()
        from django.conf import settings
        ExamSlot.objects.create(
            unit=self.unit, trimester=settings.CURRENT_TRIMESTER, date=date.today() + timedelta(days=20),
            start_time=time(9), end_time=time(12), venue="Main Hall",
        )

    def test_student_sees_timetable(self):
        r = self.s.get("/api/exams/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        rows = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(len(rows), 1)

    def test_exam_card(self):
        r = self.s.get("/api/exam-card/")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["student"]["email"], STUDENT)
        self.assertEqual(body["units"][0]["exams"][0]["venue"], "Main Hall")

    def test_exam_card_students_only(self):
        self.assertEqual(self.l.get("/api/exam-card/").status_code, 403)

    def test_student_cannot_create_slot(self):
        self.assertEqual(self.s.post("/api/exams/", {}, format="json").status_code, 403)


@override_settings(PORTAL_SYNC_KEY="secret-key")
class FeeSyncTests(TestCase):
    def post(self, body, key="secret-key"):
        return APIClient().post("/api/portal/fees/", body, format="json", HTTP_X_PORTAL_KEY=key)

    def test_wrong_key(self):
        self.assertEqual(self.post({"fees": [{"email": STUDENT, "cleared": True}]}, key="nope").status_code, 403)

    def test_upsert(self):
        r = self.post({"fees": [{"email": STUDENT, "cleared": True, "balance": "0.00"}]})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(FeeStatus.objects.get(email=STUDENT).cleared)
        self.post({"fees": [{"email": STUDENT, "cleared": False, "balance": "500"}]})
        self.assertFalse(FeeStatus.objects.get(email=STUDENT).cleared)

    def test_rejects_non_student_email_and_bad_flag(self):
        r = self.post({"fees": [{"email": "x@gmail.com", "cleared": True}, {"email": STUDENT, "cleared": "yes"}]})
        self.assertEqual([x["status"] for x in r.json()["results"]], ["not_a_student_email", "invalid_cleared"])
        self.assertEqual(FeeStatus.objects.count(), 0)

    def test_empty_list(self):
        self.assertEqual(self.post({"fees": []}).status_code, 400)
