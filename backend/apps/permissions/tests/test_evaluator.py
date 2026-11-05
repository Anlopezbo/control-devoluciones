from django.test import TestCase

from apps.permissions.models import (
    Module,
    ModulePermission,
    Role,
    UserPermissionOverride,
)
from apps.permissions.services.evaluator import (
    get_effective_permissions,
    user_can_access_module,
    user_has_permission,
)
from apps.users.models import User


class PermissionEvaluatorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="usuario_prueba",
            email="usuario_prueba@example.com",
            password="TestPassword-OnlyForTests-123!",
        )

        self.module = Module.objects.create(
            code="liquidacion-prueba",
            name="Liquidación de prueba",
            is_active=True,
        )

        self.view_permission = ModulePermission.objects.create(
            module=self.module,
            code="view",
            name="Consultar liquidaciones",
        )

        self.approve_permission = ModulePermission.objects.create(
            module=self.module,
            code="approve",
            name="Aprobar liquidaciones",
        )

        self.role = Role.objects.create(
            code="contador-prueba",
            name="Contador de prueba",
            is_active=True,
        )

        self.role.permissions.add(self.view_permission)
        self.user.role = self.role
        self.user.save()

    def test_user_inherits_role_permission(self):
        self.assertTrue(
            user_has_permission(
                self.user,
                "liquidacion-prueba.view",
            )
        )

    def test_individual_override_revokes_inherited_permission(self):
        UserPermissionOverride.objects.create(
            user=self.user,
            permission=self.view_permission,
            allowed=False,
            reason="Prueba de revocación",
        )

        self.assertFalse(
            user_has_permission(
                self.user,
                "liquidacion-prueba.view",
            )
        )

    def test_individual_override_grants_additional_permission(self):
        UserPermissionOverride.objects.create(
            user=self.user,
            permission=self.approve_permission,
            allowed=True,
            reason="Prueba de concesión",
        )

        self.assertTrue(
            user_has_permission(
                self.user,
                "liquidacion-prueba.approve",
            )
        )

    def test_inactive_module_blocks_permissions(self):
        self.module.is_active = False
        self.module.save()

        self.assertFalse(
            user_has_permission(
                self.user,
                "liquidacion-prueba.view",
            )
        )

        self.assertFalse(
            user_can_access_module(
                self.user,
                "liquidacion-prueba",
            )
        )

    def test_inactive_user_has_no_permissions(self):
        self.user.is_active = False
        self.user.save()

        self.assertEqual(
            get_effective_permissions(self.user),
            set(),
        )


from rest_framework.test import APITestCase

from apps.permissions.models import (
    Module,
    ModulePermission,
    Role,
    UserPermissionOverride,
)
from apps.users.models import User


class PermissionEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="api_test_user",
            email="api_test_user@example.com",
            password="TestPassword-OnlyForTests-123!",
        )

        self.module = Module.objects.create(
            code="liquidacion-api-test",
            name="Liquidación API de prueba",
            is_active=True,
        )

        self.view_permission = ModulePermission.objects.create(
            module=self.module,
            code="view",
            name="Consultar liquidaciones",
        )

        self.role = Role.objects.create(
            code="contador-api-test",
            name="Contador API de prueba",
            is_active=True,
        )

        self.user.role = self.role
        self.user.save()

        self.url = "/api/permissions/permission-check/"

    def test_unauthenticated_user_is_rejected(self):
        response = self.client.get(self.url)

        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_user_without_permission_is_rejected(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_with_permission_is_allowed(self):
        self.role.permissions.add(self.view_permission)

        # El endpoint exige liquidacion.view, por lo que el permiso
        # debe pertenecer al módulo real "liquidacion", no al módulo
        # de prueba "liquidacion-api-test".
        self.module.code = "liquidacion"
        self.module.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["ok"])

    def test_individual_revocation_blocks_inherited_permission(self):
        self.module.code = "liquidacion"
        self.module.save()

        self.role.permissions.add(self.view_permission)

        UserPermissionOverride.objects.create(
            user=self.user,
            permission=self.view_permission,
            allowed=False,
            reason="Prueba de revocación individual",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)