# Revisão por pares — SIMULAÇÃO

> ⚠️ **Estes comentários são uma simulação para fins didáticos.** Não foram publicados em
> nenhum Pull Request, não têm revisor real e **não contam** como o item "revisão por par" da
> Definition of Done. Foram escritos por quem implementou o código, então não são
> independentes (ver `reports/maturity_assessment.md`, GQA Q3 = N).
> Os problemas apontados são reais e verificáveis no código atual.

**PR simulado:** `feature/US11-qualidade-dados` + `feature/US12-autenticacao` → `main`

---

## Comentário 1 — 🔴 BLOQUEANTE (corretude)

**Arquivo:** `src/validate.py`, constante `REFERENCE_DATE` e regra QC05

```python
REFERENCE_DATE = pd.Timestamp("2024-09-04")
```

> A data de referência da QC05 está fixa no código. Para a base Kaggle está correta: com ela,
> 100% dos registros fecham. Mas a US11 diz "**dada uma base de funcionários**", não "dada
> esta base". Uma extração feita em outra data, como a base interna prevista no R1, terá a
> maioria dos registros reprovados na QC05 sem nenhum defeito real. O SQL tem a mesma data
> repetida em texto (`julianday('2024-09-04')`), então são dois lugares para manter
> sincronizados à mão.
>
> **Pedido:** receber a data de referência por parâmetro (`--reference-date`, padrão = data
> da extração informada no metadado da carga) e passar para o SQL como parâmetro
> (`julianday(?)`). Incluir um teste com outra data de referência.
>
> **Por que bloqueia:** sem isso, a primeira carga com dados reais vai gerar um falso alarme
> em massa, e o time vai aprender a ignorar o relatório.

**Status:** aberto. Mantém US11 em "Em revisão". Em 11/11 o problema ficou maior: o modelo
por funcionário (`src/data/employees.py`) também calcula o tempo de casa com a mesma data fixa.

---

## Comentário 2 — 🟡 SUGESTÃO DE MELHORIA (manutenibilidade / escala)

**Arquivo:** `src/webapp/security.py`, classe `LoginRateLimiter`

> O limite de tentativas guarda as falhas em um `dict` na memória do processo. Funciona
> localmente e o teste cobre, mas:
> 1. com mais de um *worker* (ex.: `gunicorn -w 4`), cada processo conta separado, e o
>    limite efetivo vira 5 × 4 = 20 tentativas;
> 2. reiniciar o servidor zera o bloqueio;
> 3. a chave `IP|e-mail` atrás de um proxy reverso usa o IP do proxy, então todos os usuários
>    compartilham o mesmo IP.
>
> **Sugestão:** isolar a interface (`retry_after`, `record_failure`, `reset`) e criar uma
> implementação com armazenamento compartilhado (Redis ou a própria tabela SQLite) para
> produção. Configurar `ProxyFix` só quando houver proxy conhecido. Não bloqueia a sprint,
> porque o uso atual é local.

**Status:** aberto, candidato ao backlog técnico.

---

## Comentário 3 — 🟠 SEGURANÇA

**Arquivos:** `paineis/*.html` e `src/webapp/security.py` (`apply_security_headers`)

```html
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://unpkg.com/lucide@latest"></script>
```

> Os painéis legados, agora atrás do login e exibindo o ranking de risco dos operadores,
> carregam três scripts de CDN **sem versão fixa** (`@latest`, ou sem versão nenhuma) e
> **sem SRI** (`integrity=`). Por isso a CSP estrita teve de ser desligada só para
> `/paineis/*`. Se uma dessas CDNs for comprometida, o script injetado roda com a sessão
> do usuário logado e lê o ranking inteiro (`risco-data.js`). Além disso, `cdn.tailwindcss.com`
> é o build de desenvolvimento do Tailwind, que a própria documentação não recomenda em
> produção.
>
> **Pedido:** fixar versões, adicionar `integrity` e `crossorigin`, ou servir os arquivos
> pela pasta `static/`. Depois disso, reativar a CSP também nos painéis.

**Status:** aberto. Risco aceito temporariamente porque a aplicação só roda em
`127.0.0.1`; deve ser resolvido antes de qualquer publicação.

---

## Resumo

| # | Tipo | Bloqueia merge? | História afetada |
|---|---|:-:|---|
| 1 | Bloqueante — corretude | Sim | US11 |
| 2 | Sugestão — escala | Não | US12 |
| 3 | Segurança — dependências de terceiros | Não para uso local; **sim** para publicação | US12 |
