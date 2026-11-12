# DataTrack · Radar de Absenteísmo

Projeto Integrador · CCD610 · Checkpoint das Aulas 7, 8 e 9 (Métodos Ágeis, Modelos de
Referência, Governança de Dados e Qualidade de Software).

O DataTrack estima **quais funcionários têm risco de absenteísmo elevado**, para que o Head de
Operações reorganize a escala antes de a meta ser afetada. O repositório tem cinco partes:

| Parte | O que faz | Onde |
|---|---|---|
| Modelo operacional (diário) | ingestão com LGPD → atributos → treino com split temporal → ranking | `src/data/ingest.py`, `src/ml/`, `src/serving/` |
| Modelo por funcionário | alvo `Sick_Days ≥ 11` na base Kaggle, quarentena QC06, portão de qualidade | `src/data/employees.py`, `src/ml/kaggle_risk.py` |
| Qualidade de dados | 6 regras (completude, unicidade, validade, consistência) em pandas **e** SQL | `src/validate.py`, `sql/quality_checks.sql` |
| Aplicação web | login, cadastro, logout, dashboard e 4 painéis protegidos | `src/webapp/`, `paineis/`, `src/dashboard.py` |
| Gestão do projeto | backlog, Kanban, review, retro, maturidade, plano de melhoria, checkpoint | `docs/`, `reports/` |

> ⚠️ **Leia antes de usar os números do modelo.** A base de trabalho
> (`..._2_otimizado.csv`) é a base do Kaggle com a coluna `Sick_Days` **regerada** para
> depender de horas extras, jornada e satisfação. Com o mesmo código, o modelo tem **AUC 0,50
> na base original** e **0,91 na otimizada**. O 0,91 mostra que o pipeline funciona, não que
> prevê absenteísmo real (`reports/data_lineage.md`, `docs/05-dados-reais.md`).

**Documento de entrega:** [`docs/entrega3_checkpoint.md`](docs/entrega3_checkpoint.md) preenche
todas as seções do enunciado e lista o que o grupo ainda precisa fazer no GitHub.

## Resultados (execução local de 11/11/2026)

| Indicador | Valor | Fonte |
|---|---:|---|
| Testes executados / aprovados / reprovados | 135 / 135 / 0 | `reports/junit.xml` |
| Cobertura de código (`src/`, linhas + ramos) | 91,0% | `reports/coverage.json` |
| Alertas do ruff | 0 | `reports/ruff.txt` |
| Regras de qualidade, base completa (100.000) | 5 aprovadas · 1 reprovada (QC06) | `reports/quality_report_full_base.md` |
| Conformidade geral, base completa | 99,37% · LIBERADA COM RESSALVAS | idem |
| Regras de qualidade, amostra fixa (defeitos injetados) | 0 aprovadas · 6 reprovadas | `reports/quality_report.md` |
| Modelo por funcionário, base otimizada | AUC 0,914 · recall 0,844 · precisão 0,608 | `reports/model_metrics.json` |
| O mesmo modelo, base Kaggle original | AUC 0,498 · recall 0,503 | `reports/data_lineage.md` |
| Baseline Sprint 1 (pontos que cumprem a DoD) | 0 de 31 | `docs/sprint_review.md` |
| Kanban (A fazer / Em andamento / Em revisão / Feito) | 2 / 2 / 8 / 0 | `docs/kanban.md` |
| Maturidade (18 perguntas) | F 5 · L 7 · P 4 · N 2 | `reports/maturity_assessment.md` |

Tudo é regenerado por `python scripts/collect_metrics.py --run` e consolidado em
[`reports/metrics.md`](reports/metrics.md). **O CI ainda não rodou no GitHub**: não existe
resultado de GitHub Actions até o repositório ser publicado.

## Instalação

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Coloque as bases em `data/raw/` (ficam fora do Git):
- `Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv` (base de trabalho)
- `Extended_Employee_Performance_and_Productivity_Data.csv` (original; opcional, só para a linhagem)

## Gerar dados, modelo e métricas

```bash
python scripts/collect_metrics.py --run
```

Esse comando roda, em ordem: pytest com cobertura, ruff, validação de qualidade (amostra e base
completa), modelo por funcionário (`paineis/risco-data.js`), gerador do painel
(`paineis/dashboard-data.js`) e comparação de linhagem. Passo a passo:

```bash
python -m src.validate --data data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv \
  --report reports/quality_report_full_base.md --json reports/quality_results_full_base.json
python -m src.ml.kaggle_risk --data data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv
python -m src.dashboard      --data data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv
python scripts/compare_bases.py \
  --original data/raw/Extended_Employee_Performance_and_Productivity_Data.csv \
  --derived  data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv
```

`src.ml.kaggle_risk` roda as 6 regras antes de treinar e **se recusa a treinar** se a base sair
`BLOQUEADA` (só passa com `--skip-quality-gate`).

## Executar a aplicação web

```bash
export DATATRACK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
# Windows PowerShell: $env:DATATRACK_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
flask --app src.webapp run                 # http://127.0.0.1:5000
```

Crie a conta em **/cadastro** ou com `flask --app src.webapp create-user`. Fluxo: `/login` →
`/dashboard` → painéis em `/paineis/*.html` (todos exigem login; a barra lateral mostra o
usuário logado e o botão de sair) → **Sair**.

| Variável | Para quê | Padrão |
|---|---|---|
| `DATATRACK_SECRET_KEY` | assina o cookie de sessão | aleatória por execução |
| `DATATRACK_DB` | SQLite de usuários | `instance/users.db` |
| `DATATRACK_ALLOW_SIGNUP` | habilita `/cadastro` | `true` |
| `DATATRACK_SECURE_COOKIE` | cookie só via HTTPS | `false` (ligar em produção) |
| `DATATRACK_SALT` | sal do hash dos IDs (LGPD) | valor de desenvolvimento |

**Segurança:** senhas com hash scrypt; mesma mensagem e tempo de resposta parecido para senha
errada e e-mail inexistente; CSRF em todo POST; logout só via POST; cookie `HttpOnly` +
`SameSite=Lax`; sessão renovada no login; `next` só aceita caminho interno; bloqueio após 5
falhas em 15 min; CSP estrita nas páginas novas. Limitações conhecidas em
`docs/peer_review_simulation.md` (comentários 2 e 3).

> **Vercel:** a versão estática não tem login (HTML estático não autentica ninguém). Para
> publicar com login, use um host Python (Render, Railway, Fly.io).

## Testes e qualidade

```bash
pytest                                                  # 135 testes
pytest --cov=src --cov-branch --cov-report=term-missing # cobertura (falha abaixo de 80%)
pytest -m auth                                          # só autenticação
pytest -m smoke                                         # smoke tests do pipeline
ruff check .
```

| ID | Dimensão | Regra | Meta |
|---|---|---|---:|
| QC01 | Completude | 8 campos obrigatórios preenchidos | 100% (crítica) |
| QC02 | Unicidade | `Employee_ID` não se repete | 100% (crítica) |
| QC03 | Validade | categorias no catálogo | 99% |
| QC04 | Validade | números na faixa (idade 18–70, nota 1–5, salário, horas, afastamentos…) | 99% |
| QC05 | Consistência | `Years_At_Company` = dias desde `Hire_Date` ÷ 365 (ref. 04/09/2024) | 99% |
| QC06 | Consistência | idade na admissão (`Age − Years_At_Company`) ≥ 18 | 99% |

## Publicar no GitHub (gestão de configuração)

O enunciado exige PRs revisados, main protegida, CI e issues ligadas às histórias. O script
abaixo prepara tudo, **mas a revisão e o merge de cada PR são feitos por uma pessoa**.

```bash
gh auth login                        # e, para o quadro: gh auth refresh -s project
python scripts/github_setup.py plan  # mostra a ordem dos 7 PRs
python scripts/github_setup.py init --repo <dono>/datatrack --project
python scripts/github_setup.py pr ingestao     # colega revisa → merge → próximo passo
python scripts/github_setup.py trace           # gera docs/rastreabilidade.md com links reais
```

Use um repositório **novo e público**: no plano gratuito, a proteção de branch só funciona em
repositório público. Guia para o revisor: `docs/pr_review_guide.md`.

## Estrutura

```
├── src/
│   ├── validate.py              # US11 — regras de qualidade
│   ├── dashboard.py             # gera paineis/dashboard-data.js
│   ├── data/ingest.py           # US3, US4 (modelo diário)
│   ├── data/employees.py        # base de funcionários (Kaggle) no esquema unificado
│   ├── ml/features.py, train.py # US2 (modelo diário, dados sintéticos)
│   ├── ml/kaggle_risk.py        # US2 (modelo por funcionário) → paineis/risco-data.js
│   ├── serving/risk.py          # US1, US5, US6
│   └── webapp/                  # US12 — Flask
├── tests/                       # 135 testes
├── sql/quality_checks.sql
├── data/sample_data.csv  data/README.md  data/dashboard_sources_snapshot.json
├── reports/                     # qualidade, SBAR, linhagem, maturidade, métricas
├── docs/                        # backlog, kanban, review, retro, plano, atas, checkpoint
├── scripts/                     # build_sample, collect_metrics, compare_bases, github_setup
├── paineis/                     # painéis HTML (servidos atrás do login)
├── apresentacao/                # slides do checkpoint (.pptx)
├── .github/workflows/tests.yml  .github/pull_request_template.md
├── pyproject.toml  requirements.txt
```

## Avisos

- Commits, PRs, revisões e feedbacks citados nos documentos são **planejados ou simulados**, e
  estão marcados como tal. O material recebido não tinha histórico Git.
- Responsáveis aparecem como Integrantes A–D: troque pelos nomes do grupo.
- Defina `DATATRACK_SALT` e `DATATRACK_SECRET_KEY` próprios fora do ambiente de desenvolvimento.
