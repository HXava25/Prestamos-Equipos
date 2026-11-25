from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("accounts.urls")),
    path("prestamos/", include("loans.urls")),
    path("", include("core.urls")),
]

handler403 = "core.views.permission_denied"
