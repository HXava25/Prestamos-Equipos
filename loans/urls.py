from django.urls import path

from loans import views

app_name = "loans"
urlpatterns = [
    path("equipos/", views.equipment_list, name="equipment_list"),
    path("", views.loan_list, name="loan_list"),
    path("solicitar/", views.loan_create, name="loan_create"),
    path("reportes/", views.loan_reports, name="reports"),
    path("<int:loan_id>/devolver/", views.loan_return, name="loan_return"),
]
