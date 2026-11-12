# SBAR — Pior falha de qualidade: QC06 (admissão antes dos 18 anos)

> Situação · Contexto (Background) · Avaliação · Recomendação.
> Base: `Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv` (100.000
> registros), avaliada localmente com `python -m src.validate` em 11/11/2026. É a base Kaggle
> com a coluna `Sick_Days` regerada (`reports/data_lineage.md`). **As colunas usadas pela QC06
> (`Age`, `Years_At_Company`) são idênticas às do original**, então os números abaixo são os
> mesmos da base original (avaliada em 06/11/2026). A base completa não vai para o Git.

## S — Situação

A regra **QC06 · Admissão com maioridade** reprovou **3.784 de 100.000 registros (3,78%)**.
Conformidade de **96,22%**, abaixo da meta de 99%. É a única regra reprovada na base real e a
de menor conformidade. Status da base: **LIBERADA COM RESSALVAS** (as regras críticas de
completude e unicidade passaram com 100%).

Nesses registros, `Age − Years_At_Company` dá menos de 18, ou seja, o funcionário teria sido
admitido ainda menor de idade:

| Idade implícita na admissão | Registros |
|---:|---:|
| 12 anos | 1 |
| 13 anos | 255 |
| 14 anos | 488 |
| 15 anos | 759 |
| 16 anos | 965 |
| 17 anos | 1.316 |
| **Total** | **3.784** |

Consulta usada: `QC06_falhas` em `sql/quality_checks.sql`.

## B — Contexto

- A base é a fonte "real" prevista no projeto (risco R1, `docs/04-planejamento-e-riscos.md`).
- As outras cinco regras passaram com 100%: zero nulos, zero IDs duplicados, todas as
  categorias no catálogo, todos os números na faixa e **`Years_At_Company` bate com
  `Hire_Date` em 100% dos registros** (usando 04/09/2024 como data de referência).
- Então o defeito **não** está no tempo de casa: está na combinação idade × tempo de casa.
- Os registros reprovados têm idade entre 22 e 27 anos (média 23,3) e se espalham por todos
  os 9 departamentos em proporções parecidas (de 10,6% a 11,8% cada), inclusive com cargo de
  *Manager*.
- Outros sinais do conjunto: todos os `Hire_Date` têm o mesmo horário (08:03:05.556036) e as
  categorias têm distribuição quase uniforme (ex.: cerca de 11 mil por departamento).

## A — Avaliação

1. **Causa provável: a base é sintética, gerada sorteando idade e tempo de casa de forma
   independente.** Um gerador sem a restrição "idade − tempo ≥ 18" produz exatamente este
   padrão: falhas concentradas nas menores idades e espalhadas de forma uniforme por
   departamento. Isto é uma **inferência**, não um fato confirmado pelo autor do dataset.
2. **Gravidade:**
   - 256 casos (12 e 13 anos) são impossíveis em qualquer regime de trabalho no Brasil.
   - 3.528 casos (14 a 17 anos) só seriam possíveis como aprendiz ou estágio, o que não bate
     com cargos como *Manager* ou *Engineer*. Na prática, todos são inconsistentes.
3. **Impacto no projeto:**
   - `Age` e `Years_At_Company` são atributos candidatos do modelo. Usar a base sem
     tratamento ensina ao modelo relações que não existem na realidade.
   - Mais grave: o resultado reforça o que o risco R1 já dizia. Esta base **não representa
     uma operação real** e não tem ausência diária. Hoje o modelo de risco só treina com
     dados sintéticos (`SyntheticSource`), e a base "real" disponível também é sintética.
4. **Por que é a pior falha:** é a única reprovação na base real, atinge 3,8% dos registros e
   passaria despercebida em qualquer checagem de nulos ou de faixa. Cada coluna isolada é
   válida; o erro só aparece cruzando duas colunas.

## R — Recomendação

| # | Ação | Responsável | Quando |
|---|---|---|---|
| 1 | Pôr os 3.784 registros em **quarentena**: excluir do treino e listar em arquivo para auditoria, sem corrigir os valores por conta própria | Integrante B (dados) | Sprint 2 |
| 2 | Tornar QC06 um **portão** no pipeline de ML (`src.validate --strict` antes de `src.ml.train`), com a meta mantida em 99% | Integrante B | Sprint 2 |
| 3 | Registrar formalmente que a base Kaggle é sintética e **levar a decisão sobre a fonte de dados** ao professor/PO (Ação 3 do `docs/improvement_plan.md`) | Integrante C | até 20/11/2026 |
| 4 | Não usar `Age` e `Years_At_Company` como atributos enquanto a fonte não for resolvida | Integrante C | imediato |

**Situação em 11/11/2026:** recomendações 1 e 4 implementadas em `src/ml/kaggle_risk.py`. Os registros da QC06 ficam fora do treino e do ranking, e `Age` não é atributo. O tempo de casa (`tenure_months`, derivado de `Hire_Date`) continua, porque a QC05 confirma 100% de coerência com `Years_At_Company` e as linhas inconsistentes já estão em quarentena. A recomendação 2 também: `python -m src.ml.kaggle_risk` roda as 6 regras antes de treinar e se recusa a treinar se a base sair `BLOQUEADA` (teste `test_cli_refuses_blocked_dataset`). A 3 ganhou um agravante: a nova base também é derivada, agora com o alvo regerado.

**Não recomendado:** "corrigir" a idade ou o tempo de casa por imputação. Sem saber qual
das duas colunas está errada, qualquer correção inventa dado.

### Como reproduzir

```bash
# coloque o CSV do Kaggle em data/raw/
python -m src.validate \
  --data data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv \
  --report reports/quality_report_full_base.md \
  --json reports/quality_results_full_base.json
```
