from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class InstitutionalLoginTests(TestCase):
    def test_institutional_email_can_be_used_to_sign_in(self):
        user = User.objects.create_user(
            username="docente-login",
            email="docente-login@uncp.edu.pe",
            password="PrestamosUNCP2026!",
            role=User.Role.DOCENTE,
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": user.email, "password": "PrestamosUNCP2026!"},
        )
        self.assertRedirects(response, reverse("core:dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_inactive_accounts_cannot_sign_in(self):
        User.objects.create_user(
            username="inactive",
            email="inactive@uncp.edu.pe",
            password="PrestamosUNCP2026!",
            role=User.Role.DOCENTE,
            is_active=False,
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "inactive@uncp.edu.pe", "password": "PrestamosUNCP2026!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
