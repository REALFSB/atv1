# Autoavaliação de maturidade do processo (CMMI / MPS.BR)

> **Escopo:** repositório DataTrack. Primeira avaliação em 06/11/2026; **reavaliação parcial
> em 11/11/2026** (só Gestão de Riscos mudou; ver "Histórico das notas" no fim). **Referência:** áreas de processo do CMMI-DEV v1.3 (REQM, PP, CM, PPQA,
> MA, RSKM) e seus equivalentes no MPS.BR (GRE, GPR, GCO, GQA, MED; riscos dentro de GPR).
> **Regra adotada:** só vale como evidência o que está em um arquivo deste repositório.
> Prática sem evidência recebe N, mesmo que o grupo afirme tê-la feito — é assim que uma
> avaliação oficial (SCAMPI / MA-MPS) trataria. Nenhum PR, commit ou aprovação foi
> inventado: o ZIP recebido **não contém a pasta `.git`**.

**Escala:** N = não praticado · P = parcialmente praticado · L = largamente praticado ·
F = totalmente praticado.

## Resumo por área

| Área | Q1 | Q2 | Q3 | Síntese |
|---|:-:|:-:|:-:|---|
| Gestão de Requisitos | F | L | P | Histórias testáveis e rastreáveis; mudança de escopo sem controle |
| Planejamento | F | L | P | Estimativa e capacidade existem; sem comparação planejado × realizado anterior |
| Gestão de Configuração | N | P | L | Sem histórico Git verificável; estratégia só documentada |
| Garantia da Qualidade | F | L | N | Testes e lint fortes; nenhuma revisão por par independente |
| Medição e Análise | F | L | P | Métricas automáticas e reproduzíveis; só um ponto de medição |
| Gestão de Riscos | F | L | L | Riscos reavaliados com registro; R1 tratado, mas surgiu R7 (dado sem proveniência) |

Contagem geral (18 perguntas, 11/11/2026): **F = 5 · L = 7 · P = 4 · N = 2**
(em 06/11/2026: F = 5 · L = 5 · P = 6 · N = 2).

---

## 1. Gestão de Requisitos (CMMI REQM · MPS.BR GRE)

| # | Pergunta | Nota | Evidência |
|---|---|:-:|---|
| Q1 | Toda história da Sprint 1 tem critério de aceite verificável (Dado/Quando/Então com valor objetivo)? | **F** | `docs/01-backlog.md`: US1–US10 com G/W/T e números (5 s, recall ≥ 0,60, 5% de nulos). `docs/backlog.md`: US11 e US12 com critérios no mesmo formato. |
| Q2 | Há rastreabilidade requisito → história → módulo → teste? | **L** | `docs/02-requisitos.md` liga RF/RNF a histórias; `docs/03-arquitetura.md` liga histórias a módulos; `docs/backlog.md` cita o teste de cada critério; testes têm comentários `# US3`, `# US4`. Falta matriz única e verificável automaticamente — a ligação teste → história depende de comentários. |
| Q3 | Mudanças de requisito passam por análise de impacto antes de entrar na sprint? | **P** | US11 e US12 (+10 pts, +48%) entraram sem registro prévio de impacto; a análise só existe agora, em `docs/backlog.md` ("Mudança de escopo"). Há registro, mas depois do fato. |

## 2. Planejamento (CMMI PP · MPS.BR GPR)

| # | Pergunta | Nota | Evidência |
|---|---|:-:|---|
| Q1 | Existe estimativa em pontos e capacidade declarada para a sprint? | **F** | `docs/04-planejamento-e-riscos.md`: pontos por história, capacidade de 22 pts com hipótese explícita (4 pessoas, 2 semanas), meta da sprint. |
| Q2 | A WBS cobre 100% do escopo da sprint? | **L** | WBS em `docs/04-planejamento-e-riscos.md` cobre US1–US10. US11 e US12 não têm pacote de trabalho. |
| Q3 | O planejado é comparado com o realizado (velocidade, burndown)? | **P** | Primeira comparação só nesta entrega (`reports/metrics.md`, seção 5). Não há burndown nem datas de início/fim por cartão, então lead time e cycle time não são mensuráveis. |

## 3. Gestão de Configuração (CMMI CM · MPS.BR GCO)

| # | Pergunta | Nota | Evidência |
|---|---|:-:|---|
| Q1 | O código está sob controle de versão com histórico rastreável (commits ligados a histórias)? | **N** | O material avaliado não contém `.git`. Não há como verificar um único commit. (Se o repositório remoto tiver histórico, a nota deve ser refeita com ele — ver plano de melhoria, ação 1.) |
| Q2 | Há estratégia de branches e de integração definida **e** praticada? | **P** | Definida: `.github/pull_request_template.md` e `docs/xp_implementation.md` §4. Praticada: sem evidência. |
| Q3 | Os itens de configuração e o que fica fora do versionamento estão identificados? | **L** | `.gitignore` exclui dados brutos (LGPD), artefatos, banco de usuários e segredos; `requirements.txt` e `pyproject.toml` listam dependências. Dependências usam `>=` sem lock file, então duas instalações podem divergir. |

## 4. Garantia da Qualidade (CMMI PPQA · MPS.BR GQA)

| # | Pergunta | Nota | Evidência |
|---|---|:-:|---|
| Q1 | Os critérios de aceite são verificados por testes automatizados que passam? | **F** | 135 testes, 135 aprovados, cobertura de 91,0% (linhas + ramos; medição de 11/11/2026, eram 107 e 90,3% em 06/11) — `reports/metrics.md`, `reports/junit.xml`, `reports/coverage.json`. Cada critério de US1–US5, US11 e US12 tem teste citado em `docs/backlog.md`. |
| Q2 | Há verificação objetiva automática (lint, cobertura mínima) aplicada a todo código? | **L** | `ruff` com 0 achados (`reports/ruff.txt`); `fail_under = 80` no `pyproject.toml`. Mas o workflow `.github/workflows/tests.yml` **nunca rodou**: hoje a verificação depende de alguém executar localmente. |
| Q3 | Existe revisão independente (por par) antes de considerar a entrega pronta? | **N** | Nenhum PR ou aprovação comprovável. `docs/peer_review_simulation.md` é **simulação** e foi feita por quem escreveu o código — não é independente. |

## 5. Medição e Análise (CMMI MA · MPS.BR MED)

| # | Pergunta | Nota | Evidência |
|---|---|:-:|---|
| Q1 | As métricas têm definição, fórmula e fonte declaradas? | **F** | `reports/metrics.md` traz fórmula e fonte de cada número; `scripts/collect_metrics.py` documenta as fontes no cabeçalho. |
| Q2 | A coleta é automática e reproduzível? | **L** | `python scripts/collect_metrics.py --run` regenera tudo; `tests/test_smoke.py::test_committed_quality_report_matches_current_code` falha se o relatório versionado divergir do código. Limitação: só roda localmente (CI não publicado) e a base completa fica fora do Git. |
| Q3 | As métricas formam série histórica usada em decisões? | **P** | Existe apenas a medição desta entrega (baseline). Ela já embasou decisões na ata (`docs/meeting_minutes.md`), mas sem série não há tendência. |

## 6. Gestão de Riscos (CMMI RSKM · MPS.BR GPR)

| # | Pergunta | Nota | Evidência |
|---|---|:-:|---|
| Q1 | Os riscos estão identificados com probabilidade, impacto, exposição, resposta e responsável? | **F** | Matriz R1–R6 em `docs/04-planejamento-e-riscos.md`, com exposição = prob. × impacto. |
| Q2 | Os riscos são reavaliados a cada sprint, com registro? | **L** (era P) | Duas reavaliações registradas: `docs/meeting_minutes.md` (06/11) e `docs/risk_log.md` (11/11), com status, exposição, ação e responsável por risco. Ainda não é "a cada sprint" comprovado: só uma sprint fechada. |
| Q3 | Riscos que se materializam geram ação com responsável e prazo? | **L** (era P) | **R1:** alvo redefinido e modelo por funcionário implementado (`src/ml/kaggle_risk.py`); quarentena da QC06 implementada (decisão D4). **R5:** regra de troca de escopo na retrospectiva. Não é F porque a decisão sobre a fonte de dados segue pendente com o professor/PO e o novo **R7** (CSV derivado sem autor nem regra registrados) ainda não tem a ação concluída. |

---

## Histórico das notas

| Data | Pergunta | De → Para | Motivo (evidência) |
|---|---|:-:|---|
| 11/11/2026 | Gestão de Riscos Q2 | P → L | `docs/risk_log.md` criado (Ação 3b do plano) |
| 11/11/2026 | Gestão de Riscos Q3 | P → L | R1 tratado em código; quarentena QC06 (`src/ml/kaggle_risk.py`, `docs/05-dados-reais.md`) |
| 11/11/2026 | Gestão de Configuração Q3 | L → L | mantida, com ressalva: entrou um dado derivado (`_2_otimizado`) sem registro de origem (R7) |

As notas N de Gestão de Configuração Q1 e Garantia da Qualidade Q3 **não mudam** até existirem
PRs revisados de verdade no GitHub (`scripts/github_setup.py`, `docs/pr_review_guide.md`).

## Leitura crítica

1. **Os pontos fortes são técnicos, os fracos são de processo.** Testes, cobertura, lint e
   métricas estão bons; o que falta é o que só existe quando há **mais de uma pessoa
   participando com registro**: revisão por par, histórico de versões, reavaliação de risco.
2. **As duas notas N vêm da mesma causa:** não existe histórico Git verificável. Uma única
   ação (repositório com PRs revisados) mexe em 3 perguntas (GC Q1, GC Q2, GQA Q3).
3. **Cuidado com o F em GQA Q1:** 90% de cobertura em código que treina com **dados
   sintéticos** prova que o código faz o que foi especificado, não que o modelo funciona na
   operação real. Qualidade de software ≠ validade do produto.
4. Em termos de MPS.BR, o projeto **não sustentaria o nível G** numa avaliação oficial: GRE
   e GPR exigem resultados que aqui estão P (controle de mudanças, acompanhamento do
   planejado × realizado). É uma autoavaliação acadêmica, não uma avaliação formal.
