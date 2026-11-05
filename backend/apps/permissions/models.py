from django.conf import settings
from django.db import models


class Module(models.Model):
    """
    Módulo funcional de Control de Devoluciones.
    """

    code = models.SlugField(
        "código",
        max_length=80,
        unique=True,
    )

    name = models.CharField(
        "nombre",
        max_length=120,
    )

    description = models.TextField(
        "descripción",
        blank=True,
    )

    is_active = models.BooleanField(
        "módulo activo",
        default=True,
    )

    display_order = models.PositiveSmallIntegerField(
        "orden de visualización",
        default=0,
    )

    class Meta:
        verbose_name = "módulo"
        verbose_name_plural = "módulos"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class ModulePermission(models.Model):
    """
    Acción que puede autorizarse dentro de un módulo.
    """

    module = models.ForeignKey(
        Module,
        on_delete=models.PROTECT,
        related_name="permissions",
        verbose_name="módulo",
    )

    code = models.SlugField(
        "código",
        max_length=100,
    )

    name = models.CharField(
        "nombre",
        max_length=120,
    )

    description = models.TextField(
        "descripción",
        blank=True,
    )

    class Meta:
        verbose_name = "permiso de módulo"
        verbose_name_plural = "permisos de módulo"
        ordering = ["module__display_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["module", "code"],
                name="unique_permission_code_per_module",
            ),
        ]

    def __str__(self):
        return f"{self.module.name}: {self.name}"


class Role(models.Model):
    """
    Plantilla reutilizable de permisos.
    """

    code = models.SlugField(
        "código",
        max_length=80,
        unique=True,
    )

    name = models.CharField(
        "nombre",
        max_length=120,
    )

    description = models.TextField(
        "descripción",
        blank=True,
    )

    permissions = models.ManyToManyField(
        ModulePermission,
        blank=True,
        related_name="roles",
        verbose_name="permisos heredados",
    )

    is_active = models.BooleanField(
        "rol activo",
        default=True,
    )

    is_system_role = models.BooleanField(
        "rol del sistema",
        default=False,
        help_text="Identifica roles protegidos del sistema.",
    )

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserPermissionOverride(models.Model):
    """
    Excepción individual sobre un permiso heredado del rol.

    allowed=True concede el permiso.
    allowed=False revoca el permiso.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="permission_overrides",
        verbose_name="usuario",
    )

    permission = models.ForeignKey(
        ModulePermission,
        on_delete=models.PROTECT,
        related_name="user_overrides",
        verbose_name="permiso",
    )

    allowed = models.BooleanField(
        "permitido",
    )

    reason = models.CharField(
        "motivo del cambio",
        max_length=255,
    )

    created_at = models.DateTimeField(
        "fecha de creación",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "fecha de actualización",
        auto_now=True,
    )

    class Meta:
        verbose_name = "excepción individual de permiso"
        verbose_name_plural = "excepciones individuales de permisos"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "permission"],
                name="unique_user_permission_override",
            ),
        ]
        ordering = ["user__username", "permission__module__name"]

    def __str__(self):
        state = "permitido" if self.allowed else "revocado"
        return (
            f"{self.user.username}: "
            f"{self.permission} ({state})"
        )

class PermissionAuditLog(models.Model):
    """
    Historial inmutable de cambios administrativos de permisos.
    """

    ACTION_CHOICES = [
        ("grant", "Permiso concedido"),
        ("revoke", "Permiso revocado"),
        ("reset", "Excepción eliminada"),
        ("module_enabled", "Módulo habilitado"),
        ("module_disabled", "Módulo deshabilitado"),
        ("role_changed", "Rol modificado"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="permission_audit_actions",
        verbose_name="administrador responsable",
    )

    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="permission_audit_events",
        verbose_name="usuario afectado",
    )

    permission = models.ForeignKey(
        ModulePermission,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="permiso afectado",
    )

    module = models.ForeignKey(
        Module,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="módulo afectado",
    )

    action = models.CharField(
        "acción",
        max_length=30,
        choices=ACTION_CHOICES,
    )

    previous_value = models.JSONField(
        "estado anterior",
        null=True,
        blank=True,
    )

    new_value = models.JSONField(
        "estado nuevo",
        null=True,
        blank=True,
    )

    reason = models.CharField(
        "motivo",
        max_length=255,
    )

    created_at = models.DateTimeField(
        "fecha y hora",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "registro de auditoría de permisos"
        verbose_name_plural = "registros de auditoría de permisos"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.get_action_display()} — "
            f"{self.created_at:%Y-%m-%d %H:%M}"
        )