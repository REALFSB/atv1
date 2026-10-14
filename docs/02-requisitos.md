# Requisitos — funcionais, não funcionais e de dados

## Funcionais
| ID | Requisito | Story |
|---|---|---|
| RF1 | Listar operadores ordenados por risco de ausência | US1 |
| RF2 | Exibir faixa de risco e 3 principais fatores | US6 |
| RF3 | Exportar a lista em CSV | US5 |
| RF4 | Alertar mudança de faixa | US7 |
| RF5 | Estimar impacto na meta da célula | US8 |
| RF6 | Gerar relatório semanal em PDF | US10 |

## Não funcionais
| ID | Requisito | Story |
|---|---|---|
| RNF1 | Desempenho do modelo: recall ≥ 0,60 e ROC-AUC ≥ 0,70 no teste temporal | US2 |
| RNF2 | Latência: lista de 155 operadores em ≤ 5 s | US1 |
| RNF3 | Explicabilidade: modelo linear com fatores por operador | US6 |
| RNF4 | Privacidade/LGPD: ID pseudonimizado, sem dados de saúde, acesso mínimo | US4 |
| RNF5 | Robustez a drift: PSI > 0,2 dispara alerta | US9 |
| RNF6 | Reprodutibilidade: semente fixa, split temporal, artefatos versionados | US2 |

## Dados
| Tema | Requisito | Story |
|---|---|---|
| Fontes | Base real do Kaggle do projeto (CSV via CsvSource + column_map) e, depois, escala/ponto do DataTrack. SyntheticSource só para desenvolvimento e testes. | US1 |
| Qualidade | Colunas obrigatórias presentes; ≤ 5% de nulos por coluna; 'absent' ∈ {0,1}. | US3 |
| Volume | Mínimo de ~5.000 linhas operador-dia, com ≥ 30 dias de histórico por operador. | US2 |
| Atualização | Carga diária (D-1) antes do início do turno; retreino por sprint ou quando houver drift. | US1, US9 |
| Restrições / LGPD | Sem dados de saúde (atestados, hábitos); ID com hash + sal (variável DATATRACK_SALT); /data fora do Git. | US4 |

> Esquema canônico (colunas obrigatórias): `employee_id, date, sector, shift, tenure_months, distance_km, overtime_hours_week, prior_absences_30d, productivity_pct, absent`. Colunas da base do Kaggle são mapeadas para ele em `CsvSource(column_map=...)`.
