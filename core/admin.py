from django.contrib import admin

from core.models import AuditEvent

admin.site.site_header = "Sistema de préstamos de equipos · UNCP"
admin.site.site_title = "Administración de préstamos UNCP"
admin.site.index_title = "Inventario y préstamos de laboratorio"


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "ip_address", "path")
    list_filter = ("action", "created_at")
    search_fields = ("actor__username", "actor__email", "detail", "ip_address")
    date_hierarchy = "created_at"
    readonly_fields = ("actor", "action", "detail", "ip_address", "path", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        from accounts.models import User

        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == User.Role.ADMIN
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)
