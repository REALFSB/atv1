# Retrospectiva da Sprint 1 — Start · Stop · Continue

| Campo | Valor |
|---|---|
| Data | 06/11/2026 |
| Formato | Start, Stop, Continue (timebox de 45 min) |
| Insumos | `docs/sprint_review.md`, `reports/metrics.md`, `docs/kanban.md` |

> Os itens abaixo partem de fatos medidos nesta sprint. As falas e votos dos integrantes
> não foram registrados neste material; o grupo deve confirmar ou ajustar a lista.

## Start — começar a fazer

- **Abrir PR por história e exigir revisão de outra pessoa.** Fato: 0 de 31 pts chegaram a
  Feito, e a única causa foi a falta de revisão.
- **Fazer análise de impacto antes de aceitar escopo novo.** Fato: +10 pts (+48%) entraram
  sem troca e sem registro.
- **Medir precisão do modelo, não só recall.** Fato: precisão de 0,21.
- **Datar a entrada e a saída de cada cartão.** Fato: sem datas, lead time e cycle time não
  são mensuráveis.

## Stop — parar de fazer

- **Parar de mover cartões para "pronto" com base em "o teste passa".** Teste verde é o
  item 2 de 6 da DoD.
- **Parar de puxar trabalho novo com a coluna Em revisão cheia.** Fato: 8 cartões para
  limite 4.
- **Parar de tratar dados sintéticos como validação do modelo.** As métricas da US2 provam
  que o pipeline roda, não que o modelo funciona na operação.

## Continue — continuar fazendo

- **Critérios de aceite com número** (5 s, 5% de nulos, recall ≥ 0,60): é o que permitiu
  transformar cada critério em teste.
- **Separação por módulo** (`data` / `ml` / `serving` / `validate` / `webapp`): cada
  história mexeu em um lugar só.
- **Métricas geradas por script, não digitadas.** `collect_metrics.py` e o teste que
  compara o relatório versionado com o código mantêm os documentos honestos.
- **Validar dados antes de usar.** A auditoria achou 3.784 registros inconsistentes que
  nenhum teste de nulos pegaria.

## Ações de melhoria (máximo 2)

| # | Ação | Responsável | Prazo | Como saberemos que funcionou |
|---|---|---|---|---|
| 1 | Toda história passa por PR com aprovação de quem **não** escreveu o código; `main` protegida | Integrante A | 20/11/2026 | 100% dos merges da Sprint 2 com aprovação; pontos em Feito ≥ 50% do comprometido |
| 2 | Limite WIP de 4 em "Em revisão" respeitado: ninguém começa história nova com a coluna cheia; escopo novo só entra trocando item de mesmo tamanho, com registro em `docs/backlog.md` | Integrante D (Scrum Master da Sprint 2) | Durante toda a Sprint 2 (até 20/11/2026) | Coluna Em revisão nunca acima de 4; crescimento de escopo ≤ 10% sem troca |

A ação 1 coincide com a ação 1 do `docs/improvement_plan.md` de propósito: a retrospectiva e
a autoavaliação chegaram ao mesmo gargalo por caminhos diferentes.
