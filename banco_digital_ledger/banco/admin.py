from django.contrib import admin
from .models import Clientes, ContasBancarias, ContasLedger, TransacoesLedger, LancamentosLedger

admin.site.register(Clientes)
admin.site.register(ContasBancarias)
admin.site.register(ContasLedger)
admin.site.register(TransacoesLedger)
admin.site.register(LancamentosLedger)
