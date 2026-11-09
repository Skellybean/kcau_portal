import re

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import User
from .validators import classify_email

PASSWORD = "Sturdy#Pass2026"


def last_code():
    match = re.search(r"\b(\d{6})\b", mail.outbox[-1].body)
    return match.group(1)


class EmailRuleTests(TestCase):
    def test_classification(self):
        self.assertEqual(classify_email("jane@students.kcau.ac.ke"), "student")
        self.assertEqual(classify_email("Jane@Students.KCAU.ac.ke"), "student")
        self.assertEqual(classify_email("dr.omondi@kcau.ac.ke"), "lecturer")

    def test_rejects_everything_else(self):
        bad = [
            "someone@gmail.com",
            "someone@kcau.ac.ke.evil.com",
            "someone@students.kcau.ac.ke.evil.com",
            "someone@evilkcau.ac.ke",
            "someone@mail.kcau.ac.ke",
            "a@b@students.kcau.ac.ke",
            "@students.kcau.ac.ke",
            "students.kcau.ac.ke",
            "",
        ]
        for email in bad:
            self.assertIsNone(classify_email(email), email)


class AuthFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def register(self, email="jane@students.kcau.ac.ke", **extra):
        payload = {"email": email, "full_name": "Jane Wanjiru", "password": PASSWORD, **extra}
        return self.client.post("/api/auth/register/", payload, format="json")

    def test_non_kca_email_cannot_register(self):
        for email in ["jane@gmail.com", "jane@kcau.ac.ke.evil.com"]:
            response = self.register(email)
            self.assertEqual(response.status_code, 400, email)
            self.assertIn("KCA", response.data["detail"])
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_student_registration_verification_and_login(self):
        self.assertEqual(self.register().status_code, 201)
        user = User.objects.get(email="jane@students.kcau.ac.ke")
        self.assertEqual(user.role, "student")
        self.assertFalse(user.is_verified)

        blocked = self.client.post(
            "/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json"
        )
        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(blocked.data["code"], "email_not_verified")

        wrong = self.client.post("/api/auth/verify/", {"email": user.email, "code": "000000"}, format="json")
        self.assertEqual(wrong.status_code, 400)

        ok = self.client.post("/api/auth/verify/", {"email": user.email, "code": last_code()}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.assertIn("token", ok.data)

        login = self.client.post("/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data["user"]["role"], "student")

    def test_staff_domain_gets_lecturer_role(self):
        self.register("dr.omondi@kcau.ac.ke")
        self.assertEqual(User.objects.get(email="dr.omondi@kcau.ac.ke").role, "lecturer")

    def test_role_cannot_be_chosen_by_the_client(self):
        self.register(role="admin")
        self.assertEqual(User.objects.get(email="jane@students.kcau.ac.ke").role, "student")

    def test_code_is_consumed_and_locks_after_too_many_attempts(self):
        self.register()
        email = "jane@students.kcau.ac.ke"
        real = last_code()
        wrong = "000000" if real != "000000" else "111111"
        for _ in range(5):
            self.client.post("/api/auth/verify/", {"email": email, "code": wrong}, format="json")
        locked = self.client.post("/api/auth/verify/", {"email": email, "code": real}, format="json")
        self.assertEqual(locked.status_code, 400)

    def test_login_with_non_kca_email_is_rejected_even_if_account_exists(self):
        User.objects.bulk_create([User(email="old@gmail.com", full_name="Old", is_verified=True)])
        user = User.objects.get(email="old@gmail.com")
        user.set_password(PASSWORD)
        user.save()
        response = self.client.post("/api/auth/login/", {"email": "old@gmail.com", "password": PASSWORD}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("token", response.data)

    def test_duplicate_registration_of_verified_account_is_refused(self):
        User.objects.create_user("jane@students.kcau.ac.ke", PASSWORD, full_name="Jane", is_verified=True)
        self.assertEqual(self.register().status_code, 400)

    def test_weak_password_rejected(self):
        response = self.register(password="12345678")
        self.assertEqual(response.status_code, 400)

    def test_password_reset_flow(self):
        user = User.objects.create_user("jane@students.kcau.ac.ke", PASSWORD, full_name="Jane", is_verified=True)
        self.client.post("/api/auth/password-reset/", {"email": user.email}, format="json")
        new_password = "Fresh#Start2027"
        done = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"email": user.email, "code": last_code(), "new_password": new_password},
            format="json",
        )
        self.assertEqual(done.status_code, 200)
        login = self.client.post("/api/auth/login/", {"email": user.email, "password": new_password}, format="json")
        self.assertEqual(login.status_code, 200)

    def test_reset_request_does_not_reveal_unknown_accounts(self):
        response = self.client.post("/api/auth/password-reset/", {"email": "nobody@students.kcau.ac.ke"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_protected_endpoints_need_token(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
        self.assertEqual(self.client.get("/api/units/").status_code, 401)

    @override_settings(KCA_STUDENT_EMAIL_DOMAINS=["students.example.ac.ke"], KCA_STAFF_EMAIL_DOMAINS=["example.ac.ke"])
    def test_domains_are_configurable(self):
        self.assertEqual(classify_email("a@students.example.ac.ke"), "student")
        self.assertIsNone(classify_email("a@students.kcau.ac.ke"))
