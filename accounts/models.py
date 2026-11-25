from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador de laboratorio"
        DOCENTE = "docente", "Docente"
        ASISTENTE = "asistente", "Asistente de laboratorio"

    email = models.EmailField("correo institucional", unique=True)
    role = models.CharField("rol", max_length=20, choices=Role.choices, default=Role.DOCENTE)

    @property
    def idle_timeout_seconds(self):
        return 30 * 60

    @property
    def display_role(self):
        return self.get_role_display()

    def __str__(self):
        return self.get_full_name() or self.username
