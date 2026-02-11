from django.contrib import admin
from .models import (
    Coordenacao,
    Controlador,
    Reagente,
    ReagenteCoordenacao,
    SaidaReagente,
)

# ======================
# COORDENAÇÃO
# ======================
class CoordenacaoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


# ======================
# CONTROLADOR
# ======================
class ControladorAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


# ======================
# INLINE: QUANTIDADE POR COORDENAÇÃO
# ======================
class ReagenteCoordenacaoInline(admin.TabularInline):
    model = ReagenteCoordenacao
    extra = 1


# ======================
# INLINE: HISTÓRICO DE SAÍDA
# ======================
class SaidaReagenteInline(admin.TabularInline):
    model = SaidaReagente
    extra = 0
    readonly_fields = ('data_saida',)


# ======================
# REAGENTE
# ======================
class ReagenteAdmin(admin.ModelAdmin):
    list_display = (
        'reagente_nome',
        'controlador',
        'armario',
        'validade',
        'ativo',
    )

    search_fields = (
        'reagente_nome',
        'fispq',
        'controlador__nome',
        'armario',
    )

    list_filter = (
        'controlador',
        'validade',
        'ativo',
    )

    ordering = ('reagente_nome',)

    inlines = [
        ReagenteCoordenacaoInline,
        SaidaReagenteInline,
    ]


# ======================
# REGISTROS
# ======================
admin.site.register(Coordenacao, CoordenacaoAdmin)
admin.site.register(Controlador, ControladorAdmin)
admin.site.register(Reagente, ReagenteAdmin)
