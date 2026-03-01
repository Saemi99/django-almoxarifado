from datetime import date

from django import forms
from django.forms import BaseInlineFormSet, ModelForm, inlineformset_factory

from .models import Coordenacao, Reagente, ReagenteCoordenacao


class ReagenteForm(ModelForm):
    class Meta:
        model = Reagente
        fields = ["reagente_nome", "fispq", "controlador", "armario", "validade", "nota_fiscal"]
        widgets = {
            "validade": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_reagente_nome(self):
        nome = (self.cleaned_data.get("reagente_nome") or "").strip()
        if not nome:
            raise forms.ValidationError("Informe o nome do reagente.")
        return nome

    def clean_fispq(self):
        fispq = (self.cleaned_data.get("fispq") or "").strip()
        if not fispq:
            raise forms.ValidationError("Informe o FISPQ.")
        return fispq

    def clean_armario(self):
        armario = (self.cleaned_data.get("armario") or "").strip()
        if not armario:
            raise forms.ValidationError("Informe o armario.")
        return armario

    def clean_validade(self):
        validade = self.cleaned_data.get("validade")
        if not validade:
            return validade

        if validade.year < 1900:
            raise forms.ValidationError("Data de validade invalida.")
        if validade.year > date.today().year + 50:
            raise forms.ValidationError("Data de validade muito distante.")
        return validade


class ReagenteCoordenacaoForm(ModelForm):
    quantidade = forms.IntegerField(min_value=1, required=True)

    class Meta:
        model = ReagenteCoordenacao
        fields = ("coordenacao", "quantidade")


class BaseReagenteCoordenacaoFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        coordenacoes = set()
        has_row = False

        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue
            if form.cleaned_data.get("DELETE"):
                continue

            has_row = True
            coordenacao = form.cleaned_data.get("coordenacao")
            quantidade = form.cleaned_data.get("quantidade")

            if coordenacao in coordenacoes:
                raise forms.ValidationError("Nao repita a mesma coordenacao.")
            coordenacoes.add(coordenacao)

            if quantidade is None or quantidade <= 0:
                raise forms.ValidationError("Quantidade deve ser maior que zero.")

        if not has_row:
            raise forms.ValidationError("Adicione ao menos uma coordenacao com quantidade.")


ReagenteCoordenacaoFormSet = inlineformset_factory(
    Reagente,
    ReagenteCoordenacao,
    form=ReagenteCoordenacaoForm,
    formset=BaseReagenteCoordenacaoFormSet,
    extra=1,
    can_delete=False,
)


class SaidaReagenteForm(forms.Form):
    reagente = forms.ModelChoiceField(queryset=Reagente.objects.none(), required=True)
    coordenacao = forms.ModelChoiceField(queryset=Coordenacao.objects.none(), required=True)
    requisitante = forms.CharField(max_length=200, required=True)
    quantidade = forms.IntegerField(min_value=1, required=True)
    observacao = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reagente"].queryset = Reagente.objects.all()
        self.fields["coordenacao"].queryset = Coordenacao.objects.all()

    def clean_requisitante(self):
        requisitante = (self.cleaned_data.get("requisitante") or "").strip()
        if not requisitante:
            raise forms.ValidationError("Informe o requisitante.")
        return requisitante

    def clean_observacao(self):
        return (self.cleaned_data.get("observacao") or "").strip()
