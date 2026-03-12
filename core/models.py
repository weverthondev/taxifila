from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Carro(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    numero = models.CharField(max_length=2)
    na_fila = models.BooleanField(default=False)
    posicao = models.IntegerField(default=0)
    em_corrida = models.BooleanField(default=False)
    chamado = models.BooleanField(default=False)
    entrou_na_fila_em = models.DateTimeField(null=True, blank=True)

    
class HistoricoChamada(models.Model):
    carros = models.CharField(max_length=100)
    horario = models.DateTimeField(default=timezone.now)
    desfeita = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['horario']
        
    def __str__(self):
        return f'Chamada {self.carros} - {self.horario}'

    def __str__(self):
        return f'Carro {self.numero}'
