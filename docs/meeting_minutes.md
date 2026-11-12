# Ata de reunião — Autoavaliação de maturidade e planejamento das próximas sprints

| Campo | Valor |
|---|---|
| Data | 06/11/2026 |
| Tipo | Reunião de equipe após Sprint Review e Retrospectiva da Sprint 1 |
| Participantes | Integrantes A, B, C, D (substituir pelos nomes e confirmar presença) |
| Pauta | (1) resultado da autoavaliação CMMI/MPS.BR; (2) plano de melhoria; (3) achados de qualidade de dados; (4) mudanças para as Sprints 2 e 3 |
| Documentos de apoio | `reports/maturity_assessment.md`, `docs/improvement_plan.md`, `reports/sbar.md`, `reports/metrics.md` |

> Esta ata registra decisões **propostas** a partir das evidências desta entrega. O grupo deve
> confirmar cada item antes de tratá-lo como decidido.

## 1. Resultado da autoavaliação

- 18 perguntas em 6 áreas: **F = 5 · L = 5 · P = 6 · N = 2**.
- As duas notas N (Gestão de Configuração Q1 e Garantia da Qualidade Q3) têm a mesma causa:
  não há histórico Git nem revisão por par comprovável.
- Ponto forte: testes (107, todos verdes), cobertura (90,3%), lint (0 achados) e métricas
  reproduzíveis. Ponto fraco: tudo o que exige registro da colaboração entre pessoas.

## 2. Achados que mudam o rumo do produto

- **R1 aconteceu.** A base Kaggle não tem ausência diária, então o modelo continua treinando
  só com dados sintéticos.
- **A base Kaggle também parece sintética.** 3.784 registros (3,78%) indicam admissão antes
  dos 18 anos, inclusive aos 12 e 13 (`reports/sbar.md`).
- **Precisão de 0,21.** Cerca de 4 em cada 5 alertas "Alta" seriam falsos.

## 3. Decisões

| # | Decisão | Responsável | Prazo |
|---|---|---|---|
| D1 | Adotar o plano de melhoria com 3 ações (PR revisado, CI como portão, tratamento de riscos/fonte de dados) | Todos | conforme o plano |
| D2 | Definition of Done mantida **sem afrouxar** o item "PR revisado por outro integrante" | Integrante A | imediato |
| D3 | US2 volta ao refinamento com novo critério: precisão ≥ 0,35 entre os 20 operadores de maior risco (valor a confirmar com o PO) | Integrante C | Planning da Sprint 2 (09/11/2026) |
| D4 | Registros que reprovam QC06 entram em quarentena; `src.validate --strict` vira etapa obrigatória antes do treino | Integrante B | 20/11/2026 |
| D5 | Levar ao professor/PO a escolha entre (a) buscar base com ausência diária ou (b) redefinir o alvo do modelo | Integrante C | 20/11/2026 |
| D6 | Escopo novo só entra na sprint trocando item de tamanho equivalente, com registro | Integrante D | a partir de 09/11/2026 |

## 4. Mudanças previstas para as próximas sprints

**Sprint 2 (09/11 a 20/11/2026) — tema: "fazer o que existe chegar a Feito"**

| Item | Tipo | Origem |
|---|---|---|
| Revisar via PR os 8 cartões em "Em revisão" (34 pts) | Processo | Ação 1 / retro |
| Publicar o workflow de CI e tornar o check obrigatório | Processo | Ação 2 |
| Resolver o comentário bloqueante #1 (data de referência parametrizável) | Técnico | Revisão simulada |
| Quarentena de QC06 + `--strict` antes do treino | Técnico | SBAR / D4 |
| Decisão sobre fonte de dados | Produto | D5 |
| Capacidade para história nova: **no máximo 8 pts** (US7) | Planejamento | Baseline: 0 pts entregues |

**Sprint 3 (23/11 a 04/12/2026) — tema: "modelo com dado de verdade"**

| Item | Tipo | Origem |
|---|---|---|
| Treinar e avaliar o modelo na fonte escolhida, com critério de precisão | Produto | D3, D5 |
| Fixar versões e SRI dos scripts de CDN nos painéis; reativar a CSP | Segurança | Revisão simulada #3 |
| US9 (drift / PSI) | Produto | Backlog Onda 2 |
| Segunda autoavaliação de maturidade, comparando com esta | Medição | Plano de melhoria |

## 5. Pendências

- Confirmar nomes, papéis e presença dos integrantes nesta ata.
- Se o repositório remoto do grupo tiver histórico de commits ou PRs, enviar os links para
  reavaliar GC Q1 e GQA Q3 (a nota atual reflete apenas o material entregue).

---

## Adendo — 11/11/2026 (troca de base)

> Registro das mudanças feitas em 11/11/2026. Mesmas regras da ata: decisões **propostas**,
> a confirmar pelo grupo.

**Fatos**
- A base de trabalho passou a ser `Extended_..._2_otimizado.csv`. Só `Sick_Days` difere do
  original (93.273 linhas), e foi regerado com correlação com horas extras (+0,59), jornada
  (+0,45) e satisfação (−0,36).
- Mesmo modelo e mesma semente: AUC **0,498** na base original e **0,914** na otimizada.
- As 6 regras de qualidade dão o mesmo resultado nas duas bases (5 aprovadas; QC06 reprova
  3.784 registros).

**Decisões propostas**

| # | Decisão | Responsável | Prazo |
|---|---|---|---|
| D7 | Toda menção ao AUC 0,91 vem acompanhada de "base semi-sintética" e do AUC 0,50 da base original | Todos | imediato |
| D8 | Registrar autor, data e regra da geração do `_2_otimizado` e versionar o script que o gerou (R7) | Integrante D | 13/11/2026 |
| D9 | Confirmar com o professor se a base semi-sintética é aceita como demonstração | Integrante C | aula de 13/11/2026 |
| D10 | Abrir os 7 PRs com `scripts/github_setup.py` e conseguir 1 revisão real por PR antes da apresentação | Integrante A | antes da Aula 10 |
