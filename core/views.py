from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import User
from core.decorators import roles_required
from loans.models import Equipment, Loan


def home(request):
    return redirect("loans:equipment_list")


def permission_denied(request, exception=None):
    return render(request, "core/403.html", status=403)


@roles_required(User.Role.ADMIN, User.Role.DOCENTE, User.Role.ASISTENTE)
def dashboard(request):
    user = request.user
    today = timezone.localdate()
    active_loans = Loan.objects.filter(status=Loan.Status.ACTIVE)
    if user.role == User.Role.DOCENTE:
        active_loans = active_loans.filter(borrower=user)
    elif user.role not in {User.Role.ADMIN, User.Role.ASISTENTE}:
        active_loans = active_loans.none()

    equipment_stats = Equipment.objects.filter(status=Equipment.Status.OPERATIVE).annotate(
        active_loan_total=Coalesce(
            Sum("loans__quantity", filter=Q(loans__status=Loan.Status.ACTIVE)),
            0,
        )
    )
    context = {
        "equipment_count": Equipment.objects.aggregate(total=Coalesce(Sum("quantity"), 0))["total"],
        "available_equipment": equipment_stats.aggregate(
            total=Coalesce(Sum(F("quantity") - F("active_loan_total")), 0)
        )["total"],
        "equipment_type_count": Equipment.objects.count(),
        "loan_count": Loan.objects.count(),
        "active_loan_count": active_loans.count(),
        "overdue_count": active_loans.filter(due_date__lt=today).count(),
        "recent_loans": active_loans.select_related("borrower", "equipment").order_by("due_date")[:6],
        "low_stock": Equipment.objects.filter(status=Equipment.Status.OPERATIVE).annotate(
            active_loan_total=Coalesce(
                Sum("loans__quantity", filter=Q(loans__status=Loan.Status.ACTIVE)),
                0,
            )
        ).order_by("name")[:4],
    }
    return render(request, "core/dashboard.html", context)
