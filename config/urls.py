from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.accounts.views import dashboard_view


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="accounts:login", permanent=False)),
    path("admin/", admin.site.urls),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("accounts/", include("apps.accounts.urls")),
    path("branches/", include("apps.branches.urls")),
    path("employees/", include("apps.employees.urls")),
    path("contracts/", include("apps.contracts.urls")),
    path("payroll/", include("apps.payroll.urls")),
    path("requests/", include("apps.requests.urls")),
    path("schedules/", include("apps.schedules.urls")),
    path("reports/", include("apps.reports.urls")),
    path("attendances/", include("apps.attendances.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
