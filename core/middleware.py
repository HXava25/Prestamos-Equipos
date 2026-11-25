import logging
import time

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger("audit")


class AccessControlMiddleware:
    """Apply account, idle-session, reminder and sensitive-access policies."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        now = int(time.time())
        if user and user.is_authenticated:
            if not user.is_active:
                logger.warning("blocked_inactive_user user=%s path=%s", user.get_username(), request.path)
                logout(request)
                messages.error(request, "La cuenta está desactivada. Contacta con administración.")
                return redirect("accounts:login")

            timeout = user.idle_timeout_seconds
            last_activity = request.session.get("last_activity")
            if last_activity and now - int(last_activity) > timeout:
                logger.info("session_timeout user=%s role=%s", user.get_username(), user.role)
                logout(request)
                messages.warning(request, "Tu sesión expiró por inactividad. Vuelve a ingresar.")
                return redirect("accounts:login")

            request.session["last_activity"] = now
            if request.path == reverse("core:dashboard"):
                self._set_reminders(request)

        response = self.get_response(request)
        if response.status_code == 403:
            logger.warning(
                "unauthorized_access user=%s path=%s ip=%s",
                user.get_username() if user and user.is_authenticated else "anonymous",
                request.path,
                request.META.get("REMOTE_ADDR", "unknown"),
            )
        return response

    @staticmethod
    def _set_reminders(request):
        user = request.user
        if user.role == user.Role.DOCENTE:
            from loans.models import Loan

            overdue = Loan.objects.filter(
                borrower=user, status=Loan.Status.ACTIVE, due_date__lt=timezone.localdate()
            ).count()
            request.session["overdue_loan_count"] = overdue
            if overdue and not request.session.get("overdue_reminder_shown"):
                messages.warning(request, f"Tienes {overdue} préstamo(s) vencido(s). Coordina la devolución.")
                request.session["overdue_reminder_shown"] = True
            elif not overdue:
                request.session.pop("overdue_reminder_shown", None)
