from django.contrib import admin
from django.db import connection
from .models import Clientes, ContasBancarias, ContasLedger, TransacoesLedger, LancamentosLedger


@admin.register(Clientes)
class ClientesAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "documento")


@admin.register(ContasBancarias)
class ContasBancariasAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "moeda", "status", "saldo_disponivel")
    
    def saldo_disponivel(self, obj):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(ll.valor_assinado), 0)
                FROM lancamentos_ledger ll
                JOIN contas_ledger cl
                  ON cl.id = ll.conta_ledger_id
                WHERE cl.conta_bancaria_id = %s
                  AND cl.tipo = 'disponivel'
                """,
                [str(obj.id)],
            )
            row = cursor.fetchone()

        saldo_centavos = row[0] if row else 0
        return f"R$ {saldo_centavos / 100:.2f}"

    saldo_disponivel.short_description = "Saldo disponível"


@admin.register(ContasLedger)
class ContasLedgerAdmin(admin.ModelAdmin):
    list_display = ("id", "conta_bancaria_id", "tipo", "criado_em")


@admin.register(TransacoesLedger)
class TransacoesLedgerAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente_id", "tipo", "chave_idempotencia", "iniciado_por", "criado_em")


@admin.register(LancamentosLedger)
class LancamentosLedgerAdmin(admin.ModelAdmin):
    list_display = ("id", "transacao_id", "conta_ledger_id", "valor_assinado", "criado_em")