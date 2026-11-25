from django.urls import path

from accounts import views

app_name = "accounts"
urlpatterns = [
    path("login/", views.InstitutionalLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
]
