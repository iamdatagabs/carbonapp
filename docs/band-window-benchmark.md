# Comparação entre baseline por profundidade, NIR completo e janela candidata

## Objetivo
Testar se a informação espectral melhora a estimativa de desvios de TOC em relação à média de treinamento da camada, e comparar espectro completo com a janela candidata 1.440–1.488 nm.

## Cenários
1. **Baseline por profundidade:** média de TOC por camada, calculada apenas nos grupos de treinamento de cada dobra externa.
2. **NIR completo:** reflectância bruta de todas as bandas disponíveis (r1100–r1648), modelando resíduos em relação ao baseline.
3. **Janela candidata:** mesmo procedimento usando bandas de 1.440 a 1.488 nm, inclusive.

Os dois modelos NIR usam a mesma família de modelos, seleção por RMSE interno agrupado e seleção de até 40 variáveis. A comparação usa as mesmas dobras externas. Pré-processamento e seleção de variáveis são ajustados dentro dos folds de treinamento.

## Validação
- Validação cruzada aninhada: 5 folds externos e 4 internos, quando o número de grupos permite.
- Agrupamentos: `Amostra` (ponto) e `Sample Number` (semântica ainda não confirmada).
- Métricas: R², MAE, RMSE e viés.
- Diferença de MAE/RMSE em relação ao baseline: valores negativos indicam erro menor.

## Limitação de seleção pós-hoc
A janela foi sugerida por análise anterior de estabilidade de bandas realizada neste mesmo conjunto de dados. Assim, embora a seleção de modelo e variáveis seja aninhada, a escolha da janela já foi informada pelo conjunto completo. O resultado é **exploratório**, não uma validação confirmatória independente. Confirmação exige amostras externas independentes ou descoberta da janela apenas nos dados de treinamento de cada dobra, com protocolo registrado previamente.

## Interpretação
- Só há evidência de ganho preditivo se MAE/RMSE caírem em relação ao baseline nas dobras externas e o padrão for razoavelmente consistente entre os agrupamentos.
- R² deve ser interpretado junto com MAE e RMSE.
- Não atribuir mecanismo químico à janela apenas por frequência de seleção.
- Não há modelagem de N, inferência causal ou alegação de independência espacial.

## Reprodução
```bash
pip install -e ".[dev]"
pytest -q
python scripts/run_band_window_benchmark.py --data "data/raw/[quad]base_nirs_refletancia.csv" --output reports/band-window-benchmark
```
Os relatórios JSON por agrupamento e o CSV consolidado são publicados como artefato do GitHub Actions.
