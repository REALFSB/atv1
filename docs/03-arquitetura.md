# Arquitetura de referência e SOLID

```mermaid
flowchart LR
  A[(Fonte: Kaggle CSV / base interna)] -->|DataSource.load| B[ingest.py<br/>validar · descartar sensíveis · pseudonimizar]
  B --> C[features.py<br/>add_features · preprocessor]
  C --> D[train.py<br/>split temporal · métricas]
  D -->|model.joblib + metrics.json| E[(artifacts/)]
  E --> F[serve.py<br/>predict_risk · faixa · fatores · CSV]
  B -->|dados do dia| F
  C -. mesma função de features .-> F
  F -->|risco-data.js| G[equipes.html<br/>Radar de Risco de Ausência]
```

## Princípios SOLID aplicados

| Princípio | Onde | Problema resolvido |
|---|---|---|
| S · SRP | ingest / features / train / serve | Um script único misturava carga, limpeza, treino e saída; agora cada módulo tem um motivo para mudar e é testável isoladamente. |
| O · OCP | train.py (MODEL_REGISTRY) | Novos algoritmos entram com register_model(), sem editar train_model(). Testado com um DummyClassifier. |
| L · LSP | ingest.py (CsvSource, SyntheticSource) | Qualquer DataSource devolve o mesmo esquema e pode substituir outra; o teste usa uma fonte em memória. |
| I · ISP | serve.py (Predictor) | Serving exige só predict_proba(); não conhece treino nem a classe do modelo. |
| D · DIP | train.py ← DataSource | train_model(source: DataSource) não sabe se os dados vêm de CSV, Kaggle ou banco; trocar a fonte não altera o treino. |

## Do backlog aos módulos

| Story | Módulo |
|---|---|
| US1 | train.py, serve.py |
| US2 | features.py, train.py |
| US3 | ingest.py |
| US4 | ingest.py |
| US5 | serve.py |
| US6 | serve.py |
| US7 | monitor.py (novo) |
| US8 | serve.py, monitor.py |
| US9 | monitor.py (novo) |
| US10 | serve.py |

## Pontos de atenção
- `features.py` é a única definição de atributos (sem duplicar lógica entre treino e serving).
- Split **temporal**: treina no passado, testa no futuro.
- `monitor.py` (US7, US9) ainda não existe — é Onda 2.
