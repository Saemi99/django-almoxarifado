from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from accounts.permissions import get_perfil
from django.core.exceptions import PermissionDenied
from django.db import transaction
from accounts.models import Perfil
from reagents.models import Coordenacao

@login_required(login_url='login')
def register_view(request):
    perfil = get_perfil(request.user)
    if perfil.tipo != "admin":
        raise PermissionDenied("Sem permissão.")
    coordenacoes = Coordenacao.objects.all()

    if request.method == "POST":
        user_form = UserCreationForm(request.POST)
        tipo = request.POST.get("tipo")
        coordenacao_id = request.POST.get("coordenacao")

        # 1) Validar tipo obrigatório
        if not tipo:
            user_form.add_error(None, "Selecione o tipo de usuário.")

        # 2) Regra de negócio: coord precisa de coordenação
        if tipo == "coord" and not coordenacao_id:
            user_form.add_error(None, "Usuário de coordenação precisa escolher uma coordenação.")

        # 3) Só salva se tudo estiver válido
        if user_form.is_valid() and not user_form.non_field_errors():
            try:
                with transaction.atomic():
                    user = user_form.save()

                    if tipo == "admin":
                        Perfil.objects.create(
                            user=user,
                            tipo="admin",
                            coordenacao=None
                        )
                    elif tipo == "coord":
                        Perfil.objects.create(
                            user=user,
                            tipo="coord",
                            coordenacao_id=coordenacao_id
                        )
                    else:
                        user_form.add_error(None, "Tipo de usuário inválido.")
                        raise ValueError("Tipo inválido")

                return redirect("login")

            except Coordenacao.DoesNotExist:
                user_form.add_error(None, "Coordenação inválida.")
            except Exception:
                user_form.add_error(None, "Não foi possível cadastrar o usuário. Tente novamente.")
    else:
        user_form = UserCreationForm()

    return render(request, "register.html", {
        "user_form": user_form,
        "coordenacoes": coordenacoes
    })
    
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            login_form = AuthenticationForm
    else:
        login_form = AuthenticationForm()

    return render(request, 'login.html', {'login_form': login_form})

def logout_view(request):
    logout(request)
    return redirect('login')