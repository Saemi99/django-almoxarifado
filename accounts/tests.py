from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Perfil
from reagents.models import Coordenacao


class PerfilConstraintTests(TestCase):
    def setUp(self):
        self.coordenacao = Coordenacao.objects.create(nome="Coord A")

    def test_perfil_admin_nao_pode_ter_coordenacao(self):
        user = User.objects.create_user(username="admin1", password="123")
        with self.assertRaises(IntegrityError):
            Perfil.objects.create(user=user, tipo="admin", coordenacao=self.coordenacao)

    def test_perfil_coord_precisa_de_coordenacao(self):
        user = User.objects.create_user(username="coord1", password="123")
        with self.assertRaises(IntegrityError):
            Perfil.objects.create(user=user, tipo="coord", coordenacao=None)

    def test_perfil_validos_passam(self):
        user_admin = User.objects.create_user(username="admin2", password="123")
        user_coord = User.objects.create_user(username="coord2", password="123")

        Perfil.objects.create(user=user_admin, tipo="admin", coordenacao=None)
        Perfil.objects.create(user=user_coord, tipo="coord", coordenacao=self.coordenacao)

        self.assertEqual(Perfil.objects.count(), 2)


class LogoutTests(TestCase):
    def test_logout_aceita_apenas_post(self):
        user = User.objects.create_user(username="u1", password="123456789")
        self.client.force_login(user)

        response_get = self.client.get(reverse("logout"))
        self.assertEqual(response_get.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

        response_post = self.client.post(reverse("logout"))
        self.assertEqual(response_post.status_code, 302)
        self.assertEqual(response_post.url, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
