# Entrega do Projeto Integrador — Checkpoint Aulas 7, 8 e 9 (CCD610)

| Campo | Preenchimento |
|---|---|
| Grupo | _preencher_ |
| Integrantes | _preencher (substituem "Integrante A–D" nos documentos)_ |
| Produto | **DataTrack · Radar de Absenteísmo**: prevê quem tem risco de faltar para o Head de Operações reorganizar a escala antes de a meta ser afetada |
| Repositório GitHub | _preencher após `python scripts/github_setup.py init --repo <dono>/datatrack`_ |
| Quadro Kanban (Miro/Trello ou GitHub Projects) | _preencher_ |
| Workflow de CI | _preencher: `https://github.com/<dono>/datatrack/actions/workflows/tests.yml`_ |
| Pull request revisado | _preencher com o PR revisado por um colega_ |

> **Situação honesta em 11/11/2026.** Tudo o que depende só do código está pronto e foi
> executado localmente: 135 testes passando, cobertura de 91,0%, ruff sem alertas, relatórios
> gerados por script. **O que depende do GitHub e de outra pessoa ainda não existe**: repositório
> com histórico, PRs, CI rodando, main protegida, issues e revisão por um colega. O roteiro
> pronto para isso está na seção "O que falta para fechar a entrega", no fim.

---

## Evolução do projeto (Aulas 1 a 9)

| Aula | Entregável | Onde está |
|---|---|---|
| 1–3 | Repositório, CRISP-DM, persona (Guilherme Ramos, Head de Operações) e Canvas MVP (F1–F6) | `README.md`, `docs/01-backlog.md` (seção Canvas MVP) |
| 4 | Backlog com 10 histórias e critérios Dado/Quando/Então | `docs/01-backlog.md`, `docs/backlog_issues.csv` |
| 5 | Pipeline modular (ingest → features → train → serve) com SOLID | `src/data`, `src/ml`, `src/serving`, `docs/03-arquitetura.md` |
| 6 | WBS, estimativas, matriz de riscos e plano da Sprint 1 | `docs/04-planejamento-e-riscos.md` |
| **7** | Sprint 1 executada: código, quadro, review e retrospectiva | `docs/backlog.md`, `docs/kanban.md`, `docs/sprint_review.md`, `docs/retrospective.md`, `docs/xp_implementation.md` |
| **8** | Autoavaliação N/P/L/F e plano com 3 ações | `reports/maturity_assessment.md`, `docs/improvement_plan.md`, `docs/meeting_minutes.md` |
| **9** | Testes, qualidade de dados, SBAR, revisão | `src/validate.py`, `sql/quality_checks.sql`, `reports/quality_report*.md`, `reports/sbar.md`, `tests/` |

A ligação Aula 8 → Aula 9 pedida no enunciado: a autoavaliação deu nota baixa em Garantia da
Qualidade (revisão) e Gestão de Riscos (R1). A resposta na Aula 9 foi a validação de dados com
6 regras, a quarentena da QC06, o portão de qualidade antes do treino e o modelo com alvo
redefinido.

---

## Parte 1 — Sprint 1 e Gestão de Configurações (Aula 7)

**Links:** repositório _preencher_ · quadro _preencher_

| Exigência do enunciado | Situação | Evidência |
|---|---|---|
| Código da Sprint 1 na main, com PRs revisados e histórico por branches | ⏳ preparado | `scripts/github_setup.py` cria 7 branches e 7 PRs em ordem de dependência; validado localmente |
| Main protegida e CI rodando nos PRs | ⏳ preparado | `.github/workflows/tests.yml`; `github_setup.py init` aplica a proteção (1 aprovação, checks obrigatórios, conversas resolvidas) |
| Quadro Kanban com issues ligadas às histórias | ⏳ preparado | `docs/kanban.md`; issues a partir de `docs/backlog_issues.csv` (12 histórias) |

### Meta da sprint e resultado

| Item | Valor |
|---|---|
| Meta | Pipeline ponta a ponta gerando a lista ranqueada por risco, com dados validados e pseudonimizados e baseline medido |
| Planejado | 21 pts (US1–US5); escopo final de **31 pts** com US11 e US12 adicionadas durante a sprint (+48%) |
| Concluído pela Definition of Done | **0 de 31 pts**: todos os critérios técnicos foram cumpridos, mas falta o PR revisado por um colega |
| Tecnicamente pronto, aguardando revisão | 31 pts (+ US6, adiantada da Onda 2) |

### Rastreabilidade das histórias

| História | Issue | Branch | Pull request e teste |
|---|---|---|---|
| US3, US4 | _#_ | `feature/US3-US4-ingestao-lgpd` | PR 1 · `tests/test_ingest.py` |
| US2 | _#_ | `feature/US2-modelo-operacional` | PR 2 · `tests/test_train.py`, `tests/test_features.py` |
| US1, US5, US6 | _#_ | `feature/US1-US5-US6-ranking` | PR 3 · `tests/test_serve.py` |
| US11 | _#_ | `feature/US11-qualidade-dados` | PR 4 · `tests/test_validate.py`, `tests/test_smoke.py` |
| US12 | _#_ | `feature/US12-autenticacao` | PR 5 · `tests/test_auth.py` |
| US2 (por funcionário), US8 | _#_ | `feature/US2-modelo-por-funcionario` | PR 6 · `tests/test_employee_model.py` |

Os números de issue e PR são preenchidos automaticamente por `python scripts/github_setup.py trace`
(gera `docs/rastreabilidade.md`).

### Ata da Sprint Review (resumo de `docs/sprint_review.md`)

- **Demonstrado:** ranking de risco com faixas e fatores; modelo com split temporal (AUC 0,754 e
  recall 0,644 em dados sintéticos); ingestão com LGPD; exportação CSV; 6 regras de qualidade
  em pandas e SQL; login com dashboard; em 11/11, modelo por funcionário na base Kaggle.
- **Feedback (simulado, identificado como tal):** "se 8 de cada 10 alertas forem falsos, os
  líderes param de olhar" (precisão de 0,21); "quero ver o motivo do risco"; painéis antigos
  apertados no celular.
- **Backlog reordenado:** (1) levar os 8 cartões em revisão a Feito via PR; (2) refinar a US2
  com critério de precisão e fonte de dados; (3) resolver o comentário bloqueante da QC05;
  (4) US7, a única história nova que cabe; (5) US8 e US10; (6) US9.

### Ata da Retrospectiva (resumo de `docs/retrospective.md`)

- **Start:** PR por história com revisão; análise de impacto antes de aceitar escopo; medir precisão; datar cartões.
- **Stop:** chamar de "pronto" o que só tem teste verde; puxar trabalho com a coluna de revisão cheia; tratar dado sintético como validação.
- **Continue:** critérios com número; módulos separados; métricas geradas por script; validar dados antes de usar.

| Ação de melhoria | Responsável | Prazo |
|---|---|---|
| PR com aprovação de quem não escreveu o código; main protegida | Integrante A | 20/11/2026 |
| WIP ≤ 4 em "Em revisão"; escopo novo só com troca registrada | Integrante D | até 20/11/2026 |

---

## Parte 2 — Autoavaliação de Maturidade (Aula 8)

**Link do checklist e evidências:** `reports/maturity_assessment.md` (18 perguntas com evidência por arquivo)

| Área de processo | Evidência (artefato) | Nota (Q1 · Q2 · Q3) |
|---|---|---|
| Gestão de Requisitos | `docs/backlog.md` (critérios G/W/T com teste citado); `docs/02-requisitos.md`; mudança de escopo registrada só depois do fato | F · L · P |
| Planejamento | `docs/04-planejamento-e-riscos.md` (pontos, capacidade, WBS sem US11/US12); baseline em `reports/metrics.md` | F · L · P |
| Gestão de Configuração | sem histórico Git verificável; estratégia em `docs/xp_implementation.md`; `.gitignore` e dependências | **N** · P · L |
| Garantia da Qualidade | 135 testes, 91,0% de cobertura, ruff 0; nenhuma revisão por par real | F · L · **N** |
| Medição e Análise | `scripts/collect_metrics.py`, `reports/metrics.md`; dois pontos de medição | F · L · P |
| Gestão de Riscos | matriz R1–R6, `docs/risk_log.md` (11/11), ações sobre R1; R7 novo | F · L · L |

Contagem: **F = 5 · L = 7 · P = 4 · N = 2** (em 06/11: F 5 · L 5 · P 6 · N 2).

### Plano de melhoria (exatamente 3 ações — `docs/improvement_plan.md`)

| Ação | Responsável e prazo | Indicador de sucesso |
|---|---|---|
| 1. Revisão por par real com histórico Git (ataca as duas notas N) | Integrante A · 20/11/2026 | 100% dos PRs mergeados com ≥ 1 aprovação de outra pessoa; ≥ 50% dos pontos em Feito na Sprint 2 |
| 2. CI como portão de merge + lock de dependências | Integrante B · 20/11/2026 | 100% dos merges com o check `tests` verde; cobertura ≥ 80%; ruff 0 |
| 3. Tratar riscos materializados, a começar pelo R1 (fonte de dados) | Integrante C (fonte) e D (registro de riscos) · 20/11 e 04/12/2026 | modelo treinado em base não sintética com recall ≥ 0,60 e AUC ≥ 0,70, **ou** registro formal de que a meta não é atingível; risco no log a cada sprint |

### Decisões do grupo (`docs/meeting_minutes.md`)

- A DoD **não** é afrouxada: sem PR revisado, nada vai para Feito.
- A US2 ganha um critério de precisão; registros da QC06 ficam em quarentena; `--strict` antes do treino (feito em 11/11).
- A Sprint 2 tem tema "levar o que existe a Feito", com no máximo 8 pts de história nova.
- (11/11) Todo AUC da base otimizada aparece com o aviso "semi-sintética" e com o AUC 0,50 da base original; registrar a origem do CSV otimizado (R7).

---

## Parte 3 — Qualidade de Dados e de Código (Aula 9)

**Links:** workflow de CI _preencher_ · PR revisado _preencher_

| Exigência do enunciado | Situação | Evidência |
|---|---|---|
| Suíte pytest passando no CI e ruff sem alertas | ✅ local · ⏳ CI | 135/135 testes, 91,0% de cobertura, ruff 0 (`reports/junit.xml`, `reports/coverage.json`, `reports/ruff.txt`) |
| Relatório de qualidade com regras, resultados e situação | ✅ | `reports/quality_report_full_base.md`, `reports/quality_report.md` |
| PR revisado por um colega, com comentários e respostas | ⏳ depende do grupo | roteiro em `docs/pr_review_guide.md`; exemplo **simulado** em `docs/peer_review_simulation.md` |

### Relatório de qualidade de dados (base `_2_otimizado`, 100.000 registros)

| Dimensão | Regra | Resultado | Situação |
|---|---|---|---|
| Completude | QC01 · 8 campos obrigatórios preenchidos | 100.000/100.000 (100,00%) | Aprovada |
| Unicidade | QC02 · `Employee_ID` único | 100.000/100.000 (100,00%) | Aprovada |
| Validade | QC03 · categorias no catálogo | 100.000/100.000 (100,00%) | Aprovada |
| Validade | QC04 · números na faixa de negócio | 100.000/100.000 (100,00%) | Aprovada |
| Consistência | QC05 · tempo de casa coerente com a admissão | 100.000/100.000 (100,00%) | Aprovada |
| Consistência | QC06 · admissão com 18 anos ou mais | 96.216/100.000 (96,22%) | **Reprovada** (meta 99%) |

Conformidade geral de **99,37%**; status **LIBERADA COM RESSALVAS**. SQL e pandas dão os mesmos
números nas 6 regras. Observação de linhagem: a base de trabalho tem `Sick_Days` regerado
(`reports/data_lineage.md`). As regras dão o mesmo resultado na base original.

### SBAR da pior falha (`reports/sbar.md`)

- **S · Situação:** a QC06 reprova 3.784 registros (3,78%): funcionários que teriam sido
  admitidos com 12 a 17 anos, 256 deles com 12 ou 13.
- **B · Contexto:** as outras 5 regras passam com 100%; o tempo de casa bate com a data de
  admissão em 100% dos casos, então o problema está na combinação idade × tempo de casa. As
  falhas se espalham por igual entre os departamentos.
- **A · Avaliação:** padrão típico de base sintética, que sorteia idade e tempo de casa de
  forma independente (inferência). É impossível em qualquer regime de trabalho para 256 casos
  e incompatível com os cargos nos demais. Reforça o R1: a base não representa uma operação real.
- **R · Recomendação:** quarentena dos registros (feito); QC06 como portão antes do treino
  (feito); não usar `Age` como atributo (feito); levar a decisão sobre a fonte de dados ao
  professor/PO (pendente). Não "corrigir" idade nem tempo de casa por imputação.

### Resumo da revisão do pull request

_Preencher com a revisão real (`docs/pr_review_guide.md`)._ Para referência, a simulação levantou:

| Comentário (simulado) | Tipo | Como resolver |
|---|---|---|
| Data de referência da QC05 fixa em 2024-09-04 no código e no SQL | Bloqueante | parâmetro `--reference-date` e `julianday(?)` no SQL |
| Limite de tentativas de login em memória por processo | Sugestão | armazenamento compartilhado em produção |
| Scripts de CDN sem versão fixa e sem SRI nos painéis | Segurança | fixar versões + `integrity`, ou servir localmente |

---

## O que falta para fechar a entrega (checklist do grupo)

| # | Tarefa | Quem | Como |
|---|---|---|---|
| 1 | Criar repositório **novo e público** no GitHub (a proteção de branch em repositório privado exige plano pago) | A | github.com/new, sem README |
| 2 | Rodar `python scripts/github_setup.py init --repo <dono>/datatrack --project` | A | cria labels, 12 issues, commit base, push, proteção da main e quadro |
| 3 | Abrir os 7 PRs em ordem (`plan` mostra a ordem); cada um **revisado por outro integrante** antes do merge | todos | `python scripts/github_setup.py pr <passo>` |
| 4 | No quadro, mover cada issue para a coluna certa; colar o link aqui | D | GitHub Projects (ou Trello/Miro, com link para as issues) |
| 5 | `python scripts/github_setup.py trace` e copiar a tabela para a Parte 1 | A | gera `docs/rastreabilidade.md` |
| 6 | Registrar autor e regra do CSV `_2_otimizado` em `docs/05-dados-reais.md` | quem gerou | R7 |
| 7 | Trocar "Integrante A–D" pelos nomes; preencher grupo e links nesta página e no slide de capa | todos | — |
