from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('fila/', views.fila_view, name='fila'),
    path('sair/', views.sair_view, name='sair'),
]