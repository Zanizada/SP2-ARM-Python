from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random

class Protocolo(Enum):
    OCPP_16 = "OCPP 1.6"
    OCPP_201 = "OCPP 2.0.1"
    LEGADO = "Protocolo Legado"

@dataclass
class Veiculo:
    id: int
    motorista: str
    bateria_atual: float
    bateria_desejada: float
    capacidade_kwh: float
    tempo_permanencia_horas: float
    plug_and_charge: bool
    energia_recebida: float = 0.0
    valor_total: float = 0.0

    def energia_necessaria(self) -> float:
        diferenca_percentual = self.bateria_desejada - self.bateria_atual
        return max(0, (diferenca_percentual / 100) * self.capacidade_kwh)

    def prioridade_ia(self) -> float:
        """
        Quanto menor o tempo de permanência e maior a energia necessária,
        maior a prioridade.
        """
        energia = self.energia_necessaria()
        return energia / self.tempo_permanencia_horas

@dataclass
class Carregador:
    id: int
    potencia_maxima_kw: float
    protocolo: Protocolo
    veiculo: Veiculo | None = None

    def protocolo_normalizado(self) -> str:
        """
        Simula um middleware que converte diferentes protocolos
        para um padrão interno único.
        """
        if self.protocolo == Protocolo.OCPP_201:
            return "Padrão interno GoodWe - OCPP 2.0.1"
        elif self.protocolo == Protocolo.OCPP_16:
            return "Convertido de OCPP 1.6 para OCPP 2.0.1"
        else:
            return "Convertido de protocolo legado para OCPP 2.0.1"

@dataclass
class SessaoRecarga:
    carregador: Carregador
    potencia_recebida_kw: float
    duracao_horas: float
    tarifa_kwh: float
    energia_entregue: float = field(init=False)
    valor: float = field(init=False)

    def __post_init__(self):
        self.energia_entregue = self.potencia_recebida_kw * self.duracao_horas
        self.valor = self.energia_entregue * self.tarifa_kwh

class ChargeGridIntelligence:
    def __init__(
        self,
        limite_predio_kw: float,
        consumo_predio_kw: float,
        tarifa_kwh: float
    ):
        self.limite_predio_kw = limite_predio_kw
        self.consumo_predio_kw = consumo_predio_kw
        self.tarifa_kwh = tarifa_kwh
        self.carregadores: list[Carregador] = []
        self.sessoes: list[SessaoRecarga] = []

    def adicionar_carregador(self, carregador: Carregador):
        self.carregadores.append(carregador)

    def potencia_disponivel(self) -> float:
        return max(0, self.limite_predio_kw - self.consumo_predio_kw)

    def autenticar_pagamento(self, veiculo: Veiculo) -> bool:
        """
        Simula Plug & Charge.
        Se o carro tiver plug_and_charge=True, a autenticação é automática.
        Caso contrário, simula validação manual por app/QR Code.
        """
        if veiculo.plug_and_charge:
            return True

        return random.choice([True, True, False])

    def balancear_demanda(self):
        carregadores_ocupados = [
            c for c in self.carregadores if c.veiculo is not None
        ]

        potencia_total_disponivel = self.potencia_disponivel()

        if not carregadores_ocupados:
            print("Nenhum veículo conectado.")
            return

        if potencia_total_disponivel <= 0:
            print("ALERTA: prédio sem potência disponível para recarga.")
            return

        carregadores_ocupados.sort(
            key=lambda c: c.veiculo.prioridade_ia(),
            reverse=True
        )

        soma_prioridades = sum(
            c.veiculo.prioridade_ia() for c in carregadores_ocupados
        )

        print("\n====== CHARGEGRID INTELLIGENCE ======")
        print(f"Horário da simulação: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"Limite contratado do prédio: {self.limite_predio_kw:.1f} kW")
        print(f"Consumo atual do prédio: {self.consumo_predio_kw:.1f} kW")
        print(f"Potência disponível para recarga: {potencia_total_disponivel:.1f} kW")
        print("\n======== SESSÕES DE RECARGA ========")

        for carregador in carregadores_ocupados:
            veiculo = carregador.veiculo

            pagamento_ok = self.autenticar_pagamento(veiculo)

            if not pagamento_ok:
                print(f"\nCarregador {carregador.id}")
                print(f"Motorista: {veiculo.motorista}")
                print("Pagamento recusado. Recarga não iniciada.")
                continue

            proporcao = veiculo.prioridade_ia() / soma_prioridades
            potencia_calculada = potencia_total_disponivel * proporcao
            potencia_final = min(potencia_calculada, carregador.potencia_maxima_kw)

            sessao = SessaoRecarga(
                carregador=carregador,
                potencia_recebida_kw=potencia_final,
                duracao_horas=1,
                tarifa_kwh=self.tarifa_kwh
            )

            veiculo.energia_recebida += sessao.energia_entregue
            veiculo.valor_total += sessao.valor
            self.sessoes.append(sessao)

            print(f"\nCarregador {carregador.id}")
            print(f"Motorista: {veiculo.motorista}")
            print(f"Protocolo original: {carregador.protocolo.value}")
            print(f"Interoperabilidade: {carregador.protocolo_normalizado()}")
            print(f"Plug & Charge: {'Sim' if veiculo.plug_and_charge else 'Não'}")
            print(f"Prioridade IA: {veiculo.prioridade_ia():.2f}")
            print(f"Potência liberada: {potencia_final:.2f} kW")
            print(f"Energia entregue: {sessao.energia_entregue:.2f} kWh")
            print(f"Valor cobrado: R$ {sessao.valor:.2f}")

    def resumo_financeiro(self):
        total_kwh = sum(sessao.energia_entregue for sessao in self.sessoes)
        total_reais = sum(sessao.valor for sessao in self.sessoes)

        print("\n===== RESUMO FINANCEIRO =====")
        print(f"Total de energia vendida: {total_kwh:.2f} kWh")
        print(f"Faturamento total: R$ {total_reais:.2f}")

        operador = total_reais * 0.70
        goodwe = total_reais * 0.20
        manutencao = total_reais * 0.10

        print("\nSplit de pagamento:")
        print(f"Dono do estacionamento: R$ {operador:.2f}")
        print(f"GoodWe/software: R$ {goodwe:.2f}")
        print(f"Manutenção/infraestrutura: R$ {manutencao:.2f}")

def main():
    sistema = ChargeGridIntelligence(
        limite_predio_kw=120,
        consumo_predio_kw=82,
        tarifa_kwh=2.10
    )

    veiculo_1 = Veiculo(
        id=1,
        motorista="Ana",
        bateria_atual=25,
        bateria_desejada=80,
        capacidade_kwh=60,
        tempo_permanencia_horas=2,
        plug_and_charge=True
    )

    veiculo_2 = Veiculo(
        id=2,
        motorista="Bruno",
        bateria_atual=40,
        bateria_desejada=90,
        capacidade_kwh=75,
        tempo_permanencia_horas=5,
        plug_and_charge=False
    )

    veiculo_3 = Veiculo(
        id=3,
        motorista="Carla",
        bateria_atual=15,
        bateria_desejada=70,
        capacidade_kwh=50,
        tempo_permanencia_horas=1.5,
        plug_and_charge=True
    )

    sistema.adicionar_carregador(
        Carregador(
            id=101,
            potencia_maxima_kw=22,
            protocolo=Protocolo.OCPP_201,
            veiculo=veiculo_1
        )
    )

    sistema.adicionar_carregador(
        Carregador(
            id=102,
            potencia_maxima_kw=11,
            protocolo=Protocolo.OCPP_16,
            veiculo=veiculo_2
        )
    )

    sistema.adicionar_carregador(
        Carregador(
            id=103,
            potencia_maxima_kw=22,
            protocolo=Protocolo.LEGADO,
            veiculo=veiculo_3
        )
    )

    sistema.balancear_demanda()
    sistema.resumo_financeiro()

main()