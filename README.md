# RACIOCINIO.md — Organização de Atendimentos

---

## Parte 1 — Modelagem do Problema

### 1. Como você classificou esse problema?

Classifiquei como um problema de **empacotamento em múltiplos recipientes** (*bin packing*) com **restrições de janelas de tempo** (*time window constraints*).

As características do enunciado que sustentam essa classificação são:

- **Itens com tamanhos variados**: cada atendimento tem uma duração em minutos — exatamente como itens com pesos diferentes em bin packing.
- **Recipientes com capacidade limitada**: cada sessão (manhã: 210 min, tarde: até 270 min) é um "recipiente" com capacidade fixa.
- **Múltiplos recipientes em paralelo**: vários consultórios operam ao mesmo tempo, e o problema é minimizar o número de consultórios abertos.
- **Restrição de janela**: a tarde não termina a qualquer hora — precisa respeitar o intervalo `[17:00, 18:00)` para a reunião de encerramento.

O objetivo implícito é **minimizar o número de consultórios**, o que é exatamente o objetivo clássico do bin packing: minimizar o número de bins usados.

---

### 2. Semelhança com problemas clássicos da computação

O problema é uma instância direta do **Bin Packing Problem (BPP)**, um problema NP-difícil clássico da computação.

**A analogia é direta**: imagine que cada sessão de um consultório é uma caixa com capacidade de 210 ou 270 minutos, e cada atendimento é um objeto com um "peso" em minutos. O objetivo é distribuir todos os objetos nas caixas usando o menor número de caixas possível.

Existe também semelhança com o **Job Scheduling in Parallel Machines**: consultórios são máquinas paralelas, atendimentos são jobs, e as janelas de tempo são deadlines. Nesse modelo, o objetivo seria minimizar o makespan ou respeitar os deadlines — exatamente o que a restrição da reunião de encerramento impõe.

---

### 3. Estruturas de dados escolhidas

**`Atendimento` (dataclass):**  
Representa um item a ser alocado. Contém `nome` (str) e `duracao` (int, em minutos). Usei `dataclass` pela legibilidade e pelo custo zero de implementação de `__init__`. Se tivesse usado uma tupla simples `(nome, duração)`, o código ficaria menos legível nos pontos de acesso, e a adição futura de campos (prioridade, tipo, etc.) seria mais trabalhosa.

**`Sessao` (dataclass):**  
Representa uma sessão de um consultório (manhã ou tarde). Contém `inicio` (minuto absoluto), `capacidade` (duração máxima da sessão em minutos), uma `list` de atendimentos e o acumulador `tempo_usado`. A `list` é a estrutura natural aqui: a ordem de inserção define a ordem cronológica dos atendimentos, e a operação principal é `append`. Se tivesse usado uma `deque`, ganharia O(1) em `appendleft`, mas não há necessidade de inserção no início. Se tivesse usado uma `dict` com chave de horário, a serialização ficaria mais fácil, mas a lógica de verificação de capacidade se complicaria.

**`Consultorio` (dataclass):**  
Encapsula um par `(Sessao manhã, Sessao tarde)` e um número identificador. Agrupa as duas sessões de um mesmo consultório, facilitando a lógica de alocação que tenta manhã antes da tarde.

**`List[Consultorio]` (lista principal):**  
A lista de consultórios cresce dinamicamente conforme a demanda. O acesso é sequencial (para o First Fit), então `list` é ideal. Uma `deque` não traria vantagem. Um `heap` faria sentido em variantes do algoritmo que buscam o consultório mais "cheio" primeiro (Best Fit), mas não foi a abordagem adotada.

---

## Parte 2 — Estratégia Algorítmica

### 4. Descrição do algoritmo em linguagem natural

1. **Leitura da entrada**: o programa lê o arquivo linha por linha. Para cada linha, extrai o nome do atendimento e sua duração. Se a linha termina com `expresso`, a duração é fixada em 10 minutos; caso contrário, extrai o número antes de `min`.

2. **Ordenação decrescente por duração**: antes de qualquer alocação, os atendimentos são ordenados do maior para o menor. Isso é a estratégia *First Fit Decreasing*: os atendimentos mais longos, que são mais difíceis de encaixar, são alocados primeiro quando os consultórios ainda estão "vazios" e têm mais espaço disponível.

3. **Iteração sobre os atendimentos ordenados**: para cada atendimento, o programa percorre os consultórios já abertos na ordem em que foram criados.

4. **Tentativa de alocação (First Fit)**: para cada consultório, tenta encaixar o atendimento na sessão da manhã primeiro. Se couber (sem ultrapassar 11:30), aloca ali. Se não couber na manhã, tenta a tarde (sem ultrapassar 18:00). Se couber em alguma sessão, aloca e passa para o próximo atendimento.

5. **Criação de novo consultório**: se nenhum consultório existente tiver espaço, o programa cria um novo consultório e aloca o atendimento nele.

6. **Geração da saída**: percorre cada consultório na ordem, imprimindo os horários calculados sequencialmente a partir de 08:00 (manhã) e 13:30 (tarde), intercalando a higienização e a reunião de encerramento nos horários corretos.

---

### 5. A solução é gulosa, exata, heurística ou outra?

A solução é **gulosa com heurística FFD (First Fit Decreasing)**.

**Gulosa** porque, a cada passo, toma a decisão localmente ótima — aloca o atendimento no primeiro consultório disponível que o aceite — sem revisar decisões anteriores.

**Com heurística FFD** porque aplica a ordenação decrescente antes da alocação, o que melhora empiricamente o resultado do algoritmo guloso puro (First Fit sem ordenação).

Cheguei a essa decisão pelo seguinte raciocínio: a solução ótima (menor número possível de consultórios) exigiria testar todas as combinações possíveis, o que é inviável mesmo para entradas médias (o bin packing é NP-difícil). A heurística FFD é conhecida por produzir resultados próximos do ótimo na maioria dos casos práticos, com complexidade O(n log n) — adequada para uma aplicação real de clínica veterinária que pode ter centenas de atendimentos por dia.

---

### 6. Entrada para a qual o algoritmo não encontraria a melhor solução

Sim. Por ser guloso, o algoritmo pode falhar em encontrar o ótimo em casos específicos. Exemplo concreto:

```
Atendimento A  120min
Atendimento B  120min
Atendimento C  90min
Atendimento D  90min
Atendimento E  90min
```

**O que acontece com FFD:**
- A (120) → Consultório 1, manhã
- B (120) → Consultório 1, manhã: não cabe (120+120=240 > 210). Vai para tarde: cabe. Fim: 15:30.
- C (90) → Consultório 1, manhã: não cabe. Tarde: 120+90=210 min, fim 17:00. Cabe.
- D (90) → Consultório 1: manhã não cabe, tarde não cabe (210+90>270). Consultório 2, manhã: cabe.
- E (90) → Consultório 1: lotado. Consultório 2, manhã: 90+90=180 ≤ 210. Cabe.

**Resultado: 2 consultórios.** Provavelmente é o ótimo aqui, mas considere:

```
Atendimento A  100min
Atendimento B  100min
Atendimento C  100min
Atendimento D  100min
Atendimento E  10min (expresso)
```

FFD aloca A e B na manhã do consultório 1 (200 min), C e D na manhã do 2 (200 min), E na manhã do 1 (sobra). Usa 2 consultórios — que é ótimo aqui. Mas se houvesse uma restrição extra de que C e D precisam ficar juntos na tarde, o algoritmo guloso não respeitaria isso, pois não há esse conceito de dependência na implementação atual.

Um caso real de subótimo acontece quando um atendimento de 60min é colocado numa manhã com 70min de espaço, bloqueando dois atendimentos de 35min que caberiam no mesmo espaço — o FFD priorizaria o maior e possivelmente forçaria abertura de novo consultório.

---

### 7. Complexidade de tempo

**O(n log n)**

Raciocínio:

- **Leitura do arquivo**: O(n) — percorre cada linha uma vez.
- **Ordenação**: O(n log n) — Python usa Timsort.
- **Loop de alocação**: para cada um dos n atendimentos, percorre no pior caso todos os consultórios abertos. O número de consultórios abertos é no máximo O(n) (se cada atendimento ocupar um consultório inteiro), e para cada consultório o teste de alocação é O(1). Logo, o loop interno é O(n) no pior caso, tornando o loop total O(n²) no pior caso.
- **Geração da saída**: O(n) — percorre todos os atendimentos alocados.

**Dominante: O(n²) no pior caso, O(n log n) no caso médio.**

Na prática, o número de consultórios abertos cresce muito mais devagar que n (pois cada consultório absorve vários atendimentos), então o comportamento observado se aproxima de O(n log n). Para entradas realistas de uma clínica (dezenas a algumas centenas de atendimentos), a diferença é imperceptível.

---

## Parte 3 — Decisões de Implementação

### 8. Como o programa decide quantos consultórios abrir?

O programa **não decide antecipadamente** — ele descobre dinamicamente. A estratégia é: só abrir um novo consultório quando nenhum dos já existentes conseguir acomodar o atendimento atual.

O critério de teste é: "cabe na manhã sem passar de 11:30, ou cabe na tarde sem passar de 18:00?" Se nenhum consultório existente satisfaz isso, cria-se um novo.

Essa abordagem é chamada de *lazy allocation* (alocação preguiçosa) e é natural para problemas de bin packing: você não sabe quantos bins vai precisar de antemão, então abre novos apenas quando necessário. Isso implicitamente minimiza o número de consultórios abertos.

---

### 9. Como os atendimentos expressos foram tratados?

Atendimentos expressos são normalizados para **10 minutos durante o parsing** e, a partir daí, tratados exatamente como qualquer outro atendimento.

A decisão foi deliberada: ao uniformizar a representação na entrada, o algoritmo de alocação não precisa de nenhum caso especial para "expresso". Isso simplifica o código e reduz o risco de bugs.

A alternativa seria criar um campo booleano `is_expresso` e tratar diferentemente em vários pontos do código — aumentaria a complexidade ciclomática sem benefício real. A única situação em que faria diferença é na saída: na exibição, verificamos se `duracao == 10` para reimprimir "expresso" em vez de "10min", mantendo fidelidade ao formato original.

Uma decisão alternativa seria pré-alocar todos os expressos no fim de cada sessão (como "preenchimento de lacunas"), o que poderia melhorar a eficiência de empacotamento. Não adotei isso para manter o algoritmo uniforme.

---

### 10. Trecho mais inteligente e trecho que poderia ser melhorado

**Parte mais inteligente — a ordenação decrescente antes da alocação:**

```python
ordenados = sorted(atendimentos, key=lambda a: a.duracao, reverse=True)
```

Uma linha que faz uma diferença enorme no resultado. Sem ela, o algoritmo seria First Fit puro: se os primeiros atendimentos na lista forem pequenos, eles ocupariam espaço que poderia ser melhor aproveitado por atendimentos grandes que aparecem depois, levando à abertura desnecessária de consultórios. A ordenação decrescente garante que os itens "difíceis" (longos) sejam alocados primeiro, quando há mais liberdade de encaixe. Essa transformação simples é o que diferencia o FF do FFD, e a garantia teórica do FFD é que ele usa no máximo `11/9 * OPT + 6/9` bins — muito próximo do ótimo.

**Parte que poderia ser melhorada — a função `tentar_alocar`:**

```python
def tentar_alocar(consultorio: Consultorio, atendimento: Atendimento) -> Optional[Sessao]:
    if consultorio.manha.cabe(atendimento):
        return consultorio.manha
    tarde = consultorio.tarde
    novo_fim = TARDE_INICIO + tarde.tempo_usado + atendimento.duracao
    if novo_fim <= TARDE_MAX_FIM:
        return tarde
    return None
```

O problema aqui é que a função não valida ativamente a restrição `>= 17:00` da reunião de encerramento para consultórios que têm a tarde vazia ou com poucos atendimentos. A regra diz que a reunião deve ocorrer *depois* das 17:00 — se a tarde de um consultório tiver apenas 30 min de atendimento (terminando às 14:00), a reunião "teoricamente" aconteceria às 14:00, o que viola a regra.

A solução atual contorna isso na saída, forçando a reunião para 17:00 se o fim real for anterior. Mas o correto seria validar isso na lógica de alocação ou garantir, na saída, que consultórios com tarde vazia exibam a reunião às 17:00 explicitamente. Um refactor extrairia um método `calcular_horario_reuniao(sessao_tarde) -> int` que encapsulasse essa lógica em um único lugar.
