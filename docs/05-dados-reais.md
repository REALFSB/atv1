# Dados reais: fonte, versões e decisão sobre o modelo

> Documento citado pelo painel Equipes & Escalas. Responde a três perguntas: de onde vêm
> os dados, o que foi alterado neles e o que o resultado do modelo pode (e não pode) afirmar.

## 1. Fontes

| Base | Linhas | Onde está | Uso |
|---|---:|---|---|
| Kaggle *Extended Employee Performance and Productivity Data* (original) | 100.000 | `data/raw/Extended_Employee_Performance_and_Productivity_Data.csv` (fora do Git) | referência de linhagem; QC01–QC06 |
| **Mesma base com `Sick_Days` regerado** (`_2_otimizado`) | 100.000 | `data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv` (fora do Git) | **base de trabalho atual**: validação, modelo, painel |
| HR Dashboard | 200 | CSV fora do repositório; agregados em `data/dashboard_sources_snapshot.json` | painel |
| Employee Productivity | 10 | idem | painel |
| Sintética operacional (`SyntheticSource`) | 148 × 60 dias | gerada em código | modelo diário (US1–US5) e testes |

## 2. O que a versão `_2_otimizado` mudou (fatos medidos)

Detalhe completo e reproduzível em `reports/data_lineage.md` (`python scripts/compare_bases.py`).

- Só a coluna `Sick_Days` mudou, em **93.273 de 100.000 linhas**. Todas as outras 19 colunas
  são idênticas, linha a linha.
- Os valores novos coincidem com os antigos em 6,7% das linhas, o que é o esperado ao acaso
  para 15 valores possíveis. Portanto a coluna foi **gerada de novo**, não corrigida.
- No original, `Sick_Days` não tinha correlação com nenhuma coluna (|r| < 0,01). Na versão
  nova, passa a ter correlação de **+0,59 com horas extras, +0,45 com jornada semanal e
  −0,36 com satisfação**.
- Efeito no modelo, com o mesmo código e a mesma semente: **AUC 0,498 → 0,914**.

**O que ainda não está registrado (o grupo precisa preencher):**
- quem gerou o arquivo, em que data e com qual regra ou script;
- por quê (ex.: "demonstrar o pipeline com um alvo que tenha sinal").

Sem isso, a linhagem fica incompleta. Isso é risco R7 em `docs/risk_log.md`.

## 3. Decisão sobre o alvo do modelo (D5 da ata de 06/11)

A ata deixou duas opções: (a) buscar uma base com ausência diária; (b) redefinir o alvo para
algo que a base atual sustente. Situação em 11/11/2026:

- **Implementado tecnicamente a opção (b):** alvo `sick_high` = `Sick_Days ≥ 11` (o mesmo
  limite de "absenteísmo elevado" que o painel já usava), modelo por funcionário em
  `src/ml/kaggle_risk.py`, holdout estratificado de 25% com semente 42.
- **Na base original o alvo não tem sinal:** AUC 0,50, recall 0,50. Nenhum modelo vai bem
  porque não há nada para aprender.
- **Na base `_2_otimizado` o modelo passa da meta da US2** (AUC 0,914, recall 0,844, precisão
  0,608), mas está reaprendendo a regra que gerou a coluna.
- **Decisão pendente com o professor/PO:** aceitar a base semi-sintética como demonstração
  declarada, ou manter a busca por dados reais. Enquanto isso, todo lugar que mostra o AUC
  também mostra o aviso (painel, relatórios, apresentação).

## 4. Proteções aplicadas ao modelo por funcionário

| Proteção | Onde | Por quê |
|---|---|---|
| `Gender` descartada na leitura; `Age` só usada na QC06 | `src/data/employees.py` | atributos protegidos não entram como preditores (LGPD, art. 6º, IX: não discriminação) |
| `Employee_ID` com SHA-256 + sal | `src/data/ingest.py::pseudonymize` | US4 |
| 3.784 registros da QC06 em quarentena | `src/ml/kaggle_risk.py::usable` | decisão D4 da ata; não "corrigimos" idade nem tempo de casa |
| Teste que exige AUC perto de 0,5 quando o alvo é ruído | `tests/test_employee_model.py::test_model_is_near_chance_when_target_is_noise` | impede que um bug "crie" sinal onde não existe |

## 5. Mudanças no gerador do painel (`src/dashboard.py`)

O painel citava `python -m src.dashboard`, mas o módulo não estava no repositório. Agora está.

- Com a base original, o gerador reproduz **exatamente** os agregados por departamento e o
  bloco de qualidade do `dashboard-data.js` anterior (verificado em 11/11/2026).
- **Uma diferença intencional:** o gráfico por ano de admissão agora usa o ano real de
  `Hire_Date`. O arquivo anterior estimava o ano a partir do tempo de casa em meses, o que
  colocava 419 funcionários no ano errado.
- As bases HR Dashboard e Employee Productivity não têm CSV no repositório. Os números delas
  são reaproveitados de um retrato congelado, com nota explicando a origem.
