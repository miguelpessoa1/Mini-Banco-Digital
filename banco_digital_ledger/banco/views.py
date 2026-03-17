from django.shortcuts import render
from django.db import connection
import json


def query_valor_unico(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        row = cursor.fetchone()
    return row[0] if row else 0


def query_varias_linhas(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        rows = cursor.fetchall()
    return rows


def get_totais_dashboard():
    total_clientes = query_valor_unico("SELECT COUNT(*) FROM clientes")
    total_contas = query_valor_unico("SELECT COUNT(*) FROM contas_bancarias")
    total_transacoes = query_valor_unico("SELECT COUNT(*) FROM transacoes_ledger")

    saldo_total_centavos = query_valor_unico(
        """
        SELECT COALESCE(SUM(ll.valor_assinado), 0)
        FROM lancamentos_ledger ll
        JOIN contas_ledger cl
          ON cl.id = ll.conta_ledger_id
        WHERE cl.tipo = 'disponivel'
        """
    )

    return {
        "total_clientes": total_clientes,
        "total_contas": total_contas,
        "total_transacoes": total_transacoes,
        "saldo_total": saldo_total_centavos / 100,
    }


def get_ultimas_transacoes():
    return query_varias_linhas(
        """
        SELECT tipo, iniciado_por, criado_em
        FROM transacoes_ledger
        ORDER BY criado_em DESC
        LIMIT 10
        """
    )


def get_transacoes_por_dia():
    rows = query_varias_linhas(
        """
        SELECT DATE(criado_em) AS dia, COUNT(*) AS total
        FROM transacoes_ledger
        GROUP BY DATE(criado_em)
        ORDER BY dia
        """
    )

    labels = [str(row[0]) for row in rows]
    valores = [row[1] for row in rows]

    return {
        "labels_transacoes": json.dumps(labels),
        "valores_transacoes": json.dumps(valores),
    }


def get_maiores_saldos():
    rows = query_varias_linhas(
        """
        SELECT
            cb.id,
            c.nome_completo,
            COALESCE(SUM(ll.valor_assinado), 0) AS saldo_centavos
        FROM contas_bancarias cb
        JOIN clientes c
          ON c.id = cb.cliente_id
        JOIN contas_ledger cl
          ON cl.conta_bancaria_id = cb.id
        LEFT JOIN lancamentos_ledger ll
          ON ll.conta_ledger_id = cl.id
        WHERE cl.tipo = 'disponivel'
        GROUP BY cb.id, c.nome_completo
        ORDER BY saldo_centavos DESC
        LIMIT 5
        """
    )

    return [(row[0], row[1], row[2] / 100) for row in rows]


def get_contas_mais_movimentadas():
    return query_varias_linhas(
        """
        SELECT
            cb.id,
            c.nome_completo,
            COUNT(ll.id) AS total_lancamentos
        FROM contas_bancarias cb
        JOIN clientes c
          ON c.id = cb.cliente_id
        JOIN contas_ledger cl
          ON cl.conta_bancaria_id = cb.id
        LEFT JOIN lancamentos_ledger ll
          ON ll.conta_ledger_id = cl.id
        GROUP BY cb.id, c.nome_completo
        ORDER BY total_lancamentos DESC
        LIMIT 5
        """
    )


def dashboard(request):
    context = {}
    context.update(get_totais_dashboard())
    context["ultimas_transacoes"] = get_ultimas_transacoes()
    context.update(get_transacoes_por_dia())
    context["maiores_saldos"] = get_maiores_saldos()
    context["contas_mais_movimentadas"] = get_contas_mais_movimentadas()

    return render(request, "banco/dashboard.html", context)


def extrato_conta(request, conta_id):
    extrato = query_varias_linhas(
        """
        SELECT
            tl.tipo,
            ll.valor_assinado,
            ll.criado_em
        FROM lancamentos_ledger ll
        JOIN transacoes_ledger tl
          ON tl.id = ll.transacao_id
        JOIN contas_ledger cl
          ON cl.id = ll.conta_ledger_id
        WHERE cl.conta_bancaria_id = %s
          AND cl.tipo = 'disponivel'
        ORDER BY ll.criado_em DESC
        """,
        [str(conta_id)],
    )

    extrato = [(row[0], row[1] / 100, row[2]) for row in extrato]

    return render(
        request,
        "banco/extrato_conta.html",
        {"extrato": extrato, "conta_id": conta_id},
    )