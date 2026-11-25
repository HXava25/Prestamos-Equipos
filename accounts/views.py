import logging
import time

from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy

from accounts.forms import InstitutionalLoginForm

logger = logging.getLogger("audit")


class InstitutionalLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = InstitutionalLoginForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        username = form.cleaned_data.get("username", "unknown")
        logger.warning(
            "login_failed username=%s ip=%s",
            username,
            self.request.META.get("REMOTE_ADDR", "unknown"),
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session["last_activity"] = int(time.time())
        return response


def logout_view(request):
    if request.method != "POST":
        return redirect("loans:equipment_list")
    logout(request)
    return redirect(reverse_lazy("loans:equipment_list"))
