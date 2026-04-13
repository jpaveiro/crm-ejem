"""
URL configuration for ccrm_ejem project.

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
from core import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('vendedor/dashboard/', views.vendedor_dashboard_view, name='vendedor-dashboard'),
    path('diretoria/dashboard/', views.diretoria_dashboard_view, name='diretoria-dashboard'),
    path('diretoria/exportar/', views.exportar_excel, name='exportar_excel'),
    path('diretoria/vendedores/', views.vendedores_view, name='vendedores'),
    path('diretoria/vendedores/criar/', views.vendedor_criar_view, name='vendedor-criar'),
    path('diretoria/vendedores/<int:pk>/editar/', views.vendedor_editar_view, name='vendedor-editar'),
    path('diretoria/vendedores/<int:pk>/excluir/', views.vendedor_excluir_view, name='vendedor-excluir'),
    path('diretoria/produtos/', views.produtos_view, name='produtos'),
    path('diretoria/produtos/criar/', views.produto_criar_view, name='produto-criar'),
    path('diretoria/produtos/<int:pk>/editar/', views.produto_editar_view, name='produto-editar'),
    path('diretoria/produtos/<int:pk>/excluir/', views.produto_excluir_view, name='produto-excluir'),
    path('admin/', admin.site.urls)
]
