import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Carro, HistoricoChamada

class FilaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('fila', self.channel_name)
        await self.accept()
        await self.enviar_fila()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('fila', self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        acao = data.get('acao')
        usuario = self.scope['user']

        if acao == 'entrar':
            await self.entrar_fila(usuario)
            await self.broadcast_fila([])
        elif acao == 'sair':
            await self.sair_fila(usuario)
            await self.broadcast_fila([])
        elif acao == 'chamar':
            quantidade = data.get('quantidade', 1)
            chamados = await self.chamar_carros(quantidade)
            await self.broadcast_fila(chamados)
        elif acao == 'desfazer':
            historico_id = data.get('historico_id')
            await self.desfazer_chamada(historico_id)
            await self.broadcast_fila([])

    async def broadcast_fila(self, chamados=[]):
        fila = await self.get_fila()
        historico = await self.get_historico()
        await self.channel_layer.group_send('fila', {
            'type': 'fila_update',
            'fila': fila,
            'chamados': chamados,
            'historico': historico,
        })

    async def fila_update(self, event):
        usuario = self.scope['user']
        fila = event['fila']
        chamados = event.get('chamados', [])
        historico = event.get('historico', [])
        posicao_atual = next((c['posicao'] for c in fila if c['numero'] == usuario.username), 0)
        await self.send(text_data=json.dumps({
            'fila': fila,
            'posicao_atual': posicao_atual,
            'chamados': chamados,
            'historico': historico,
        }))

    async def enviar_fila(self):
        fila = await self.get_fila()
        historico = await self.get_historico()
        usuario = self.scope['user']
        posicao_atual = next((c['posicao'] for c in fila if c['numero'] == usuario.username), 0)
        await self.send(text_data=json.dumps({
            'fila': fila,
            'posicao_atual': posicao_atual,
            'chamados': [],
            'historico': historico,
        }))

    @database_sync_to_async
    def get_fila(self):
        from django.utils import timezone
        carros = Carro.objects.filter(na_fila=True).order_by('posicao')
        resultado = []
        for c in carros:
            if c.entrou_na_fila_em:
                diff = timezone.now() - c.entrou_na_fila_em
                minutos = int(diff.total_seconds() // 60)
                tempo = f'{minutos}min' if minutos > 0 else 'agora'
            else:
                tempo = ''
            resultado.append({'numero': c.numero, 'posicao': c.posicao, 'tempo': tempo})
        return resultado
    
    @database_sync_to_async
    def get_historico(self):
        historico = HistoricoChamada.objects.filter(desfeita=False)[:10]
        return [{'id': h.id, 'carros': h.carros, 'horario': h.horario.strftime('%H:%M')} for h in historico]

    @database_sync_to_async
    def entrar_fila(self, usuario):
        from django.utils import timezone
        carro = Carro.objects.get(usuario=usuario)
        if not carro.na_fila:
            ultima_posicao = Carro.objects.filter(na_fila=True).count()
            carro.na_fila = True
            carro.posicao = ultima_posicao + 1
            carro.entrou_na_fila_em = timezone.now()
            carro.save()

    @database_sync_to_async
    def sair_fila(self, usuario):
        carro = Carro.objects.get(usuario=usuario)
        if carro.na_fila:
            posicao_saindo = carro.posicao
            carro.na_fila = False
            carro.posicao = 0
            carro.save()
            carros_atras = Carro.objects.filter(na_fila=True, posicao__gt=posicao_saindo)
            for c in carros_atras:
                c.posicao -= 1
                c.save()

    @database_sync_to_async
    def chamar_carros(self, quantidade):
        carros = list(Carro.objects.filter(na_fila=True).order_by('posicao')[:quantidade])
        chamados = [c.numero for c in carros]
        posicoes_originais = {c.numero: c.posicao for c in carros}

        for carro in carros:
            posicao_saindo = carro.posicao
            carro.na_fila = False
            carro.posicao = 0
            carro.save()
            carros_atras = Carro.objects.filter(na_fila=True, posicao__gt=posicao_saindo)
            for c in carros_atras:
                c.posicao -= 1
                c.save()

        if chamados:
            detalhes = ','.join([f'{n}:{posicoes_originais[n]}' for n in chamados])
            HistoricoChamada.objects.create(carros=detalhes)

        return chamados

    @database_sync_to_async
    def desfazer_chamada(self, historico_id):
        try:
            historico = HistoricoChamada.objects.get(id=historico_id, desfeita=False)
            entradas = historico.carros.split(',')

            for entrada in entradas:
                numero, posicao_original = entrada.split(':')
                posicao_original = int(posicao_original)

                try:
                    carro = Carro.objects.get(numero=numero)
                    if not carro.na_fila:
                        carros_afetados = Carro.objects.filter(na_fila=True, posicao__gte=posicao_original)
                        for c in carros_afetados:
                            c.posicao += 1
                            c.save()
                        carro.na_fila = True
                        carro.posicao = posicao_original
                        carro.save()
                except Carro.DoesNotExist:
                    pass

            historico.desfeita = True
            historico.save()
        except HistoricoChamada.DoesNotExist:
            pass