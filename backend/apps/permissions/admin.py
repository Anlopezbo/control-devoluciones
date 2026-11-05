from django.contrib import admin

from .models import (
    Module,
    ModulePermission,
    Role,
    UserPermissionOverride,
    PermissionAuditLog,
)


class ModulePermissionInline(admin.TabularInline):
    model = ModulePermission
    extra = 0


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "is_active",
        "display_order",
    )

    list_filter = ("is_active",)
    search_fields = ("name", "code")
    inlines = [ModulePermissionInline]


@admin.register(ModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "module",
        "code",
    )

    list_filter = ("module",)
    search_fields = (
        "name",
        "code",
        "module__name",
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "is_active",
        "is_system_role",
    )

    list_filter = (
        "is_active",
        "is_system_role",
    )

    search_fields = (
        "name",
        "code",
    )

    filter_horizontal = ("permissions",)


@admin.register(UserPermissionOverride)
class UserPermissionOverrideAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "permission",
        "allowed",
        "updated_at",
    )

    list_filter = (
        "allowed",
        "permission__module",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "permission__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(PermissionAuditLog)
class PermissionAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "actor",
        "action",
        "target_user",
        "module",
        "permission",
        "reason",
    )

    list_filter = (
        "action",
        "created_at",
        "module",
    )

    search_fields = (
        "actor__username",
        "actor__first_name",
        "actor__last_name",
        "target_user__username",
        "target_user__first_name",
        "target_user__last_name",
        "reason",
    )

    readonly_fields = (
        "actor",
        "target_user",
        "permission",
        "module",
        "action",
        "previous_value",
        "new_value",
        "reason",
        "created_at",
    )

    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False