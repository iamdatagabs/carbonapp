# Dicionário preliminar de dados — CarbonApp

Este documento descreve apenas o que foi observado no arquivo `data/raw/[quad]base_nirs_refletancia.csv`. Campos cuja interpretação científica ainda não foi confirmada permanecem explicitamente pendentes.

## Estrutura

- 266 registros.
- 281 colunas.
- 6 colunas de metadados.
- 275 colunas espectrais.
- Variáveis espectrais de r1100 a r1648, em passos de 2 nm.

## Colunas de metadados

| Coluna | Tipo observado | Descrição preliminar | Pendência |
|---|---|---|---|
| `Indice` | inteiro | Índice sequencial do registro | Confirmar se é apenas índice técnico |
| `Amostra` | identificador | Código/identificador da amostra | Confirmar unidade amostral |
| `Profundidade` | categórico | Código A–I | Mapear para intervalo físico em cm |
| `Sample Number` | identificador | Identificador alfanumérico | Confirmar relação com Amostra |
| `TOC` | numérico | Carbono orgânico total | Confirmar unidade e método de referência |
| `N` | numérico | Nitrogênio | Confirmar se representa nitrogênio total, unidade e método |

## Variáveis espectrais

Cada coluna `rXXXX` representa uma leitura espectral associada ao comprimento de onda XXXX nm. A faixa observada é 1100–1648 nm, com incremento de 2 nm, totalizando 275 variáveis.

Os valores são numéricos decimais. A interpretação exata (refletância, transformação, correção, escala e unidade instrumental) deve ser confirmada com o protocolo de aquisição e o histórico de processamento. O nome do arquivo contém `[quad]`, mas isso, isoladamente, não documenta a operação matemática aplicada.

## Distribuição observada dos códigos de profundidade

| Código | Número de registros |
|---|---:|
| A | 32 |
| B | 28 |
| C | 26 |
| D | 30 |
| E | 30 |
| F | 31 |
| G | 27 |
| H | 30 |
| I | 32 |

Não assumir que A corresponde à camada superficial ou que a ordem alfabética equivale à ordem vertical até confirmar a tabela de correspondência experimental.

## Resumo numérico dos alvos

| Variável | N não ausente | Mínimo | Máximo | Média |
|---|---:|---:|---:|---:|
| TOC | 266 | 1,00 | 37,00 | 11,9361 |
| N | 266 | 0,19 | 2,80 | 0,8955 |

Os valores são reportados na escala armazenada no CSV. Unidades ainda não confirmadas; não usar estes valores como concentrações com unidade definida até validar a documentação laboratorial.

## Regras para ingestão

1. Preservar o CSV original sem sobrescrita.
2. Não usar as seis colunas iniciais como preditores espectrais automaticamente.
3. Selecionar as bandas pelo nome/padrão espectral validado, não por posição fixa.
4. Verificar tipos, valores ausentes, valores infinitos, duplicatas e faixas plausíveis.
5. Validar explicitamente o mapeamento de profundidade.
6. Registrar hash/versão do arquivo de origem e parâmetros de qualquer transformação.
7. Não preencher unidades ou significados ausentes por inferência.
