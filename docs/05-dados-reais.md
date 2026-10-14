# Dados reais: mescla, limpeza e resultado

## O que foi feito (`src/harmonize.py`)
| Base (Kaggle) | Linhas | Papel |
|---|---|---|
| Extended Employee Performance and Productivity | 100,000 | base de treino (tem `Sick_Days`) |
| HR Dashboard | 200 | harmonizada, sem rótulo |
| Employee Productivity | 10 | harmonizada, sem rótulo |

- **Mescla por empilhamento**, com coluna `source`. As três bases não têm chave comum (IDs de formatos diferentes, uma sem ID), então não há join linha a linha; seria inventar relação entre pessoas diferentes.
- **Padronização:** nomes de colunas, salário anual → mensal, percentuais 0–100 → escala 1–5 (satisfação e desempenho), datas ("Jan-20" → mês/ano) → tempo de casa em meses, IDs com prefixo da fonte.
- **Limpeza:** espaços removidos, duplicados descartados, valores fora de faixa viram nulo (idade, jornada, satisfação etc.). Resultado: 100,210 linhas, 100,000 rotuladas.
- **LGPD/governança:** `Name` (HR Dashboard) nunca entra no esquema; nome, idade, gênero e `Sick_Days` são descartados antes do treino; ID vira hash com sal.
- **Rótulo:** `absent = 1` se `Sick_Days ≥ 11` (≈ 27% dos funcionários).
- Arquivo gerado: `data/processed/funcionarios_unificado.csv` (fora do Git).

## Resultado do modelo com a base real
| Métrica | Valor | Meta |
|---|---|---|
| ROC-AUC | 0.504 | ≥ 0,70 |
| Recall | 0.521 | ≥ 0,60 |
| Precisão | 0.271 | — |
| Atende às metas? | **não** | |

**Interpretação:** AUC ≈ 0,50 é equivalente a sorteio. Testei também gradient boosting e outros rótulos (`Sick_Days ≥ 7`, `Resigned`): todos ≈ 0,50, e as correlações de `Sick_Days` com qualquer variável são ≈ 0. A base é, na prática, aleatória: não há padrão de faltas para aprender. Isso é limite dos dados, não do código.

**O que o sistema faz a respeito:** o painel (`equipes.html`) exibe aviso vermelho quando as metas não são atingidas, e o `train.py` imprime alerta. Nenhuma meta foi relaxada para "passar".

## Painel calculado das bases (`src/dashboard.py`)
- 100.210 registros; completude média 99,9% (só `Age` tem nulos após a limpeza, por valores fora da faixa).
- Produtividade média 49,9 pts (meta de 50): a base Extended tem desempenho uniforme de 1 a 5, então todos os departamentos ficam ≈ 50 pts. A HR Dashboard (200) varia de 42 a 56 e a Employee Productivity (10) fica em ≈ 84.
- Retenção 90,0% (10.010 desligados, só na Extended); absenteísmo elevado (≥ 11 dias) em 26,8% dos rotulados; média de 7,0 dias/ano.
- Com as bases pooled quase todas as metas aparecem "Na Meta": é consequência de dados sem sinal (risco R7), não de relaxar alvo. Filtrando por base os desvios aparecem.

## Próximos passos possíveis
1. Coletar dados internos reais (ponto/escala) e plugar via `DataSource`, sem mudar o treino.
2. Revisar a meta da US2 e o rótulo com o professor, assumindo o resultado como achado do projeto.
3. Usar `SyntheticSource` apenas para demonstrar o fluxo, sempre rotulado como demo.
