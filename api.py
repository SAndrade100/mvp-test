from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from datetime import datetime

app = FastAPI(
    title="Amazon Products API",
    description="API para análise de dados de produtos da Amazon",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class Product(BaseModel):
    id: int
    asin: str
    title: str
    img_url: Optional[str]
    product_url: Optional[str]
    stars: Optional[float]
    reviews: Optional[int]
    price: Optional[float]
    is_best_seller: Optional[bool]
    bought_in_last_month: Optional[int]
    category_name: Optional[str]
    created_at: Optional[str]

class ProductStats(BaseModel):
    total_products: int
    total_categories: int
    avg_rating: float
    avg_price: float
    best_sellers_count: int
    top_categories: List[dict]

class CategoryStats(BaseModel):
    category_name: str
    product_count: int
    avg_rating: float
    avg_price: float
    best_sellers_count: int

# Configuração da base de dados
DB_PATH = "amazon_products.db"

def get_db_connection():
    """Cria conexão com a base de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Para retornar dicionários
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conexão à base de dados: {e}")

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "Amazon Products API",
        "version": "1.0.0",
        "endpoints": {
            "/products": "Lista produtos com filtros",
            "/products/{asin}": "Produto específico por ASIN",
            "/stats": "Estatísticas gerais",
            "/categories": "Lista de categorias",
            "/categories/{category}/stats": "Estatísticas por categoria",
            "/search": "Pesquisa de produtos"
        }
    }

@app.get("/products", response_model=List[Product])
async def get_products(
    limit: int = Query(10, ge=1, le=100, description="Número de produtos a retornar"),
    offset: int = Query(0, ge=0, description="Número de produtos a saltar"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    min_price: Optional[float] = Query(None, ge=0, description="Preço mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Preço máximo"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Rating mínimo"),
    best_seller_only: Optional[bool] = Query(None, description="Apenas best sellers")
):
    """Lista produtos com filtros opcionais"""
    
    conn = get_db_connection()
    try:
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        
        if category:
            query += " AND category_name = ?"
            params.append(category)
        
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
        
        if min_rating is not None:
            query += " AND stars >= ?"
            params.append(min_rating)
        
        if best_seller_only is not None:
            query += " AND is_best_seller = ?"
            params.append(best_seller_only)
        
        query += " ORDER BY reviews DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        products = [dict(row) for row in cursor.fetchall()]
        
        return products
    
    finally:
        conn.close()

@app.get("/products/{asin}", response_model=Product)
async def get_product(asin: str):
    """Obter produto específico por ASIN"""
    
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT * FROM products WHERE asin = ?", (asin,))
        product = cursor.fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        return dict(product)
    
    finally:
        conn.close()

@app.get("/stats", response_model=ProductStats)
async def get_stats():
    """Estatísticas gerais dos produtos"""
    
    conn = get_db_connection()
    try:
        # Estatísticas gerais
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_products,
                COUNT(DISTINCT category_name) as total_categories,
                AVG(stars) as avg_rating,
                AVG(price) as avg_price,
                SUM(CASE WHEN is_best_seller = 1 THEN 1 ELSE 0 END) as best_sellers_count
            FROM products
        """)
        stats = cursor.fetchone()
        
        # Top categorias
        cursor = conn.execute("""
            SELECT category_name, COUNT(*) as count
            FROM products
            GROUP BY category_name
            ORDER BY count DESC
            LIMIT 10
        """)
        top_categories = [{"category": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        return ProductStats(
            total_products=stats[0],
            total_categories=stats[1],
            avg_rating=round(stats[2], 2) if stats[2] else 0,
            avg_price=round(stats[3], 2) if stats[3] else 0,
            best_sellers_count=stats[4],
            top_categories=top_categories
        )
    
    finally:
        conn.close()

@app.get("/categories")
async def get_categories():
    """Lista todas as categorias disponíveis"""
    
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT 
                category_name,
                COUNT(*) as product_count,
                AVG(stars) as avg_rating,
                AVG(price) as avg_price
            FROM products
            GROUP BY category_name
            ORDER BY product_count DESC
        """)
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                "category_name": row[0],
                "product_count": row[1],
                "avg_rating": round(row[2], 2) if row[2] else 0,
                "avg_price": round(row[3], 2) if row[3] else 0
            })
        
        return categories
    
    finally:
        conn.close()

@app.get("/categories/{category}/stats", response_model=CategoryStats)
async def get_category_stats(category: str):
    """Estatísticas de uma categoria específica"""
    
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as product_count,
                AVG(stars) as avg_rating,
                AVG(price) as avg_price,
                SUM(CASE WHEN is_best_seller = 1 THEN 1 ELSE 0 END) as best_sellers_count
            FROM products
            WHERE category_name = ?
        """, (category,))
        
        stats = cursor.fetchone()
        
        if stats[0] == 0:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        
        return CategoryStats(
            category_name=category,
            product_count=stats[0],
            avg_rating=round(stats[1], 2) if stats[1] else 0,
            avg_price=round(stats[2], 2) if stats[2] else 0,
            best_sellers_count=stats[3]
        )
    
    finally:
        conn.close()

@app.get("/search", response_model=List[Product])
async def search_products(
    q: str = Query(..., description="Termo de pesquisa"),
    limit: int = Query(10, ge=1, le=100, description="Número de resultados")
):
    """Pesquisa produtos por título"""
    
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT * FROM products 
            WHERE title LIKE ? 
            ORDER BY reviews DESC 
            LIMIT ?
        """, (f"%{q}%", limit))
        
        products = [dict(row) for row in cursor.fetchall()]
        return products
    
    finally:
        conn.close()

@app.get("/analytics/price-distribution")
async def get_price_distribution():
    """Distribuição de preços por faixas"""
    
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT 
                CASE 
                    WHEN price < 10 THEN '0-10'
                    WHEN price < 25 THEN '10-25'
                    WHEN price < 50 THEN '25-50'
                    WHEN price < 100 THEN '50-100'
                    WHEN price < 200 THEN '100-200'
                    ELSE '200+'
                END as price_range,
                COUNT(*) as count
            FROM products
            WHERE price IS NOT NULL
            GROUP BY price_range
            ORDER BY 
                CASE 
                    WHEN price < 10 THEN 1
                    WHEN price < 25 THEN 2
                    WHEN price < 50 THEN 3
                    WHEN price < 100 THEN 4
                    WHEN price < 200 THEN 5
                    ELSE 6
                END
        """)
        
        distribution = [{"price_range": row[0], "count": row[1]} for row in cursor.fetchall()]
        return distribution
    
    finally:
        conn.close()

@app.get("/analytics/rating-distribution")
async def get_rating_distribution():
    """Distribuição de ratings"""
    
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT 
                ROUND(stars) as rating,
                COUNT(*) as count
            FROM products
            WHERE stars IS NOT NULL
            GROUP BY ROUND(stars)
            ORDER BY rating
        """)
        
        distribution = [{"rating": row[0], "count": row[1]} for row in cursor.fetchall()]
        return distribution
    
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
