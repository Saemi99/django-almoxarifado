import unicodedata
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.db.models import CharField, F, Func, Q, Value
from django.db.models.functions import Lower, Replace
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.permissions import get_perfil

from .forms import ReagenteCoordenacaoFormSet, ReagenteForm, SaidaReagenteForm
from .models import Coordenacao, Reagente, ReagenteCoordenacao, SaidaReagente


class Unaccent(Func):
    function = "UNACCENT"
    output_field = CharField()


_ACCENT_REPLACEMENTS = [
    ("\u00c1", "a"), ("\u00c0", "a"), ("\u00c2", "a"), ("\u00c3", "a"), ("\u00c4", "a"),
    ("\u00c9", "e"), ("\u00c8", "e"), ("\u00ca", "e"), ("\u00cb", "e"),
    ("\u00cd", "i"), ("\u00cc", "i"), ("\u00ce", "i"), ("\u00cf", "i"),
    ("\u00d3", "o"), ("\u00d2", "o"), ("\u00d4", "o"), ("\u00d5", "o"), ("\u00d6", "o"),
    ("\u00da", "u"), ("\u00d9", "u"), ("\u00db", "u"), ("\u00dc", "u"),
    ("\u00c7", "c"), ("\u00d1", "n"),
    ("\u00e1", "a"), ("\u00e0", "a"), ("\u00e2", "a"), ("\u00e3", "a"), ("\u00e4", "a"),
    ("\u00e9", "e"), ("\u00e8", "e"), ("\u00ea", "e"), ("\u00eb", "e"),
    ("\u00ed", "i"), ("\u00ec", "i"), ("\u00ee", "i"), ("\u00ef", "i"),
    ("\u00f3", "o"), ("\u00f2", "o"), ("\u00f4", "o"), ("\u00f5", "o"), ("\u00f6", "o"),
    ("\u00fa", "u"), ("\u00f9", "u"), ("\u00fb", "u"), ("\u00fc", "u"),
    ("\u00e7", "c"), ("\u00f1", "n"),
]


def _normalize_text(value):
    value = (value or "").strip().lower()
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _accent_fold_expr(field_name):
    expr = F(field_name)
    if connection.vendor == "postgresql":
        expr = Unaccent(expr)
    else:
        for src, dst in _ACCENT_REPLACEMENTS:
            expr = Replace(expr, Value(src), Value(dst))
    return Lower(expr)


def _order_by_nome_sem_acentos(queryset, field_name):
    folded = _accent_fold_expr(field_name)
    return queryset.annotate(_sort_nome=folded).order_by("_sort_nome", field_name)


@login_required(login_url="login")
def home(request):
    search = request.GET.get("search", "")
    ordenar = request.GET.get("ordenar", "")

    qs = ReagenteCoordenacao.objects.select_related(
        "reagente", "coordenacao", "reagente__controlador"
    ).filter(quantidade__gt=0)

    if search:
        normalized_search = _normalize_text(search)
        qs = qs.annotate(
            reagente_nome_fold=_accent_fold_expr("reagente__reagente_nome"),
            fispq_fold=_accent_fold_expr("reagente__fispq"),
            controlador_fold=_accent_fold_expr("reagente__controlador__nome"),
            coordenacao_fold=_accent_fold_expr("coordenacao__nome"),
        ).filter(
            Q(reagente_nome_fold__contains=normalized_search)
            | Q(fispq_fold__contains=normalized_search)
            | Q(controlador_fold__contains=normalized_search)
            | Q(coordenacao_fold__contains=normalized_search)
        )

    coord_id = request.GET.get("coord")
    if coord_id:
        qs = qs.filter(coordenacao_id=coord_id)

    if ordenar == "validade":
        qs = qs.order_by("reagente__validade")
    elif ordenar == "nome":
        qs = _order_by_nome_sem_acentos(qs, "reagente__reagente_nome")

    perfil = get_perfil(request.user)

    if perfil.tipo == "coord":
        qs = qs.filter(coordenacao=perfil.coordenacao)
        coordenacoes = Coordenacao.objects.filter(id=perfil.coordenacao_id)
    else:
        coordenacoes = Coordenacao.objects.all()

    today = timezone.localdate()
    warning_limit = today + timedelta(days=365)
    linhas = list(qs)
    for linha in linhas:
        validade = linha.reagente.validade
        if validade < today:
            linha.validade_status = "expired"
        elif validade <= warning_limit:
            linha.validade_status = "warning"
        else:
            linha.validade_status = "ok"

    context = {"linhas": linhas, "coordenacoes": coordenacoes}
    return render(request, "home.html", context)


@login_required(login_url="login")
def saida_reagente(request):
    perfil = get_perfil(request.user)
    if perfil.tipo != "admin":
        raise PermissionDenied("Sem permissao.")

    if request.method == "POST":
        form = SaidaReagenteForm(request.POST)
        if not form.is_valid():
            for erros in form.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            return redirect("saida_reagente")

        reagente = form.cleaned_data["reagente"]
        coordenacao = form.cleaned_data["coordenacao"]
        requisitante = form.cleaned_data["requisitante"]
        quantidade = form.cleaned_data["quantidade"]
        observacao = form.cleaned_data["observacao"]

        try:
            with transaction.atomic():
                rc = ReagenteCoordenacao.objects.select_for_update().get(
                    reagente=reagente,
                    coordenacao=coordenacao,
                )

                if rc.quantidade < quantidade:
                    messages.error(request, "Quantidade insuficiente em estoque!")
                    return redirect("saida_reagente")

                SaidaReagente.objects.create(
                    reagente=reagente,
                    coordenacao=coordenacao,
                    requisitante=requisitante,
                    quantidade=quantidade,
                    observacao=observacao,
                )

                rc.quantidade -= quantidade
                rc.save()

                messages.success(request, "Saida registrada com sucesso!")
                return redirect("home")

        except ReagenteCoordenacao.DoesNotExist:
            messages.error(request, "Este reagente nao esta disponivel para esta coordenacao!")
        except Exception as e:
            messages.error(request, f"Erro ao registrar saida: {str(e)}")

        return redirect("saida_reagente")

    reagente_id = request.GET.get("reagente")
    coord_id = request.GET.get("coord")
    qtd_disponivel = None

    if reagente_id and coord_id:
        try:
            rc = ReagenteCoordenacao.objects.get(
                reagente_id=reagente_id,
                coordenacao_id=coord_id,
            )
            qtd_disponivel = rc.quantidade
        except ReagenteCoordenacao.DoesNotExist:
            qtd_disponivel = 0

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


@login_required(login_url="login")
def registro_reagente(request):
    perfil = get_perfil(request.user)
    if perfil.tipo != "admin":
        raise PermissionDenied("Sem permissao.")
    if request.method == "POST":
        form_reagente = ReagenteForm(request.POST, request.FILES)
        formset = ReagenteCoordenacaoFormSet(request.POST)

        if form_reagente.is_valid() and formset.is_valid():
            reagente = form_reagente.save()
            formset.instance = reagente
            formset.save()
            messages.success(request, "Reagente registrado com sucesso!")
            return redirect("home")
        messages.error(request, "Erro ao registrar reagente. Verifique os campos.")
    else:
        form_reagente = ReagenteForm()
        formset = ReagenteCoordenacaoFormSet()

    return render(request, "registro.html", {"form": form_reagente, "formset": formset})


@login_required(login_url="login")
def historico_saida(request):
    search = request.GET.get("search", "")
    ordenar = request.GET.get("ordenar", "")

    saidas = SaidaReagente.objects.select_related(
        "reagente", "coordenacao", "reagente__controlador"
    )

    if search:
        normalized_search = _normalize_text(search)
        saidas = saidas.annotate(
            reagente_nome_fold=_accent_fold_expr("reagente__reagente_nome"),
            fispq_fold=_accent_fold_expr("reagente__fispq"),
            controlador_fold=_accent_fold_expr("reagente__controlador__nome"),
            coordenacao_fold=_accent_fold_expr("coordenacao__nome"),
            requisitante_fold=_accent_fold_expr("requisitante"),
        ).filter(
            Q(reagente_nome_fold__contains=normalized_search)
            | Q(fispq_fold__contains=normalized_search)
            | Q(controlador_fold__contains=normalized_search)
            | Q(coordenacao_fold__contains=normalized_search)
            | Q(requisitante_fold__contains=normalized_search)
        )

    coord_id = request.GET.get("coord")
    if coord_id:
        saidas = saidas.filter(coordenacao_id=coord_id)

    if ordenar == "validade":
        saidas = saidas.order_by("reagente__validade")
    elif ordenar == "nome":
        saidas = _order_by_nome_sem_acentos(saidas, "reagente__reagente_nome")
    else:
        saidas = saidas.order_by("-data_saida")

    perfil = get_perfil(request.user)

    if perfil.tipo == "coord":
        saidas = saidas.filter(coordenacao=perfil.coordenacao)
        coordenacoes = Coordenacao.objects.filter(id=perfil.coordenacao_id)
    else:
        coordenacoes = Coordenacao.objects.all()

    context = {"saidas": saidas, "coordenacoes": coordenacoes}
    return render(request, "historico.html", context)


@login_required(login_url="login")
def gerar_relatorio(request):
    perfil = get_perfil(request.user)
    if perfil.tipo != "admin":
        raise PermissionDenied("Sem permissao.")
    return render(request, "relatorio.html")
