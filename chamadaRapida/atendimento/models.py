from django.db import models
from django.utils import timezone

class TipoSenha(models.TextChoices):
    NORMAL = 'N', 'Normal'
    PRIORITARIA = 'P', 'Prioritária'

class Senha(models.Model):
    """
    Modelo para representar senhas de atendimento
    """
    numero = models.IntegerField()
    tipo = models.CharField(
        max_length=1,
        choices=TipoSenha.choices,
        default=TipoSenha.NORMAL
    )
    data_hora_emissao = models.DateTimeField(default=timezone.now)
    atendida = models.BooleanField(default=False)
    desistiu = models.BooleanField(default=False)
    data_hora_atendimento = models.DateTimeField(null=True, blank=True)
    posto_atendimento = models.ForeignKey(
        'PostoAtendimento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='senhas_atendidas'
    )
    
    def __str__(self):
        return f"{self.tipo}{self.numero}"
    
    class Meta:
        ordering = ['data_hora_emissao']
        verbose_name = 'Senha'
        verbose_name_plural = 'Senhas'

class PostoAtendimento(models.Model):
    """
    Modelo para representar postos de atendimento
    """
    numero = models.IntegerField(unique=True)
    ativo = models.BooleanField(default=True)
    ocupado = models.BooleanField(default=False)
    senha_atual = models.OneToOneField(
        Senha,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posto_atual'
    )
    
    def __str__(self):
        return f"Posto {self.numero}"
    
    class Meta:
        ordering = ['numero']
        verbose_name = 'Posto de Atendimento'
        verbose_name_plural = 'Postos de Atendimento'

class Simulacao(models.Model):
    """
    Modelo para controlar a simulação de atendimento
    """
    em_andamento = models.BooleanField(default=False)
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    contador_senha_normal = models.IntegerField(default=0)
    contador_senha_prioritaria = models.IntegerField(default=0)
    senhas_atendidas = models.IntegerField(default=0)
    desistencias = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Simulação {self.id}"
    
    class Meta:
        verbose_name = 'Simulação'
        verbose_name_plural = 'Simulações'