# DataTrack · Radar de Absenteísmo

Painel de operações (HTML + Tailwind, publicado na Vercel) com um pipeline de Machine Learning que prevê o **risco de ausência de cada operador no próximo turno**, para que o Head de Operações remaneje a escala antes de a meta ser afetada.

Projeto Integrador · CCD610 · Checkpoint (Aulas 4–6): requisitos → arquitetura/SOLID → planejamento.

## Estrutura do repositório

```
├── index.html        # redireciona para a aplicação em paineis/
├── paineis/           # páginas HTML e dados estáticos consumidos pelo painel
│   ├── index.html, equipes.html, metas.html, relatorios.html
│   └── risco-data.js  # gerado pelo serving e lido por equipes.html
├── src/
│   ├── data/ingest.py       # fontes, validação e pseudonimização
│   ├── ml/features.py       # engenharia compartilhada de atributos
│   ├── ml/train.py          # treino, split temporal e métricas
│   ├── serving/risk.py      # inferência, ranking e exportações
│   └── ingest.py, features.py, train.py, serve.py  # aliases compatíveis
├── tests/            # pytest, um arquivo por módulo
├── docs/             # backlog, requisitos, arquitetura/SOLID, WBS, riscos, Sprint 1
├── data/             # dados brutos (fora do Git)
└── artifacts/        # model.joblib e metrics.json (fora do Git)
```

## Como executar

```bash
pip install -r requirements.txt
python -m pytest -q                    # testes
python -m src.ml.train                 # treina com dados sintéticos e salva artifacts/
python -m src.serving.risk             # gera artifacts/ranking.csv e paineis/risco-data.js
```

Com a base real (Kaggle) em CSV, ajuste `column_map` em `CsvSource` para o esquema descrito em `docs/02-requisitos.md` e rode:

```bash
python -m src.ml.train --source csv --path data/minha_base.csv
python -m src.serving.risk --source csv --path data/minha_base.csv
```

Defina `DATATRACK_SALT` no ambiente (sal do hash dos IDs; LGPD). Os dados sintéticos servem para validar o pipeline: **suas métricas não representam a operação real**.

## Painel ligado ao modelo
Após executar os comandos de treino e serving, abra [`paineis/index.html`](paineis/index.html) (ou [`index.html`](index.html), que redireciona para lá). A página [`paineis/equipes.html`](paineis/equipes.html) mostra as faixas, o ranking dos 10 maiores riscos (filtro por setor) e exporta a lista completa em CSV. Faça commit de `paineis/risco-data.js` atualizado para a Vercel publicar. Enquanto a fonte for sintética, a página exibe o selo *DADOS SINTÉTICOS (DEMO)*.

Os comandos e imports antigos (`python -m src.train`, `python -m src.serve` e `src.ingest`, por exemplo) continuam disponíveis como aliases de compatibilidade.

## Arquitetura e SOLID
Ingestão → features → treino → artefato → serving. Detalhes e diagrama em [`docs/03-arquitetura.md`](docs/03-arquitetura.md). `train_model(source: DataSource)` depende da abstração, não de um CSV.

## Documentação do checkpoint
[`01-backlog`](docs/01-backlog.md) · [`02-requisitos`](docs/02-requisitos.md) · [`03-arquitetura`](docs/03-arquitetura.md) · [`04-planejamento-e-riscos`](docs/04-planejamento-e-riscos.md) · `docs/backlog_issues.csv` (importação para GitHub Issues/Trello).
