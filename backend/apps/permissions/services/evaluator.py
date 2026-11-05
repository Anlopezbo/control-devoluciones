from django.core.exceptions import ObjectDoesNotExist

from apps.permissions.models import (
    Module,
    ModulePermission,
    UserPermissionOverride,
)


def get_effective_permissions(user):
    """
    Devuelve los códigos de los permisos efectivos de un usuario.

    Reglas:
    1. Los permisos del rol constituyen la base.
    2. Las excepciones individuales prevalecen sobre el rol.
    3. Los permisos de módulos inactivos no se conceden.
    4. Los usuarios inactivos no tienen permisos funcionales.

    El resultado contiene códigos con formato:
        modulo.codigo_permiso
    """

    if not user.is_authenticated or not user.is_active:
        return set()

    # Obtener el rol asignado, si existe.
    try:
        role = user.role
    except ObjectDoesNotExist:
        role = None

    effective_permissions = set()

    # 1. Cargar los permisos heredados del rol.
    if role and role.is_active:
        inherited_permissions = (
            role.permissions
            .filter(module__is_active=True)
            .values_list("module__code", "code")
        )

        effective_permissions = {
            f"{module_code}.{permission_code}"
            for module_code, permission_code in inherited_permissions
        }

    # 2. Aplicar las excepciones individuales.
    overrides = (
        UserPermissionOverride.objects
        .filter(
            user=user,
            permission__module__is_active=True,
        )
        .values_list(
            "permission__module__code",
            "permission__code",
            "allowed",
        )
    )

    for module_code, permission_code, allowed in overrides:
        permission_code_full = (
            f"{module_code}.{permission_code}"
        )

        if allowed:
            effective_permissions.add(permission_code_full)
        else:
            effective_permissions.discard(permission_code_full)

    return effective_permissions


def user_has_permission(user, permission_code):
    """
    Comprueba si el usuario tiene un permiso funcional específico.

    Ejemplo:
        user_has_permission(user, "liquidacion.view")
    """

    return permission_code in get_effective_permissions(user)


def user_can_access_module(user, module_code):
    """
    Comprueba si el usuario puede acceder a un módulo.

    Un módulo solo es accesible si:
    - El usuario está autenticado y activo.
    - El módulo existe y está activo.
    - El usuario tiene al menos un permiso efectivo en él.
    """

    if not user.is_authenticated or not user.is_active:
        return False

    module_is_active = Module.objects.filter(
        code=module_code,
        is_active=True,
    ).exists()

    if not module_is_active:
        return False

    prefix = f"{module_code}."

    return any(
        permission.startswith(prefix)
        for permission in get_effective_permissions(user)
    )