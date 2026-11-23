# Frontend e APIs

O CarbonApp mantém duas aplicações web/API distintas. Não misture seus endpoints nem suas condições de implantação.

## 1. Dashboard científico (Python + frontend estático)

O dashboard em `apps/frontend/` consome a API de pesquisa Python/FastAPI.

### Executar localmente

```bash
pip install -e ".[api,dev]"
uvicorn carbonapp.api:create_app --factory --reload
```

A API usa por padrão `data/raw/[quad]base_nirs_refletancia.csv`. Defina `CARBONAPP_DATA_PATH` para apontar para outro arquivo.

Sirva `apps/frontend/index.html` por HTTP (por exemplo, `python -m http.server 5500 --directory apps/frontend`). Para outra origem, defina `window.CARBONAPP_API_BASE` antes de carregar `app.js` e configure `CARBONAPP_CORS_ORIGINS` com uma lista separada por vírgulas de origens exatas. Não use origem curinga nem habilite credenciais sem necessidade.

### Rotas de pesquisa

- `GET /health`
- `GET /api/v1/metadata/depths`
- `GET /api/v1/dataset/summary?target=TOC|N`
- `GET /api/v1/profiles/{point_id}?target=TOC|N`
- `GET /api/v1/profiles-3d?target=TOC|N`

O dashboard oferece catálogo pesquisável de pontos/camadas, comparação de perfis verticais de múltiplos pontos, exportação CSV e visualização 3D categórica ponto × profundidade com seleção de TOC/N. A dimensão horizontal da visualização 3D representa categorias de pontos, não coordenadas geográficas; não é interpolação nem volume georreferenciado.

A API pública de pesquisa está publicada em [carbonapp-research-api.onrender.com](https://carbonapp-research-api.onrender.com/), com documentação interativa em [/docs](https://carbonapp-research-api.onrender.com/docs). O serviço está em plano gratuito e pode entrar em suspensão por inatividade; a primeira requisição após esse período pode demorar. As rotas públicas atuais são somente leitura (GET). Não adicione gravação ou dados pessoais identificáveis sem autenticação, autorização e revisão de segurança.

O dashboard está publicado em [GitHub Pages](https://iamdatagabs.github.io/carbonapp/). O workflow publica `apps/frontend/`; o `index.html` na raiz redireciona para o dashboard como fallback para configurações Pages que servem a raiz.

## 2. MVP de captura (Java + PostgreSQL + web/Android)

O MVP de produto usa:
- `apps/backend/`: API Java 21 / Spring Boot e persistência PostgreSQL;
- `apps/web/`: cliente web responsivo para captura e consulta de registros;
- `apps/mobile/`: protótipo Android em Kotlin/Jetpack Compose.

### Executar localmente

Na raiz do repositório:

```bash
docker compose up --build
```

A aplicação web de captura pode ser servida separadamente:

```bash
python -m http.server 5500 --directory apps/web
```

Abra `http://localhost:5500`. Consulte os READMEs em `apps/backend/`, `apps/web/` e `apps/mobile/` para requisitos e detalhes específicos.

O contrato OpenAPI do MVP Java está em [openapi-v1.yaml](openapi-v1.yaml). Ele descreve health, metadados de profundidade e registros de campo. Não é o contrato da API Python de pesquisa.

### Limites de implantação

O backend Java é um scaffold de desenvolvimento, não pronto para exposição pública com dados reais. Autenticação, autorização, migrações de banco gerenciadas, controles de auditoria, rate limiting e sincronização idempotente ainda precisam ser implementados. O primeiro salvamento Android permanece apenas em memória; ainda não há persistência offline nem sincronização.

Não introduza dados pessoais/sensíveis nem exponha o MVP sem controles de segurança, privacidade e integridade apropriados.
