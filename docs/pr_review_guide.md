# Guia da revisão por par (para o colega revisor)

> A Entrega 3 exige um **PR revisado por um colega, com comentários e respostas
> registrados**. Este guia existe para que a revisão seja real e útil, não um "LGTM".
> A simulação em `docs/peer_review_simulation.md` serve como exemplo do nível esperado,
> mas **não substitui** a revisão: ela foi escrita por quem fez o código.

## Como revisar (20–40 min por PR)

1. Leia a história ligada (`Closes #N`) e os critérios de aceite em `docs/backlog.md`.
2. Confirme que o CI está verde (ruff + pytest 3.11 e 3.12).
3. Para cada critério de aceite, ache o teste que o comprova. Se faltar, comente.
4. Rode localmente pelo menos uma vez: `pip install -r requirements.txt && pytest -q`.
5. Deixe **pelo menos 3 comentários em linha**, classificados no início:
   - `[bloqueante]` impede o merge (bug, critério sem teste, risco de segurança/LGPD);
   - `[sugestão]` melhoria opcional;
   - `[pergunta]` algo que não ficou claro.
6. Use **Request changes** se houver bloqueante; **Approve** só quando todos os
   bloqueantes tiverem resposta e commit de correção.

## Pontos que valem olhar em cada PR

| PR | O que conferir |
|---|---|
| ingestao | o hash usa sal vindo de variável de ambiente? colunas de saúde são mesmo descartadas? |
| modelo | o split temporal impede vazamento? a meta de recall e AUC está no teste? |
| ranking | o CSV exportado tem todas as linhas? os fatores fazem sentido? |
| qualidade | as 6 regras cobrem as 4 dimensões? SQL e pandas dão o mesmo número? a data de referência fixa (comentário simulado #1) é aceitável? |
| autenticacao | senha só em hash? mesma mensagem para usuário inexistente? CSRF no logout? |
| modelo-funcionarios | `Gender` e `Age` estão fora dos atributos? o aviso de base semi-sintética aparece no painel? |

## Como o autor responde

- Responda **cada** comentário no próprio PR: "corrigido em `abc123`" ou "não vou mudar
  porque …".
- Não faça merge com conversa aberta (ative *Require conversation resolution* na proteção).

## Registro para a entrega (copiar para `docs/entrega3_checkpoint.md`, Parte 3)

| PR | Revisor | Comentário | Tipo | Resposta / resolução |
|---|---|---|---|---|
| #… | … | … | bloqueante / sugestão | corrigido em `…` / justificativa |
