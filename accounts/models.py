from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from reagents.models import Coordenacao

# Create your models here.
class Perfil(models.Model):
    TIPO_USUARIO = (
        ('admin', 'Administrador'),
        ('coord', 'Usuário da Coordenação'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO)
    coordenacao = models.ForeignKey(Coordenacao, on_delete=models.PROTECT, blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="perfil_admin_sem_coordenacao_ou_coord_com_coordenacao",
                condition=(
                    (Q(tipo="admin") & Q(coordenacao__isnull=True)) |
                    (Q(tipo="coord") & Q(coordenacao__isnull=False))
                ),
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.tipo}"