from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from accounts.models import Perfil

@receiver(post_save, sender=User)
def garantir_perfil_admin(sender, instance, created, **kwargs):
    if instance.is_superuser or instance.is_staff:
        perfil, _ = Perfil.objects.get_or_create(
            user=instance,
            defaults={"tipo": "admin", "coordenacao": None}
        )
        if perfil.tipo != "admin":
            perfil.tipo = "admin"
            perfil.coordenacao = None
            perfil.save(update_fields=["tipo", "coordenacao"])
