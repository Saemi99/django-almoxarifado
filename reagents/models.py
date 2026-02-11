from django.db import models

class Coordenacao(models.Model):
    id = models.AutoField(primary_key=True)
    nome =  models.CharField(max_length=200)

    def __str__(self):
        return self.nome
    
class Controlador(models.Model):
    id = models.AutoField(primary_key=True)
    nome =  models.CharField(max_length=200)

    def __str__(self):
        return self.nome

class Reagente(models.Model):
    id = models.AutoField(primary_key=True)
    reagente_nome = models.CharField(max_length=200)
    fispq = models.CharField(max_length=50)

    controlador = models.ForeignKey(Controlador, on_delete=models.PROTECT, related_name='reagentes')
    
    armario = models.CharField(max_length=50)

    validade = models.DateField('data de validade')
    data_entrada = models.DateTimeField(auto_now_add=True)
    nota_fiscal = models.FileField(upload_to='notas_fiscais/', blank=True, null=True)

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.reagente_nome
    
class ReagenteCoordenacao(models.Model):
    reagente = models.ForeignKey(Reagente, on_delete=models.CASCADE)
    coordenacao = models.ForeignKey(Coordenacao, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('reagente','coordenacao')

    def __str__(self):
        return f"{self.reagente} - {self.coordenacao}:{self.quantidade}"
    
class SaidaReagente(models.Model):
    reagente= models.ForeignKey(Reagente, on_delete=models.PROTECT)
    coordenacao = models.ForeignKey(Coordenacao, on_delete=models.PROTECT)

    requisitante = models.CharField(max_length=200)
    quantidade = models.PositiveIntegerField()

    data_saida = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.reagente} - {self.quantidade} ({self.coordenacao})"