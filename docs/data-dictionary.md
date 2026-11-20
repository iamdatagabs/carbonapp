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
| `Amostra` | identificador | Código/identificador da amostra | Confirmar unidade amostral |
| `Profundidade` | categórico | Código A–I | Recuperar a correspondência exata entre cada código e seus limites físicos em cm |
| `Sample Number` | identificador | Identificador alfanumérico | Confirmar relação com Amostra |
| `TOC` | numérico | Carbono orgânico total | Confirmar unidade e método de referência |
| `N` | numérico | Nitrogênio | Confirmar se representa nitrogênio total, unidade e método |

## Variáveis espectrais

Cada coluna `rXXXX` representa uma leitura espectral associada ao comprimento de onda XXXX nm. A faixa observada é 1100–1648 nm, com incremento de 2 nm, totalizando 275 variáveis.

Os valores são numéricos decimais. A interpretação exata (refletância, transformação, correção, escala e unidade instrumental) deve ser confirmada com o protocolo de aquisição e o histórico de processamento. O nome do arquivo contém `[quad]`, mas isso, isoladamente, não documenta a operação matemática aplicada.

## Profundidade do solo — informação metodológica confirmada

O experimento abrange um perfil vertical de solo de **0 a 200 cm (2 m)** e utiliza nove classes/códigos de profundidade (A–I). As camadas não devem ser presumidas como tendo espessuras iguais: segundo a informação metodológica confirmada pelo autor, as camadas superficiais têm aproximadamente 10–20 cm, enquanto a camada mais profunda tem espessura próxima de 90 cm.

A tabela exata que associa cada código A–I aos limites superior e inferior em centímetros ainda precisa ser transcrita da dissertação. Portanto:

- não converter A–I em números ordinais para análise;
- não assumir que A corresponde à superfície ou que a ordem alfabética representa a ordem vertical;
- não atribuir espessuras exatas a cada classe com base apenas nas aproximações acima;
- manter a geometria vertical do perfil parametrizada pelos limites reais de cada camada assim que a tabela for recuperada.

Para a visualização 3D, representar as nove camadas com suas espessuras reais, e não como nove blocos de mesma altura. Até a transcrição da tabela, a interface deve identificar os limites como pendentes e não apresentar uma escala vertical quantitativa enganosa.

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

**Regra de particionamento:** todas as linhas de um mesmo `Sample Number` devem ficar juntas na mesma partição de treino, validação ou teste. Isso evita que medições associadas ao mesmo resultado laboratorial sejam distribuídas entre treino e teste.
