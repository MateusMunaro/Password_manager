import random
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Senha, PostoAtendimento, Simulacao, TipoSenha

def index(request):
    """
    View principal que renderiza a página inicial
    """
    # Inicializa os postos de atendimento se ainda não existirem
    if PostoAtendimento.objects.count() == 0:
        for i in range(1, 6):
            # Por padrão, os 3 primeiros postos estão ativos
            ativo = i <= 3
            PostoAtendimento.objects.create(numero=i, ativo=ativo, ocupado=False)
    
    # Inicializa ou recupera a simulação atual
    simulacao = Simulacao.objects.filter(em_andamento=True).first()
    if not simulacao:
        simulacao = Simulacao.objects.create(em_andamento=True)
    
    # Recupera informações para o template
    postos = PostoAtendimento.objects.all()
    senhas_normais = Senha.objects.filter(tipo=TipoSenha.NORMAL, atendida=False, desistiu=False).count()
    senhas_prioritarias = Senha.objects.filter(tipo=TipoSenha.PRIORITARIA, atendida=False, desistiu=False).count()
    
    context = {
        'simulacao': simulacao,
        'postos': postos,
        'senhas_normais': senhas_normais,
        'senhas_prioritarias': senhas_prioritarias,
    }
    
    return render(request, 'atendimento/index.html', context)

@csrf_exempt
def gerar_senha(request):
    """
    API para gerar uma nova senha
    """
    if request.method == 'POST':
        # Determinar o tipo de senha (normal ou prioritária)
        tipo = request.POST.get('tipo')
        if tipo not in [TipoSenha.NORMAL, TipoSenha.PRIORITARIA]:
            tipo = random.choice([TipoSenha.NORMAL, TipoSenha.PRIORITARIA])
        
        # Obter a simulação atual
        simulacao = Simulacao.objects.filter(em_andamento=True).first()
        
        # Gerar número sequencial de acordo com o tipo
        if tipo == TipoSenha.NORMAL:
            numero = simulacao.contador_senha_normal + 1
            simulacao.contador_senha_normal = numero
        else:
            numero = simulacao.contador_senha_prioritaria + 1
            simulacao.contador_senha_prioritaria = numero
        
        simulacao.save()
        
        # Criar a senha
        senha = Senha.objects.create(
            numero=numero,
            tipo=tipo
        )
        
        return JsonResponse({
            'status': 'success',
            'senha': str(senha)
        })
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})

@csrf_exempt
def chamar_proxima_senha(request):
    """
    API para chamar a próxima senha de acordo com a regra 2N:1P
    """
    if request.method == 'POST':
        # Obter a simulação atual
        simulacao = Simulacao.objects.filter(em_andamento=True).first()
        
        # Verificar se há postos livres
        posto_livre = PostoAtendimento.objects.filter(ativo=True, ocupado=False).first()
        if not posto_livre:
            return JsonResponse({
                'status': 'error',
                'message': 'Não há postos disponíveis'
            })
        
        # Implementar a lógica 2N:1P
        senhas_atendidas = Senha.objects.filter(atendida=True).count()
        
        # Determinar qual tipo de senha chamar
        if senhas_atendidas % 3 == 2:  # A cada 3 senhas, a 3ª é prioritária
            # Chamar senha prioritária
            proxima_senha = Senha.objects.filter(
                tipo=TipoSenha.PRIORITARIA, 
                atendida=False,
                desistiu=False
            ).order_by('data_hora_emissao').first()
            
            if not proxima_senha:
                # Se não houver senha prioritária, chamar normal
                proxima_senha = Senha.objects.filter(
                    tipo=TipoSenha.NORMAL, 
                    atendida=False,
                    desistiu=False
                ).order_by('data_hora_emissao').first()
        else:
            # Chamar senha normal
            proxima_senha = Senha.objects.filter(
                tipo=TipoSenha.NORMAL, 
                atendida=False,
                desistiu=False
            ).order_by('data_hora_emissao').first()
            
            if not proxima_senha:
                # Se não houver senha normal, chamar prioritária
                proxima_senha = Senha.objects.filter(
                    tipo=TipoSenha.PRIORITARIA, 
                    atendida=False,
                    desistiu=False
                ).order_by('data_hora_emissao').first()
        
        if not proxima_senha:
            return JsonResponse({
                'status': 'error',
                'message': 'Não há senhas aguardando atendimento'
            })
        
        # Atualizar a senha e o posto
        proxima_senha.atendida = True
        proxima_senha.data_hora_atendimento = timezone.now()
        proxima_senha.posto_atendimento = posto_livre
        proxima_senha.save()
        
        posto_livre.ocupado = True
        posto_livre.senha_atual = proxima_senha
        posto_livre.save()
        
        simulacao.senhas_atendidas += 1
        simulacao.save()
        
        return JsonResponse({
            'status': 'success',
            'senha': str(proxima_senha),
            'posto': posto_livre.numero
        })
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})

@csrf_exempt
def finalizar_atendimento(request):
    """
    API para finalizar o atendimento de um posto
    """
    if request.method == 'POST':
        posto_id = request.POST.get('posto_id')
        try:
            posto = PostoAtendimento.objects.get(id=posto_id)
            if posto.ocupado and posto.senha_atual:
                posto.ocupado = False
                senha = posto.senha_atual
                posto.senha_atual = None
                posto.save()
                
                return JsonResponse({
                    'status': 'success',
                    'posto': posto.numero,
                    'senha': str(senha)
                })
            return JsonResponse({
                'status': 'error',
                'message': 'O posto não está ocupado'
            })
        except PostoAtendimento.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Posto não encontrado'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})

@csrf_exempt
def simular_desistencia(request):
    """
    API para simular a desistência de um cliente
    """
    if request.method == 'POST':
        # Selecionar uma senha que está aguardando atendimento
        senhas_aguardando = Senha.objects.filter(atendida=False, desistiu=False)
        if senhas_aguardando.exists():
            # Selecionar uma senha aleatória para desistir
            index = random.randint(0, senhas_aguardando.count() - 1)
            senha_desistente = senhas_aguardando[index]
            senha_desistente.desistiu = True
            senha_desistente.save()
            
            simulacao = Simulacao.objects.filter(em_andamento=True).first()
            simulacao.desistencias += 1
            simulacao.save()
            
            return JsonResponse({
                'status': 'success',
                'senha': str(senha_desistente)
            })
        
        return JsonResponse({
            'status': 'error',
            'message': 'Não há senhas aguardando para desistir'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})

@csrf_exempt
def alternar_posto(request):
    """
    API para ativar/desativar um posto de atendimento
    """
    if request.method == 'POST':
        posto_id = request.POST.get('posto_id')
        try:
            posto = PostoAtendimento.objects.get(id=posto_id)
            
            # Verificar se é um dos 3 primeiros postos (que devem estar sempre ativos)
            if posto.numero <= 3:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Os 3 primeiros postos devem estar sempre ativos'
                })
            
            # Não permitir desativar um posto ocupado
            if posto.ocupado and posto.ativo:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Não é possível desativar um posto ocupado'
                })
            
            posto.ativo = not posto.ativo
            posto.save()
            
            return JsonResponse({
                'status': 'success',
                'posto': posto.numero,
                'ativo': posto.ativo
            })
        except PostoAtendimento.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Posto não encontrado'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})

@csrf_exempt
def encerrar_simulacao(request):
    """
    API para encerrar a simulação e mostrar os resultados
    """
    if request.method == 'POST':
        simulacao = Simulacao.objects.filter(em_andamento=True).first()
        if simulacao:
            simulacao.em_andamento = False
            simulacao.data_fim = timezone.now()
            simulacao.save()
            
            # Obter todas as senhas atendidas, ordenadas pela data de atendimento (pilha)
            senhas_atendidas = Senha.objects.filter(
                atendida=True
            ).order_by('-data_hora_atendimento')
            
            # Converter para lista de strings
            lista_senhas = [str(senha) for senha in senhas_atendidas]
            
            return JsonResponse({
                'status': 'success',
                'senhas_atendidas': lista_senhas,
                'total_atendidas': simulacao.senhas_atendidas,
                'total_desistencias': simulacao.desistencias
            })
        
        return JsonResponse({
            'status': 'error',
            'message': 'Não há simulação em andamento'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})

def obter_status(request):
    """
    API para obter o status atual do sistema
    """
    simulacao = Simulacao.objects.filter(em_andamento=True).first()
    if not simulacao:
        return JsonResponse({
            'status': 'error',
            'message': 'Não há simulação em andamento'
        })
    
    # Obter postos
    postos = PostoAtendimento.objects.all()
    postos_info = []
    for posto in postos:
        info = {
            'id': posto.id,
            'numero': posto.numero,
            'ativo': posto.ativo,
            'ocupado': posto.ocupado,
            'senha_atual': str(posto.senha_atual) if posto.senha_atual else None
        }
        postos_info.append(info)
    
    # Obter senhas aguardando
    senhas_normais = list(Senha.objects.filter(
        tipo=TipoSenha.NORMAL, 
        atendida=False, 
        desistiu=False
    ).order_by('data_hora_emissao')[:2].values('id', 'numero', 'tipo'))
    
    senhas_prioritarias = list(Senha.objects.filter(
        tipo=TipoSenha.PRIORITARIA, 
        atendida=False, 
        desistiu=False
    ).order_by('data_hora_emissao')[:2].values('id', 'numero', 'tipo'))
    
    # Determinando as próximas duas senhas
    proximas_senhas = []
    
    # Lógica 2N:1P
    senhas_atendidas = Senha.objects.filter(atendida=True).count()
    ciclo_atual = senhas_atendidas % 3
    
    if ciclo_atual == 2:  # A próxima senha deve ser prioritária
        if senhas_prioritarias:
            proximas_senhas.append({
                'numero': senhas_prioritarias[0]['numero'],
                'tipo': senhas_prioritarias[0]['tipo']
            })
            # A segunda próxima seria normal
            if len(senhas_normais) > 0:
                proximas_senhas.append({
                    'numero': senhas_normais[0]['numero'],
                    'tipo': senhas_normais[0]['tipo']
                })
            elif len(senhas_prioritarias) > 1:
                proximas_senhas.append({
                    'numero': senhas_prioritarias[1]['numero'],
                    'tipo': senhas_prioritarias[1]['tipo']
                })
        elif senhas_normais:
            # Se não houver prioritárias, chamar normais
            proximas_senhas.append({
                'numero': senhas_normais[0]['numero'],
                'tipo': senhas_normais[0]['tipo']
            })
            if len(senhas_normais) > 1:
                proximas_senhas.append({
                    'numero': senhas_normais[1]['numero'],
                    'tipo': senhas_normais[1]['tipo']
                })
    else:  # A próxima senha deve ser normal
        if senhas_normais:
            proximas_senhas.append({
                'numero': senhas_normais[0]['numero'],
                'tipo': senhas_normais[0]['tipo']
            })
            # A segunda próxima depende do ciclo
            if ciclo_atual == 0 and len(senhas_normais) > 1:
                # Se estamos no início do ciclo, a segunda também é normal
                proximas_senhas.append({
                    'numero': senhas_normais[1]['numero'],
                    'tipo': senhas_normais[1]['tipo']
                })
            elif ciclo_atual == 1 and senhas_prioritarias:
                # Se estamos no meio do ciclo, a segunda é prioritária
                proximas_senhas.append({
                    'numero': senhas_prioritarias[0]['numero'],
                    'tipo': senhas_prioritarias[0]['tipo']
                })
            elif len(senhas_normais) > 1:
                # Fallback para normal se não houver prioritárias
                proximas_senhas.append({
                    'numero': senhas_normais[1]['numero'],
                    'tipo': senhas_normais[1]['tipo']
                })
        elif senhas_prioritarias:
            # Se não houver normais, chamar prioritárias
            proximas_senhas.append({
                'numero': senhas_prioritarias[0]['numero'],
                'tipo': senhas_prioritarias[0]['tipo']
            })
            if len(senhas_prioritarias) > 1:
                proximas_senhas.append({
                    'numero': senhas_prioritarias[1]['numero'],
                    'tipo': senhas_prioritarias[1]['tipo']
                })
    
    # Determinar próximo posto disponível
    proximo_posto = PostoAtendimento.objects.filter(ativo=True, ocupado=False).first()
    proximo_posto_numero = proximo_posto.numero if proximo_posto else None
    
    total_aguardando = Senha.objects.filter(atendida=False, desistiu=False).count()
    
    return JsonResponse({
        'status': 'success',
        'simulacao': {
            'id': simulacao.id,
            'em_andamento': simulacao.em_andamento,
            'senhas_atendidas': simulacao.senhas_atendidas,
            'desistencias': simulacao.desistencias
        },
        'postos': postos_info,
        'proximas_senhas': proximas_senhas,
        'proximo_posto': proximo_posto_numero,
        'total_aguardando': total_aguardando
    })