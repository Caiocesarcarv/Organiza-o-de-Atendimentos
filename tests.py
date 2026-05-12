#!/usr/bin/env python3
"""
Testes automatizados para o organizador de atendimentos.
Cobrem todas as regras do problema.
"""

import unittest
from solve import (
    Atendimento, Sessao, Consultorio, organizar, parse_atendimentos,
    MANHA_INICIO, MANHA_FIM, TARDE_INICIO, TARDE_MIN_FIM, TARDE_MAX_FIM, EXPRESSO_DUR
)
import tempfile, os


class TestAtendimento(unittest.TestCase):
    def test_expresso_tem_10_minutos(self):
        a = Atendimento("Vacina", EXPRESSO_DUR)
        self.assertEqual(a.duracao, 10)

    def test_duracao_normal(self):
        a = Atendimento("Cirurgia", 90)
        self.assertEqual(a.duracao, 90)


class TestSessao(unittest.TestCase):
    def setUp(self):
        self.sessao = Sessao(MANHA_INICIO, MANHA_FIM - MANHA_INICIO)  # 210 min

    def test_cabe_atendimento_que_se_encaixa(self):
        a = Atendimento("Consulta", 30)
        self.assertTrue(self.sessao.cabe(a))

    def test_nao_cabe_atendimento_maior_que_capacidade(self):
        a = Atendimento("Cirurgia longa", 300)
        self.assertFalse(self.sessao.cabe(a))

    def test_adicionar_atualiza_tempo_usado(self):
        a = Atendimento("Consulta", 45)
        self.sessao.adicionar(a)
        self.assertEqual(self.sessao.tempo_usado, 45)

    def test_nao_cabe_quando_cheio(self):
        self.sessao.adicionar(Atendimento("A", 120))
        self.sessao.adicionar(Atendimento("B", 90))
        # Já usou 210 min = exatamente cheio
        self.assertFalse(self.sessao.cabe(Atendimento("C", 10)))

    def test_tempo_fim_correto(self):
        self.sessao.adicionar(Atendimento("A", 60))
        self.assertEqual(self.sessao.tempo_fim(), MANHA_INICIO + 60)


class TestManha(unittest.TestCase):
    def test_manha_nao_ultrapassa_1130(self):
        """Sessão da manhã nunca deve ultrapassar 11:30 (210 min a partir de 08:00)."""
        consultorios = organizar([
            Atendimento("A", 90),
            Atendimento("B", 90),
            Atendimento("C", 90),
        ])
        for c in consultorios:
            self.assertLessEqual(c.manha.tempo_usado, MANHA_FIM - MANHA_INICIO,
                msg=f"Consultório {c.numero}: manhã ultrapassa 11:30")


class TestTarde(unittest.TestCase):
    def test_reuniao_apos_17h(self):
        """Reunião de encerramento deve ocorrer depois das 17:00."""
        consultorios = organizar([
            Atendimento("A", 60),
            Atendimento("B", 60),
            Atendimento("C", 60),
            Atendimento("D", 60),
        ])
        for c in consultorios:
            fim = TARDE_INICIO + c.tarde.tempo_usado
            reuniao = max(fim, TARDE_MIN_FIM)
            self.assertGreaterEqual(reuniao, TARDE_MIN_FIM,
                msg=f"Consultório {c.numero}: reunião antes das 17:00")

    def test_reuniao_antes_18h(self):
        """Tarde não pode ultrapassar 18:00."""
        consultorios = organizar([
            Atendimento("A", 120),
            Atendimento("B", 120),
        ])
        for c in consultorios:
            fim = TARDE_INICIO + c.tarde.tempo_usado
            self.assertLessEqual(fim, TARDE_MAX_FIM,
                msg=f"Consultório {c.numero}: tarde ultrapassa 18:00")


class TestExpresso(unittest.TestCase):
    def test_expresso_alocado_corretamente(self):
        """Atendimentos expressos (10min) devem ser alocados sem erro."""
        atendimentos = [Atendimento("Vacina", EXPRESSO_DUR) for _ in range(5)]
        consultorios = organizar(atendimentos)
        total = sum(
            len(c.manha.atendimentos) + len(c.tarde.atendimentos)
            for c in consultorios
        )
        self.assertEqual(total, 5)


class TestQuantidadeConsultorios(unittest.TestCase):
    def test_poucos_atendimentos_um_consultorio(self):
        """Atendimentos pequenos devem caber em 1 consultório."""
        atendimentos = [Atendimento(f"Consulta {i}", 30) for i in range(4)]
        consultorios = organizar(atendimentos)
        # 4 * 30 = 120 min < capacidade total de 1 consultório (210+270)
        self.assertEqual(len(consultorios), 1)

    def test_todos_atendimentos_alocados(self):
        """Nenhum atendimento pode ser perdido."""
        entrada = [
            Atendimento("Cirurgia", 120), Atendimento("Castração", 90),
            Atendimento("Consulta", 45), Atendimento("Vacina", 10),
            Atendimento("Exame", 60), Atendimento("Raio-X", 30),
        ]
        consultorios = organizar(entrada)
        total = sum(
            len(c.manha.atendimentos) + len(c.tarde.atendimentos)
            for c in consultorios
        )
        self.assertEqual(total, len(entrada))


class TestParse(unittest.TestCase):
    def test_parse_lê_arquivo_corretamente(self):
        conteudo = "Cirurgia 90min\nVacina expresso\nConsulta 30min\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(conteudo)
            nome = f.name
        try:
            resultado = parse_atendimentos(nome)
            self.assertEqual(len(resultado), 3)
            self.assertEqual(resultado[0].duracao, 90)
            self.assertEqual(resultado[1].duracao, EXPRESSO_DUR)
            self.assertEqual(resultado[2].duracao, 30)
        finally:
            os.unlink(nome)

    def test_parse_arquivo_real(self):
        resultado = parse_atendimentos("atendimentos.txt")
        self.assertEqual(len(resultado), 23)


class TestEntradaCompleta(unittest.TestCase):
    def test_entrada_original_produz_solucao_valida(self):
        """Teste de integração com o arquivo de entrada fornecido no desafio."""
        atendimentos = parse_atendimentos("atendimentos.txt")
        consultorios = organizar(atendimentos)

        # Todos alocados
        total = sum(len(c.manha.atendimentos) + len(c.tarde.atendimentos) for c in consultorios)
        self.assertEqual(total, 23)

        for c in consultorios:
            # Manhã respeita 11:30
            self.assertLessEqual(c.manha.tempo_usado, MANHA_FIM - MANHA_INICIO)
            # Tarde respeita 18:00
            fim_tarde = TARDE_INICIO + c.tarde.tempo_usado
            self.assertLessEqual(fim_tarde, TARDE_MAX_FIM)


if __name__ == "__main__":
    unittest.main(verbosity=2)
