# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Clientes(models.Model):
    id = models.UUIDField(primary_key=True)
    nome_completo = models.TextField()
    documento = models.TextField(unique=True, blank=True, null=True)
    criado_em = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.nome_completo

    class Meta:
        managed = False
        db_table = 'clientes'


class ContasBancarias(models.Model):
    id = models.UUIDField(primary_key=True)
    cliente = models.OneToOneField(Clientes, models.DO_NOTHING, blank=True, null=True)
    moeda = models.CharField(max_length=3)
    status = models.TextField()
    criado_em = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Conta de {self.cliente}"

    class Meta:
        managed = False 
        db_table = 'contas_bancarias'


class ContasLedger(models.Model):
    id = models.UUIDField(primary_key=True)
    conta_bancaria = models.ForeignKey(ContasBancarias, models.DO_NOTHING, blank=True, null=True)
    tipo = models.TextField()
    criado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'contas_ledger'
        unique_together = (('conta_bancaria', 'tipo'),)

class LancamentosLedger(models.Model):
    id = models.UUIDField(primary_key=True)
    transacao = models.ForeignKey('TransacoesLedger', models.DO_NOTHING)
    conta_ledger = models.ForeignKey(ContasLedger, models.DO_NOTHING)
    valor_assinado = models.BigIntegerField()
    criado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'lancamentos_ledger'


class TransacoesLedger(models.Model):
    id = models.UUIDField(primary_key=True)
    tipo = models.TextField()
    chave_idempotencia = models.UUIDField(unique=True)
    dados = models.JSONField(blank=True, null=True)
    iniciado_por = models.TextField()
    criado_em = models.DateTimeField()
    cliente = models.ForeignKey(Clientes, models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.cliente} - {self.id}"

    class Meta:
        managed = False
        db_table = 'transacoes_ledger'
