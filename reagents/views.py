from django.views import View
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Reagente, Coordenacao, Controlador, SaidaReagente, ReagenteCoordenacao
from .forms import ReagenteForm, ReagenteCoordenacaoFormSet

@login_required(login_url='login')
def home(request):
    search = request.GET.get('search', '')
    ordenar = request.GET.get('ordenar', '')

    qs = ReagenteCoordenacao.objects.select_related(
        "reagente", "coordenacao", "reagente__controlador"
    )

    if search:
        qs = qs.filter(
            Q(reagente__reagente_nome__icontains=search) |
            Q(reagente__fispq__icontains=search) |
            Q(reagente__controlador__nome__icontains=search) |
            Q(coordenacao__nome__icontains=search)
        )

    coord_id = request.GET.get("coord")
    if coord_id:
        qs = qs.filter(coordenacao_id=coord_id)

    if ordenar == 'validade':
        qs = qs.order_by('reagente__validade')
    elif ordenar == 'nome':
        qs = qs.order_by('reagente__reagente_nome')

    coordenacoes = Coordenacao.objects.all()

    context = {
        'linhas': qs,
        'coordenacoes': coordenacoes
    }

    return render(request, 'home.html', context)

@login_required(login_url='login')
def saida_reagente(request):
    if request.method == 'POST':
        reagente_id = request.POST.get('reagente')
        requisitante = request.POST.get('requisitante')
        quantidade = int(request.POST.get('quantidade'))
        coordenacao_id = request.POST.get('coordenacao')
        observacao = request.POST.get('observacao', '')
        
        try:
            # Buscar o reagente
            reagente = Reagente.objects.get(id=reagente_id)
            
            # Buscar a quantidade disponível para a coordenação
            rc = ReagenteCoordenacao.objects.get(
                reagente=reagente,
                coordenacao_id=coordenacao_id
            )
            
            # Verificar se há quantidade suficiente
            if rc.quantidade >= quantidade:
                # Registrar saída
                SaidaReagente.objects.create(
                    reagente=reagente,
                    coordenacao_id=coordenacao_id,
                    requisitante=requisitante,
                    quantidade=quantidade,
                    observacao=observacao
                )
                
                # Atualizar quantidade
                rc.quantidade -= quantidade
                rc.save()
                
                messages.success(request, 'Saída registrada com sucesso!')
            else:
                messages.error(request, 'Quantidade insuficiente em estoque!')
                
        except Reagente.DoesNotExist:
            messages.error(request, 'Reagente não encontrado!')
        except ReagenteCoordenacao.DoesNotExist:
            messages.error(request, 'Este reagente não está disponível para esta coordenação!')
        except Exception as e:
            messages.error(request, f'Erro ao registrar saída: {str(e)}')
        
        return redirect('saida_reagente')
    
    # GET request
    reagente_id = request.GET.get("reagente")
    coord_id = request.GET.get("coord")
    qtd_disponivel = request.GET.get("qtd")

    reagentes = Reagente.objects.all()
    coordenacoes = Coordenacao.objects.all()
    saidas = SaidaReagente.objects.select_related("reagente", "coordenacao")

    context = {
        "reagentes": reagentes,
        "coordenacoes": coordenacoes,
        "saidas": saidas,
        "reagente_sel": reagente_id,
        "coord_sel": coord_id,
        "qtd_disponivel": qtd_disponivel,
    }

    return render(request, "saida.html", context)

@login_required(login_url='login')
def registro_reagente(request):
    if request.method == 'POST':
        form_reagente = ReagenteForm(request.POST, request.FILES)
        formset = ReagenteCoordenacaoFormSet(request.POST)
        
        if form_reagente.is_valid() and formset.is_valid():
            reagente = form_reagente.save()
            formset.instance = reagente
            formset.save()
            messages.success(request, 'Reagente registrado com sucesso!')
            return redirect("home")
        else:
            messages.error(request, 'Erro ao registrar reagente. Verifique os campos.')
    else:
        form_reagente = ReagenteForm()
        formset = ReagenteCoordenacaoFormSet()
    
    return render(request, 'registro.html', {
        "form": form_reagente,
        "formset": formset
    })

@login_required(login_url='login')
def historico_saida(request):
    search = request.GET.get('search', '')
    ordenar = request.GET.get('ordenar', '')

    saidas = SaidaReagente.objects.select_related(
        "reagente", "coordenacao", "reagente__controlador"
    )

    if search:
        saidas = saidas.filter(
            Q(reagente__reagente_nome__icontains=search) |
            Q(reagente__fispq__icontains=search) |
            Q(reagente__controlador__nome__icontains=search) |
            Q(coordenacao__nome__icontains=search) |
            Q(requisitante__icontains=search)
        )

    coord_id = request.GET.get("coord")
    if coord_id:
        saidas = saidas.filter(coordenacao_id=coord_id)

    if ordenar == 'validade':
        saidas = saidas.order_by('reagente__validade')
    elif ordenar == 'nome':
        saidas = saidas.order_by('reagente__reagente_nome')
    else:
        saidas = saidas.order_by('-data_saida')

    coordenacoes = Coordenacao.objects.all()

    context = {
        'saidas': saidas,
        'coordenacoes': coordenacoes
    }

    return render(request, 'historico.html', context)

@login_required(login_url='login')
def gerar_relatorio(request):
    return render(request, 'relatorio.html')