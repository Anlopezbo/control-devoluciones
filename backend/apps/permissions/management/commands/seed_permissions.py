from django.core.management.base import BaseCommand
from django.db import transaction

from apps.permissions.models import Module, ModulePermission


MODULES = [
    {
        "code": "dashboard",
        "name": "Panel de control",
        "description": "Indicadores generales y resumen operativo.",
        "display_order": 1,
        "permissions": [
            ("view", "Consultar indicadores"),
        ],
    },
    {
        "code": "sorteos",
        "name": "Gestión de sorteos",
        "description": "Administración de sorteos y sus estados.",
        "display_order": 2,
        "permissions": [
            ("view", "Consultar sorteos"),
            ("create", "Crear sorteos"),
            ("change", "Modificar sorteos"),
            ("activate", "Activar sorteos"),
            ("close", "Cerrar sorteos"),
        ],
    },
    {
        "code": "mezcla",
        "name": "Carga de mezcla",
        "description": "Importación y validación de la mezcla de billetería.",
        "display_order": 3,
        "permissions": [
            ("view", "Consultar mezcla"),
            ("upload", "Cargar archivos de mezcla"),
            ("validate", "Validar mezcla"),
            ("export", "Exportar resultados"),
        ],
    },
    {
        "code": "devolucion-electronica",
        "name": "Devolución electrónica",
        "description": "Carga y validación de devoluciones reportadas.",
        "display_order": 4,
        "permissions": [
            ("view", "Consultar devoluciones electrónicas"),
            ("upload", "Cargar archivos de devolución"),
            ("validate", "Validar devoluciones"),
            ("export", "Exportar resultados"),
        ],
    },
    {
        "code": "recepcion",
        "name": "Recepción de billetería",
        "description": "Registro de entregas físicas de billetería.",
        "display_order": 5,
        "permissions": [
            ("view", "Consultar recepciones"),
            ("create", "Registrar recepciones"),
            ("change", "Modificar recepciones"),
        ],
    },
    {
        "code": "cajas",
        "name": "Control de cajas recibidas",
        "description": "Seguimiento de cajas y su recepción.",
        "display_order": 6,
        "permissions": [
            ("view", "Consultar cajas"),
            ("create", "Registrar cajas"),
            ("change", "Modificar cajas"),
        ],
    },
    {
        "code": "auditoria",
        "name": "Auditoría de billetería",
        "description": "Lectura, verificación y cierre de auditorías.",
        "display_order": 7,
        "permissions": [
            ("view", "Consultar auditorías"),
            ("scan", "Registrar lecturas de códigos de barras"),
            ("validate", "Validar resultados de auditoría"),
            ("close", "Cerrar auditorías"),
        ],
    },
    {
        "code": "inconsistencias",
        "name": "Gestión de inconsistencias",
        "description": "Registro, investigación y resolución de diferencias.",
        "display_order": 8,
        "permissions": [
            ("view", "Consultar inconsistencias"),
            ("create", "Registrar inconsistencias"),
            ("resolve", "Resolver inconsistencias"),
            ("export", "Exportar inconsistencias"),
        ],
    },
    {
        "code": "liquidacion",
        "name": "Liquidación y contabilidad",
        "description": "Conciliación y cierre de liquidaciones.",
        "display_order": 9,
        "permissions": [
            ("view", "Consultar liquidaciones"),
            ("create", "Crear registros de liquidación"),
            ("change", "Modificar liquidaciones"),
            ("approve", "Aprobar liquidaciones"),
            ("close", "Cerrar liquidaciones"),
            ("export", "Exportar informes contables"),
        ],
    },
]


class Command(BaseCommand):
    help = "Crea o actualiza el catálogo inicial de módulos y permisos."

    @transaction.atomic
    def handle(self, *args, **options):
        created_modules = 0
        updated_modules = 0
        created_permissions = 0
        updated_permissions = 0

        for item in MODULES:
            module, created = Module.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                    "display_order": item["display_order"],
                },
            )

            if created:
                created_modules += 1
            else:
                updated_modules += 1

            for permission_code, permission_name in item["permissions"]:
                permission, permission_created = (
                    ModulePermission.objects.update_or_create(
                        module=module,
                        code=permission_code,
                        defaults={
                            "name": permission_name,
                        },
                    )
                )

                if permission_created:
                    created_permissions += 1
                else:
                    updated_permissions += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Catálogo procesado correctamente.\n"
                f"Módulos creados: {created_modules}\n"
                f"Módulos actualizados: {updated_modules}\n"
                f"Permisos creados: {created_permissions}\n"
                f"Permisos actualizados: {updated_permissions}"
            )
        )