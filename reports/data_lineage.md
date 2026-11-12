# Linhagem de dados — base original × base "otimizada"

> Gerado por `python scripts/compare_bases.py`. Governança (DAMA-DMBOK, linhagem e proveniência): toda versão derivada de uma fonte precisa dizer o que mudou e por quê.

## Arquivos

| Papel | Arquivo | Linhas | SHA-256 |
|---|---|---:|---|
| Original (Kaggle) | `Extended_Employee_Performance_and_Productivity_Data.csv` | 100000 | `2b1e07caf58e7678…` |
| Derivada | `Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv` | 100000 | `e434bd7b983c67af…` |

## O que mudou

- Mesmas linhas, mesma ordem e mesmas colunas: **sim**.
- Colunas alteradas: **`Sick_Days` (93273 linhas)**.
- Linhas com alguma alteração: **93273 de 100000** (93,3%).
- `Sick_Days` igual ao original em apenas 6727 linhas (6,7%): perto do acaso para 15 valores possíveis (0 a 14), ou seja, a coluna foi **gerada de novo**, não corrigida.
- Média de `Sick_Days`: 7,01 → 7,00; desvio-padrão 4,33 → 4,10. A distribuição foi preservada; a **relação com as outras colunas** não.

## Correlação de `Sick_Days` com as demais colunas numéricas

| Coluna | Original | Otimizada |
|---|---:|---:|
| `Overtime_Hours` | 0,004 | 0,586 |
| `Work_Hours_Per_Week` | -0,001 | 0,447 |
| `Employee_Satisfaction_Score` | -0,001 | -0,363 |
| `Monthly_Salary` | 0,004 | -0,005 |
| `Remote_Work_Frequency` | 0,000 | -0,005 |
| `Performance_Score` | 0,003 | -0,003 |
| `Age` | 0,007 | -0,002 |
| `Years_At_Company` | -0,004 | 0,002 |
| `Training_Hours` | 0,000 | 0,002 |
| `Promotions` | -0,003 | -0,001 |
| `Team_Size` | 0,000 | 0,001 |
| `Projects_Handled` | -0,005 | 0,000 |

Na base original nenhuma correlação passa de 0,01 em módulo. Na derivada, `Sick_Days` passa a depender de horas extras, jornada e (negativamente) da satisfação.

## Efeito no modelo de risco (mesmo código, mesma semente)

| Métrica | Base original | Base otimizada | Meta |
|---|---:|---:|---:|
| ROC-AUC | 0,498 | 0,914 | ≥ 0,700 |
| Recall | 0,503 | 0,844 | ≥ 0,600 |
| Precisão (limiar 0,5) | 0,265 | 0,608 | — |
| Precisão no top 10% | 0,258 | 0,888 | — |
| Atinge a meta da US2 | não | sim | |

## Leitura

1. Na base original o modelo é equivalente a sortear (AUC ≈ 0,50): não há sinal de afastamento nas outras colunas.
2. A melhora para AUC > 0,9 vem **inteiramente** da regeneração do alvo. O modelo está reaprendendo a regra usada para criar a coluna, não descobrindo um padrão de absenteísmo real.
3. Uso aceitável: **demonstração do pipeline** com base semi-sintética, declarada como tal em todo lugar onde o número aparece (painel, relatórios, apresentação).
4. Uso **não** aceitável: apresentar o AUC como resultado em dados reais do Kaggle.
5. Falta registrar **quem** gerou a coluna e **com qual regra**. Sem isso, a linhagem fica incompleta (ver `docs/05-dados-reais.md`).
