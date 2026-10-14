# Backlog — DataTrack · Radar de Absenteísmo

> Persona: **Guilherme Ramos, Head de Operações**. Cada story aponta para uma funcionalidade do Canvas MVP (F1–F6) e para o módulo que a implementa.

## Funcionalidades do Canvas MVP

| ID | Funcionalidade | Tela/Área |
|---|---|---|
| F1 | Lista de funcionários ranqueada por risco de absenteísmo elevado | Equipes & Escalas |
| F2 | Exportação da lista de risco (CSV/PDF) | Relatórios |
| F3 | Alerta de mudança de faixa de risco | Dashboard Geral |
| F4 | Impacto estimado da ausência na meta da célula | Gestão de Metas |
| F5 | Validação de qualidade e proteção dos dados | Dados / LGPD |
| F6 | Painel de saúde do modelo (drift) | Dashboard Geral |

## Épicos

| ID | Épico |
|---|---|
| E1 | Previsão de risco de ausência |
| E2 | Ação e comunicação com a operação |
| E3 | Dados confiáveis e governança |

## Onda 1 (MVP · Sprint 1)

### US1 · Previsão de risco de ausência · 5 pts · `train.py, serve.py`
**Como** Guilherme, **quero** uma lista de funcionários ordenada por risco de absenteísmo elevado (≥ 11 dias/ano), **para** agir de forma preventiva (escala, banco de horas, conversa com o líder) e proteger as metas.

- Canvas: F1 · Tipo: funcional
- **Dado** a base de funcionários carregada e validada
- **Quando** abro Equipes & Escalas
- **Então** a lista aparece ordenada do maior para o menor risco, gerada em até 5 s

### US2 · Previsão de risco de ausência · 8 pts · `features.py, train.py`
**Como** Guilherme, **quero** que o modelo identifique a maior parte das ausências reais, **para** confiar na lista e agir sobre ela.

- Canvas: F1 · Tipo: métrica do modelo
- **Dado** o modelo treinado com dados históricos
- **Quando** é avaliado em 25% dos funcionários reservados (teste estratificado)
- **Então** recall ≥ 0,60 e ROC-AUC ≥ 0,70, registrados em metrics.json

### US3 · Dados confiáveis e governança · 3 pts · `ingest.py`
**Como** Guilherme, **quero** que dados incompletos ou inválidos sejam barrados antes do treino, **para** evitar decisões baseadas em dado ruim.

- Canvas: F5 · Tipo: dados
- **Dado** um arquivo com mais de 5% de nulos em uma coluna obrigatória
- **Quando** o pipeline executa a ingestão
- **Então** o processo é interrompido com erro que lista cada coluna e seu % de nulos

### US4 · Dados confiáveis e governança · 3 pts · `ingest.py`
**Como** Guilherme, **quero** que o sistema não use nome, idade, gênero, identificadores diretos nem dados de saúde dos funcionários, **para** cumprir a LGPD e preservar a confiança do time.

- Canvas: F5 · Tipo: dados / LGPD
- **Dado** uma base com ID, nome, idade, gênero e dias de afastamento
- **Quando** a ingestão é executada
- **Então** o ID sai como hash com sal e nome, idade, gênero e dias de afastamento são descartados antes do treino

### US5 · Ação e comunicação com a operação · 2 pts · `serve.py`
**Como** Guilherme, **quero** exportar a lista de risco em CSV, **para** compartilhar com os líderes de célula.

- Canvas: F2 · Tipo: funcional
- **Dado** uma lista de risco gerada
- **Quando** clico em exportar
- **Então** recebo um CSV com todas as linhas e as colunas rank, risco e faixa

## Onda 2 (Sprint 2+)

### US6 · Previsão de risco de ausência · 3 pts · `serve.py`
**Como** Líder de célula, **quero** ver a faixa (Alta/Média/Baixa) e os 3 principais fatores de cada risco, **para** explicar a decisão ao operador e agir na causa.

- Canvas: F1 · Tipo: explicabilidade
- **Dado** um operador com risco calculado
- **Quando** consulto o detalhe
- **Então** vejo a faixa e exatamente 3 fatores que mais elevam o risco

### US7 · Ação e comunicação com a operação · 5 pts · `monitor.py (novo)`
**Como** Guilherme, **quero** ser alertado quando um operador mudar de faixa de risco, **para** agir a tempo, sem olhar a lista toda dia.

- Canvas: F3 · Tipo: funcional
- **Dado** o ranking de ontem e o de hoje
- **Quando** um operador passa de Média para Alta
- **Então** o Dashboard exibe alerta com nome da célula e a mudança

### US8 · Ação e comunicação com a operação · 8 pts · `serve.py, monitor.py`
**Como** Guilherme, **quero** ver o impacto estimado das ausências previstas na meta de cada célula, **para** decidir onde remanejar primeiro.

- Canvas: F4 · Tipo: funcional
- **Dado** o risco por operador e a meta diária da célula
- **Quando** abro Gestão de Metas
- **Então** vejo a perda esperada de unidades por célula, ordenada

### US9 · Dados confiáveis e governança · 5 pts · `monitor.py (novo)`
**Como** Guilherme, **quero** ser avisado quando os dados novos se afastarem dos dados de treino, **para** saber quando retreinar o modelo.

- Canvas: F6 · Tipo: dados / drift
- **Dado** dados novos de uma semana
- **Quando** o PSI de qualquer feature passa de 0,2
- **Então** o painel sinaliza drift e sugere retreino

### US10 · Ação e comunicação com a operação · 3 pts · `serve.py`
**Como** Guilherme, **quero** receber um relatório semanal de risco por célula em PDF, **para** levar o tema às reuniões de operação.

- Canvas: F2 · Tipo: funcional
- **Dado** a semana fechada
- **Quando** solicito o relatório em Relatórios
- **Então** recebo PDF com risco médio e top 5 operadores por célula

## Revisão INVEST

Todas revisadas: Independent (US7–US10 dependem só do ranking da US1), Negotiable (descrevem necessidade, não técnica), Valuable (ligadas a F1–F6), Estimable, Small (≤ 8 pts, cabem em 1 sprint) e Testable (G/W/T com número). US2 foi mantida com 8 pts por ser o limite de 'Small'.

## Critério de priorização

Valor para a persona no Canvas MVP, desempatado por dependência técnica. Primeiro entram as stories que fecham o ciclo de valor mínimo (US1 lista → US2 confiança → US5 exportação) e as que removem o maior risco, que está nos dados (US3, US4), conforme a Aula 6. Alertas, impacto em metas, drift e PDF ficam na Onda 2 porque dependem do ranking existir. A ordem não foi definida pela facilidade técnica.
