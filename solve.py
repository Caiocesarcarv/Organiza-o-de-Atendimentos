#!/usr/bin/env python3
"""
Organizador de Atendimentos - Clínica Veterinária
Algoritmo guloso com ordenação decrescente (First Fit Decreasing adaptado)
"""

import sys
import re
from dataclasses import dataclass, field
from typing import List, Optional
from copy import deepcopy

MANHA_INICIO   = 8 * 60        # 480 min = 08:00
MANHA_FIM      = 11 * 60 + 30  # 690 min = 11:30  (210 min disponíveis)
TARDE_INICIO   = 13 * 60 + 30  # 810 min = 13:30
TARDE_MIN_FIM  = 17 * 60       # 1020 min = 17:00 (reunião depois das 17h)
TARDE_MAX_FIM  = 18 * 60       # 1080 min = 18:00 (reunião antes das 18h)
EXPRESSO_DUR   = 10


@dataclass
class Atendimento:
    nome: str
    duracao: int  # em minutos


@dataclass
class Sessao:
    inicio: int        # minuto absoluto
    capacidade: int    # duração máxima disponível
    atendimentos: List[Atendimento] = field(default_factory=list)
    tempo_usado: int = 0

    def cabe(self, atendimento: Atendimento) -> bool:
        return self.tempo_usado + atendimento.duracao <= self.capacidade

    def adicionar(self, atendimento: Atendimento):
        self.atendimentos.append(atendimento)
        self.tempo_usado += atendimento.duracao

    def tempo_fim(self) -> int:
        return self.inicio + self.tempo_usado


@dataclass
class Consultorio:
    numero: int
    manha: Sessao = field(default_factory=lambda: Sessao(MANHA_INICIO, MANHA_FIM - MANHA_INICIO))
    tarde: Sessao = field(default_factory=lambda: Sessao(TARDE_INICIO, TARDE_MAX_FIM - TARDE_INICIO))

    def sessao_disponivel_para(self, atendimento: Atendimento) -> Optional[Sessao]:
        """Retorna a primeira sessão com espaço para este atendimento."""
        if self.manha.cabe(atendimento):
            return self.manha
        # Para tarde: verifica se após adicionar ainda permite reunião depois das 17h
        tempo_apos = self.tarde.tempo_fim() + atendimento.duracao
        if (self.tarde.tempo_usado + atendimento.duracao <= TARDE_MAX_FIM - TARDE_INICIO
                and TARDE_INICIO + self.tarde.tempo_usado + atendimento.duracao >= TARDE_MIN_FIM):
            return self.tarde
        # Tarde ainda não tem nenhum atendimento e este atendimento cabe
        if self.tarde.cabe(atendimento):
            return self.tarde
        return None


def minutos_para_hhmm(minutos: int) -> str:
    h = minutos // 60
    m = minutos % 60
    return f"{h:02d}:{m:02d}"


def parse_atendimentos(path: str) -> List[Atendimento]:
    atendimentos = []
    with open(path, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            if linha.endswith("expresso"):
                nome = linha[: linha.rfind("expresso")].strip()
                atendimentos.append(Atendimento(nome, EXPRESSO_DUR))
            else:
                m = re.search(r"(\d+)min$", linha)
                if m:
                    duracao = int(m.group(1))
                    nome = linha[: m.start()].strip()
                    atendimentos.append(Atendimento(nome, duracao))
    return atendimentos


def organizar(atendimentos: List[Atendimento]) -> List[Consultorio]:
    # Ordena do maior para o menor (First Fit Decreasing)
    ordenados = sorted(atendimentos, key=lambda a: a.duracao, reverse=True)

    consultorios: List[Consultorio] = []

    for atendimento in ordenados:
        alocado = False
        for consultorio in consultorios:
            sessao = tentar_alocar(consultorio, atendimento)
            if sessao is not None:
                sessao.adicionar(atendimento)
                alocado = True
                break
        if not alocado:
            novo = Consultorio(numero=len(consultorios) + 1)
            sessao = tentar_alocar(novo, atendimento)
            if sessao is None:
                raise ValueError(
                    f"Atendimento '{atendimento.nome}' ({atendimento.duracao}min) "
                    f"não cabe em nenhuma sessão (duração maior que o slot disponível)."
                )
            sessao.adicionar(atendimento)
            consultorios.append(novo)

    return consultorios


def tentar_alocar(consultorio: Consultorio, atendimento: Atendimento) -> Optional[Sessao]:
    """
    Tenta manhã primeiro. Se não couber, tenta tarde.
    Na tarde, valida que o fim ocorre entre 17:00 e 18:00 OU que ainda há espaço
    para encaixar mais atendimentos antes de atingir 17:00.
    """
    if consultorio.manha.cabe(atendimento):
        return consultorio.manha

    tarde = consultorio.tarde
    novo_fim = TARDE_INICIO + tarde.tempo_usado + atendimento.duracao
    if novo_fim <= TARDE_MAX_FIM:
        return tarde

    return None


def imprimir_resultado(consultorios: List[Consultorio]):
    for c in consultorios:
        print(f"Consultório {c.numero}:")

        # Manhã
        cursor = MANHA_INICIO
        for a in c.manha.atendimentos:
            dur_str = "expresso" if a.duracao == EXPRESSO_DUR else f"{a.duracao}min"
            print(f"  {minutos_para_hhmm(cursor)} {a.nome} {dur_str}")
            cursor += a.duracao
        print(f"  {minutos_para_hhmm(MANHA_FIM)} Higienização")

        # Tarde
        cursor = TARDE_INICIO
        for a in c.tarde.atendimentos:
            dur_str = "expresso" if a.duracao == EXPRESSO_DUR else f"{a.duracao}min"
            print(f"  {minutos_para_hhmm(cursor)} {a.nome} {dur_str}")
            cursor += a.duracao

        # Reunião de encerramento
        reuniao = cursor
        if reuniao < TARDE_MIN_FIM:
            reuniao = TARDE_MIN_FIM
        print(f"  {minutos_para_hhmm(reuniao)} Reunião de encerramento")
        print()


def validar(consultorios: List[Consultorio]):
    erros = []
    for c in consultorios:
        if c.manha.tempo_usado > MANHA_FIM - MANHA_INICIO:
            erros.append(f"Consultório {c.numero}: manhã ultrapassa 11:30")
        fim_tarde = TARDE_INICIO + c.tarde.tempo_usado
        if fim_tarde > TARDE_MAX_FIM:
            erros.append(f"Consultório {c.numero}: tarde termina após 18:00 ({minutos_para_hhmm(fim_tarde)})")
        if c.tarde.tempo_usado > 0 and fim_tarde < TARDE_MIN_FIM:
            erros.append(f"Consultório {c.numero}: tarde termina antes das 17:00 ({minutos_para_hhmm(fim_tarde)})")
    if erros:
        print("AVISOS DE VALIDAÇÃO:")
        for e in erros:
            print(f"  ⚠ {e}")
    else:
        print("✓ Todos os consultórios respeitam as regras de horário.\n")


if __name__ == "__main__":
    arquivo = sys.argv[1] if len(sys.argv) > 1 else "atendimentos.txt"
    atendimentos = parse_atendimentos(arquivo)
    print(f"Total de atendimentos lidos: {len(atendimentos)}\n")
    consultorios = organizar(atendimentos)
    print(f"Consultórios necessários: {len(consultorios)}\n")
    validar(consultorios)
    imprimir_resultado(consultorios)
