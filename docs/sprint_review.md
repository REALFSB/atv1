# Ata da Sprint Review — Sprint 1

| Campo | Valor |
|---|---|
| Projeto | DataTrack · Radar de Absenteísmo (CCD610) |
| Sprint | 1 |
| Data da revisão | 06/11/2026 |
| Participantes | Integrantes A, B, C, D (substituir pelos nomes); PO representado pela persona Guilherme Ramos (**simulado**) |
| Meta da sprint | Pipeline modular ponta a ponta (ingest → features → train → serve) gerando a lista ranqueada por risco, com dados validados e pseudonimizados e baseline medido |

## 1. Funcionalidades desenvolvidas

| História | O que foi demonstrado | Evidência executável |
|---|---|---|
| US1 Lista ranqueada | Ranking de 148 operadores por risco, faixas Alta/Média/Baixa, tela Equipes & Escalas | `python -m src.serving.risk` → `paineis/risco-data.js`; `tests/test_serve.py` |
| US2 Modelo | Regressão logística com split temporal: **ROC-AUC 0,754 · recall 0,644 · precisão 0,210** (dados sintéticos, semente 42) | `python -m src.ml.train`; `tests/test_train.py` |
| US3 Dados ruins barrados | Erro com nome da coluna e % de nulos quando passa de 5% | `tests/test_ingest.py` |
| US4 LGPD | ID com SHA-256 + sal; colunas de saúde descartadas | `tests/test_ingest.py` |
| US5 Exportação CSV | CSV com todas as linhas e colunas `rank`, `risk`, `band` | `artifacts/ranking.csv`; `tests/test_serve.py` |
| US11 Qualidade de dados | 6 regras (completude, unicidade, validade ×2, consistência ×2) em pandas **e** SQL, com paridade testada; relatório por regra | `python -m src.validate`; `reports/quality_report*.md` |
| US12 Login | Login, cadastro, logout, rotas protegidas, hash scrypt, CSRF, limite de tentativas; dashboard com indicadores reais | `flask --app src.webapp run`; `tests/test_auth.py` |

## 2. Incremento entregue

**Incremento técnico (funciona e está testado):** aplicação web local com login que dá
acesso ao dashboard e aos 4 painéis; pipeline de ML ponta a ponta; validador de qualidade de
dados com relatório. 107 testes passando, cobertura de 90,3%, ruff sem achados.

**O que o incremento NÃO é, dito sem rodeio:**
1. **Não está "Pronto" pela DoD.** Falta a revisão por par em PR (item 6 abaixo). Pela
   regra do Scrum, nada aqui é incremento liberável até isso acontecer.
2. **O modelo não foi validado com dados reais.** Recall e AUC vêm de dados sintéticos
   gerados pelo próprio projeto. A base Kaggle não tem ausência diária e, pela auditoria
   de qualidade, também parece sintética (`reports/sbar.md`).
3. **A precisão de 0,21 significa que ~79% dos alertas "Alta" seriam falsos alarmes**,
   mesmo com a meta de recall atingida. A meta da US2 não fala de precisão; essa lacuna
   precisa ser discutida com o PO.

## 3. Definition of Done

| # | Critério | US1 | US2 | US3 | US4 | US5 | US11 | US12 |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | Critérios de aceite G/W/T cobertos por teste automatizado | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 | Suíte inteira verde (`pytest`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | Cobertura de `src/` ≥ 80% | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4 | `ruff check` sem achados | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 5 | README / docs atualizados | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 6 | PR revisado e aprovado por outro integrante | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | **Resultado** | Em revisão | Em revisão | Em revisão | Em revisão | Em revisão | Em revisão | Em revisão |

Itens 1–5 foram verificados por execução local em 06/11/2026 (`reports/metrics.md`). O item 6
não tem evidência: o material entregue não tem histórico Git nem PRs. US11 tem, além disso,
um comentário bloqueante aberto na revisão simulada (`docs/peer_review_simulation.md`, #1).

## 4. Feedbacks — ⚠️ SIMULAÇÃO

> Os feedbacks abaixo são **simulados** para fins didáticos. Nenhuma pessoa real (PO,
> usuário ou líder de célula) avaliou o sistema. As personas são fictícias.

| # | Quem (persona simulada) | Feedback simulado | Encaminhamento |
|---|---|---|---|
| F1 | Guilherme Ramos, Head de Operações | "A lista ajuda, mas se 8 de cada 10 alertas 'Alta' forem falsos, meus líderes param de olhar em uma semana." | Incluir meta de precisão (ou de precisão nos top-10) na US2 — Sprint 2 |
| F2 | Guilherme Ramos | "Quero ver o motivo do risco antes de falar com o operador." | US6 já implementada; priorizar a revisão dela |
| F3 | Líder de célula (persona) | "Login funcionou no celular, mas os painéis antigos ficam apertados na tela pequena." | Os painéis legados usam layout fixo; registrar como débito de UI |
| F4 | Professor/avaliador (persona) | "Os números do relatório de qualidade batem com o que o código calcula?" | Sim: `tests/test_smoke.py` falha se o relatório versionado divergir |

## 5. Métrica de baseline (Sprint 1)

| Métrica | Valor | Como foi calculada |
|---|---:|---|
| Pontos planejados | 21 | `docs/04-planejamento-e-riscos.md` |
| Pontos comprometidos ao final (com escopo adicionado) | 31 | 21 + US11 (5) + US12 (5) |
| Crescimento de escopo | +48% | 10 ÷ 21 |
| **Velocidade (pontos que atendem a DoD)** | **0** | Σ pontos em Feito |
| Pontos tecnicamente prontos, aguardando revisão | 31 | Σ pontos da Sprint 1 em Em revisão |
| Testes / aprovados | 107 / 107 | `reports/junit.xml` |
| Cobertura | 90,3% | `reports/coverage.json` |
| Conformidade dos dados — base Kaggle | 99,37% (5 de 6 regras) | `reports/quality_results_full_base.json` |
| ROC-AUC / recall / precisão (sintético) | 0,754 / 0,644 / 0,210 | `artifacts/metrics.json` |

**Baseline a usar na Sprint 2:** velocidade **0 pts** pela DoD e **31 pts** de capacidade
técnica demonstrada. A comparação útil na próxima sprint é se a diferença entre os dois
números cai, ou seja, se o trabalho atravessa a revisão.

## 6. Status final do Kanban

| A fazer | Em andamento | Em revisão | Feito |
|:-:|:-:|:-:|:-:|
| 2 histórias · 10 pts | 2 histórias · 11 pts | 8 histórias · 34 pts | 0 histórias · 0 pts |

Detalhe por cartão em `docs/kanban.md`. "Em revisão" está com 8 cartões para limite WIP de 4.

## 7. Decisões da revisão

1. Nenhuma história é aceita como Feita até existir PR revisado (ação 1 do plano de melhoria).
2. A US2 volta ao refinamento para incluir um critério de precisão (feedback simulado F1).
3. A escolha da fonte de dados real vira prioridade da Sprint 2 (SBAR, recomendação 3).

## 8. Como o backlog foi reordenado

| Antes da revisão (ordem da Sprint 1) | Depois da revisão (ordem para a Sprint 2) | Motivo |
|---|---|---|
| 1. US4 · 2. US3 · 3. US1 · 4. US2 · 5. US12 · 6. US11 · 7. US5 | **1.** Levar os 8 cartões de "Em revisão" a Feito via PR | Velocidade 0 pela DoD: terminar vale mais que começar |
| Onda 2: US6, US7, US8, US9, US10 | **2.** US2 de volta ao refinamento: critério de precisão + fonte de dados | Feedback simulado F1 e risco R1 |
| | **3.** Comentário bloqueante #1 (data de referência fixa na QC05) | Impede reutilizar a US11 com outra extração |
| | **4.** US7 · alerta de mudança de faixa (5 pts) | Único item novo cabível na capacidade de 8 pts |
| | **5.** US8 e US10 (em andamento, protótipos sem cálculo real) | Dependem de um modelo confiável |
| | **6.** US9 · drift | Só faz sentido com dados reais entrando |

## 9. Atualização de 11/11/2026 (já dentro da Sprint 2)

- **Base trocada** para `Extended_..._2_otimizado.csv`. Só `Sick_Days` mudou (93,3% das linhas),
  regerado com correlação com horas extras, jornada e satisfação (`reports/data_lineage.md`).
- **US2 refinada (item 2 acima):** modelo por funcionário com alvo `Sick_Days ≥ 11`
  (`src/ml/kaggle_risk.py`). Na base original: **AUC 0,498**. Na base otimizada: **AUC 0,914,
  recall 0,844, precisão 0,608**. O ganho vem da regeneração do alvo, não do modelo.
- **Decisão D4 executada:** 3.784 registros da QC06 em quarentena, fora do treino e do ranking.
- **Geradores que faltavam no repositório:** `src/dashboard.py` (dados dos painéis) e o modelo
  que produz `paineis/risco-data.js`. Os painéis citavam esses comandos, mas o código não
  estava no ZIP.
- **Correções de configuração:** o ZIP recebido em 11/11 não tinha `.github/workflows/tests.yml`,
  `.gitignore`, `src/__init__.py` nem o ícone do app, e 1 teste falhava (logout nos painéis
  novos). Tudo foi restaurado e corrigido.
- **Métricas em 11/11:** 135 testes (135 aprovados), cobertura de 91,0%, ruff com 0 achados
  (eram 107 testes e 90,3% em 06/11).
- O quadro **não muda de coluna**: nenhum cartão tem PR revisado. A nova tarefa da US2 entra
  como tarefa da história já existente, não como história nova (regra da retrospectiva).
