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
| RF7 | Painel (KPIs, metas, departamentos) calculado das bases reais, com filtro por base | US1 |
| RF8 | Relatórios sob demanda em CSV, XLSX e PDF | US5 |

## Não funcionais
| ID | Requisito | Story |
|---|---|---|
| RNF1 | Desempenho do modelo: recall ≥ 0,60 e ROC-AUC ≥ 0,70 no teste estratificado (25% reservado) | US2 |
| RNF2 | Latência: lista de 155 operadores em ≤ 5 s | US1 |
| RNF3 | Explicabilidade: modelo linear com fatores por operador | US6 |
| RNF4 | Privacidade/LGPD: ID pseudonimizado, sem dados de saúde, acesso mínimo | US4 |
| RNF5 | Robustez a drift: PSI > 0,2 dispara alerta | US9 |
| RNF6 | Reprodutibilidade: semente fixa, split estratificado, artefatos versionados | US2 |

## Dados
| Tema | Requisito | Story |
|---|---|---|
| Fontes | 3 bases do Kaggle (Extended Employee Performance: 100 mil funcionários; HR Dashboard: 200; Employee Productivity: 10), mescladas por empilhamento em harmonize.py. Só a primeira tem rótulo (Sick_Days). SyntheticSource só para testes; depois, escala/ponto do DataTrack. | US1 |
| Qualidade | Colunas obrigatórias presentes; ≤ 5% de nulos por coluna; 'absent' ∈ {0,1}. | US3 |
| Volume | Mínimo de ~5.000 funcionários rotulados (real: 100.000, atendido). | US2 |
| Atualização | Bases do Kaggle são fotografias estáticas; na operação, carga periódica (alvo diário) e retreino por sprint ou quando houver drift. | US1, US9 |
| Restrições / LGPD | Sem dados de saúde como feature; Sick_Days só gera o rótulo (e é descartado), pois dias de afastamento são dado ligado à saúde; nome, idade e gênero descartados; ID com hash + sal (DATATRACK_SALT); /data fora do Git. | US4 |

> Esquema canônico (colunas obrigatórias): `employee_id, department, job_title, education_level, tenure_months, monthly_salary, weekly_hours, overtime_hours, training_hours, projects, satisfaction, performance_score, remote_pct, team_size, promotions, absent`. `absent = 1` quando `Sick_Days ≥ 11`. Ver `docs/05-dados-reais.md`.
