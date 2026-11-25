from django.contrib import admin
from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from core.models import record_audit
from loans.models import Equipment, Loan


@admin.action(description="Marcar equipos seleccionados en mantenimiento")
def mark_equipment_maintenance(modeladmin, request, queryset):
    equipment_codes = list(queryset.values_list("code", flat=True))
    updated = queryset.update(status=Equipment.Status.MAINTENANCE)
    record_audit(request, "equipos_mantenimiento", f"equipos={equipment_codes}")
    modeladmin.message_user(request, f"{updated} equipo(s) marcado(s) en mantenimiento.")


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "laboratory", "status", "quantity", "available_quantity", "days_since_maintenance")
    list_filter = ("laboratory", "status", "category")
    search_fields = ("code", "name", "category", "brand", "model_name")
    actions = (mark_equipment_maintenance,)

    @admin.display(description="Días desde mantenimiento", ordering="last_maintenance")
    def days_since_maintenance(self, obj):
        return obj.days_since_maintenance if obj.days_since_maintenance is not None else "Sin registro"

    def has_module_permission(self, request):
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == "admin"
        )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            active_loan_total=Coalesce(
                Sum("loans__quantity", filter=Q(loans__status=Loan.Status.ACTIVE)),
                0,
            )
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        record_audit(
            request,
            "equipo_actualizado_admin" if change else "equipo_registrado_admin",
            f"equipo={obj.code}",
        )

    def delete_model(self, request, obj):
        record_audit(request, "equipo_eliminado", f"equipo={obj.code}")
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        codes = list(queryset.values_list("code", flat=True))
        record_audit(request, "equipos_eliminados", f"equipos={codes}")
        super().delete_queryset(request, queryset)


@admin.action(description="Enviar recordatorio de devolución")
def send_return_reminders(modeladmin, request, queryset):
    sent = 0
    for loan in queryset.filter(status=Loan.Status.ACTIVE).select_related("borrower", "equipment"):
        if loan.borrower.email:
            send_mail(
                subject=f"Devolución pendiente: {loan.equipment.name}",
                message=f"Recuerda devolver {loan.equipment.name} antes del {loan.due_date:%d/%m/%Y}.",
                from_email=None,
                recipient_list=[loan.borrower.email],
                fail_silently=False,
            )
            sent += 1
    record_audit(request, "recordatorios_devolucion", f"enviados={sent}")
    modeladmin.message_user(request, f"Recordatorios enviados a {sent} usuario(s).")


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("borrower", "equipment", "loan_date", "due_date", "status", "quantity", "overdue_days")
    list_filter = ("status", "loan_date", "due_date", "borrower")
    search_fields = ("equipment__code", "equipment__name", "borrower__first_name", "borrower__last_name", "borrower__username")
    date_hierarchy = "loan_date"
    autocomplete_fields = ("borrower", "equipment")
    readonly_fields = ("created_at", "returned_at", "overdue_days")
    actions = (send_return_reminders,)

    def has_module_permission(self, request):
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == "admin"
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        record_audit(
            request,
            "prestamo_actualizado_admin" if change else "prestamo_registrado_admin",
            f"prestamo={obj.pk}; equipo={obj.equipment_id}",
        )

    def delete_model(self, request, obj):
        record_audit(request, "prestamo_eliminado", f"prestamo={obj.pk}")
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        ids = list(queryset.values_list("pk", flat=True))
        record_audit(request, "prestamos_eliminados", f"prestamos={ids}")
        super().delete_queryset(request, queryset)
