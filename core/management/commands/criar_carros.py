from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Carro

class Command(BaseCommand):
    help = 'Cria os 32 carros do ponto'

    def handle(self, *args, **kwargs):
        for i in range(1, 33):
            numero = str(i).zfill(2)
            username = numero
            password = f'taxi{numero}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password=password)
                Carro.objects.create(usuario=user, numero=numero)
                self.stdout.write(f'Carro {numero} criado!')
            else:
                self.stdout.write(f'Carro {numero} já existe!')
        self.stdout.write('Pronto!')