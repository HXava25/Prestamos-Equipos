from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class DashboardTests(TestCase):
    def test_anonymous_user_can_open_admin_login(self):
        response = self.client.get(reverse("admin:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "name=\"username\"")

    def test_homepage_opens_the_public_equipment_catalog(self):
        response = self.client.get(reverse("core:home"))

        self.assertRedirects(response, reverse("loans:equipment_list"))

    def test_workforce_case_routes_are_not_installed(self):
        response = self.client.get("/personal/asistencia/")

        self.assertEqual(response.status_code, 404)

    def test_dashboard_renders_for_authenticated_user(self):
        user = User.objects.create_user(
            username="lab-docente",
            email="lab-docente@uncp.edu.pe",
            password="PrestamosUNCP2026!",
            role=User.Role.DOCENTE,
            first_name="Lucía",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hola, Lucía.")
        self.assertContains(response, "Próximas devoluciones")

    def test_dashboard_rejects_accounts_with_roles_from_the_removed_case(self):
        user = User.objects.create_user(
            username="former-employee",
            email="former-employee@example.com",
            password="test-password",
            role="empleado",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 403)
