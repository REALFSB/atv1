# DataTrack · Radar de Absenteísmo

Painel de operações (HTML + Tailwind, publicado na Vercel) com um pipeline de Machine Learning que prevê o **risco de absenteísmo elevado (≥ 11 dias de afastamento/ano) de cada funcionário**, para o Head de Operações agir antes de a meta ser afetada.

Projeto Integrador · CCD610 · Checkpoint (Aulas 4–6): requisitos → arquitetura/SOLID → planejamento.

## Estrutura do repositório

```
├── index.html, equipes.html, metas.html, relatorios.html   # painel web (equipes.html exibe o Radar de Risco)
├── datatrack.js      # utilitários do painel: agregação, status das metas, menu, exportações
├── dashboard-data.js # agregados dos 3 CSVs lidos pelas 4 páginas (gerado por src.dashboard)
├── risco-data.js     # saída do modelo lida por equipes.html (gerada por src.serve)
├── src/
│   ├── harmonize.py  # mescla e limpeza das 3 bases do Kaggle em um esquema único
│   ├── ingest.py     # DataSource (abstração), KaggleHRSource, CsvSource, SyntheticSource, validação, LGPD
│   ├── dashboard.py  # agregados do painel (soma/contagem por fonte × departamento) → dashboard-data.js
│   ├── features.py   # engenharia de atributos (única, usada por treino e serving)
│   ├── train.py      # treino, split estratificado, métricas, registro de modelos
│   └── serve.py      # inferência: ranking, faixa, fatores, exportação CSV
├── tests/            # pytest, um arquivo por módulo
├── docs/             # backlog, requisitos, arquitetura/SOLID, WBS, riscos, Sprint 1
├── data/raw/         # os 3 CSVs do Kaggle (fora do Git)
├── data/processed/   # base unificada gerada (fora do Git)
└── artifacts/        # model.joblib e metrics.json (fora do Git)
```

## Como executar

```bash
pip install -r requirements.txt
python -m pytest -q                                       # testes
python -m src.train --source kaggle --path data/raw       # treina com a base real
python -m src.serve --source kaggle --path data/raw       # gera artifacts/ranking.csv e risco-data.js
python -m src.dashboard --path data/raw                    # gera dashboard-data.js (KPIs, metas, relatórios)
```

Sem a base, use `--source synthetic` (dados sintéticos só para demonstrar o fluxo). Com outro CSV já no esquema do projeto: `--source csv --path arquivo.csv`.

**Resultado atual com a base real: AUC 0,50 / recall 0,52 — abaixo da meta.** As bases do Kaggle não têm padrão de faltas para aprender (detalhes em [`docs/05-dados-reais.md`](docs/05-dados-reais.md)); o painel mostra aviso e o ranking não deve apoiar decisões.

Defina `DATATRACK_SALT` no ambiente (sal do hash dos IDs; LGPD). Os dados sintéticos servem para validar o pipeline: **suas métricas não representam a operação real**.

## Painel ligado aos dados
Nenhum número do painel é digitado à mão. `python -m src.dashboard` agrega os 3 CSVs e grava `dashboard-data.js`; as quatro páginas calculam KPIs, gráficos, metas e relatórios a partir dele. O seletor **Todas as bases / Extended / HR Dashboard / Productivity** recalcula tudo (média ponderada). Como as bases não têm série diária, o antigo filtro *Hoje/Semana/Mês* virou filtro por base, e o gráfico de produtividade mostra o índice por **ano de admissão**.

- **Produtividade** = desempenho (1–5) convertido para 0–100, a mesma escala usada em `harmonize.py`.
- **Metas** (alvo de produtividade, satisfação, horas extras, afastamento) são *parâmetros de negócio* definidos em `src/dashboard.py` (`PARAMS`): não existem nas bases e podem ser trocados. O realizado é sempre calculado.
- **Relatórios**: CSV, XLSX e PDF gerados no navegador; o histórico e as metas personalizadas ficam no `localStorage`.
- Campos que uma base não possui aparecem como "–" (ex.: horas extras na HR Dashboard). Afastamento só é exibido para grupos com 5+ pessoas (LGPD).

## Radar de risco (modelo)
Após `python -m src.train` e `python -m src.serve`, abra `equipes.html`: a seção **Radar de Risco de Ausência** mostra as faixas, o ranking dos 10 maiores riscos (filtro por departamento) e exporta a lista completa em CSV. Faça commit do `risco-data.js` atualizado para a Vercel publicar. A página exibe a origem dos dados (*BASE KAGGLE* ou *DADOS SINTÉTICOS (DEMO)*) e um **aviso vermelho quando o modelo não atinge as metas**.

## Arquitetura e SOLID
Ingestão → features → treino → artefato → serving. Detalhes e diagrama em [`docs/03-arquitetura.md`](docs/03-arquitetura.md). `train_model(source: DataSource)` depende da abstração, não de um CSV.

## Documentação do checkpoint
[`01-backlog`](docs/01-backlog.md) · [`02-requisitos`](docs/02-requisitos.md) · [`03-arquitetura`](docs/03-arquitetura.md) · [`04-planejamento-e-riscos`](docs/04-planejamento-e-riscos.md) · [`05-dados-reais`](docs/05-dados-reais.md) · `docs/backlog_issues.csv` (importação para GitHub Issues/Trello).
