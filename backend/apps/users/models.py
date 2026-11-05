from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuario interno de Control de Devoluciones.
    """

    email = models.EmailField(
        "correo electrónico",
        unique=True,
    )

    employee_code = models.CharField(
        "código de empleado",
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )

    role = models.ForeignKey(
        "permissions.Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="rol",
    )

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["last_name", "first_name", "username"]

    def __str__(self):
        return self.get_full_name() or self.username