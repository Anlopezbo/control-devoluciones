from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions.api.permissions import HasModulePermission


class PermissionCheckView(APIView):
    """
    Endpoint temporal para comprobar los permisos efectivos.
    """

    permission_classes = [HasModulePermission]
    required_permission = "liquidacion.view"

    def get(self, request):
        return Response(
            {
                "ok": True,
                "message": (
                    "Tienes permiso para consultar liquidaciones."
                ),
                "permission": self.required_permission,
            }
        )