from django.contrib import admin
from .models import Senha, PostoAtendimento, Simulacao

@admin.register(Senha)
class SenhaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'data_hora_emissao', 'atendida', 'desistiu', 'data_hora_atendimento', 'posto_atendimento')
    list_filter = ('tipo', 'atendida', 'desistiu')
    search_fields = ('numero',)
    date_hierarchy = 'data_hora_emissao'

@admin.register(PostoAtendimento)
class PostoAtendimentoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'ativo', 'ocupado', 'senha_atual')
    list_filter = ('ativo', 'ocupado')
    search_fields = ('numero',)

@admin.register(Simulacao)
class SimulacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'em_andamento', 'data_inicio', 'data_fim', 'senhas_atendidas', 'desistencias')
    list_filter = ('em_andamento',)
    readonly_fields = ('data_inicio',)