from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Perfil
from reagents.forms import ReagenteCoordenacaoFormSet, ReagenteForm
from reagents.models import (
    Controlador,
    Coordenacao,
    Reagente,
    ReagenteCoordenacao,
    SaidaReagente,
)


class ReagentesViewTests(TestCase):
    def setUp(self):
        self.coord_a = Coordenacao.objects.create(nome="Coord A")
        self.coord_b = Coordenacao.objects.create(nome="Coord B")
        self.controlador = Controlador.objects.create(nome="Controlador X")
        self.reagente = Reagente.objects.create(
            reagente_nome="Acetona",
            fispq="F-001",
            controlador=self.controlador,
            armario="A1",
            validade=date(2030, 1, 1),
        )
        self.reagente_rc_a = ReagenteCoordenacao.objects.create(
            reagente=self.reagente,
            coordenacao=self.coord_a,
            quantidade=10,
        )
        self.reagente_rc_b_zero = ReagenteCoordenacao.objects.create(
            reagente=self.reagente,
            coordenacao=self.coord_b,
            quantidade=0,
        )

        self.admin_user = User.objects.create_user(username="admin_user", password="123456789")
        Perfil.objects.create(user=self.admin_user, tipo="admin", coordenacao=None)

        self.coord_user = User.objects.create_user(username="coord_user", password="123456789")
        Perfil.objects.create(user=self.coord_user, tipo="coord", coordenacao=self.coord_a)

    def test_coord_nao_pode_acessar_saida(self):
        self.client.force_login(self.coord_user)
        response = self.client.get(reverse("saida_reagente"))
        self.assertEqual(response.status_code, 403)

    def test_coord_nao_pode_acessar_registro(self):
        self.client.force_login(self.coord_user)
        response = self.client.get(reverse("registro_reagente"))
        self.assertEqual(response.status_code, 403)

    def test_admin_pode_acessar_saida(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("saida_reagente"))
        self.assertEqual(response.status_code, 200)

    def test_saida_post_reduz_estoque_e_cria_saida(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("saida_reagente"),
            data={
                "reagente": self.reagente.id,
                "coordenacao": self.coord_a.id,
                "quantidade": 3,
                "requisitante": "Fulano",
                "observacao": "teste",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

        self.reagente_rc_a.refresh_from_db()
        self.assertEqual(self.reagente_rc_a.quantidade, 7)
        self.assertEqual(SaidaReagente.objects.count(), 1)

    def test_saida_post_nao_deixa_estoque_negativo(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("saida_reagente"),
            data={
                "reagente": self.reagente.id,
                "coordenacao": self.coord_a.id,
                "quantidade": 999,
                "requisitante": "Fulano",
                "observacao": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("saida_reagente"))

        self.reagente_rc_a.refresh_from_db()
        self.assertEqual(self.reagente_rc_a.quantidade, 10)
        self.assertEqual(SaidaReagente.objects.count(), 0)

    def test_saida_post_requisitante_vazio_e_rejeitado(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("saida_reagente"),
            data={
                "reagente": self.reagente.id,
                "coordenacao": self.coord_a.id,
                "quantidade": 1,
                "requisitante": "   ",
                "observacao": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("saida_reagente"))

        self.reagente_rc_a.refresh_from_db()
        self.assertEqual(self.reagente_rc_a.quantidade, 10)
        self.assertEqual(SaidaReagente.objects.count(), 0)

    def test_home_filtra_quantidade_zero(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        linhas = list(response.context["linhas"])
        self.assertIn(self.reagente_rc_a, linhas)
        self.assertNotIn(self.reagente_rc_b_zero, linhas)

    def test_home_coord_ve_apenas_sua_coordenacao(self):
        self.client.force_login(self.coord_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        linhas = list(response.context["linhas"])
        self.assertEqual(linhas, [self.reagente_rc_a])

    def test_home_ordem_nome_sem_acentos_aproxima_termos(self):
        reagente_sem_acento = Reagente.objects.create(
            reagente_nome="Alcool 70",
            fispq="F-002",
            controlador=self.controlador,
            armario="A2",
            validade=date(2031, 1, 1),
        )
        reagente_com_acento = Reagente.objects.create(
            reagente_nome="Alcool 46",
            fispq="F-003",
            controlador=self.controlador,
            armario="A3",
            validade=date(2031, 1, 1),
        )
        ReagenteCoordenacao.objects.create(
            reagente=reagente_sem_acento,
            coordenacao=self.coord_a,
            quantidade=5,
        )
        ReagenteCoordenacao.objects.create(
            reagente=reagente_com_acento,
            coordenacao=self.coord_a,
            quantidade=5,
        )

        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("home"), data={"ordenar": "nome"})
        self.assertEqual(response.status_code, 200)

        nomes = [item.reagente.reagente_nome for item in response.context["linhas"]]
        idx_sem = nomes.index("Alcool 70")
        idx_com = nomes.index("Alcool 46")
        self.assertEqual(abs(idx_sem - idx_com), 1)


class ReagentesFormValidationTests(TestCase):
    def setUp(self):
        self.coord_a = Coordenacao.objects.create(nome="Coord A")
        self.controlador = Controlador.objects.create(nome="Controlador X")

    def test_reagente_form_rejeita_validade_muito_distante(self):
        form = ReagenteForm(
            data={
                "reagente_nome": "Acetona",
                "fispq": "F-001",
                "controlador": self.controlador.id,
                "armario": "A1",
                "validade": "2099-01-01",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("validade", form.errors)

    def test_reagente_form_rejeita_campos_texto_so_espaco(self):
        form = ReagenteForm(
            data={
                "reagente_nome": "   ",
                "fispq": "   ",
                "controlador": self.controlador.id,
                "armario": "   ",
                "validade": "2030-01-01",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("reagente_nome", form.errors)
        self.assertIn("fispq", form.errors)
        self.assertIn("armario", form.errors)

    def test_formset_rejeita_quantidade_zero(self):
        parent = Reagente.objects.create(
            reagente_nome="Acetona",
            fispq="F-001",
            controlador=self.controlador,
            armario="A1",
            validade=date(2030, 1, 1),
        )
        formset = ReagenteCoordenacaoFormSet(
            data={
                "reagentecoordenacao_set-TOTAL_FORMS": "1",
                "reagentecoordenacao_set-INITIAL_FORMS": "0",
                "reagentecoordenacao_set-MIN_NUM_FORMS": "0",
                "reagentecoordenacao_set-MAX_NUM_FORMS": "1000",
                "reagentecoordenacao_set-0-coordenacao": str(self.coord_a.id),
                "reagentecoordenacao_set-0-quantidade": "0",
            },
            instance=parent,
        )
        self.assertFalse(formset.is_valid())

    def test_formset_rejeita_coordenacao_duplicada(self):
        parent = Reagente.objects.create(
            reagente_nome="Acido",
            fispq="F-002",
            controlador=self.controlador,
            armario="A2",
            validade=date(2030, 1, 1),
        )
        formset = ReagenteCoordenacaoFormSet(
            data={
                "reagentecoordenacao_set-TOTAL_FORMS": "2",
                "reagentecoordenacao_set-INITIAL_FORMS": "0",
                "reagentecoordenacao_set-MIN_NUM_FORMS": "0",
                "reagentecoordenacao_set-MAX_NUM_FORMS": "1000",
                "reagentecoordenacao_set-0-coordenacao": str(self.coord_a.id),
                "reagentecoordenacao_set-0-quantidade": "3",
                "reagentecoordenacao_set-1-coordenacao": str(self.coord_a.id),
                "reagentecoordenacao_set-1-quantidade": "2",
            },
            instance=parent,
        )
        self.assertFalse(formset.is_valid())
