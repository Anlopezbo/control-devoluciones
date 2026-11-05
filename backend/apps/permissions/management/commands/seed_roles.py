from django.core.management.base import BaseCommand
from django.db import transaction

from apps.permissions.models import Module, ModulePermission, Role


ROLE_DEFINITIONS = {
    "administrador-sistema": {
        "name": "Administrador del sistema",
        "description": (
            "Administración de usuarios, roles, permisos "
            "y configuración general del sistema."
        ),
        "is_system_role": True,
        "permission_codes": "__ALL__",
    },
    "coordinador-devoluciones": {
        "name": "Coordinador de devoluciones",
        "description": (
            "Supervisión de recepción, auditoría, "
            "conciliación y liquidación."
        ),
        "is_system_role": True,
        "permission_codes": [
            "dashboard.view",
            "sorteos.view",
            "sorteos.create",
            "sorteos.change",
            "sorteos.activate",
            "sorteos.close",
            "mezcla.view",
            "mezcla.upload",
            "mezcla.validate",
            "mezcla.export",
            "devolucion-electronica.view",
            "devolucion-electronica.upload",
            "devolucion-electronica.validate",
            "devolucion-electronica.export",
            "recepcion.view",
            "recepcion.create",
            "recepcion.change",
            "cajas.view",
            "cajas.create",
            "cajas.change",
            "auditoria.view",
            "auditoria.scan",
            "auditoria.validate",
            "auditoria.close",
            "inconsistencias.view",
            "inconsistencias.create",
            "inconsistencias.resolve",
            "inconsistencias.export",
            "liquidacion.view",
            "liquidacion.create",
            "liquidacion.change",
            "liquidacion.approve",
            "liquidacion.close",
            "liquidacion.export",
        ],
    },
    "responsable-recepcion": {
        "name": "Responsable de recepción",
        "description": (
            "Registro y seguimiento de recepciones "
            "físicas y cajas recibidas."
        ),
        "is_system_role": True,
        "permission_codes": [
            "dashboard.view",
            "sorteos.view",
            "recepcion.view",
            "recepcion.create",
            "recepcion.change",
            "cajas.view",
            "cajas.create",
            "cajas.change",
        ],
    },
    "auditor-billeteria": {
        "name": "Auditor de billetería",
        "description": (
            "Verificación física de billetería y gestión "
            "de inconsistencias."
        ),
        "is_system_role": True,
        "permission_codes": [
            "dashboard.view",
            "sorteos.view",
            "recepcion.view",
            "cajas.view",
            "auditoria.view",
            "auditoria.scan",
            "auditoria.validate",
            "auditoria.close",
            "inconsistencias.view",
            "inconsistencias.create",
            "inconsistencias.resolve",
        ],
    },
    "responsable-liquidacion": {
        "name": "Responsable de liquidación",
        "description": (
            "Conciliación de devoluciones y gestión "
            "de liquidaciones contables."
        ),
        "is_system_role": True,
        "permission_codes": [
            "dashboard.view",
            "sorteos.view",
            "devolucion-electronica.view",
            "devolucion-electronica.validate",
            "devolucion-electronica.export",
            "inconsistencias.view",
            "inconsistencias.resolve",
            "inconsistencias.export",
            "liquidacion.view",
            "liquidacion.create",
            "liquidacion.change",
            "liquidacion.approve",
            "liquidacion.close",
            "liquidacion.export",
        ],
    },
    "consulta": {
        "name": "Consulta",
        "description": (
            "Acceso de solo lectura a la información "
            "de los módulos operativos."
        ),
        "is_system_role": True,
        "permission_codes": [
            f"{module.code}.view"
            for module in Module.objects.all()
            if any(
                permission.code == "view"
                for permission in module.permissions.all()
            )
        ],
    },
}


class Command(BaseCommand):
    help = "Crea o actualiza los roles base del sistema."

    @transaction.atomic
    def handle(self, *args, **options):
        # Resolver los permisos disponibles en la base de datos.
        available_permissions = {
            f"{permission.module.code}.{permission.code}": permission
            for permission in ModulePermission.objects.select_related(
                "module"
            )
        }

        created_roles = 0
        updated_roles = 0

        for role_code, definition in ROLE_DEFINITIONS.items():
            role, created = Role.objects.update_or_create(
                code=role_code,
                defaults={
                    "name": definition["name"],
                    "description": definition["description"],
                    "is_system_role": definition["is_system_role"],
                    "is_active": True,
                },
            )

            if created:
                created_roles += 1
            else:
                updated_roles += 1

            requested_codes = definition["permission_codes"]

            if requested_codes == "__ALL__":
                permissions = list(available_permissions.values())
            else:
                missing_codes = [
                    code
                    for code in requested_codes
                    if code not in available_permissions
                ]

                if missing_codes:
                    raise ValueError(
                        f"El rol '{role_code}' referencia permisos "
                        f"inexistentes: {missing_codes}"
                    )

                permissions = [
                    available_permissions[code]
                    for code in requested_codes
                ]

            # Actualiza la plantilla sin modificar excepciones individuales.
            role.permissions.set(permissions)

        self.stdout.write(
            self.style.SUCCESS(
                "Roles procesados correctamente.\n"
                f"Roles creados: {created_roles}\n"
                f"Roles actualizados: {updated_roles}"
            )
        )