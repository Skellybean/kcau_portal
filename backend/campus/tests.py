from datetime import time

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User

from .models import Announcement, Enrollment, PendingRegistration, Result, TimetableSlot, Unit
from .sync import claim_pending


def make_user(email, role, name, **extra):
    return User.objects.create_user(email, "Sturdy#Pass2026", full_name=name, role=role, is_verified=True, **extra)


def client_for(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


TRIMESTER = "2026 Trimester 3"


@override_settings(CURRENT_TRIMESTER=TRIMESTER, PORTAL_SYNC_KEY="test-portal-key")
class CampusAccessTests(TestCase):
    def setUp(self):
        cache.clear()
        self.s1 = make_user("one@students.kcau.ac.ke", "student", "Student One")
        self.s2 = make_user("two@students.kcau.ac.ke", "student", "Student Two")
        self.lec = make_user("lec@kcau.ac.ke", "lecturer", "Lecturer")
        self.other_lec = make_user("lec2@kcau.ac.ke", "lecturer", "Other Lecturer")
        self.admin = make_user("admin@kcau.ac.ke", "admin", "Admin", is_staff=True)

        self.unit = Unit.objects.create(code="DIT 201", title="Databases", credits=3, lecturer=self.lec)
        self.other_unit = Unit.objects.create(code="DIT 210", title="Networks", credits=3, lecturer=self.other_lec)
        Enrollment.objects.create(student=self.s1, unit=self.unit, trimester=TRIMESTER)
        self.slot = TimetableSlot.objects.create(unit=self.unit, day=0, start_time=time(8), end_time=time(10), venue="LH1")
        self.other_slot = TimetableSlot.objects.create(unit=self.other_unit, day=1, start_time=time(8), end_time=time(10), venue="LH2")
        Result.objects.create(student=self.s1, unit=self.unit, cat_mark=25, exam_mark=50)
        Result.objects.create(student=self.s2, unit=self.unit, cat_mark=10, exam_mark=20)

    def test_student_only_sees_own_results(self):
        data = client_for(self.s1).get("/api/results/").data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["grade"], "A")
        self.assertEqual(float(data[0]["total"]), 75.0)

    def test_student_cannot_write_results(self):
        response = client_for(self.s1).post(
            "/api/results/",
            {"student": self.s1.id, "unit": self.unit.id, "cat_mark": 30, "exam_mark": 70, "academic_year": "2027/2028"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_lecturer_only_records_results_for_own_units(self):
        client = client_for(self.lec)
        ok = client.post(
            "/api/results/",
            {"student": self.s2.id, "unit": self.unit.id, "cat_mark": 20, "exam_mark": 40, "academic_year": "2027/2028"},
            format="json",
        )
        self.assertEqual(ok.status_code, 201)
        denied = client.post(
            "/api/results/",
            {"student": self.s2.id, "unit": self.other_unit.id, "cat_mark": 20, "exam_mark": 40, "academic_year": "2027/2028"},
            format="json",
        )
        self.assertEqual(denied.status_code, 400)

    def test_marks_are_range_checked(self):
        response = client_for(self.admin).post(
            "/api/results/",
            {"student": self.s2.id, "unit": self.unit.id, "cat_mark": 45, "exam_mark": 40, "academic_year": "2028/2029"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_timetable_is_scoped_to_the_user(self):
        student_slots = client_for(self.s1).get("/api/timetable/").data
        self.assertEqual([s["unit_code"] for s in student_slots], ["DIT 201"])
        lecturer_slots = client_for(self.lec).get("/api/timetable/").data
        self.assertEqual([s["unit_code"] for s in lecturer_slots], ["DIT 201"])
        self.assertEqual(len(client_for(self.admin).get("/api/timetable/").data), 2)

    def test_students_cannot_enrol_themselves_in_the_app(self):
        client = client_for(self.s2)
        self.assertIn(client.post(f"/api/units/{self.unit.id}/enroll/").status_code, (404, 405))
        self.assertFalse(Enrollment.objects.filter(student=self.s2).exists())
        # Creating a unit or touching units is also closed to students.
        self.assertEqual(client.post("/api/units/", {"code": "X", "title": "X"}, format="json").status_code, 403)

    def test_registered_flag_and_my_units_follow_the_current_trimester(self):
        Enrollment.objects.create(student=self.s1, unit=self.other_unit, trimester="2026 Trimester 2")
        client = client_for(self.s1)
        mine = client.get("/api/units/?mine=1").data
        self.assertEqual([u["code"] for u in mine], ["DIT 201"])
        catalog = {u["code"]: u["registered"] for u in client.get("/api/units/").data}
        self.assertEqual(catalog, {"DIT 201": True, "DIT 210": False})

    def sync(self, items, key="test-portal-key"):
        headers = {"HTTP_X_PORTAL_KEY": key} if key is not None else {}
        return APIClient().post("/api/portal/registrations/", {"registrations": items}, format="json", **headers)

    def test_portal_sync_requires_the_key(self):
        item = {"email": "two@students.kcau.ac.ke", "unit_code": "DIT 201", "trimester": TRIMESTER}
        self.assertEqual(self.sync([item], key=None).status_code, 403)
        self.assertEqual(self.sync([item], key="wrong").status_code, 403)
        self.assertFalse(Enrollment.objects.filter(student=self.s2).exists())

    @override_settings(PORTAL_SYNC_KEY="")
    def test_portal_sync_is_off_without_a_configured_key(self):
        self.assertEqual(self.sync([{"email": "a"}], key="").status_code, 503)

    def test_portal_registration_appears_in_the_virtual_campus(self):
        item = {"email": "two@students.kcau.ac.ke", "unit_code": "dit 201", "trimester": TRIMESTER}
        response = self.sync([item])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["status"], "registered")
        self.assertEqual(self.sync([item]).data["results"][0]["status"], "registered")  # idempotent
        self.assertEqual(Enrollment.objects.filter(student=self.s2).count(), 1)
        mine = client_for(self.s2).get("/api/units/?mine=1").data
        self.assertEqual([u["code"] for u in mine], ["DIT 201"])
        slots = client_for(self.s2).get("/api/timetable/").data
        self.assertEqual([x["unit_code"] for x in slots], ["DIT 201"])

    def test_portal_drop_removes_the_unit(self):
        item = {"email": "one@students.kcau.ac.ke", "unit_code": "DIT 201", "trimester": TRIMESTER, "action": "drop"}
        self.assertEqual(self.sync([item]).data["results"][0]["status"], "dropped")
        self.assertEqual(client_for(self.s1).get("/api/units/?mine=1").data, [])

    def test_portal_sync_rejects_bad_rows_without_creating_anything(self):
        rows = [
            {"email": "someone@gmail.com", "unit_code": "DIT 201", "trimester": TRIMESTER},
            {"email": "lec@kcau.ac.ke", "unit_code": "DIT 201", "trimester": TRIMESTER},
            {"email": "two@students.kcau.ac.ke", "unit_code": "NOPE 999", "trimester": TRIMESTER},
            {"email": "two@students.kcau.ac.ke", "unit_code": "DIT 201", "trimester": ""},
        ]
        statuses = [r["status"] for r in self.sync(rows).data["results"]]
        self.assertEqual(statuses, ["not_a_student_email", "not_a_student_email", "unknown_unit", "missing_trimester"])
        self.assertEqual(Enrollment.objects.exclude(student=self.s1).count(), 0)
        self.assertEqual(PendingRegistration.objects.count(), 0)

    def test_registration_before_signup_is_applied_when_the_student_verifies(self):
        item = {"email": "new@students.kcau.ac.ke", "unit_code": "DIT 201", "trimester": TRIMESTER}
        self.assertEqual(self.sync([item]).data["results"][0]["status"], "pending_until_signup")
        self.assertEqual(PendingRegistration.objects.count(), 1)
        newcomer = make_user("new@students.kcau.ac.ke", "student", "New Student")
        self.assertEqual(claim_pending(newcomer), 1)
        self.assertEqual(PendingRegistration.objects.count(), 0)
        self.assertEqual([u["code"] for u in client_for(newcomer).get("/api/units/?mine=1").data], ["DIT 201"])

    def test_only_admin_changes_units(self):
        payload = {"code": "NEW 100", "title": "New", "credits": 3}
        self.assertEqual(client_for(self.s1).post("/api/units/", payload, format="json").status_code, 403)
        self.assertEqual(client_for(self.lec).post("/api/units/", payload, format="json").status_code, 403)
        self.assertEqual(client_for(self.admin).post("/api/units/", payload, format="json").status_code, 201)

    def test_announcement_audiences_and_permissions(self):
        Announcement.objects.create(title="All", body="x", audience="all", author=self.admin)
        Announcement.objects.create(title="Students", body="x", audience="students", author=self.admin)
        Announcement.objects.create(title="Lecturers", body="x", audience="lecturers", author=self.admin)

        student_titles = {a["title"] for a in client_for(self.s1).get("/api/announcements/").data}
        self.assertEqual(student_titles, {"All", "Students"})
        lecturer_titles = {a["title"] for a in client_for(self.lec).get("/api/announcements/").data}
        self.assertEqual(lecturer_titles, {"All", "Lecturers"})

        self.assertEqual(
            client_for(self.s1).post("/api/announcements/", {"title": "t", "body": "b"}, format="json").status_code, 403
        )
        created = client_for(self.lec).post("/api/announcements/", {"title": "Notes", "body": "Read ch.4"}, format="json")
        self.assertEqual(created.status_code, 201)
        pin = client_for(self.lec).post(
            "/api/announcements/", {"title": "Pin", "body": "b", "pinned": True}, format="json"
        )
        self.assertEqual(pin.status_code, 400)

        other = client_for(self.other_lec)
        self.assertEqual(other.delete(f"/api/announcements/{created.data['id']}/").status_code, 403)
        self.assertEqual(client_for(self.lec).delete(f"/api/announcements/{created.data['id']}/").status_code, 204)

    def test_dashboard_for_student(self):
        data = client_for(self.s1).get("/api/dashboard/").data
        self.assertEqual(data["unit_count"], 1)
        self.assertEqual(data["results_count"], 1)
        self.assertEqual(data["average_mark"], 75.0)

    def test_dashboard_for_lecturer_has_no_marks(self):
        data = client_for(self.lec).get("/api/dashboard/").data
        self.assertNotIn("average_mark", data)
        self.assertEqual(data["unit_count"], 1)

    def test_profile_update_cannot_change_role_or_email(self):
        client = client_for(self.s1)
        response = client.patch(
            "/api/auth/me/",
            {"full_name": "Renamed", "role": "admin", "email": "x@gmail.com", "year_of_study": 3},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.role, "student")
        self.assertEqual(self.s1.email, "one@students.kcau.ac.ke")
        self.assertEqual(self.s1.full_name, "Renamed")


LINK = "https://meet.example.com/dit201-demo"


@override_settings(CURRENT_TRIMESTER=TRIMESTER)
class OnlineClassTests(TestCase):
    def setUp(self):
        cache.clear()
        self.s1 = make_user("one@students.kcau.ac.ke", "student", "Student One")
        self.s2 = make_user("two@students.kcau.ac.ke", "student", "Student Two")
        self.lec = make_user("lec@kcau.ac.ke", "lecturer", "Lecturer")
        self.other_lec = make_user("lec2@kcau.ac.ke", "lecturer", "Other Lecturer")
        self.admin = make_user("admin@kcau.ac.ke", "admin", "Admin", is_staff=True)
        self.unit = Unit.objects.create(code="DIT 201", title="Databases", credits=3, lecturer=self.lec)
        self.other_unit = Unit.objects.create(code="DIT 210", title="Networks", credits=3, lecturer=self.other_lec)
        Enrollment.objects.create(student=self.s1, unit=self.unit, trimester=TRIMESTER)
        self.slot = TimetableSlot.objects.create(
            unit=self.unit, day=0, start_time=time(8), end_time=time(10), venue="LH1"
        )
        self.other_slot = TimetableSlot.objects.create(
            unit=self.other_unit, day=1, start_time=time(8), end_time=time(10), venue="LH2"
        )

    def new_slot(self, **extra):
        payload = {"unit": self.unit.id, "day": 2, "start_time": "09:00", "end_time": "11:00"}
        payload.update(extra)
        return client_for(self.admin).post("/api/timetable/", payload, format="json")

    def test_online_class_needs_no_venue_and_may_wait_for_its_link(self):
        response = self.new_slot(mode="online")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["mode"], "online")
        self.assertEqual(response.data["meeting_link"], "")

    def test_in_person_and_hybrid_classes_need_a_venue(self):
        self.assertEqual(self.new_slot(mode="in_person", venue="").status_code, 400)
        self.assertEqual(self.new_slot(mode="hybrid", venue="", meeting_link=LINK).status_code, 400)
        self.assertEqual(self.new_slot(mode="hybrid", venue="Room B12", meeting_link=LINK).status_code, 201)

    def test_only_https_links_are_accepted(self):
        for bad in ["http://meet.example.com/x", "javascript:alert(1)", "ftp://example.com/x", "meet.example.com/x"]:
            response = self.new_slot(mode="online", meeting_link=bad)
            self.assertEqual(response.status_code, 400, bad)
        self.assertEqual(self.new_slot(mode="online", meeting_link=LINK).status_code, 201)

    def test_lecturer_can_post_the_link_for_their_own_unit(self):
        response = client_for(self.lec).patch(
            f"/api/timetable/{self.slot.id}/",
            {"mode": "online", "meeting_link": LINK, "meeting_note": "Passcode 1234"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.slot.refresh_from_db()
        self.assertEqual((self.slot.mode, self.slot.meeting_link, self.slot.meeting_note), ("online", LINK, "Passcode 1234"))

    def test_lecturer_cannot_touch_another_lecturers_slot(self):
        response = client_for(self.lec).patch(
            f"/api/timetable/{self.other_slot.id}/", {"mode": "online", "meeting_link": LINK}, format="json"
        )
        self.assertEqual(response.status_code, 404)
        self.other_slot.refresh_from_db()
        self.assertEqual(self.other_slot.meeting_link, "")

    def test_lecturer_cannot_change_time_venue_or_unit(self):
        client_for(self.lec).patch(
            f"/api/timetable/{self.slot.id}/",
            {"mode": "online", "meeting_link": LINK, "venue": "Hacked", "day": 4, "start_time": "01:00", "unit": self.other_unit.id},
            format="json",
        )
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.venue, "LH1")
        self.assertEqual(self.slot.day, 0)
        self.assertEqual(self.slot.start_time, time(8))
        self.assertEqual(self.slot.unit_id, self.unit.id)

    def test_lecturers_cannot_create_or_delete_slots_and_students_cannot_edit(self):
        payload = {"unit": self.unit.id, "day": 2, "start_time": "09:00", "end_time": "11:00", "venue": "X"}
        self.assertEqual(client_for(self.lec).post("/api/timetable/", payload, format="json").status_code, 403)
        self.assertEqual(client_for(self.lec).delete(f"/api/timetable/{self.slot.id}/").status_code, 403)
        self.assertEqual(
            client_for(self.s1).patch(f"/api/timetable/{self.slot.id}/", {"meeting_link": LINK}, format="json").status_code, 403
        )

    def test_students_only_see_links_for_units_they_registered_in(self):
        for slot in (self.slot, self.other_slot):
            slot.mode, slot.meeting_link = "online", LINK
            slot.save()
        seen = client_for(self.s1).get("/api/timetable/").data
        self.assertEqual([(x["unit_code"], x["meeting_link"]) for x in seen], [("DIT 201", LINK)])
        self.assertEqual(client_for(self.s2).get("/api/timetable/").data, [])

    def test_switching_back_to_in_person_clears_the_link(self):
        self.slot.mode, self.slot.meeting_link, self.slot.meeting_note = "online", LINK, "note"
        self.slot.save()
        response = client_for(self.admin).patch(f"/api/timetable/{self.slot.id}/", {"mode": "in_person"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.data["meeting_link"], response.data["meeting_note"]), ("", ""))

    def test_lecturer_cannot_switch_a_venue_less_slot_to_in_person(self):
        online = TimetableSlot.objects.create(
            unit=self.unit, day=3, start_time=time(9), end_time=time(11), venue="", mode="online", meeting_link=LINK
        )
        response = client_for(self.lec).patch(f"/api/timetable/{online.id}/", {"mode": "in_person"}, format="json")
        self.assertEqual(response.status_code, 400)
        online.refresh_from_db()
        self.assertEqual(online.mode, "online")
