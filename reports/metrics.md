# Métricas do projeto

> Gerado automaticamente por `python scripts/collect_metrics.py --run` em 2026-11-11 22:00 (America/Sao_Paulo), a partir de execuções **locais** reais. Nenhum número deste arquivo foi digitado à mão. O workflow de CI ainda não foi publicado, portanto não há resultado de GitHub Actions.

## 1. Testes automatizados (pytest)

| Métrica | Valor |
|---|---:|
| Testes executados | 135 |
| Aprovados | 135 |
| Reprovados (falhas + erros) | 0 |
| Ignorados | 0 |
| Tempo total | 10,82 s |

Testes por arquivo:

| Arquivo | Testes |
|---|---:|
| `tests/test_auth.py` | 42 |
| `tests/test_employee_model.py` | 19 |
| `tests/test_features.py` | 2 |
| `tests/test_ingest.py` | 6 |
| `tests/test_repo.py` | 9 |
| `tests/test_serve.py` | 5 |
| `tests/test_smoke.py` | 3 |
| `tests/test_train.py` | 6 |
| `tests/test_validate.py` | 43 |

## 2. Cobertura de código (pytest-cov, linhas + ramos)

- **Cobertura total de `src/`: 91,0%** (869/939 linhas · 136/166 ramos)
- Meta configurada em `pyproject.toml` (`fail_under = 80`).

| Arquivo | Cobertura |
|---|---:|
| `src/__init__.py` | 100,0% |
| `src/dashboard.py` | 85,5% |
| `src/data/__init__.py` | 100,0% |
| `src/data/employees.py` | 100,0% |
| `src/data/ingest.py` | 84,4% |
| `src/features.py` | 100,0% |
| `src/ingest.py` | 100,0% |
| `src/ml/__init__.py` | 100,0% |
| `src/ml/features.py` | 100,0% |
| `src/ml/kaggle_risk.py` | 100,0% |
| `src/ml/train.py` | 84,2% |
| `src/serve.py` | 100,0% |
| `src/serving/__init__.py` | 100,0% |
| `src/serving/risk.py` | 74,0% |
| `src/train.py` | 100,0% |
| `src/validate.py` | 96,8% |
| `src/webapp/__init__.py` | 77,1% |
| `src/webapp/__main__.py` | 0,0% |
| `src/webapp/auth.py` | 91,7% |
| `src/webapp/db.py` | 98,3% |
| `src/webapp/indicators.py` | 83,9% |
| `src/webapp/security.py` | 100,0% |
| `src/webapp/views.py` | 89,8% |

## 3. Análise estática (ruff)

- Achados atuais: **0** (regras E, W, F, I, UP, B, SIM, S; ver `pyproject.toml`).
- Antes da configuração desta entrega, o mesmo conjunto de regras apontava 24 achados (14 no código herdado + 10 no código novo); todos foram corrigidos ou justificados com `noqa` comentado (falsos positivos S105 em mensagens de erro).

## 4. Qualidade dos dados

| Base | Registros | Regras aprovadas | Regras reprovadas | Conformidade geral | Status |
|---|---:|---:|---:|---:|---|
| Amostra fixa `data/sample_data.csv` | 30 | 0 | 6 | 95,56% | BLOQUEADA |
| Base completa `_2_otimizado` (local, fora do Git) | 100000 | 5 | 1 | 99,37% | LIBERADA COM RESSALVAS |

Conformidade geral = Σ aprovados ÷ Σ avaliados nas 6 regras. Na amostra, os 6 defeitos são **injetados de propósito** (ver `data/README.md`). A base completa é a versão `_2_otimizado`, com `Sick_Days` regerado (`reports/data_lineage.md`); as regras QC01–QC06 não olham `Sick_Days` além da faixa, então o resultado é igual ao da base original. Detalhe em `reports/quality_report.md` e `reports/quality_report_full_base.md`.

## 4b. Modelo de risco por funcionário (`src.ml.kaggle_risk`)

| Métrica | Valor | Meta |
|---|---:|---:|
| ROC-AUC | 0,914 | ≥ 0,700 |
| Recall | 0,844 | ≥ 0,600 |
| Precisão (limiar 0,5) | 0,608 | — |
| Precisão no top 10% de risco | 0,888 | — |
| Treino / teste | 72162 / 24054 | holdout estratificado |
| Em quarentena (QC06) | 3784 | fora do treino |

Alvo: `Sick_Days >= 11`. Base: `Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv`. **Na base original do Kaggle o mesmo código dá AUC ≈ 0,50** (`reports/data_lineage.md`): o resultado acima mede a recuperação da regra usada para regerar `Sick_Days`, não absenteísmo real.

## 5. Baseline da Sprint 1

| Métrica | Valor | Fórmula |
|---|---:|---|
| Pontos comprometidos (escopo final) | 31 | Σ pontos das histórias com Sprint = 1 |
| Pontos planejados no início | 21 | `docs/04-planejamento-e-riscos.md` |
| **Velocidade (DoD completa)** | **0** | Σ pontos em Feito |
| Pontos aguardando revisão por par | 31 | Σ pontos em Em revisão |
| Taxa de conclusão pela DoD | 0,0% | Feito ÷ comprometido |

## 6. Distribuição das histórias no Kanban

| Coluna | Histórias | Pontos |
|---|---:|---:|
| A fazer | 2 | 10 |
| Em andamento | 2 | 11 |
| Em revisão | 8 | 34 |
| Feito | 0 | 0 |
| **Total** | **12** | **55** |

## 7. Maturidade por área (autoavaliação)

| Área | Q1 | Q2 | Q3 | Síntese |
|---|:-:|:-:|:-:|---|
| Gestão de Requisitos | F | L | P | Histórias testáveis e rastreáveis; mudança de escopo sem controle |
| Planejamento | F | L | P | Estimativa e capacidade existem; sem comparação planejado × realizado anterior |
| Gestão de Configuração | N | P | L | Sem histórico Git verificável; estratégia só documentada |
| Garantia da Qualidade | F | L | N | Testes e lint fortes; nenhuma revisão por par independente |
| Medição e Análise | F | L | P | Métricas automáticas e reproduzíveis; só um ponto de medição |
| Gestão de Riscos | F | L | L | Riscos reavaliados com registro; R1 tratado, mas surgiu R7 (dado sem proveniência) |

Contagem: F = 5 · L = 7 · P = 4 · N = 2.

Escala: N = não praticado · P = parcialmente · L = largamente · F = totalmente. Justificativas em `reports/maturity_assessment.md`.
