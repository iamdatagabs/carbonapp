# Auditoria técnica inicial — CarbonApp

**Data da auditoria:** 20/11/2026  
**Branch de trabalho:** `research/reproducible-core`  
**Escopo:** inspeção estática do repositório, dos notebooks e da base espectral versionada. Nenhum experimento foi reexecutado nesta etapa.

## 1. Estado do repositório

O repositório contém:
- `Filtro_Carbono.ipynb`
- `RFE_Carbon.ipynb`
- `data/raw/[quad]base_nirs_refletancia.csv`
- `docs/Dissertacao.pdf`
- README ainda sem documentação substantiva.

A base CSV tem aproximadamente 1,49 MB e foi lida diretamente pelo conteúdo público do GitHub.

## 2. Auditoria da base

| Propriedade | Resultado observado |
|---|---:|
| Registros | 266 |
| Colunas totais | 281 |
| Colunas de metadados | 6 |
| Variáveis espectrais | 275 |
| Primeira variável espectral | r1100 |
| Última variável espectral | r1648 |
| Incremento espectral | 2 nm |
| Valores ausentes em TOC | 0 |
| Valores ausentes em N | 0 |

As seis colunas iniciais são `Indice`, `Amostra`, `Profundidade`, `Sample Number`, `TOC` e `N`. As demais colunas são leituras de refletância identificadas pelo comprimento de onda.

### Alvos observados

| Variável | Mínimo | Máximo | Média |
|---|---:|---:|---:|
| TOC | 1 | 37 | 11,9361 |
| N | 0,19 | 2,80 | 0,8955 |

**Atenção:** unidades e base de expressão dos valores de TOC e N ainda precisam ser confirmadas na dissertação, nos protocolos laboratoriais ou no dicionário original. Os números acima são estatísticas descritivas calculadas diretamente da coluna, não uma interpretação físico-química.

### Profundidade

A coluna `Profundidade` contém nove códigos categóricos: A, B, C, D, E, F, G, H e I. Frequências observadas:

| Código | Registros |
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

A correspondência entre A–I e os intervalos físicos de profundidade deve ser documentada explicitamente antes de qualquer gráfico estratigráfico. Não se deve ordenar alfabeticamente e assumir que isso representa a profundidade sem validar o mapeamento.

## 3. Achados nos notebooks

### `Filtro_Carbono.ipynb`
- O conjunto de preditores é definido por posição (`data.iloc[:, 6:]`), tornando o código dependente da ordem das colunas.
- A seleção por correlação de Pearson é calculada usando todo o conjunto antes da separação treino/teste: risco de vazamento de informação.
- O escalonador e a seleção ANOVA são ajustados antes da validação cruzada. Para uma estimativa sem viés, ambos devem ser ajustados dentro de cada fold.
- A validação cruzada é executada sobre uma matriz já transformada/selecionada, em vez de um pipeline completo dentro de cada fold.
- O notebook depende de montagem do Google Drive e caminho local específico do autor.

### `RFE_Carbon.ipynb`
- O notebook contém experimentos para TOC e também um bloco com `N` como alvo, o que confirma que o nitrogênio já foi explorado no código.
- Há uma divisão com `test_size=0.8` em um experimento. Isso reserva 80% para teste e deve ser tratado como experimento exploratório, não comparado diretamente aos demais sem justificativa.
- A seleção RFE é ajustada antes da validação cruzada posterior; a seleção precisa ocorrer dentro de cada fold.
- Em alguns trechos, o objeto RFE é obtido de um pipeline que inclui escalonamento, mas a transformação posterior é aplicada diretamente aos dados não escalonados. A seleção de colunas pode ser reaproveitada, mas o fluxo deve ser refeito como pipeline único.
- A ordenação de coeficientes usa valores assinados em ordem decrescente. Para ranking por magnitude, deve-se usar valor absoluto e interpretar sinais separadamente.
- Também há dependência do Google Drive.

## 4. Riscos metodológicos prioritários

1. **Vazamento de dados:** seleção de atributos, escalonamento e outras transformações precisam ser aprendidos somente com os dados de treino de cada fold.
2. **Dependência entre amostras:** os identificadores e códigos de profundidade indicam estrutura por amostra/perfil. Antes de usar divisão aleatória convencional, verificar se observações do mesmo perfil, ponto ou amostra relacionada podem aparecer simultaneamente em treino e teste.
3. **Validação externa:** reservar um teste independente ou adotar validação agrupada por unidade experimental, conforme o desenho amostral.
4. **Rastreabilidade:** registrar versão da base, colunas usadas, filtros, transformações, sementes, partições e hiperparâmetros.
5. **Unidades e metadados:** documentar unidades de TOC/N, método laboratorial, mapeamento A–I, significado de `Indice`/`Amostra`/`Sample Number` e o processamento que originou a base quadrática.

## 5. Decisões para o novo núcleo

- Preservar os notebooks originais como histórico de pesquisa.
- Construir pipelines reprodutíveis em Python, sem caminhos locais fixos.
- Tratar TOC e N como alvos independentes, compartilhando engenharia de dados e validação.
- Comparar baselines simples e os algoritmos da dissertação antes de ampliar o espaço de modelos.
- Manter pré-processamento espectral, seleção de variáveis e otimização dentro da validação cruzada.
- Só gerar modelos TinyML após selecionar modelos com desempenho e estabilidade demonstrados.
- Só representar volume 3D espacial quando houver coordenadas/distribuição espacial suficientes; com profundidade e concentração, o produto cientificamente correto é um perfil vertical.

## 6. Próximas verificações

- [ ] Confirmar unidades e métodos de referência de TOC e N.
- [ ] Confirmar o mapeamento dos códigos A–I para intervalos de profundidade.
- [ ] Inspecionar duplicatas e estrutura de agrupamento dos identificadores.
- [ ] Confirmar se a base quadrática é a mesma usada nos resultados publicados.
- [ ] Reproduzir os resultados originais com protocolo de validação documentado.
- [ ] Implementar testes de integridade e contrato de dados.


## 7. Estrutura de repetição e agrupamento (verificação adicional)

A inspeção dos identificadores encontrou 224 valores únicos em `Sample Number` para 266 linhas. A multiplicidade é:
- 189 identificadores aparecem uma vez;
- 28 identificadores aparecem duas vezes;
- 7 identificadores aparecem três vezes.

Nas 224 unidades identificadas por `Sample Number`, os valores de TOC e N são constantes entre as linhas repetidas. Isso é compatível com medições espectrais replicadas associadas ao mesmo resultado de referência, mas a natureza exata da repetição deve ser confirmada no protocolo experimental.

**Implicação metodológica crítica:** todas as linhas com o mesmo `Sample Number` devem permanecer no mesmo grupo durante a separação treino/teste e a validação cruzada. Caso contrário, réplicas espectrais associadas ao mesmo valor laboratorial podem aparecer simultaneamente no treino e no teste, causando vazamento entre partições. A validação inicial deve usar divisão agrupada por `Sample Number` (por exemplo, GroupKFold ou GroupShuffleSplit), com a escolha final condicionada ao desenho experimental.

Também foram observados 28 valores únicos em `Amostra` e 224 combinações únicas `Amostra × Profundidade`. A semântica dos identificadores e sua relação com o plano amostral ainda precisa ser confirmada.

A correlação de Pearson bruta entre TOC e N nesta base é aproximadamente 0,9351. Isso é uma descrição exploratória da base, não evidência de que um alvo possa substituir o outro nem de que ambos tenham o mesmo processo de referência.
