# Organização de Atendimentos — Clínica Veterinária

Solução para o desafio de escalonamento de atendimentos veterinários em múltiplos consultórios, respeitando as janelas de tempo de cada sessão.

---

## Requisitos

- **Python 3.8+**
- Sem dependências externas — usa apenas biblioteca padrão (`sys`, `re`, `dataclasses`, `unittest`)

Para verificar sua versão:

```bash
python3 --version
```

---

## Estrutura do repositório

```
.
├── solve.py           # Programa principal
├── tests.py           # Suíte de testes automatizados
├── atendimentos.txt   # Entrada de dados (lista de atendimentos)
└── RACIOCINIO.md      # Justificativa das decisões técnicas
```

---

## Como executar

### Rodar o programa principal

```bash
python3 solve.py atendimentos.txt
```

O programa lê o arquivo de entrada, distribui os atendimentos entre consultórios e imprime a agenda completa no terminal.

**Saída esperada:**

```
Total de atendimentos lidos: 23

Consultórios necessários: 3

✓ Todos os consultórios respeitam as regras de horário.

Consultório 1:
  08:00 Cirurgia ortopédica em cão atropelado 120min
  10:00 Castração de gato adulto 90min
  11:30 Higienização
  13:30 Castração de cadela em fase reprodutiva 90min
  ...
  18:00 Reunião de encerramento
...
```

### Rodar com outro arquivo de entrada

```bash
python3 solve.py outro_arquivo.txt
```

O formato esperado é um atendimento por linha:

```
Nome do atendimento 30min
Nome de atendimento rápido expresso
```

---

## Como executar os testes

```bash
python3 tests.py
```

São **16 testes automatizados** cobrindo:

- Parsing correto do arquivo de entrada
- Duração de atendimentos expressos (10 min)
- Sessão da manhã nunca ultrapassa 11:30
- Sessão da tarde nunca ultrapassa 18:00
- Reunião de encerramento ocorre após 17:00
- Nenhum atendimento é perdido na alocação
- Integração completa com o arquivo `atendimentos.txt`

Saída esperada:

```
Ran 16 tests in 0.003s

OK
```

---

## Algoritmo

A solução usa **First Fit Decreasing (FFD)**: ordena os atendimentos do maior para o menor e aloca cada um no primeiro consultório com espaço disponível. Novos consultórios são abertos somente quando nenhum existente comporta o atendimento. Isso minimiza o número de consultórios sem necessidade de força bruta.

Para entender as decisões de modelagem, estruturas de dados, complexidade e trade-offs, consulte o arquivo [`RACIOCINIO.md`](./RACIOCINIO.md).
