# Documentação do CarbonApp

Esta pasta reúne a documentação científica, metodológica, técnica e de produto do CarbonApp. O repositório mantém dois contextos relacionados, mas distintos: o núcleo de pesquisa em espectroscopia NIR e o MVP de captura/gestão de dados de campo.

## Comece por aqui

| Objetivo | Documento |
|---|---|
| Entender o sistema e a evolução do MVP | [Arquitetura da aplicação](application-architecture.md) |
| Executar o fluxo científico completo | [Execução reprodutível](reproducible-run.md) |
| Entender os dados e suas limitações | [Dicionário de dados](data-dictionary.md) |
| Consultar a API de pesquisa e o dashboard | [Frontend e APIs](api-and-frontend.md) |
| Consultar o contrato da API Java | [OpenAPI v1](openapi-v1.yaml) |
| Consultar a auditoria inicial e suas atualizações | [Auditoria técnica](technical-audit.md) |
| Consultar o trabalho acadêmico de origem | [Dissertação](Dissertacao.pdf) |

## Dados e metodologia

- [Metodologia estatística e desenho experimental](statistical-methodology.md)
- [Metodologia de incerteza e intervalos conformais](uncertainty-methodology.md)
- [Protocolo de interpretabilidade espectral](interpretability-protocol.md)
- [Protocolo TinyML](tinyml-protocol.md)
- [Protocolo de estabilidade de seleção de bandas](band-stability-protocol.md)
- [Resultados de estabilidade de bandas](band-stability-results.md)
- [Benchmark profundidade versus NIR](depth-versus-nir-benchmark.md)
- [Benchmark NIR por camada](layerwise-nir-benchmark.md)
- [Resultados do benchmark NIR por camada](layerwise-nir-results.md)
- [Benchmark NIR dentro da profundidade](within-depth-nir-benchmark.md)
- [Benchmark de janela espectral](band-window-benchmark.md)
- [Auditoria de resíduos em profundidade/NIR](depth-nir-residual-audit.md)
- [Auditoria de qualidade espectral](spectral-qc-audit.md)
- [Comparação de pré-processamento](preprocessing-comparison-protocol.md)
- [Comparação de modelos](model-comparison-protocol.md)

## Convenções de leitura

- Documentos de protocolo descrevem procedimentos; documentos de resultados registram achados de execuções específicas. Não confundir resultados exploratórios com validação externa.
- A dissertação e os registros laboratoriais são fontes primárias para confirmar unidades, métodos de referência e proveniência.
- Permanecem explícitas as incertezas sobre a semântica de `Sample Number`, unidades/métodos de TOC e N e independência espacial dos pontos.
- A API Python de pesquisa e a API Java do MVP são serviços diferentes, com responsabilidades e contratos próprios.
- A documentação não substitui revisão científica, validação laboratorial, análise de segurança ou aprovação para uso operacional.

## Manutenção

Ao adicionar um documento, inclua-o nesta página e classifique-o por finalidade. Registre data, versão de dados, configuração, semente e origem dos artefatos em relatórios de resultados. Atualize também o README da raiz quando a mudança afetar a orientação geral do repositório.
