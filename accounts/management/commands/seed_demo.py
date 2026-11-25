from datetime import datetime, time, timedelta

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from loans.models import Equipment, Loan


ROLE_GROUPS = {
    User.Role.ADMIN: "Administradores de laboratorio",
    User.Role.DOCENTE: "Docentes",
    User.Role.ASISTENTE: "Asistentes de laboratorio",
}
FORMER_WORKFORCE_USERS = (
    "rrhh-admin",
    "jefe-sistemas",
    "empleado-01",
    "empleado-02",
    "empleado-03",
    "empleado-04",
    "empleado-05",
    "empleado-06",
    "empleado-07",
    "contador",
)
FORMER_WORKFORCE_GROUPS = (
    "Administradores de RRHH",
    "Jefes de área",
    "Empleados",
    "Contadores",
)


class Command(BaseCommand):
    help = "Crea las cuentas, grupos y datos demo del sistema de préstamos UNCP."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="PrestamosUNCP2026!", help="Contraseña compartida de las cuentas demo.")

    def handle(self, *args, **options):
        password = options["password"]
        self._remove_former_workforce_demo_data()
        groups = self._create_groups()
        users = self._create_users(groups, password)
        equipment = self._create_equipment()
        self._create_loans(users, equipment)
        self.stdout.write(self.style.SUCCESS(
            "Datos listos: 10 equipos y 15 préstamos de demostración. "
            f"Contraseña demo: {password}"
        ))

    def _remove_former_workforce_demo_data(self):
        User.objects.filter(username__in=FORMER_WORKFORCE_USERS).delete()
        Group.objects.filter(name__in=FORMER_WORKFORCE_GROUPS).delete()

    def _create_groups(self):
        groups = {
            role: Group.objects.get_or_create(name=name)[0]
            for role, name in ROLE_GROUPS.items()
        }
        permission_map = {
            User.Role.ADMIN: {
                "loans": {"equipment": {"view", "add", "change", "delete"}, "loan": {"view", "add", "change", "delete"}},
                "core": {"auditevent": {"view"}},
            },
            User.Role.DOCENTE: {
                "loans": {"equipment": {"view"}, "loan": {"view", "add"}},
            },
            User.Role.ASISTENTE: {
                "loans": {"equipment": {"view"}, "loan": {"view", "change"}},
            },
        }
        for role, app_models in permission_map.items():
            permissions = []
            for app_label, models in app_models.items():
                for model_name, actions in models.items():
                    content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                    permissions.extend(
                        Permission.objects.filter(
                            content_type=content_type,
                            codename__in=[f"{action}_{model_name}" for action in actions],
                        )
                    )
            groups[role].permissions.set(permissions)
        return groups

    def _create_users(self, groups, password):
        specifications = (
            ("lab-admin", "Jorge", "Vargas", User.Role.ADMIN, True),
            ("docente-01", "Lucía", "Paredes", User.Role.DOCENTE, False),
            ("docente-02", "Marco", "Salazar", User.Role.DOCENTE, False),
            ("asistente", "Rosa", "Cárdenas", User.Role.ASISTENTE, False),
        )
        users = {}
        for username, first, last, role, staff in specifications:
            email = f"{username}@uncp.edu.pe"
            user, _created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "role": role,
                    "is_staff": staff,
                },
            )
            user.email = email
            user.first_name = first
            user.last_name = last
            user.role = role
            user.is_staff = staff
            user.is_active = True
            user.set_password(password)
            user.save()
            user.groups.set([groups[role]])
            users[username] = user
        return users

    def _create_equipment(self):
        specifications = (
            ("LAB-001", "Laptop ThinkPad", "Lenovo", "E14", "Laptop", "Laboratorio 1", 6),
            ("LAB-002", "Laptop ProBook", "HP", "440 G9", "Laptop", "Laboratorio 1", 5),
            ("LAB-003", "Proyector Epson", "Epson", "X49", "Proyector", "Laboratorio 2", 3),
            ("LAB-004", "Cámara Canon", "Canon", "EOS 250D", "Cámara", "Laboratorio 2", 2),
            ("LAB-005", "Kit Arduino Uno", "Arduino", "Rev3", "Electrónica", "Laboratorio 3", 12),
            ("LAB-006", "Router inalámbrico", "TP-Link", "Archer C6", "Redes", "Laboratorio 4", 5),
            ("LAB-007", "Switch administrable", "Cisco", "CBS250", "Redes", "Laboratorio 4", 4),
            ("LAB-008", "Microscopio digital", "AmScope", "M150C", "Periférico", "Laboratorio 5", 2),
            ("LAB-009", "Tablet de dibujo", "Wacom", "One", "Periférico", "Laboratorio 2", 3),
            ("LAB-010", "Multímetro digital", "Fluke", "117", "Electrónica", "Laboratorio 3", 8),
        )
        return [
            Equipment.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "brand": brand,
                    "model_name": model,
                    "category": category,
                    "laboratory": laboratory,
                    "quantity": quantity,
                    "status": Equipment.Status.OPERATIVE,
                    "last_maintenance": timezone.localdate() - timedelta(days=index * 17 + 10),
                },
            )[0]
            for index, (code, name, brand, model, category, laboratory, quantity) in enumerate(specifications)
        ]

    def _create_loans(self, users, equipment):
        if Loan.objects.exists():
            return
        today = timezone.localdate()
        borrowers = (users["docente-01"], users["docente-02"], users["asistente"])
        for index in range(15):
            loan_date = today - timedelta(days=index * 2 + 1)
            due_date = today + timedelta(days=(index % 7) - 3)
            Loan.objects.create(
                borrower=borrowers[index % len(borrowers)],
                equipment=equipment[index % len(equipment)],
                quantity=1,
                loan_date=loan_date,
                due_date=max(due_date, loan_date + timedelta(days=1)),
                status=Loan.Status.RETURNED if index < 10 else Loan.Status.ACTIVE,
                returned_at=(
                    timezone.make_aware(datetime.combine(loan_date + timedelta(days=1), time(16, 0)))
                    if index < 10
                    else None
                ),
                return_condition=Loan.ReturnCondition.OPERATIVE if index < 10 else "",
                comments="Registro de demostración" if index % 3 == 0 else "",
            )
