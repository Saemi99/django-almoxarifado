from types import SimpleNamespace
from django.core.exceptions import PermissionDenied
from accounts.models import Perfil

def get_perfil(user):
    if not user.is_authenticated:
        raise PermissionDenied("Usuário não autenticado.")

    # Superuser/staff sempre tratado como admin, mesmo sem Perfil
    if user.is_superuser or user.is_staff:
        return SimpleNamespace(tipo="admin", coordenacao=None, coordenacao_id=None)

    try:
        return user.perfil
    except Perfil.DoesNotExist:
        raise PermissionDenied("Usuário sem perfil.")

def is_admin(user):
    return get_perfil(user).tipo == "admin"

def is_coord(user):
    return get_perfil(user).tipo == "coord"
