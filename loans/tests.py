from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from core.models import AuditEvent
from loans.forms import LoanForm
from loans.models import Equipment, Loan


class LoanFormTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="docente-test",
            email="docente-test@uncp.edu.pe",
            password="PrestamosUNCP2026!",
            role=User.Role.DOCENTE,
        )
        self.equipment = Equipment.objects.create(
            code="TEST-001",
            name="Laptop de prueba",
            category="Laptop",
            laboratory="Laboratorio 1",
            quantity=4,
        )
        self.tomorrow = timezone.localdate() + timedelta(days=1)

    def make_form(self, **overrides):
        data = {
            "equipment": self.equipment.pk,
            "quantity": 1,
            "loan_date": timezone.localdate().isoformat(),
            "due_date": self.tomorrow.isoformat(),
            "comments": "",
        }
        data.update(overrides)
        return LoanForm(data, borrower=self.teacher)

    def test_return_date_must_be_after_loan_date(self):
        form = self.make_form(due_date=timezone.localdate().isoformat())
        self.assertFalse(form.is_valid())
        self.assertIn("due_date", form.errors)

    def test_teacher_cannot_exceed_three_active_loans(self):
        for index in range(3):
            Loan.objects.create(
                borrower=self.teacher,
                equipment=self.equipment,
                loan_date=timezone.localdate(),
                due_date=self.tomorrow,
                quantity=1,
            )
        form = self.make_form()
        self.assertFalse(form.is_valid())
        self.assertIn("No puedes tener más de 3 préstamos activos.", form.non_field_errors())

    def test_requested_quantity_cannot_exceed_stock(self):
        self.equipment.quantity = 1
        self.equipment.save(update_fields=["quantity"])
        Loan.objects.create(
            borrower=self.teacher,
            equipment=self.equipment,
            loan_date=timezone.localdate(),
            due_date=self.tomorrow,
            quantity=1,
        )
        form = self.make_form()
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_comments_strip_html_tags(self):
        form = self.make_form(comments="<script>alert(1)</script> Necesito el equipo")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["comments"], "alert(1) Necesito el equipo")


class LoanReturnViewTests(TestCase):
    def setUp(self):
        self.assistant = User.objects.create_user(
            username="asistente-test",
            email="asistente-test@uncp.edu.pe",
            password="PrestamosUNCP2026!",
            role=User.Role.ASISTENTE,
        )
        self.teacher = User.objects.create_user(
            username="docente-test",
            email="docente-test@uncp.edu.pe",
            password="PrestamosUNCP2026!",
            role=User.Role.DOCENTE,
        )
        equipment = Equipment.objects.create(
            code="TEST-002",
            name="Proyector de prueba",
            category="Proyector",
            laboratory="Laboratorio 2",
            quantity=2,
        )
        self.loan = Loan.objects.create(
            borrower=self.teacher,
            equipment=equipment,
            loan_date=timezone.localdate(),
            due_date=timezone.localdate() + timedelta(days=3),
        )
        self.url = reverse("loans:loan_return", args=[self.loan.pk])

    def test_only_assistant_can_register_a_return(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            self.url,
            {"return_condition": Loan.ReturnCondition.OPERATIVE, "comments": ""},
        )
        self.assertEqual(response.status_code, 403)
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.status, Loan.Status.ACTIVE)

    def test_assistant_return_is_audited(self):
        self.client.force_login(self.assistant)
        response = self.client.post(
            self.url,
            {"return_condition": Loan.ReturnCondition.OPERATIVE, "comments": "Sin observaciones"},
        )
        self.assertRedirects(response, reverse("loans:loan_list"))
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.status, Loan.Status.RETURNED)
        self.assertTrue(AuditEvent.objects.filter(action="devolucion_registrada").exists())


class PublicCatalogTests(TestCase):
    def test_guest_can_read_the_public_equipment_catalog(self):
        Equipment.objects.create(
            code="PUBLIC-001",
            name="Equipo visible",
            category="Prueba",
            laboratory="Laboratorio 1",
            quantity=1,
        )
        response = self.client.get(reverse("loans:equipment_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Equipo visible")
        self.assertContains(response, "Ingresar")

    def test_catalog_filters_by_category(self):
        Equipment.objects.create(
            code="FILTER-001",
            name="Proyector para filtrar",
            category="Proyector",
            laboratory="Laboratorio 2",
            quantity=1,
        )
        Equipment.objects.create(
            code="FILTER-002",
            name="Router fuera del filtro",
            category="Redes",
            laboratory="Laboratorio 4",
            quantity=1,
        )

        response = self.client.get(reverse("loans:equipment_list"), {"categoria": "Proyector"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proyector para filtrar")
        self.assertNotContains(response, "Router fuera del filtro")
