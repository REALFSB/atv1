# Relatório de Qualidade dos Dados

- **Base avaliada:** `data/sample_data.csv` (30 registros)
- **Data de referência das regras de consistência:** 2024-09-04
- **Gerado por:** `python -m src.validate` (valores calculados na execução, não editados à mão)

## Resultado por regra

| ID | Regra | Dimensão | Avaliados | Aprovados | Reprovados | Conformidade | Meta | Status | SQL = pandas |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| QC01 | Campos obrigatórios preenchidos (crítica) | Completude | 30 | 28 | 2 | 93,33% | 100,00% | **REPROVADA** | sim |
| QC02 | Employee_ID único (crítica) | Unicidade | 30 | 28 | 2 | 93,33% | 100,00% | **REPROVADA** | sim |
| QC03 | Categorias no domínio permitido | Validade | 30 | 29 | 1 | 96,67% | 99,00% | **REPROVADA** | sim |
| QC04 | Valores numéricos na faixa de negócio | Validade | 30 | 29 | 1 | 96,67% | 99,00% | **REPROVADA** | sim |
| QC05 | Tempo de casa coerente com a admissão | Consistência | 30 | 29 | 1 | 96,67% | 99,00% | **REPROVADA** | sim |
| QC06 | Admissão com maioridade | Consistência | 30 | 29 | 1 | 96,67% | 99,00% | **REPROVADA** | sim |

## Consolidado

- Regras aprovadas: **0 de 6**
- Regras reprovadas: **6** (QC01, QC02, QC03, QC04, QC05, QC06)
- Verificações (registro × regra) avaliadas: 180 · aprovadas: 172
- **Conformidade geral:** 95,56% (soma dos aprovados ÷ soma dos avaliados, todas as regras)
- **Status final da base:** **BLOQUEADA**
- Pior regra (menor conformidade): QC01

Critério do status final: qualquer regra crítica (meta 100%) reprovada → **BLOQUEADA** (a base não entra no pipeline); só regras não críticas reprovadas → **LIBERADA COM RESSALVAS**; todas aprovadas → **LIBERADA**.

## Registros reprovados (até 20 IDs por regra)

- **QC01** (2): 25, 30
- **QC02** (2): 7, 7
- **QC03** (1): 27
- **QC04** (1): 28
- **QC05** (1): 29
- **QC06** (1): 20
