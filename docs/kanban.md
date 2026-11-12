# Kanban demonstrativo — fim da Sprint 1

> Estado do quadro na entrega de 06/11/2026. A coluna de cada cartão segue a evidência
> disponível no repositório, não a intenção. A tabela "Quadro" é lida por
> `scripts/collect_metrics.py` para gerar as métricas — mantenha o formato.

## Regras do quadro

| Coluna | Entra quando | Limite WIP |
|---|---|:-:|
| **A fazer** | história refinada, com critérios de aceite e pontos | — |
| **Em andamento** | alguém começou; existe código ou protótipo, mas critérios ainda não passam | 3 |
| **Em revisão** | todos os critérios de aceite têm teste verde, ruff limpo, cobertura ≥ 80%; falta revisão por par | 4 |
| **Feito** | atende **toda** a Definition of Done, inclusive PR revisado e mergeado | — |

Nenhuma história está em *Feito* porque nenhuma tem revisão por par comprovada (não há
histórico Git nem PR). Mover para *Feito* sem essa evidência seria declarar algo que não
dá para provar.

## Visão do quadro

| A fazer | Em andamento | Em revisão | Feito |
|---|---|---|---|
| US7 · Alerta de mudança de faixa (5) | US8 · Impacto na meta (8) — tela `metas.html` sem cálculo real | US1 · Lista ranqueada (5) | — |
| US9 · Drift / PSI (5) | US10 · Relatório PDF (3) — tela `relatorios.html` sem geração de PDF | US2 · Recall/AUC (8) | |
| | | US3 · Barrar dados ruins (3) | |
| | | US4 · LGPD (3) | |
| | | US5 · Exportar CSV (2) | |
| | | US11 · Qualidade de dados (5) | |
| | | US12 · Login (5) | |
| | | US6 · Fatores de risco (3) ⚠ acima do WIP | |

⚠ **WIP estourado em "Em revisão":** 8 cartões para limite 4. É o sintoma do gargalo: o
trabalho anda até a revisão e para ali.

## Quadro (fonte das métricas)

| ID | História | Pontos | Sprint | Coluna |
|---|---|---:|---|---|
| US1 | Lista ranqueada por risco | 5 | 1 | Em revisão |
| US2 | Modelo com recall/AUC mínimos | 8 | 1 | Em revisão |
| US3 | Barrar dados incompletos | 3 | 1 | Em revisão |
| US4 | Proteção LGPD | 3 | 1 | Em revisão |
| US5 | Exportar CSV | 2 | 1 | Em revisão |
| US11 | Regras de qualidade de dados | 5 | 1 (adicionada) | Em revisão |
| US12 | Login e rotas protegidas | 5 | 1 (adicionada) | Em revisão |
| US6 | Fatores de risco por operador | 3 | Onda 2 (já implementada) | Em revisão |
| US8 | Impacto na meta da célula | 8 | Onda 2 | Em andamento |
| US10 | Relatório semanal em PDF | 3 | Onda 2 | Em andamento |
| US7 | Alerta de mudança de faixa | 5 | Onda 2 | A fazer |
| US9 | Drift (PSI > 0,2) | 5 | Onda 2 | A fazer |

## Distribuição

| Coluna | Histórias | Pontos |
|---|---:|---:|
| A fazer | 2 | 10 |
| Em andamento | 2 | 11 |
| Em revisão | 8 | 34 |
| Feito | 0 | 0 |
| **Total** | **12** | **55** |

Os mesmos números, recalculados a partir da tabela acima, estão em `reports/metrics.md`.

## Atualização de 11/11/2026

Nenhum cartão mudou de coluna. O modelo por funcionário e o gerador do painel entraram como
**tarefas** da US2 e da US8, que já estavam no quadro (regra da retrospectiva: nada de história
nova sem troca). Para chegar a *Feito*, cada cartão precisa do PR correspondente em
`scripts/github_setup.py plan` revisado e mergeado.
