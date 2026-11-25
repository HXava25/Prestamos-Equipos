from django import forms
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.html import strip_tags

from accounts.models import User
from loans.models import Equipment, Loan


class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ("equipment", "quantity", "loan_date", "due_date", "comments")
        widgets = {
            "loan_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "due_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "comments": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
        }

    def __init__(self, *args, borrower=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.borrower = borrower
        self.fields["equipment"].queryset = Equipment.objects.filter(
            status=Equipment.Status.OPERATIVE
        ).annotate(
            active_loan_total=Coalesce(
                Sum("loans__quantity", filter=Q(loans__status=Loan.Status.ACTIVE)),
                Value(0),
            )
        )
        self.fields["equipment"].label_from_instance = lambda equipment: (
            f"{equipment.name} · {equipment.laboratory} · disponibles: {equipment.available_quantity}"
        )
        self.fields["comments"].required = False

    def clean_due_date(self):
        due_date = self.cleaned_data["due_date"]
        loan_date = self.cleaned_data.get("loan_date")
        if loan_date and due_date <= loan_date:
            raise forms.ValidationError("La fecha de devolución debe ser posterior al préstamo.")
        return due_date

    def clean_comments(self):
        return strip_tags(self.cleaned_data.get("comments", "")).strip()

    def clean(self):
        cleaned = super().clean()
        equipment = cleaned.get("equipment")
        quantity = cleaned.get("quantity")
        borrower = self.borrower
        if borrower and borrower.role == User.Role.DOCENTE:
            active_count = Loan.objects.filter(
                borrower=borrower, status=Loan.Status.ACTIVE
            ).count()
            if active_count >= 3:
                raise forms.ValidationError("No puedes tener más de 3 préstamos activos.")
        if equipment and equipment.status != Equipment.Status.OPERATIVE:
            self.add_error("equipment", "Solo se pueden solicitar equipos operativos.")
        if equipment and quantity:
            available = equipment.available_quantity
            if quantity > available:
                self.add_error(
                    "quantity",
                    f"Solo hay {available} unidad(es) disponibles de este equipo.",
                )
        return cleaned


class ReturnForm(forms.Form):
    return_condition = forms.ChoiceField(
        label="Estado del equipo al devolver",
        choices=Loan.ReturnCondition.choices,
    )
    comments = forms.CharField(
        label="Observaciones",
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean_comments(self):
        return strip_tags(self.cleaned_data.get("comments", "")).strip()
