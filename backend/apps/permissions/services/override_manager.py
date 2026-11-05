from django.core.exceptions import ValidationError
from django.db import transaction

from apps.permissions.models import (
    ModulePermission,
    PermissionAuditLog,
    UserPermissionOverride,
)


def _validate_actor(actor):
    """
    Verifica que la operación tenga un administrador responsable.
    """
    if not actor or not actor.is_authenticated:
        raise ValidationError(
            "La operación requiere un administrador autenticado."
        )

    if not actor.is_active or not actor.is_staff:
        raise ValidationError(
            "El usuario no está autorizado para administrar permisos."
        )


def _validate_reason(reason):
    """
    Exige un motivo para mantener la trazabilidad administrativa.
    """
    reason = (reason or "").strip()

    if not reason:
        raise ValidationError(
            "Debes indicar el motivo del cambio de permisos."
        )

    if len(reason) > 255:
        raise ValidationError(
            "El motivo no puede superar los 255 caracteres."
        )

    return reason


@transaction.atomic
def set_user_permission_override(
    *,
    actor,
    target_user,
    permission,
    allowed,
    reason,
):
    """
    Crea o actualiza una excepción individual y registra su auditoría.

    allowed=True concede el permiso.
    allowed=False revoca el permiso.

    Si el estado no cambia, no crea un registro de auditoría adicional.
    """
    _validate_actor(actor)
    reason = _validate_reason(reason)

    if not target_user.is_active:
        raise ValidationError(
            "No se pueden modificar permisos de un usuario inactivo."
        )

    if not isinstance(permission, ModulePermission):
        raise ValidationError(
            "Debes proporcionar un permiso de módulo válido."
        )

    if not permission.module.is_active:
        raise ValidationError(
            "No se pueden asignar excepciones a un módulo inactivo."
        )

    if not isinstance(allowed, bool):
        raise ValidationError(
            "El estado del permiso debe ser verdadero o falso."
        )

    override = (
        UserPermissionOverride.objects
        .select_for_update()
        .filter(
            user=target_user,
            permission=permission,
        )
        .first()
    )

    if override and override.allowed == allowed:
        return override

    previous_value = {
        "override_exists": override is not None,
        "allowed": override.allowed if override else None,
    }

    if override:
        override.allowed = allowed
        override.reason = reason
        override.save(
            update_fields=["allowed", "reason", "updated_at"]
        )
    else:
        override = UserPermissionOverride.objects.create(
            user=target_user,
            permission=permission,
            allowed=allowed,
            reason=reason,
        )

    action = "grant" if allowed else "revoke"

    PermissionAuditLog.objects.create(
        actor=actor,
        target_user=target_user,
        permission=permission,
        module=permission.module,
        action=action,
        previous_value=previous_value,
        new_value={
            "override_exists": True,
            "allowed": allowed,
        },
        reason=reason,
    )

    return override


@transaction.atomic
def reset_user_permission_override(
    *,
    actor,
    target_user,
    permission,
    reason,
):
    """
    Elimina una excepción individual y registra la operación.

    Al eliminarla, el usuario vuelve a heredar el permiso de su rol.
    """
    _validate_actor(actor)
    reason = _validate_reason(reason)

    override = (
        UserPermissionOverride.objects
        .select_for_update()
        .filter(
            user=target_user,
            permission=permission,
        )
        .first()
    )

    if override is None:
        return False

    previous_value = {
        "override_exists": True,
        "allowed": override.allowed,
    }

    PermissionAuditLog.objects.create(
        actor=actor,
        target_user=target_user,
        permission=permission,
        module=permission.module,
        action="reset",
        previous_value=previous_value,
        new_value={
            "override_exists": False,
            "allowed": None,
        },
        reason=reason,
    )

    override.delete()

    return True