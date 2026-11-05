from django.urls import path

from apps.permissions.views import PermissionCheckView


app_name = "permissions"

urlpatterns = [
    path(
        "permission-check/",
        PermissionCheckView.as_view(),
        name="permission-check",
    ),
]

