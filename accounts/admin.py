from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class CampusUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (("Perfil institucional", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Perfil institucional", {"fields": ("email", "role")}),)

    def has_module_permission(self, request):
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == User.Role.ADMIN
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == User.Role.ADMIN
        )
