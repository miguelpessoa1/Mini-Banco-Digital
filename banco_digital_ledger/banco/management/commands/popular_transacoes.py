import random
import uuid

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Cria clientes, contas e gera transações de teste no ledger"

    def add_arguments(self, parser):
        parser.add_argument("--clientes", type=int, default=50)
        parser.add_argument("--transacoes", type=int, default=10000)

    def handle(self, *args, **options):
        total_clientes = options["clientes"]
        total_transacoes = options["transacoes"]

        self.stdout.write(self.style.WARNING("Iniciando população do banco..."))

        conta_sistema_id = self.get_or_create_conta_sistema()
        clientes_contas = self.criar_clientes_e_contas(total_clientes)

        self.stdout.write(self.style.SUCCESS(f"{len(clientes_contas)} contas prontas para uso."))

        self.gerar_transacoes(clientes_contas, conta_sistema_id, total_transacoes)

        self.stdout.write(self.style.SUCCESS("População concluída com sucesso."))

    def get_or_create_conta_sistema(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM contas_ledger
                WHERE tipo = 'sistema'
                LIMIT 1
                """
            )
            row = cursor.fetchone()

            if row:
                return row[0]

            conta_sistema_id = str(uuid.uuid4())

            cursor.execute(
                """
                INSERT INTO contas_ledger (id, conta_bancaria_id, tipo, criado_em)
                VALUES (%s, NULL, 'sistema', NOW())
                """,
                [conta_sistema_id],
            )

            return conta_sistema_id

    def criar_clientes_e_contas(self, total_clientes):
        contas = []

        with connection.cursor() as cursor:
            for i in range(total_clientes):
                cliente_id = str(uuid.uuid4())
                conta_bancaria_id = str(uuid.uuid4())
                conta_disponivel_id = str(uuid.uuid4())
                conta_bloqueado_id = str(uuid.uuid4())

                nome = f"Cliente Teste {i+1}"
                documento = f"{10000000000 + i}"

                cursor.execute(
                    """
                    INSERT INTO clientes (id, nome_completo, documento, criado_em)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (documento) DO NOTHING
                    """,
                    [cliente_id, nome, documento],
                )

                cursor.execute(
                    """
                    SELECT id
                    FROM clientes
                    WHERE documento = %s
                    """,
                    [documento],
                )
                cliente_id = cursor.fetchone()[0]

                cursor.execute(
    """
    INSERT INTO contas_bancarias (id, cliente_id, moeda, status, criado_em)
    VALUES (%s, %s, 'BRL', 'ativa', NOW())
    ON CONFLICT (cliente_id) DO NOTHING
    """,
    [conta_bancaria_id, cliente_id],
)

                cursor.execute(
    """
    SELECT id
    FROM contas_bancarias
    WHERE cliente_id = %s
    """,
    [cliente_id],
)

                conta_bancaria_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO contas_ledger (id, conta_bancaria_id, tipo, criado_em)
                    VALUES (%s, %s, 'disponivel', NOW())
                    ON CONFLICT (conta_bancaria_id, tipo) DO NOTHING
                    """,
                    [conta_disponivel_id, conta_bancaria_id],
                )

                cursor.execute(
                    """
                    INSERT INTO contas_ledger (id, conta_bancaria_id, tipo, criado_em)
                    VALUES (%s, %s, 'bloqueado', NOW())
                    ON CONFLICT (conta_bancaria_id, tipo) DO NOTHING
                    """,
                    [conta_bloqueado_id, conta_bancaria_id],
                )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT cb.id, cb.cliente_id, cl.id
                FROM contas_bancarias cb
                JOIN contas_ledger cl
                  ON cl.conta_bancaria_id = cb.id
                WHERE cl.tipo = 'disponivel'
                """
            )
            rows = cursor.fetchall()

        for row in rows:
            contas.append(
                {
                    "conta_bancaria_id": row[0],
                    "cliente_id": row[1],
                    "conta_disponivel_id": row[2],
                }
            )

        return contas

    def gerar_transacoes(self, clientes_contas, conta_sistema_id, total_transacoes):

        for conta in clientes_contas:
            valor_inicial = random.randint(5000, 50000)

            try:
                self.executar_funcao(
                    "postar_deposito",
                    [
                        str(conta["cliente_id"]),
                        str(conta["conta_disponivel_id"]),
                        str(conta_sistema_id),
                        valor_inicial,
                        str(uuid.uuid4()),
                        "script_inicial",
                    ],
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro no depósito inicial: {e}"))
        
        for i in range(total_transacoes):
            operacao = random.choices(
                ["deposito", "saque", "transferencia"],
                weights=[50, 20, 30],
                k=1,
            )[0]

            try:
                if operacao == "deposito":
                    conta = random.choice(clientes_contas)
                    valor = random.randint(100, 20000)

                    self.executar_funcao(
                        "postar_deposito",
                        [
                            str(conta["cliente_id"]),
                            str(conta["conta_disponivel_id"]),
                            str(conta_sistema_id),
                            valor,
                            str(uuid.uuid4()),
                            "script",
                        ],
                    )

                elif operacao == "saque":
                    conta = random.choice(clientes_contas)
                    valor = random.randint(100, 10000)

                    self.executar_funcao(
                        "postar_saque",
                        [
                            str(conta["cliente_id"]),
                            str(conta["conta_disponivel_id"]),
                            str(conta_sistema_id),
                            valor,
                            str(uuid.uuid4()),
                            "script",
                        ],
                    )

                else:
                    origem = random.choice(clientes_contas)
                    destino = random.choice(clientes_contas)

                    while destino["conta_disponivel_id"] == origem["conta_disponivel_id"]:
                        destino = random.choice(clientes_contas)

                    valor = random.randint(100, 10000)

                    self.executar_funcao(
                        "postar_transferencia",
                        [
                            str(origem["cliente_id"]),
                            str(destino["cliente_id"]),
                            str(origem["conta_disponivel_id"]),
                            str(destino["conta_disponivel_id"]),
                            valor,
                            str(uuid.uuid4()),
                            "script",
                        ],
                    )

                if (i + 1) % 1000 == 0:
                    self.stdout.write(self.style.WARNING(f"{i + 1} transações processadas..."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro na transação {i + 1}: {e}"))
                continue

    def executar_funcao(self, nome_funcao, params):
        placeholders = ", ".join(["%s"] * len(params))

        with transaction.atomic():
            with connection.cursor() as cursor:
                sql = f"SELECT {nome_funcao}({placeholders})"
                self.stdout.write(f"Executando: {sql} com params={params}")
                cursor.execute(sql, params)