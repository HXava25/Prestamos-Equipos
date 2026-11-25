from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    action = models.CharField(max_length=80)
    detail = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "evento de auditoría"
        verbose_name_plural = "eventos de auditoría"

    def __str__(self):
        return f"{self.created_at:%d/%m/%Y %H:%M} · {self.action}"


def record_audit(request, action, detail=""):
    import logging

    logger = logging.getLogger("audit")
    user = getattr(request, "user", None)
    actor = user if user and user.is_authenticated else None
    ip_address = request.META.get("REMOTE_ADDR")
    if ip_address:
        from django.core.exceptions import ValidationError
        from django.core.validators import validate_ipv46_address

        try:
            validate_ipv46_address(ip_address)
        except ValidationError:
            ip_address = None
    AuditEvent.objects.create(
        actor=actor,
        action=action[:80],
        detail=detail[:2000],
        ip_address=ip_address or None,
        path=getattr(request, "path", "")[:255],
    )
    logger.info(
        "action=%s actor=%s ip=%s path=%s detail=%s",
        action,
        actor.get_username() if actor else "anonymous",
        ip_address or "unknown",
        getattr(request, "path", ""),
        detail,
    )
