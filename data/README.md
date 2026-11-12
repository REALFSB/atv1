# Dados

## `sample_data.csv` — amostra fixa (versionada)

30 registros com o esquema da base Kaggle *Extended Employee Performance and Productivity
Data*, extraídos da versão `_2_otimizado` (a base de trabalho desde 11/11/2026). É **fixa e
reproduzível**: gerada por `scripts/build_sample.py`, sem aleatoriedade.

| Employee_ID | Origem | Defeito | Regra que deve reprovar |
|---|---|---|---|
| 1–24 | Copiados **sem alteração** da base original | — (o ID 20 já vem inconsistente da base: 23 anos e 9 de casa) | QC06 (ID 20, defeito natural) |
| 25 | Base original + defeito injetado | `Department` vazio | QC01 completude |
| 7 (era 26) | Base original + defeito injetado | `Employee_ID` trocado para 7, duplicando o ID 7 | QC02 unicidade (as 2 ocorrências) |
| 27 | Base original + defeito injetado | `Gender` = `M` | QC03 domínio |
| 28 | Base original + defeito injetado | `Performance_Score` = 7 | QC04 faixa |
| 29 | Base original + defeito injetado | `Years_At_Company` +3 anos | QC05 consistência |
| 30 | Base original + defeito injetado | `Monthly_Salary` = `N/D` (não numérico) | QC01 completude |

Os defeitos dos IDs 25–30 são **artificiais** e servem só para que cada regra tenha pelo
menos um caso reprovado no smoke test. Por isso a amostra aparece como `BLOQUEADA`: esse é o
resultado esperado, não um diagnóstico dos dados reais.

## `raw/` — bases completas (fora do Git)

| Arquivo | O que é |
|---|---|
| `Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv` | **base de trabalho**: Kaggle com `Sick_Days` regerado (semi-sintética, ver `reports/data_lineage.md`) |
| `Extended_Employee_Performance_and_Productivity_Data.csv` | original do Kaggle; usada só para a linhagem (`scripts/compare_bases.py`) |

Ficam no `.gitignore` por tamanho (~11 MB cada) e por conterem atributos de pessoas.

```bash
python scripts/build_sample.py --raw data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv
```

## `dashboard_sources_snapshot.json`

Agregados congelados das bases HR Dashboard (200) e Employee Productivity (10), cujos CSVs não
estão no repositório. Usado por `src/dashboard.py`.
