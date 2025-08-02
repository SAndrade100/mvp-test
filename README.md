# Amazon Products API - Sistema de Análise de Dados

Esta aplicação processa dados de produtos da Amazon a partir de um arquivo CSV e disponibiliza uma API REST para análise dos dados.

## 📁 Estrutura do Projeto

```
mvp-test/
├── data/
│   └── amazon.csv          # Arquivo de dados dos produtos
├── csv_to_sqlite.py        # Script para migração CSV → SQLite
├── api.py                  # API FastAPI
├── main.py                 # Script principal
├── requirements.txt        # Dependências Python
├── amazon_products.db      # Base de dados SQLite (criada automaticamente)
└── README.md              # Este arquivo
```

## 🚀 Como Usar

### 1. Execução Automática (Recomendada)

```bash
python main.py
```

Este comando irá:
- Verificar se os dados já foram importados
- Importar o CSV para SQLite (se necessário)
- Mostrar estatísticas dos dados
- Perguntar se deseja iniciar a API

### 2. Execução Manual

#### Importar dados do CSV para SQLite:
```bash
python csv_to_sqlite.py
```

#### Iniciar apenas a API:
```bash
python api.py
```

Ou usando uvicorn diretamente:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Estrutura dos Dados

O arquivo CSV contém as seguintes colunas:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `asin` | string | Identificador único do produto Amazon |
| `title` | string | Título do produto |
| `imgUrl` | string | URL da imagem do produto |
| `productURL` | string | URL do produto na Amazon |
| `stars` | float | Avaliação em estrelas (0-5) |
| `reviews` | integer | Número de reviews |
| `price` | float | Preço em libras (£) |
| `isBestSeller` | boolean | Se é best seller |
| `boughtInLastMonth` | integer | Comprados no último mês |
| `categoryName` | string | Nome da categoria |

## 🔌 Endpoints da API

A API estará disponível em `http://localhost:8000`

### Documentação Automática
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Principais Endpoints

#### Produtos
- `GET /products` - Lista produtos com filtros
  - `limit` (int): Número de produtos (padrão: 10, máx: 100)
  - `offset` (int): Produtos a saltar (paginação)
  - `category` (string): Filtrar por categoria
  - `min_price` (float): Preço mínimo
  - `max_price` (float): Preço máximo
  - `min_rating` (float): Rating mínimo
  - `best_seller_only` (bool): Apenas best sellers

- `GET /products/{asin}` - Produto específico por ASIN

- `GET /search?q={termo}` - Pesquisa produtos por título

#### Estatísticas
- `GET /stats` - Estatísticas gerais
- `GET /categories` - Lista todas as categorias
- `GET /categories/{category}/stats` - Estatísticas por categoria

#### Análises
- `GET /analytics/price-distribution` - Distribuição de preços
- `GET /analytics/rating-distribution` - Distribuição de ratings

## 📈 Exemplos de Uso

### Obter produtos em promoção (preço baixo)
```bash
curl "http://localhost:8000/products?max_price=25&limit=5"
```

### Best sellers de uma categoria
```bash
curl "http://localhost:8000/products?category=Hi-Fi%20Speakers&best_seller_only=true"
```

### Produtos bem avaliados
```bash
curl "http://localhost:8000/products?min_rating=4.5&limit=10"
```

### Pesquisar produtos
```bash
curl "http://localhost:8000/search?q=bluetooth%20speaker"
```

### Estatísticas gerais
```bash
curl "http://localhost:8000/stats"
```

## 🛠️ Funcionalidades

### Script de Migração (`csv_to_sqlite.py`)
- ✅ Leitura otimizada do CSV em chunks
- ✅ Limpeza e validação dos dados
- ✅ Conversão de tipos apropriados
- ✅ Criação de índices para performance
- ✅ Tratamento de duplicados
- ✅ Estatísticas após importação

### API FastAPI (`api.py`)
- ✅ Endpoints RESTful completos
- ✅ Documentação automática (Swagger)
- ✅ Validação de dados com Pydantic
- ✅ Filtros avançados
- ✅ Paginação
- ✅ Análises estatísticas
- ✅ Pesquisa de texto
- ✅ CORS habilitado
- ✅ Tratamento de erros

## 🔧 Dependências

- **FastAPI**: Framework web moderno para APIs
- **Uvicorn**: Servidor ASGI para FastAPI
- **Pandas**: Manipulação e análise de dados
- **Pydantic**: Validação de dados
- **SQLite3**: Base de dados (incluída no Python)

## 📝 Notas Técnicas

1. **Performance**: O SQLite é otimizado com índices nas colunas mais consultadas
2. **Escalabilidade**: Para grandes volumes, considere migrar para PostgreSQL
3. **Segurança**: Para produção, adicione autenticação e rate limiting
4. **Monitorização**: Considere adicionar logging estruturado

## 🐛 Troubleshooting

### Erro: "Files above 50MB cannot be synchronized"
Se o arquivo CSV for muito grande, o VS Code pode ter limitações. Execute diretamente no terminal:
```bash
python csv_to_sqlite.py
```

### Erro de dependências
Reinstale as dependências:
```bash
pip install -r requirements.txt
```

### Porto 8000 ocupado
Altere o porto na API ou pare outros serviços:
```bash
uvicorn api:app --port 8001
```

## 🚀 Próximos Passos

1. **Frontend**: Criar interface web com React/Vue
2. **Cache**: Implementar Redis para cache de consultas
3. **Autenticação**: Adicionar JWT/OAuth
4. **Métricas**: Integrar Prometheus/Grafana
5. **Deploy**: Containerizar com Docker
6. **Testes**: Adicionar testes unitários e integração
