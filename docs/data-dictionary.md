# Dicionário preliminar de dados — CarbonApp

Este documento descreve o que foi observado no arquivo `data/raw/[quad]base_nirs_refletancia.csv` e as informações metodológicas confirmadas até o momento. Campos cuja interpretação ainda não foi confirmada permanecem explicitamente pendentes.

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
| `Amostra` | identificador | Número do ponto/parcela de coleta; identifica o perfil vertical | Confirmar se pontos distintos são unidades independentes ou se pertencem a blocos/agrupamentos |
| `Profundidade` | categórico | Letra A–I que identifica a camada dentro de cada ponto | Correspondência física confirmada na tabela abaixo |
| `Sample Number` | identificador | Identificador alfanumérico | Confirmar relação com Amostra |
| `TOC` | numérico | Carbono orgânico total | Confirmar unidade e método de referência |
| `N` | numérico | Nitrogênio | Confirmar se representa nitrogênio total, unidade e método |

## Variáveis espectrais

Cada coluna `rXXXX` representa uma leitura espectral associada ao comprimento de onda XXXX nm. A faixa observada é 1100–1648 nm, com incremento de 2 nm, totalizando 275 variáveis.

Os valores são numéricos decimais. A interpretação exata (refletância, transformação, correção, escala e unidade instrumental) deve ser confirmada com o protocolo de aquisição e o histórico de processamento. O nome do arquivo contém `[quad]`, mas isso, isoladamente, não documenta a operação matemática aplicada.

## Profundidade do solo — intervalos físicos confirmados

O experimento abrange um perfil vertical de solo de **0 a 200 cm (2 m)**, dividido em nove camadas de espessuras variáveis. O autor confirmou a correspondência exata entre os códigos do CSV e os intervalos físicos:

| Código | Limite superior (cm) | Limite inferior (cm) | Espessura (cm) |
|---|---:|---:|---:|
| A | 0 | 10 | 10 |
| B | 10 | 20 | 10 |
| C | 20 | 40 | 20 |
| D | 40 | 60 | 20 |
| E | 60 | 80 | 20 |
| F | 80 | 100 | 20 |
| G | 100 | 130 | 30 |
| H | 130 | 160 | 30 |
| I | 160 | 200 | 40 |

A profundidade é uma variável categórica no CSV, mas possui uma ordem física conhecida. Cada letra identifica uma camada coletada dentro do ponto indicado por `Amostra`; portanto, as observações de diferentes profundidades do mesmo ponto são medidas repetidas/pareadas no desenho vertical. A aplicação deve manter a categoria original (A–I) e associar cada código aos limites numéricos acima por meio de um dicionário explícito, sem depender da ordenação alfabética implícita.

Para visualizações do perfil, usar os limites reais das camadas e respeitar as espessuras desiguais. A profundidade pode ser representada no eixo vertical (0 cm na superfície e 200 cm na base); não interpolar nem sugerir continuidade espacial lateral sem dados que sustentem essa operação.

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

As frequências acima descrevem os registros no CSV, não a espessura física nem a ordem vertical das camadas.

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
5. Validar explicitamente a correspondência A–I com os intervalos físicos.
6. Registrar hash/versão do arquivo de origem e parâmetros de qualquer transformação.
7. Não preencher unidades ou significados ausentes por inferência.

## Identificadores repetidos e agrupamento

A base possui 224 valores únicos de `Sample Number` em 266 registros:
- 189 identificadores com uma linha;
- 28 identificadores com duas linhas;
- 7 identificadores com três linhas.

Os valores de TOC e N são iguais entre registros que compartilham o mesmo `Sample Number`. A hipótese de que sejam réplicas espectrais deve ser validada com o protocolo experimental. Até lá, `Sample Number` deve ser preservado como identificador de agrupamento e jamais usado como preditor numérico.

**Regra de particionamento:** todas as linhas de um mesmo `Sample Number` devem ficar juntas na mesma partição de treino, validação ou teste. Isso evita que medições associadas ao mesmo resultado laboratorial sejam distribuídas entre treino e teste. Em análises inferenciais por profundidade, a unidade de pareamento/cluster é o ponto identificado por `Amostra`, e não cada linha nem cada camada isoladamente.
