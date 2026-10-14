# Planejamento e riscos

## WBS (regra dos 100%: cada story aparece em ao menos um pacote)

**1. Projeto: DataTrack · Radar de Absenteísmo**

| ID | Fase (CRISP-DM) | Pacote de trabalho | Story | Resp. |
|---|---|---|---|---|
| 1.1 | Entendimento | Redigir stories e critérios de aceite (G/W/T) | US1–US10 | A |
| 2.1 | Dados | Implementar DataSource, CsvSource e SyntheticSource | US1 | A |
| 2.2 | Dados | Validar qualidade dos dados (nulos, colunas, rótulo) | US3 | B |
| 2.3 | Dados | Pseudonimizar IDs e descartar colunas sensíveis | US4 | B |
| 2.4 | Dados | Harmonizar e mesclar as 3 bases do Kaggle | US3 | B |
| 3.1 | Modelagem | Implementar features.py compartilhado por treino e serving | US2 | C |
| 3.2 | Modelagem | Treinar baseline logístico com split estratificado | US2 | C |
| 3.3 | Modelagem | Registrar métricas e checar metas (recall/AUC) | US2 | C |
| 4.1 | Serving | Implementar predict_risk e ranking ordenado | US1 | D |
| 4.2 | Serving | Implementar exportação CSV | US5 | D |
| 4.3 | Serving | Calcular faixa e 3 fatores por operador | US6 | D |
| 4.4 | Serving | Agregar as bases para o painel (dashboard.py) e ligar as 4 páginas aos dados | US1 | D |
| 4.5 | Serving | Gerar relatórios CSV/XLSX/PDF no painel | US5 | D |
| 5.1 | Qualidade | Escrever testes pytest por módulo | US1–US5 | A–D |
| 5.2 | Qualidade | Abrir e revisar Pull Request com colega | US1–US5 | A–D |
| 5.3 | Qualidade | Atualizar README e diagrama de arquitetura | US1–US5 | A |
| 6.1 | Evolução (Onda 2) | Implementar monitor.py com alerta de faixa | US7 | — |
| 6.2 | Evolução (Onda 2) | Estimar impacto na meta por célula | US8 | — |
| 6.3 | Evolução (Onda 2) | Calcular PSI e sinalizar drift | US9 | — |
| 6.4 | Evolução (Onda 2) | Gerar relatório semanal em PDF | US10 | — |

## Estimativas (story points)

> Proposta inicial — validar no Planning Poker do grupo (escala 1, 2, 3, 5, 8, 13).

| Story | Onda | Pontos |
|---|---|---|
| US1 | 1 | 5 |
| US2 | 1 | 8 |
| US3 | 1 | 3 |
| US4 | 1 | 3 |
| US5 | 1 | 2 |
| US6 | 2 | 3 |
| US7 | 2 | 5 |
| US8 | 2 | 8 |
| US9 | 2 | 5 |
| US10 | 2 | 3 |

**Onda 1:** 21 pts · **Onda 2:** 24 pts.

## Matriz de riscos

| Risco | Descrição | Prob. | Impacto | Exposição | Resposta | Resp. |
|---|---|---|---|---|---|---|
| R1 | OCORREU · Base do Kaggle sem sinal preditivo (AUC 0,50 mesmo com gradient boosting) e fora da operação brasileira (DADOS) | Alta | Alta | 9 | Mitigar: painel bloqueia ranking com aviso; coletar base interna (DataSource permite trocar sem mexer no treino) | A |
| R2 | OCORREU · Recall/AUC abaixo da meta com a base real (MODELO) | Média | Alta | 6 | Mitigar: medir sempre; revisar a meta ou o rótulo só com dado que tenha sinal | C |
| R3 | Dados pessoais de funcionários expostos / sem base legal (LGPD) | Média | Alta | 6 | Evitar: sem dados de saúde, hash com sal, acesso mínimo | B |
| R4 | Drift após a implantação degrada o modelo (MODELO) | Média | Média | 4 | Mitigar: PSI e alerta (US9) + retreino por sprint | C |
| R5 | Escopo cresce com alertas, impacto em metas e relatórios | Média | Média | 4 | Mitigar: Canvas MVP e backlog em ondas como fronteira | D |
| R7 | Metas do painel (alvos) são parâmetros assumidos, não metas reais da empresa; com bases aleatórias quase tudo "atinge" (DADOS) | Alta | Média | 6 | Aceitar e sinalizar: alvos em `PARAMS`, documentados; trocar quando houver meta real | A |
| R6 | Capacidade do grupo menor que o previsto (provas, outras disciplinas) | Alta | Média | 6 | Mitigar: capacidade conservadora (22 pts); cortar US5 se necessário | A |

Exposição = probabilidade × impacto (1 a 3). Reavaliar a cada sprint.

## Plano da Sprint 1

**Meta:** Entregar o pipeline modular ponta a ponta (ingest → features → train → serve) que gera a lista de funcionários ranqueada por risco de absenteísmo, com dados validados e pseudonimizados e baseline medido.

- Stories: US1, US2, US3, US4, US5 = **21 pts**
- Capacidade assumida: **22 pts** (hipótese: 4 integrantes, 2 semanas; a velocidade real só é conhecida após a Sprint 1)
- Pacotes da WBS: 2.1–2.3, 3.1–3.3, 4.1, 4.2, 4.4, 4.5, 5.1–5.3
- Definição de pronto: critérios G/W/T verificados + testes verdes + PR revisado por um colega
- Riscos monitorados: R1, R2, R3, R6, R7
