from django.contrib import messages
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from core.decorators import roles_required
from core.models import record_audit
from loans.forms import LoanForm, ReturnForm
from loans.models import Equipment, Loan


def equipment_list(request):
    all_equipment = Equipment.objects.annotate(
        active_loan_total=Coalesce(
            Sum("loans__quantity", filter=Q(loans__status=Loan.Status.ACTIVE)),
            0,
        )
    )
    equipment = all_equipment
    query = request.GET.get("q", "").strip()
    status = request.GET.get("estado", "")
    laboratory = request.GET.get("laboratorio", "")
    category = request.GET.get("categoria", "")
    if query:
        equipment = equipment.filter(
            Q(code__icontains=query) | Q(name__icontains=query) | Q(category__icontains=query)
        )
    if status in Equipment.Status.values:
        equipment = equipment.filter(status=status)
    if laboratory:
        equipment = equipment.filter(laboratory=laboratory)
    if category:
        equipment = equipment.filter(category=category)
    available_units = Equipment.objects.filter(status=Equipment.Status.OPERATIVE).annotate(
        active_loan_total=Coalesce(
            Sum("loans__quantity", filter=Q(loans__status=Loan.Status.ACTIVE)),
            0,
        )
    ).aggregate(total=Coalesce(Sum(F("quantity") - F("active_loan_total")), 0))["total"]
    context = {
        "equipment": equipment,
        "query": query,
        "selected_status": status,
        "selected_laboratory": laboratory,
        "selected_category": category,
        "available_units": available_units,
        "equipment_type_count": Equipment.objects.count(),
        "laboratories": Equipment.objects.order_by().values_list("laboratory", flat=True).distinct(),
        "categories": Equipment.objects.order_by().values_list("category", flat=True).distinct(),
    }
    return render(request, "loans/equipment_list.html", context)


@roles_required(User.Role.ADMIN, User.Role.DOCENTE, User.Role.ASISTENTE)
def loan_list(request):
    loans = Loan.objects.select_related("borrower", "equipment")
    if request.user.role == User.Role.DOCENTE:
        loans = loans.filter(borrower=request.user)
    status = request.GET.get("estado", "")
    if status in Loan.Status.values:
        loans = loans.filter(status=status)
    return render(request, "loans/loan_list.html", {"loans": loans, "selected_status": status})


@roles_required(User.Role.ADMIN, User.Role.DOCENTE, User.Role.ASISTENTE)
def loan_create(request):
    borrower = request.user
    if request.method == "POST":
        form = LoanForm(request.POST, borrower=borrower)
        if form.is_valid():
            try:
                with transaction.atomic():
                    if borrower.role == User.Role.DOCENTE:
                        User.objects.select_for_update().get(pk=borrower.pk)
                        active_count = Loan.objects.filter(
                            borrower=borrower,
                            status=Loan.Status.ACTIVE,
                        ).count()
                        if active_count >= 3:
                            form.add_error(None, "No puedes tener más de 3 préstamos activos.")
                    equipment = Equipment.objects.select_for_update().get(
                        pk=form.cleaned_data["equipment"].pk
                    )
                    if not form.errors:
                        if equipment.available_quantity < form.cleaned_data["quantity"]:
                            form.add_error("quantity", "El inventario cambió; actualiza la cantidad disponible.")
                        else:
                            loan = form.save(commit=False)
                            loan.equipment = equipment
                            loan.borrower = borrower
                            loan.save()
                            record_audit(
                                request,
                                "prestamo_registrado",
                                f"préstamo={loan.pk}; equipo={equipment.code}",
                            )
                            messages.success(request, "La solicitud de préstamo quedó registrada.")
                            return redirect("loans:loan_list")
            except Equipment.DoesNotExist as exc:
                raise Http404("El equipo ya no existe.") from exc
    else:
        form = LoanForm(
            borrower=borrower,
            initial={"loan_date": timezone.localdate(), "equipment": request.GET.get("equipo")},
        )
    return render(request, "loans/loan_form.html", {"form": form})


@roles_required(User.Role.ASISTENTE)
def loan_return(request, loan_id):
    loan = get_object_or_404(Loan.objects.select_related("equipment", "borrower"), pk=loan_id)
    if loan.status != Loan.Status.ACTIVE:
        messages.info(request, "Este préstamo ya fue devuelto.")
        return redirect("loans:loan_list")
    if request.method == "POST":
        form = ReturnForm(request.POST)
        if form.is_valid():
            loan.status = Loan.Status.RETURNED
            from django.utils import timezone

            loan.returned_at = timezone.now()
            loan.return_condition = form.cleaned_data["return_condition"]
            if form.cleaned_data["comments"]:
                loan.comments = f"{loan.comments}\nDevolución: {form.cleaned_data['comments']}".strip()
            loan.save(update_fields=["status", "returned_at", "return_condition", "comments"])
            if loan.return_condition != Loan.ReturnCondition.OPERATIVE:
                loan.equipment.status = Equipment.Status.MAINTENANCE
                loan.equipment.save(update_fields=["status"])
            record_audit(request, "devolucion_registrada", f"préstamo={loan.pk}; condición={loan.return_condition}")
            messages.success(request, "La devolución quedó registrada.")
            return redirect("loans:loan_list")
    else:
        form = ReturnForm()
    return render(request, "loans/return_form.html", {"form": form, "loan": loan})


@roles_required(User.Role.ADMIN)
def loan_reports(request):
    today = timezone.localdate()
    return render(
        request,
        "loans/reports.html",
        {
            "loan_count": Loan.objects.count(),
            "active_count": Loan.objects.filter(status=Loan.Status.ACTIVE).count(),
            "overdue_count": Loan.objects.filter(
                status=Loan.Status.ACTIVE, due_date__lt=today
            ).count(),
            "by_laboratory": Loan.objects.values("equipment__laboratory").annotate(
                loans=Count("id"),
                units=Sum("quantity"),
                overdue=Count(
                    "id",
                    filter=Q(status=Loan.Status.ACTIVE, due_date__lt=today),
                ),
            ).order_by("equipment__laboratory"),
            "by_borrower": Loan.objects.values(
                "borrower__first_name", "borrower__last_name", "borrower__username"
            ).annotate(
                loans=Count("id"),
                active=Count("id", filter=Q(status=Loan.Status.ACTIVE)),
            ).order_by("-loans")[:10],
        },
    )
