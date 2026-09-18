from django.core.management.base import BaseCommand
from django.db import transaction

from reservas.models import Veiculo


class Command(BaseCommand):
    help = "Cria frota didática: 8 leves e 2 coletivos. Não sobrescreve veículos existentes."

    @transaction.atomic
    def handle(self, *args, **options):
        criados = 0
        for prefixo, categoria, quantidade in [("VL", "LEVE", 8), ("VC", "COLETIVO", 2)]:
            for numero in range(1, quantidade + 1):
                _, novo = Veiculo.objects.get_or_create(codigo=f"{prefixo}-{numero:02}", defaults={"categoria": categoria})
                criados += int(novo)
        self.stdout.write(self.style.SUCCESS(f"Frota didática: {criados} veículo(s) criado(s). Cadastros existentes preservados."))
