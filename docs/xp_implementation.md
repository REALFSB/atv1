# Estrutura de implementação com práticas XP

> **Aviso de honestidade:** este repositório foi entregue **sem histórico Git**. Os commits e
> branches abaixo são **sugestões documentadas para execução futura** — nenhum deles foi
> criado. A ordem "teste antes do código" é a sequência TDD proposta; não há como provar, pelo
> material entregue, que os arquivos foram escritos nessa ordem.

## 1. Organização do código por funcionalidade

Cada pasta corresponde a uma responsabilidade do produto (SRP) e a histórias do backlog:

```
src/
├── data/ingest.py        # US3, US4 — fontes, validação de nulos, pseudonimização (LGPD)
├── ml/features.py        # US2 — atributos compartilhados entre treino e serving
├── ml/train.py           # US2 — split temporal, métricas, registro de modelos (OCP)
├── serving/risk.py       # US1, US5, US6 — ranking, faixas, fatores, exportação CSV/JS
├── validate.py           # US11 — 6 regras de qualidade, paridade SQL × pandas, relatório
└── webapp/               # US12 — aplicação Flask
    ├── auth.py           #   login, cadastro, logout, @login_required
    ├── db.py             #   usuários em SQLite, hash scrypt
    ├── security.py       #   CSRF, next seguro, limite de tentativas, cabeçalhos
    ├── views.py          #   dashboard e painéis legados protegidos
    ├── indicators.py     #   lê reports/metrics.json (números reais)
    ├── templates/ static/
sql/quality_checks.sql    # US11 — mesmas regras em SQL
tests/                    # um arquivo de teste por funcionalidade
```

| Funcionalidade | Código | Testes |
|---|---|---|
| Ingestão e LGPD (US3, US4) | `src/data/ingest.py` | `tests/test_ingest.py` |
| Atributos (US2) | `src/ml/features.py` | `tests/test_features.py` |
| Treino (US2) | `src/ml/train.py` | `tests/test_train.py` |
| Ranking e exportação (US1, US5, US6) | `src/serving/risk.py` | `tests/test_serve.py` |
| Qualidade de dados (US11) | `src/validate.py`, `sql/quality_checks.sql` | `tests/test_validate.py`, `tests/test_smoke.py` |
| Autenticação (US12) | `src/webapp/` | `tests/test_auth.py` |

## 2. TDD — ciclo vermelho → verde → refatorar

Para cada história, a sequência proposta é: (1) escrever o teste do critério de aceite e
vê-lo falhar; (2) escrever o mínimo de código para passar; (3) refatorar com os testes verdes.

**Exemplo concreto — QC06 (admissão com maioridade), US11:**

```python
# 1. VERMELHO — tests/test_validate.py (falha: check_admission_age ainda não existe)
def test_admission_before_18_fails_qc06_only():
    # 22 anos com 5 anos de casa → admitido aos 17
    assert failed_rules(make_df(r2={"Age": "22"})) == {"QC06": 1}

# 2. VERDE — src/validate.py
def check_admission_age(df):
    evaluated = df["Age"].notna() & df["Years_At_Company"].notna()
    ok = (df["Age"] - df["Years_At_Company"]) >= MIN_ADMISSION_AGE
    return evaluated, ok.fillna(False) | ~evaluated

# 3. REFATORAR — extrair MIN_ADMISSION_AGE, adicionar a mesma regra em SQL
#    e o teste de paridade test_sql_and_pandas_agree.
```

**Evidência verificável de que os testes restringem o código** (executado nesta entrega):
alterar `MIN_ADMISSION_AGE` de 18 para 17 faz **3 testes falharem**; alterar só o SQL
(`>= 18` para `>= 17`) faz o teste de paridade falhar. Ou seja, nem o motor pandas nem o
SQL podem mudar sozinhos sem que a suíte acuse.

Ordem TDD sugerida por história:

| História | Teste escrito primeiro | Função implementada depois |
|---|---|---|
| US3 | `test_validate_rejects_more_than_5pct_nulls_and_names_column` | `ingest.validate` |
| US4 | `test_pseudonymize_is_deterministic_and_hides_ids` | `ingest.pseudonymize` |
| US1 | `test_ranking_is_sorted_desc_with_bands` | `risk.predict_risk` |
| US2 | `test_time_split_has_no_leakage`, `test_metrics_meet_targets_on_synthetic` | `train.time_split`, `train.train_model` |
| US5 | `test_export_csv_keeps_all_rows` | `risk.export_risk_csv` |
| US11 | `test_single_defect_is_caught_only_by_its_rule[*]` | `validate.check_*` |
| US11 | `test_sql_and_pandas_agree[*]` | `sql/quality_checks.sql`, `validate.run_sql_checks` |
| US12 | `test_login_with_valid_credentials_redirects_to_dashboard` | `auth.login`, `db.authenticate` |
| US12 | `test_private_pages_redirect_anonymous_user_to_login[*]` | `auth.login_required` |
| US12 | `test_logout_ends_session` | `auth.logout` |

## 3. Commits sugeridos (apenas documentação — não executados)

Padrão [Conventional Commits](https://www.conventionalcommits.org/): `tipo(escopo): resumo`,
um commit = uma mudança atômica, teste antes da implementação.

```text
# feature/US11-qualidade-dados
test(validate): cobre regras QC01–QC06 com um defeito por regra
feat(validate): implementa regras de completude, unicidade, validade e consistência
test(validate): exige paridade entre SQL e pandas
feat(sql): adiciona consultas QC01–QC06 em sql/quality_checks.sql
feat(data): adiciona amostra fixa de 30 registros com 6 defeitos documentados
test(smoke): valida pipeline de qualidade na amostra fixa
docs(reports): gera relatório de qualidade e SBAR da regra QC06

# feature/US12-autenticacao
test(auth): cobre login válido, senha errada, campos vazios e usuário inexistente
feat(auth): implementa login com hash scrypt e mensagem genérica de erro
test(auth): exige login para dashboard e painéis
feat(auth): protege rotas privadas e painéis legados
test(auth): cobre logout via POST com CSRF
feat(auth): implementa logout e proteção CSRF
feat(ui): cria tela de login responsiva com mostrar/ocultar senha
feat(ui): cria dashboard com indicadores lidos de reports/metrics.json

# chore/qualidade-ci
build: adiciona pyproject.toml com pytest, pytest-cov e ruff
style: corrige 14 achados do ruff no código herdado
ci: adiciona workflow tests.yml (lint + testes + cobertura)
```

## 4. Estratégia de branches (para execução futura)

Modelo: **trunk-based com branches curtas por história** (adequado a equipe pequena e
sprints de 2 semanas).

```
main ─────●─────────────●─────────────●────────▶   (sempre verde, protegida)
           \           / \           /
            feature/US11-qualidade-dados
                          feature/US12-autenticacao
```

| Regra | Definição |
|---|---|
| Nome | `feature/US<n>-<slug>`, `fix/<slug>`, `chore/<slug>`, `docs/<slug>` |
| Vida útil | ≤ 3 dias; se passar disso, quebrar a história |
| Origem e destino | sempre de `main` para `main` |
| Merge | Pull Request com o template `.github/pull_request_template.md`, **squash merge** |
| Proteção de `main` | 1 aprovação obrigatória + workflow `tests` verde + branch atualizada |
| Quem revisa | integrante que **não** escreveu o código |
| Após o merge | apagar a branch; mover o cartão para *Feito* só depois do merge |

Comandos para quando o repositório tiver histórico:

```bash
git switch main && git pull
git switch -c feature/US11-qualidade-dados
# ... commits atômicos (seção 3) ...
git push -u origin feature/US11-qualidade-dados
gh pr create --fill --base main          # preencher o template, pedir revisão
```
