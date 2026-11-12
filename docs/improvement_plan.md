# Plano de melhoria de processo

> Derivado de `reports/maturity_assessment.md`. Exatamente três ações, escolhidas pelo número
> de perguntas que cada uma move, e não pela facilidade. Responsáveis seguem a convenção
> A–D de `docs/04-planejamento-e-riscos.md` — **substituir pelos nomes reais do grupo**.
> Sprint 2: 09/11 a 20/11/2026 · Sprint 3: 23/11 a 04/12/2026.

## Ação 1 — Revisão por par real, com histórico Git verificável

| Campo | Definição |
|---|---|
| **Problema identificado** | Não há histórico de versões nem revisão independente comprovável. Gera as duas notas N (GC Q1, GQA Q3) e trava todo o quadro em "Em revisão" (0 pts em Feito). |
| **Ação corretiva** | Publicar o repositório com histórico; proteger `main` (1 aprovação obrigatória, sem push direto); abrir um PR por história seguindo `docs/xp_implementation.md` §4; revisor ≠ autor. Começar pelos 8 cartões parados em "Em revisão". |
| **Responsável** | Integrante A (dono do processo); cada autor abre os próprios PRs |
| **Prazo** | 20/11/2026 (fim da Sprint 2) |
| **Indicador de sucesso** | % de PRs mergeados em `main` com ≥ 1 aprovação de outra pessoa = **100%**; pontos em Feito na Sprint 2 ≥ **50%** do comprometido |
| **Critério de validação** | `gh pr list --state merged --json number,reviews` mostra aprovação em todos os PRs; tela de *Branch protection rules* de `main` com a regra ativa; reavaliar GC Q1 e GQA Q3 com esses links como evidência |

## Ação 2 — Integração contínua ativa como portão de merge

| Campo | Definição |
|---|---|
| **Problema identificado** | Testes, cobertura mínima e lint existem, mas só rodam se alguém lembrar (GQA Q2 = L, MA Q2 = L). O workflow `.github/workflows/tests.yml` nunca executou. |
| **Ação corretiva** | Publicar o workflow; tornar o check `tests` obrigatório na proteção de `main`; adicionar um *lock file* de dependências (`pip-tools` → `requirements.lock`) para que CI e máquinas locais instalem as mesmas versões (GC Q3). |
| **Responsável** | Integrante B |
| **Prazo** | 20/11/2026 (fim da Sprint 2) |
| **Indicador de sucesso** | 100% dos merges em `main` com o check `tests` verde; cobertura ≥ 80% em todas as execuções; 0 achados do ruff |
| **Critério de validação** | Aba *Actions* mostra execuções verdes ligadas a cada PR mergeado; um PR de teste com cobertura < 80% é bloqueado (prova de que o portão funciona) |

## Ação 3 — Tratar riscos materializados, começando pelo R1 (fonte de dados real)

| Campo | Definição |
|---|---|
| **Problema identificado** | R1 aconteceu e ficou sem ação: o modelo só treina com dados sintéticos, porque a base Kaggle não tem ausência diária (GRi Q3 = P). Os riscos também não eram reavaliados com registro (GRi Q2 = P). A auditoria de qualidade achou 3.784 registros inconsistentes (QC06, `reports/sbar.md`), outro sinal de que a base é sintética. |
| **Ação corretiva** | (a) Decidir, com o professor/PO, entre buscar uma base com ausência diária ou redefinir o alvo do modelo para algo que a base atual sustenta (ex.: `Sick_Days` acima do percentil 75); (b) criar `docs/risk_log.md` com uma linha por risco por sprint (status, exposição, ação). |
| **Responsável** | Integrante C (modelagem) para (a); Integrante D para (b) |
| **Prazo** | Decisão (a) até 20/11/2026; modelo treinado na base escolhida até 04/12/2026; (b) a cada revisão de sprint a partir de 20/11/2026 |
| **Indicador de sucesso** | `artifacts/metrics.json` com `source` ≠ `synthetic`, mantendo recall ≥ 0,60 e AUC ≥ 0,70 **ou** registro formal de que a meta não é atingível com dados reais; 100% dos riscos com linha no log em cada sprint |
| **Critério de validação** | `python -m src.ml.train --source csv --path <base>` roda e grava métricas; `docs/risk_log.md` tem entradas datadas de 20/11 e 04/12; reavaliar GRi Q2 e Q3 |

## Efeito esperado na próxima autoavaliação

| Pergunta | Hoje | Meta após as ações |
|---|:-:|:-:|
| GC Q1 — histórico rastreável | N | L |
| GC Q2 — branches praticadas | P | L |
| GC Q3 — itens de configuração | L | F |
| GQA Q2 — verificação automática | L | F |
| GQA Q3 — revisão independente | N | L |
| MA Q2 — coleta reproduzível | L | F |
| GRi Q2 — reavaliação de riscos | P | L |
| GRi Q3 — ação sobre risco materializado | P | L |

## Situação em 11/11/2026

| Ação | Status | Evidência |
|---|---|---|
| 1 — Revisão por par real | **Preparada, não executada.** Script e guia prontos; falta criar o repositório, abrir os PRs e um colega revisar | `scripts/github_setup.py` (testado localmente: 7 PRs em sequência, CI verde em cada etapa), `docs/pr_review_guide.md` |
| 2 — CI como portão | **Preparada, não executada.** Workflow pronto; a proteção da `main` exige os checks `ruff` e `pytest (3.11/3.12)` | `.github/workflows/tests.yml`, `scripts/github_setup.py init` |
| 3 — Riscos / R1 | **Parcial.** Alvo redefinido, modelo por funcionário, quarentena QC06, portão de qualidade antes do treino e registro de riscos criados. A decisão sobre a fonte segue pendente, e surgiu o R7 | `src/ml/kaggle_risk.py`, `docs/risk_log.md`, `docs/05-dados-reais.md`, `reports/data_lineage.md` |
