"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import register_view, login_view, logout_view
from reagents.views import registro_reagente, home, saida_reagente, gerar_relatorio, historico_saida

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # Redirecionar raiz para home
    path('home/', home, name='home'),
    path('saida/', saida_reagente, name='saida_reagente'),
    path('historico/', historico_saida, name='historico_saida'),
    path('entrada/', registro_reagente, name='registro_reagente'),
    path('registro/', register_view, name='register'),
    path('relatorio/', gerar_relatorio, name='gerar_relatorio'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
