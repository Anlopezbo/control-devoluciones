from rest_framework.permissions import BasePermission

from apps.permissions.services.evaluator import (
    user_has_permission,
)


class HasModulePermission(BasePermission):
    """
    Comprueba los permisos funcionales del usuario.

    Las vistas deben declarar el permiso requerido mediante
    el atributo required_permission.

    Ejemplo:
        required_permission = "liquidacion.view"
    """

    message = "No tienes permiso para realizar esta operación."

    def has_permission(self, request, view):
        user = request.user

        # Exigir una sesión autenticada.
        if not user or not user.is_authenticated:
            return False

        # Las cuentas inactivas no pueden ejecutar operaciones.
        if not user.is_active:
            return False

        # La vista debe declarar explícitamente el permiso requerido.
        permission_code = getattr(
            view,
            "required_permission",
            None,
        )

        if not permission_code:
            # Fallar de forma segura si olvidamos configurar la vista.
            return False

        return user_has_permission(
            user,
            permission_code,
        )