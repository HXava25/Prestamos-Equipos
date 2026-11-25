from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Equipment(models.Model):
    class Status(models.TextChoices):
        OPERATIVE = "operativo", "Operativo"
        MAINTENANCE = "mantenimiento", "En mantenimiento"
        RETIRED = "baja", "Dado de baja"

    code = models.CharField("código patrimonial", max_length=30, unique=True)
    name = models.CharField("nombre", max_length=100)
    brand = models.CharField("marca", max_length=60, blank=True)
    model_name = models.CharField("modelo", max_length=60, blank=True)
    category = models.CharField("categoría", max_length=60)
    status = models.CharField("estado", max_length=20, choices=Status.choices, default=Status.OPERATIVE)
    laboratory = models.CharField("laboratorio", max_length=80)
    quantity = models.PositiveIntegerField("unidades", default=1, validators=[MinValueValidator(1)])
    last_maintenance = models.DateField("último mantenimiento", null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "equipo"
        verbose_name_plural = "equipos"

    @property
    def days_since_maintenance(self):
        if not self.last_maintenance:
            return None
        return (timezone.localdate() - self.last_maintenance).days

    @property
    def available_quantity(self):
        if self.status != self.Status.OPERATIVE:
            return 0
        if hasattr(self, "active_loan_total"):
            return max(self.quantity - self.active_loan_total, 0)
        borrowed = self.loans.filter(status=Loan.Status.ACTIVE).aggregate(
            total=models.Sum("quantity")
        )["total"] or 0
        return max(self.quantity - borrowed, 0)

    def __str__(self):
        return f"{self.code} · {self.name}"


class Loan(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "activo", "Activo"
        RETURNED = "devuelto", "Devuelto"

    class ReturnCondition(models.TextChoices):
        OPERATIVE = "operativo", "Operativo"
        MAINTENANCE = "mantenimiento", "Requiere mantenimiento"
        DAMAGED = "danado", "Dañado"

    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="docente",
        on_delete=models.PROTECT,
        related_name="loans",
    )
    equipment = models.ForeignKey(
        Equipment, verbose_name="equipo", on_delete=models.PROTECT, related_name="loans"
    )
    quantity = models.PositiveIntegerField("cantidad", default=1, validators=[MinValueValidator(1)])
    loan_date = models.DateField("fecha de préstamo", default=timezone.localdate)
    due_date = models.DateField("fecha de devolución")
    returned_at = models.DateTimeField("devuelto el", null=True, blank=True)
    status = models.CharField("estado", max_length=16, choices=Status.choices, default=Status.ACTIVE)
    return_condition = models.CharField(
        "estado al devolver",
        max_length=20,
        choices=ReturnCondition.choices,
        blank=True,
    )
    comments = models.CharField("observaciones", max_length=500, blank=True)
    created_at = models.DateTimeField("registrado el", auto_now_add=True)

    class Meta:
        ordering = ["-loan_date", "-created_at"]
        verbose_name = "préstamo"
        verbose_name_plural = "préstamos"

    @property
    def overdue_days(self):
        if self.status != self.Status.ACTIVE or self.due_date >= timezone.localdate():
            return 0
        return (timezone.localdate() - self.due_date).days

    def __str__(self):
        return f"{self.equipment.name} · {self.borrower}"
