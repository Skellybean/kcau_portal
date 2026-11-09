from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

admin.site.site_header = "KCA Virtual Campus"
admin.site.site_title = "KCA Virtual Campus"
admin.site.index_title = "Administration"


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("campus.urls")),
]
