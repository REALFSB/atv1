# DataTrack · Radar de Absenteísmo

Painel de operações (HTML + Tailwind, publicado na Vercel) com um pipeline de Machine Learning que prevê o **risco de ausência de cada operador no próximo turno**, para que o Head de Operações remaneje a escala antes de a meta ser afetada.

Projeto Integrador · CCD610 · Checkpoint (Aulas 4–6): requisitos → arquitetura/SOLID → planejamento.

## Estrutura do repositório

```
├── index.html, equipes.html, metas.html, relatorios.html   # painel web (equipes.html exibe o Radar de Risco)
├── risco-data.js     # saída do modelo lida por equipes.html (gerada por src.serve)
├── src/
│   ├── ingest.py     # DataSource (abstração), CsvSource, SyntheticSource, validação, LGPD
│   ├── features.py   # engenharia de atributos (única, usada por treino e serving)
│   ├── train.py      # treino, split temporal, métricas, registro de modelos
│   └── serve.py      # inferência: ranking, faixa, fatores, exportação CSV
├── tests/            # pytest, um arquivo por módulo
├── docs/             # backlog, requisitos, arquitetura/SOLID, WBS, riscos, Sprint 1
├── data/             # dados brutos (fora do Git)
└── artifacts/        # model.joblib e metrics.json (fora do Git)
```

## Como executar

```bash
pip install -r requirements.txt
python -m pytest -q                    # testes
python -m src.train                    # treina com dados sintéticos e salva artifacts/
python -m src.serve                    # gera artifacts/ranking.csv e risco-data.js (painel)
```

Com a base real (Kaggle) em CSV, ajuste `column_map` em `CsvSource` para o esquema descrito em `docs/02-requisitos.md` e rode:

```bash
python -m src.train --source csv --path data/minha_base.csv
python -m src.serve --source csv --path data/minha_base.csv
```

Defina `DATATRACK_SALT` no ambiente (sal do hash dos IDs; LGPD). Os dados sintéticos servem para validar o pipeline: **suas métricas não representam a operação real**.

## Painel ligado ao modelo
Após `python -m src.train` e `python -m src.serve`, abra `equipes.html`: a seção **Radar de Risco de Ausência** mostra as faixas, o ranking dos 10 maiores riscos (filtro por setor) e exporta a lista completa em CSV. Faça commit do `risco-data.js` atualizado para a Vercel publicar. Enquanto a fonte for sintética, a página exibe o selo *DADOS SINTÉTICOS (DEMO)*.

## Arquitetura e SOLID
Ingestão → features → treino → artefato → serving. Detalhes e diagrama em [`docs/03-arquitetura.md`](docs/03-arquitetura.md). `train_model(source: DataSource)` depende da abstração, não de um CSV.

## Documentação do checkpoint
[`01-backlog`](docs/01-backlog.md) · [`02-requisitos`](docs/02-requisitos.md) · [`03-arquitetura`](docs/03-arquitetura.md) · [`04-planejamento-e-riscos`](docs/04-planejamento-e-riscos.md) · `docs/backlog_issues.csv` (importação para GitHub Issues/Trello).
