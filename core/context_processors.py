from django.urls import reverse


def navigation_context(request):
    user = getattr(request, "user", None)
    role = getattr(user, "role", "")
    links = []
    if user and user.is_authenticated:
        links = [
            {"label": "Inventario", "url": reverse("loans:equipment_list")},
            {"label": "Préstamos", "url": reverse("loans:loan_list")},
        ]
        if role == "admin":
            links.append({"label": "Reportes", "url": reverse("loans:reports")})
    return {"navigation_links": links}
