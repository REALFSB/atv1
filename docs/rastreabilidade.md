# Rastreabilidade: história → issue → branch → PR → teste

> **Versão planejada.** As colunas *Issue* e *Pull request* só ganham número e link quando
> `scripts/github_setup.py` rodar no GitHub. Depois disso, rode
> `python scripts/github_setup.py trace` para sobrescrever este arquivo com os links reais e o
> status de revisão de cada PR. Nada aqui foi criado no GitHub ainda.

| História | Issue | Branch | Pull request (ordem de merge) | Teste que comprova o critério |
|---|---|---|---|---|
| US3 · barrar dados ruins | a criar | `feature/US3-US4-ingestao-lgpd` | PR 1 · `feat(data): ingestão com validação de nulos e pseudonimização` | `tests/test_ingest.py::test_validate_rejects_*` |
| US4 · LGPD | a criar | `feature/US3-US4-ingestao-lgpd` | PR 1 (mesmo PR) | `tests/test_ingest.py::test_pseudonymize_*`, `test_sensitive_columns_are_dropped` |
| US2 · modelo (diário) | a criar | `feature/US2-modelo-operacional` | PR 2 · `feat(ml): atributos e treino com split temporal` | `tests/test_train.py`, `tests/test_features.py` |
| US1 · ranking | a criar | `feature/US1-US5-US6-ranking` | PR 3 · `feat(serving): ranking, exportação CSV e fatores` | `tests/test_serve.py::test_ranking_is_sorted_desc_with_bands` |
| US5 · CSV | a criar | `feature/US1-US5-US6-ranking` | PR 3 (mesmo PR) | `tests/test_serve.py::test_export_csv_keeps_all_rows` |
| US6 · fatores | a criar | `feature/US1-US5-US6-ranking` | PR 3 (mesmo PR) | `tests/test_serve.py::test_top_factors_returns_three_per_operator` |
| US11 · qualidade de dados | a criar | `feature/US11-qualidade-dados` | PR 4 · `feat(validate): 6 regras em pandas e SQL` | `tests/test_validate.py`, `tests/test_smoke.py` |
| US12 · login | a criar | `feature/US12-autenticacao` | PR 5 · `feat(webapp): login, cadastro, logout e rotas protegidas` | `tests/test_auth.py` |
| US2 · modelo por funcionário | (mesma issue da US2) | `feature/US2-modelo-por-funcionario` | PR 6 · `feat(ml): modelo por funcionário e gerador do painel` | `tests/test_employee_model.py` |
| US8 · painel de metas (dados) | a criar | `feature/US2-modelo-por-funcionario` | PR 6 (mesmo PR) | `tests/test_employee_model.py::test_dashboard_*` |
| — documentação | — | `docs/sprint-1-gestao` | PR 7 · `docs: Sprint 1, autoavaliação, plano de melhoria e métricas` | — |

**Validação local do plano (11/11/2026):** os 7 PRs foram aplicados em sequência num
repositório Git local (`--dry-run`), e em cada etapa a `main` resultante passou em
`pytest --cov` e `ruff`. Resultado: 9 → 15 → 23 → 28 → 74 → 116 → 135 testes, cobertura entre
82,4% e 91,0%, 0 alertas. Isso mostra que a ordem de merge funciona; **não** substitui o CI
real nem a revisão.
