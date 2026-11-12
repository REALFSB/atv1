# Backlog da Sprint 1 — DataTrack · Radar de Absenteísmo

> **Persona:** Guilherme Ramos, Head de Operações (persona fictícia do projeto).
> **Origem:** US1–US5 vêm de `docs/01-backlog.md` (planejamento da Sprint 1, 21 pts).
> US11 e US12 entraram **durante** a Sprint 1, por exigência das Aulas 9 e do módulo de
> login — ver a seção *Mudança de escopo* abaixo.
> Estimativas de US11 e US12 são **propostas**: validar no Planning Poker do grupo
> (escala 1, 2, 3, 5, 8, 13).

## Resumo

| ID | História (resumo) | Pontos | Prioridade | MoSCoW | Entrada |
|---|---|---:|:-:|:-:|---|
| US4 | Proteger dados pessoais (LGPD) | 3 | 1 | Must | Planejada |
| US3 | Barrar dados incompletos/inválidos | 3 | 2 | Must | Planejada |
| US1 | Lista ranqueada por risco de ausência | 5 | 3 | Must | Planejada |
| US2 | Modelo com recall/AUC mínimos | 8 | 4 | Must | Planejada |
| US12 | Login e proteção das páginas | 5 | 5 | Must | Adicionada na sprint |
| US11 | Regras de qualidade de dados com relatório | 5 | 6 | Should | Adicionada na sprint |
| US5 | Exportar lista em CSV | 2 | 7 | Should | Planejada |
| | **Total** | **31** | | | 21 planejados + 10 adicionados |

**Critério de prioridade:** primeiro o que remove risco legal e de dados (US4, US3 — o risco
R1/R3 da matriz), depois o ciclo mínimo de valor (US1 → US2). US12 sobe para *Must* porque
expor o ranking de risco de pessoas sem login viola o próprio RNF4 (acesso mínimo). US11
amplia US3 (de "barrar" para "medir e relatar"), por isso fica logo abaixo. US5 é
conveniência: pode ser cortada se a capacidade apertar (já previsto no risco R6).

---

## US1 · Lista ranqueada por risco de ausência · 5 pts · Prioridade 3 (Must)

**Como** Guilherme, **quero** uma lista de operadores ordenada por risco de ausência no
próximo turno, **para** remanejar pessoas antes de a escala furar.

**Critérios de aceite**
- **Dado** dados de 60 dias de 155 operadores, **quando** gero a lista, **então** ela vem
  ordenada do maior para o menor risco, com `rank` de 1 a N.
- **Então** cada operador tem faixa `Alta`, `Média` ou `Baixa`.
- **Então** a lista é gerada em até 5 s (RNF2).

Testes: `tests/test_serve.py::test_ranking_is_sorted_desc_with_bands`,
`test_latency_under_5s_for_155_operators`.

## US2 · Modelo com recall e AUC mínimos · 8 pts · Prioridade 4 (Must)

**Como** Guilherme, **quero** que o modelo identifique a maior parte das ausências reais,
**para** confiar na lista.

**Critérios de aceite**
- **Dado** o modelo treinado, **quando** avaliado nos últimos 25% dos dias (split temporal),
  **então** recall ≥ 0,60 e ROC-AUC ≥ 0,70, gravados em `artifacts/metrics.json`.
- **Então** não há vazamento: a maior data de treino é anterior à menor data de teste.

Testes: `tests/test_train.py::test_metrics_meet_targets_on_synthetic`,
`test_time_split_has_no_leakage`.
⚠️ Critério atendido **apenas com dados sintéticos** (ver Sprint Review, item 2).

## US3 · Barrar dados incompletos ou inválidos · 3 pts · Prioridade 2 (Must)

**Como** Guilherme, **quero** que dados incompletos sejam barrados antes do treino, **para**
evitar decisões com dado ruim.

**Critérios de aceite**
- **Dado** um arquivo com mais de 5% de nulos em coluna obrigatória, **quando** a ingestão
  roda, **então** o processo para com erro que lista cada coluna e seu % de nulos.
- **Dado** coluna obrigatória ausente, **então** o erro cita o nome da coluna.

Testes: `tests/test_ingest.py::test_validate_rejects_*`.

## US4 · Proteger dados pessoais (LGPD) · 3 pts · Prioridade 1 (Must)

**Como** Guilherme, **quero** que o sistema não use identificadores diretos nem dados de
saúde, **para** cumprir a LGPD.

**Critérios de aceite**
- **Dado** uma base com ID e colunas de saúde, **quando** a ingestão roda, **então** o ID
  sai como hash SHA-256 com sal e as colunas de saúde são descartadas.
- **Então** o mesmo ID com o mesmo sal gera sempre o mesmo hash; sal diferente gera hash
  diferente.

Testes: `tests/test_ingest.py::test_pseudonymize_*`, `test_sensitive_columns_are_dropped`.

## US5 · Exportar lista em CSV · 2 pts · Prioridade 7 (Should)

**Como** Guilherme, **quero** exportar a lista em CSV, **para** compartilhar com os líderes.

**Critérios de aceite**
- **Dado** uma lista gerada, **quando** exporto, **então** o CSV tem todas as linhas e as
  colunas `rank`, `risk` e `band`.

Teste: `tests/test_serve.py::test_export_csv_keeps_all_rows`.

## US11 · Regras de qualidade de dados com relatório · 5 pts · Prioridade 6 (Should)

**Como** Guilherme, **quero** que a base passe por regras de qualidade com um relatório
por regra, **para** saber se posso confiar nela antes de usar.

**Critérios de aceite**
- **Dado** uma base de funcionários, **quando** rodo `python -m src.validate`, **então**
  recebo, para cada uma das 6 regras, avaliados, aprovados, reprovados, % de conformidade
  e status.
- **Então** as regras cobrem completude, unicidade, validade e consistência.
- **Dado** que uma regra crítica (completude ou unicidade) reprova, **então** o status final
  da base é `BLOQUEADA`; com `--strict`, o comando retorna código 1.
- **Então** as consultas de `sql/quality_checks.sql` dão exatamente os mesmos números que
  o motor pandas.

Testes: `tests/test_validate.py` (todos), `tests/test_smoke.py`.

## US12 · Login e proteção das páginas · 5 pts · Prioridade 5 (Must)

**Como** Guilherme, **quero** entrar com e-mail e senha, **para** que só pessoas autorizadas
vejam o ranking de risco dos operadores.

**Critérios de aceite**
- **Dado** credenciais válidas, **quando** entro, **então** vou para o dashboard com
  saudação e botão de sair.
- **Dado** senha errada ou e-mail inexistente, **então** vejo a mesma mensagem
  "E-mail ou senha inválidos." (não revela se o e-mail existe).
- **Dado** campos vazios, **então** vejo o erro de cada campo e a requisição retorna 400.
- **Dado** que não estou logado, **quando** abro o dashboard ou um painel, **então** sou
  levado ao login e, após entrar, volto à página pedida.
- **Quando** saio, **então** a sessão termina e as páginas privadas voltam a exigir login.
- **Então** a senha é armazenada só como hash (nunca em texto puro).

Testes: `tests/test_auth.py` (todos).

---

## Mudança de escopo durante a sprint

| Item | Valor |
|---|---|
| Planejado no início | 21 pts (US1–US5) para capacidade assumida de 22 pts |
| Adicionado durante a sprint | US11 (5) + US12 (5) = 10 pts (+48%) |
| Removido para compensar | nada |
| Análise de impacto registrada antes da entrada | **não** (registrada só nesta revisão) |

Isso é o risco **R5** (crescimento de escopo) acontecendo. A retrospectiva trata o assunto.

## Fora da Sprint 1 (Onda 2)

US6 (fatores de risco), US7 (alerta de mudança de faixa), US8 (impacto na meta), US9
(drift/PSI), US10 (relatório PDF) — detalhes em `docs/01-backlog.md`. Situação de cada uma
no quadro: `docs/kanban.md`.
