from accounts.permissions import get_perfil


def auth_flags(request):
    user = getattr(request, "user", None)
    is_admin = False

    if user and user.is_authenticated:
        try:
            is_admin = get_perfil(user).tipo == "admin"
        except Exception:
            is_admin = False

    return {"is_admin": is_admin}
