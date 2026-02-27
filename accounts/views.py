from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from accounts.models import Perfil
from reagents.models import Coordenacao

def register_view(request):
    coordenacoes = Coordenacao.objects.all()

    if request.method == "POST":
        user_form = UserCreationForm(request.POST)
        tipo = request.POST.get("tipo")
        coordenacao_id = request.POST.get("coordenacao")

        if user_form.is_valid() and tipo:
            user = user_form.save()

            if tipo == "admin":
                Perfil.objects.create(
                    user=user,
                    tipo="admin",
                    coordenacao=None
                )
            else:
                if not coordenacao_id:
                    user_form.add_error(None, "Usuário de coordenação precisa escolher uma coordenação.")
                else:
                    Perfil.objects.create(
                        user=user,
                        tipo="coord",
                        coordenacao_id=coordenacao_id
                    )

            return redirect('login')
    else:
        user_form = UserCreationForm()

    return render(request, 'register.html', {
        'user_form': user_form,
        'coordenacoes': coordenacoes
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