from django.forms import ModelForm, inlineformset_factory
from .models import Reagente, ReagenteCoordenacao

class ReagenteForm(ModelForm):
    class Meta:
        model = Reagente
        fields = ['reagente_nome', 'fispq', 'controlador', 'armario', 'validade', 'nota_fiscal']

ReagenteCoordenacaoFormSet = inlineformset_factory(
    Reagente,
    ReagenteCoordenacao,
    fields=("coordenacao", "quantidade"),
    extra=1,
    can_delete=False
)

