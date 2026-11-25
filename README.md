# Sistema de gestión de préstamos de equipos de laboratorio · UNCP

Aplicación web en Django para consultar el inventario de los laboratorios de la Universidad Nacional del Centro del Perú, solicitar equipos y registrar devoluciones. Esta entrega contiene **solamente el caso 1** de la práctica.

Los nombres, códigos, cantidades, cuentas y movimientos de `seed_demo` son datos ficticios. Las fotografías del catálogo son ilustrativas y no corresponden a los equipos concretos del inventario.

## Funcionalidades

- Catálogo público con búsqueda por código, nombre o categoría y filtros por laboratorio, categoría y estado.
- Disponibilidad calculada a partir de unidades registradas menos préstamos activos.
- Solicitudes autenticadas con validación de stock, fechas y un máximo de tres préstamos activos por docente.
- Historial de préstamos. Cada docente solo ve sus solicitudes; el personal autorizado consulta el registro general.
- Devolución registrada por un asistente, incluida la condición del equipo y su pase a mantenimiento cuando corresponde.
- Reportes de actividad por laboratorio y docente, vencimientos y préstamos activos.
- Django Admin personalizado para inventario, préstamos, usuarios y auditoría.
- Diseño responsive en español, con navegación clara para escritorio y móvil.

## Organización

```text
config/                 Ajustes, middleware y rutas Django
accounts/               Usuario institucional, autenticación, roles y grupos demo
core/                   Panel de préstamos, permisos comunes y auditoría
loans/                  Inventario, préstamos, devoluciones, reportes y Admin
templates/
  accounts/             Inicio de sesión
  core/                 Panel y errores de acceso
  loans/                Catálogo, solicitudes, historial y reportes
  partials/             Campos reutilizables de formularios
static/
  css/app.css           Estilos responsive del sistema
  js/app.js             Accesibilidad, mensajes y entradas de contenido
  images/               Fotografías referenciales con créditos
manage.py               Comandos de Django
requirements.txt        Dependencia de Django
```

`accounts.User` contiene las tres funciones del caso: administrador de laboratorio, docente y asistente. `core.AuditEvent` conserva la trazabilidad de acciones relevantes.

Al migrar una base de la versión combinada anterior, la migración del caso 1 elimina las tablas y los registros de auditoría del caso de asistencia/permisos, además de las cuentas demo antiguas indicadas en la migración. Es una limpieza irreversible; conserva una copia de `db.sqlite3` antes de migrar si necesitas guardar información de esa versión.

## Tecnologías

- Python 3.10 o posterior.
- Django 5.2.
- SQLite para desarrollo y evaluación local.
- HTML de Django, CSS y JavaScript sin frameworks adicionales de frontend.

## Instalación en Windows

Abre PowerShell en la carpeta del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

$env:DJANGO_SECRET_KEY = "reemplaza-esta-clave-en-tu-entorno"
$env:DJANGO_DEBUG = "True"
$env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost"

python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abre <http://127.0.0.1:8000/> para ver el catálogo de equipos. El acceso al sistema es <http://127.0.0.1:8000/cuentas/login/> y la administración está en <http://127.0.0.1:8000/admin/>.

Si el puerto 8000 está ocupado, inicia el servidor en otro puerto:

```powershell
python manage.py runserver 127.0.0.1:8010
```

## Cuentas de demostración

El comando `seed_demo` crea o actualiza las siguientes cuentas. La contraseña inicial compartida es `PrestamosUNCP2026!`.

| Usuario | Rol | Correo |
|---|---|---|
| `lab-admin` | Administrador de laboratorio | `lab-admin@uncp.edu.pe` |
| `docente-01` | Docente | `docente-01@uncp.edu.pe` |
| `docente-02` | Docente | `docente-02@uncp.edu.pe` |
| `asistente` | Asistente de laboratorio | `asistente@uncp.edu.pe` |

El catálogo público no requiere autenticación. Para solicitar un préstamo, ingresa como `docente-01` o `docente-02`; las devoluciones las registra `asistente`. `lab-admin` puede ingresar a Django Admin y consultar reportes.

`seed_demo` prepara diez equipos y hasta quince préstamos de muestra. También retira de la base local las cuentas y grupos demo del anterior caso de asistencia/permisos. No elimina las cuentas de préstamos ni su historial. No ejecutes el comando con datos institucionales reales sin revisar primero su efecto.

Para cambiar la contraseña compartida de las cuentas demo:

```powershell
python manage.py seed_demo --password "OtraClaveLocal2026!"
```

## Flujo de préstamo

1. Revisa disponibilidad, laboratorio y estado del equipo en el catálogo.
2. Ingresa con la cuenta institucional de docente.
3. Selecciona un equipo operativo, cantidad y fechas de préstamo/devolución.
4. Consulta el estado de la solicitud desde **Préstamos**.
5. El asistente registra la devolución y la condición del equipo.

El sistema acepta un máximo de tres préstamos activos por docente. Las fechas deben ser coherentes y la solicitud vuelve a validar el stock al guardarse para reducir conflictos por solicitudes simultáneas. Las observaciones se limpian de etiquetas HTML antes de almacenarse.

## Roles y autorización

| Rol | Acciones |
|---|---|
| Invitado | Consulta y filtra el inventario público |
| Docente | Solicita equipos y consulta su propio historial |
| Asistente de laboratorio | Consulta préstamos y registra devoluciones |
| Administrador de laboratorio | Gestiona equipos y préstamos en Django Admin, revisa reportes y auditoría |

Los permisos se verifican en el servidor; ocultar un botón en la interfaz no sustituye la autorización. Las cuentas deben tener el grupo correspondiente para usar los permisos administrativos de Django.

## Inventario, préstamos y reportes

Cada equipo registra código patrimonial único, nombre, marca, modelo, categoría, estado, laboratorio, unidades y última fecha de mantenimiento. El inventario se puede buscar por código, nombre o categoría.

La disponibilidad se calcula con las unidades en préstamos activos. El administrador puede registrar altas, cambios y bajas; marcar equipos en mantenimiento; consultar filtros y búsquedas; y revisar reportes por laboratorio, docente y vencimiento.

El asistente cierra un préstamo indicando si el equipo volvió operativo, requiere mantenimiento o está dañado. Toda solicitud y devolución queda registrada en el historial; las acciones administrativas y devoluciones relevantes generan auditoría.

## Seguridad y auditoría

- Formularios POST protegidos con CSRF.
- Contraseñas almacenadas con los hashers de Django.
- Sesión `HttpOnly`, `SameSite=Lax` y vencimiento por inactividad a los 30 minutos.
- Validación de roles y propiedad del historial en el servidor.
- Revalidación de inventario dentro de una transacción al solicitar equipos.
- `AccessControlMiddleware` bloquea cuentas desactivadas, expira sesiones y registra intentos no autorizados.
- `core.AuditEvent` guarda actor, fecha, IP, acción y ruta. Solo el administrador de laboratorio puede consultar eventos desde Django Admin.
- El correo de recordatorio usa el backend de consola; no se envía correo real.

Para HTTPS, define `DJANGO_SECURE_COOKIES=True`. Antes de desplegar, configura una clave privada en `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, hosts permitidos, HTTPS y un servicio de correo.

## Pruebas y comprobaciones

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

La suite cubre validaciones de préstamo, stock, límite por docente, sanitización de observaciones, permisos para devolver equipos, auditoría, catálogo, sesión, inicio de sesión y panel.

## Evidencias para la entrega

1. Muestra el catálogo y aplica búsqueda y filtros de laboratorio/categoría.
2. Como docente, intenta solicitar más unidades de las disponibles y guarda una captura del error de validación.
3. Registra una solicitud válida y enseña el préstamo en el historial.
4. Como asistente, registra la devolución y captura su condición.
5. Como `lab-admin`, muestra equipos, acciones administrativas, reportes y auditoría en `/admin/`.
6. Prueba que un docente no pueda consultar el historial de otro rol.
7. Muestra el proyecto solo con el caso 1: no incluye rutas, pantallas ni lógica de asistencia/permisos.

## Créditos de las fotografías

Las imágenes locales del catálogo sirven únicamente como referencias visuales; no representan los activos específicos de la UNCP.

- “ARDX - Arduino Experimentation Kit (Inside the box)” — oomlout, [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/), [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:ARDX_-_Arduino_Experimentation_Kit_(Inside_the_box).jpg).
- “Microscope” — Homedust, [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/), [Flickr](https://www.flickr.com/photos/159630537@N08/42342826561).
- “Macbook Laptop” — Negative Space, [CC0](https://creativecommons.org/publicdomain/zero/1.0/), [StockSnap](https://stocksnap.io/photo/macbook-laptop-UNB7V2H5L4).
- “OHP-sch” — mailer_diablo, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:OHP-sch.JPG).
