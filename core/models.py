from django.db import models
from django.contrib.auth.models import User

class Produto(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    custo_compra = models.FloatField()
    preco_final = models.FloatField()
    quantidade_estoque = models.IntegerField(default=0)

    def __str__(self):
        return self.nome

class Venda(models.Model):
    nome_cliente = models.CharField(max_length=255)
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='vendas',
    )
    quantidade = models.PositiveIntegerField()
    vendedor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='vendas',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    @property
    def lucro(self):
        return (self.produto.preco_final - self.produto.custo_compra) * self.quantidade

    def __str__(self):
        return f'{self.produto.nome} — {self.nome_cliente}'
