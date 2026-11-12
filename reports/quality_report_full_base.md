# Relatório de Qualidade dos Dados

- **Base avaliada:** `data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv` (100000 registros)
- **Data de referência das regras de consistência:** 2024-09-04
- **Gerado por:** `python -m src.validate` (valores calculados na execução, não editados à mão)

## Resultado por regra

| ID | Regra | Dimensão | Avaliados | Aprovados | Reprovados | Conformidade | Meta | Status | SQL = pandas |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| QC01 | Campos obrigatórios preenchidos (crítica) | Completude | 100000 | 100000 | 0 | 100,00% | 100,00% | **APROVADA** | sim |
| QC02 | Employee_ID único (crítica) | Unicidade | 100000 | 100000 | 0 | 100,00% | 100,00% | **APROVADA** | sim |
| QC03 | Categorias no domínio permitido | Validade | 100000 | 100000 | 0 | 100,00% | 99,00% | **APROVADA** | sim |
| QC04 | Valores numéricos na faixa de negócio | Validade | 100000 | 100000 | 0 | 100,00% | 99,00% | **APROVADA** | sim |
| QC05 | Tempo de casa coerente com a admissão | Consistência | 100000 | 100000 | 0 | 100,00% | 99,00% | **APROVADA** | sim |
| QC06 | Admissão com maioridade | Consistência | 100000 | 96216 | 3784 | 96,22% | 99,00% | **REPROVADA** | sim |

## Consolidado

- Regras aprovadas: **5 de 6**
- Regras reprovadas: **1** (QC06)
- Verificações (registro × regra) avaliadas: 600000 · aprovadas: 596216
- **Conformidade geral:** 99,37% (soma dos aprovados ÷ soma dos avaliados, todas as regras)
- **Status final da base:** **LIBERADA COM RESSALVAS**
- Pior regra (menor conformidade): QC06

Critério do status final: qualquer regra crítica (meta 100%) reprovada → **BLOQUEADA** (a base não entra no pipeline); só regras não críticas reprovadas → **LIBERADA COM RESSALVAS**; todas aprovadas → **LIBERADA**.

## Registros reprovados (até 20 IDs por regra)

- **QC06** (3784): 20, 82, 172, 218, 227, 231, 247, 274, 294, 299, 302, 304, 309, 319, 322, 381, 390, 413, 456, 463 … (+3764)
