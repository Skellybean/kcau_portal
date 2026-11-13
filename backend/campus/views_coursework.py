import hmac
import os
import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.validators import classify_email

from .models_coursework import Assessment, ExamSlot, FeeStatus, Submission
from .permissions import FeesCleared, IsAdminRoleOrReadOnly, IsStaffRole, IsStaffRoleOrReadOnly
from .serializers_coursework import AssessmentSerializer, ExamSlotSerializer, StaffSubmissionSerializer
from .views import units_for

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 20000
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".zip"}


class AssessmentViewSet(viewsets.ModelViewSet):
    """CATs and assignments. Students read theirs and submit; lecturers set work for their own units."""

    serializer_class = AssessmentSerializer
    permission_classes = [IsStaffRoleOrReadOnly]

    def get_permissions(self):
        if self.action == "submit":
            return [IsAuthenticated(), FeesCleared()]
        return super().get_permissions()

    def get_queryset(self):
        qs = Assessment.objects.select_related("unit")
        user = self.request.user
        if not user.is_admin_role:
            qs = qs.filter(unit__in=units_for(user))
        unit = self.request.query_params.get("unit")
        if unit and unit.isdigit():
            qs = qs.filter(unit_id=int(unit))
        return qs.distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated and user.is_student:
            rows = Submission.objects.filter(student=user).defer("file_data")
            context["submissions"] = {row.assessment_id: row for row in rows}
        return context

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def submit(self, request, pk=None):
        """Send or replace a typed answer and/or one file. Multipart fields: text_answer, file."""
        user = request.user
        if not user.is_student:
            raise PermissionDenied("Only students submit work.")
        assessment = self.get_object()  # limited to units the student is registered in
        if not assessment.accepting:
            return Response({"detail": "The deadline has passed and this work is closed."}, status=status.HTTP_400_BAD_REQUEST)

        text = str(request.data.get("text_answer") or "").strip()
        upload = request.FILES.get("file")
        if not text and upload is None:
            return Response({"detail": "Add an answer or attach a file."}, status=status.HTTP_400_BAD_REQUEST)
        if text and not assessment.allow_text:
            return Response({"detail": "This work does not accept a typed answer. Attach a file."}, status=status.HTTP_400_BAD_REQUEST)
        if upload is not None and not assessment.allow_file:
            return Response({"detail": "This work does not accept files. Type your answer."}, status=status.HTTP_400_BAD_REQUEST)
        if len(text) > MAX_TEXT_CHARS:
            return Response({"detail": f"Typed answers are limited to {MAX_TEXT_CHARS} characters."}, status=status.HTTP_400_BAD_REQUEST)
        if upload is not None:
            extension = os.path.splitext(upload.name)[1].lower()
            if extension not in ALLOWED_EXTENSIONS:
                allowed = ", ".join(sorted(e.lstrip(".") for e in ALLOWED_EXTENSIONS))
                return Response({"detail": f"That file type is not accepted. Use: {allowed}."}, status=status.HTTP_400_BAD_REQUEST)
            if upload.size > MAX_UPLOAD_BYTES:
                return Response({"detail": "Files can be at most 5 MB."}, status=status.HTTP_400_BAD_REQUEST)

        submission = Submission.objects.filter(assessment=assessment, student=user).first()
        if submission is None:
            submission = Submission(assessment=assessment, student=user)
        elif submission.marks is not None:
            return Response({"detail": "This work has already been marked and can no longer be changed."}, status=status.HTTP_400_BAD_REQUEST)

        if text:
            submission.text_answer = text
        if upload is not None:
            submission.file_name = os.path.basename(upload.name)[:255]
            submission.file_type = (upload.content_type or "")[:100]
            submission.file_size = upload.size
            submission.file_data = upload.read()
        submission.submitted_at = timezone.now()
        submission.save()
        return Response(self.get_serializer(assessment).data)


class SubmissionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """For lecturers and administrators: list submissions, download files, record marks and feedback."""

    serializer_class = StaffSubmissionSerializer
    permission_classes = [IsStaffRole]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        qs = Submission.objects.select_related("student", "assessment", "assessment__unit").defer("file_data")
        user = self.request.user
        if user.is_lecturer:
            qs = qs.filter(assessment__unit__lecturer=user)
        assessment = self.request.query_params.get("assessment")
        if assessment and assessment.isdigit():
            qs = qs.filter(assessment_id=int(assessment))
        return qs

    @action(detail=True, methods=["get"])
    def file(self, request, pk=None):
        submission = self.get_object()
        full = Submission.objects.only("file_name", "file_type", "file_data").get(pk=submission.pk)
        if not full.file_data:
            return Response({"detail": "This submission has no file."}, status=status.HTTP_404_NOT_FOUND)
        safe_name = re.sub(r"[^\w.\- ]", "_", full.file_name or "submission")
        response = HttpResponse(bytes(full.file_data), content_type=full.file_type or "application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{safe_name}"'
        response["X-Content-Type-Options"] = "nosniff"
        return response


class ExamSlotViewSet(viewsets.ModelViewSet):
    """Exam timetable. Students see exams for units they are registered in this trimester."""

    serializer_class = ExamSlotSerializer
    permission_classes = [IsAdminRoleOrReadOnly]

    def get_queryset(self):
        qs = ExamSlot.objects.select_related("unit")
        user = self.request.user
        if user.is_admin_role:
            trimester = self.request.query_params.get("trimester")
            return qs.filter(trimester=trimester) if trimester else qs
        return qs.filter(unit__in=units_for(user), trimester=settings.CURRENT_TRIMESTER).distinct()


class ExamCardView(APIView):
    """The student's exam card: identity, registered units and where and when each exam is sat.

    Blocked for students with outstanding fees by the default FeesCleared permission.
    """

    def get(self, request):
        user = request.user
        if not user.is_student:
            raise PermissionDenied("Exam cards are for students.")
        units = units_for(user).distinct()
        slots = ExamSlot.objects.filter(unit__in=units, trimester=settings.CURRENT_TRIMESTER).select_related("unit")
        by_unit = {}
        for slot in slots:
            by_unit.setdefault(slot.unit_id, []).append(slot)
        rows = []
        for unit in units.order_by("code"):
            rows.append({
                "code": unit.code,
                "title": unit.title,
                "credits": unit.credits,
                "exams": [
                    {"date": s.date, "start_time": s.start_time, "end_time": s.end_time, "venue": s.venue}
                    for s in by_unit.get(unit.id, [])
                ],
            })
        return Response({
            "student": {
                "full_name": user.full_name,
                "email": user.email,
                "admission_number": user.admission_number,
                "programme": user.programme,
            },
            "trimester": settings.CURRENT_TRIMESTER,
            "units": rows,
            "generated_at": timezone.now(),
        })


class PortalFeeSyncView(APIView):
    """Called by the KCA portal to say whose fees are cleared.

    POST /api/portal/fees/ with header ``X-Portal-Key`` and a body like
    {"fees": [{"email": "jane@students.kcau.ac.ke", "cleared": true, "balance": "0.00"}]}
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "auth"
    MAX_ITEMS = 5000

    def post(self, request):
        expected = settings.PORTAL_SYNC_KEY
        if not expected:
            return Response({"detail": "Portal sync is not enabled."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        supplied = request.headers.get("X-Portal-Key", "")
        if not hmac.compare_digest(supplied.encode(), expected.encode()):
            return Response({"detail": "Invalid portal key."}, status=status.HTTP_403_FORBIDDEN)

        items = request.data.get("fees") if isinstance(request.data, dict) else None
        if not isinstance(items, list) or not items:
            return Response({"detail": "Send a non-empty 'fees' list."}, status=status.HTTP_400_BAD_REQUEST)
        if len(items) > self.MAX_ITEMS:
            return Response({"detail": f"At most {self.MAX_ITEMS} rows per request."}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for item in items:
            item = item if isinstance(item, dict) else {}
            email = str(item.get("email") or "").strip().lower()
            outcome = apply_fee_status(email, item.get("cleared"), item.get("balance"))
            results.append({"email": email, "status": outcome})
        return Response({"results": results})


def apply_fee_status(email, cleared, balance=None):
    """Create or update one fee record. Returns a short status string."""
    if classify_email(email) != "student":
        return "not_a_student_email"
    if not isinstance(cleared, bool):
        return "invalid_cleared"
    amount = None
    if balance not in (None, ""):
        try:
            amount = Decimal(str(balance))
        except InvalidOperation:
            return "invalid_balance"
    FeeStatus.objects.update_or_create(email=email, defaults={"cleared": cleared, "balance": amount})
    return "updated"
