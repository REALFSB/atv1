# Registro de riscos por sprint

> Criado pela Ação 3(b) do `docs/improvement_plan.md`. Uma linha por risco a cada revisão.
> Exposição = probabilidade × impacto (1–3 cada), como em `docs/04-planejamento-e-riscos.md`.

## Revisão de 11/11/2026 (Sprint 2, semana 1)

| ID | Risco | Status | Exposição | O que aconteceu | Ação | Resp. |
|---|---|---|:-:|---|---|---|
| R1 | Base real não serve ao modelo | **Materializado** | 9 | Base Kaggle original sem sinal para o alvo (AUC 0,50); a versão `_2_otimizado` tem `Sick_Days` regerado | Alvo redefinido (`Sick_Days ≥ 11`); decisão sobre a fonte levada ao professor/PO | C |
| R2 | Modelo abaixo da meta de recall | Mitigado com ressalva | 4 | Meta atingida só na base semi-sintética | Manter aviso em todos os lugares onde o número aparece | C |
| R3 | Violação de LGPD | Controlado | 3 | `Gender` fora do modelo; IDs com hash e sal; quarentena QC06 | Revisar no PR da US2 | B |
| R4 | Dependência de uma pessoa no modelo | Aberto | 4 | Sem evidência de pareamento ou revisão | Revisão por PR (Ação 1) | A |
| R5 | Crescimento de escopo | **Materializado** | 6 | +48% na Sprint 1; nesta semana entraram o modelo por funcionário e o gerador do painel como tarefas da US2/US8, sem história nova | Escopo novo só com troca (retro, ação 2) | D |
| R6 | Prazo apertado para a apresentação | Aberto | 4 | PRs ainda não abertos | Rodar `scripts/github_setup.py` até 13/11 | A |
| **R7** | **Dado derivado sem proveniência** (novo) | **Materializado** | 6 | CSV `_2_otimizado` sem registro de autor, data e regra | Preencher `docs/05-dados-reais.md` §2; guardar o script gerador no repositório | D |
