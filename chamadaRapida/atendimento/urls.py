from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/gerar-senha/', views.gerar_senha, name='gerar_senha'),
    path('api/chamar-proxima/', views.chamar_proxima_senha, name='chamar_proxima'),
    path('api/finalizar-atendimento/', views.finalizar_atendimento, name='finalizar_atendimento'),
    path('api/simular-desistencia/', views.simular_desistencia, name='simular_desistencia'),
    path('api/alternar-posto/', views.alternar_posto, name='alternar_posto'),
    path('api/encerrar-simulacao/', views.encerrar_simulacao, name='encerrar_simulacao'),
    path('api/status/', views.obter_status, name='obter_status'),
]