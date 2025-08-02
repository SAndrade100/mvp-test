import pandas as pd
import sqlite3
import os
from typing import Optional

def create_database_schema(db_path: str):
    """Cria o esquema da base de dados SQLite"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cria a tabela products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            img_url TEXT,
            product_url TEXT,
            stars REAL,
            reviews INTEGER,
            price REAL,
            is_best_seller BOOLEAN,
            bought_in_last_month INTEGER,
            category_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Cria índices para melhor performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_asin ON products(asin)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON products(category_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stars ON products(stars)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price ON products(price)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_best_seller ON products(is_best_seller)')
    
    conn.commit()
    conn.close()
    print("Base de dados criada com sucesso!")

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa e prepara os dados do CSV"""
    print("A limpar e preparar os dados...")
    
    # Remove aspas extras das colunas de texto
    text_columns = ['asin', 'title', 'imgUrl', 'productURL', 'categoryName']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip('"')
    
    # Converte tipos de dados
    if 'stars' in df.columns:
        df['stars'] = pd.to_numeric(df['stars'], errors='coerce')
    
    if 'reviews' in df.columns:
        df['reviews'] = pd.to_numeric(df['reviews'], errors='coerce').fillna(0).astype(int)
    
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
    
    if 'isBestSeller' in df.columns:
        df['isBestSeller'] = df['isBestSeller'].map({'True': True, 'False': False, True: True, False: False})
    
    if 'boughtInLastMonth' in df.columns:
        df['boughtInLastMonth'] = pd.to_numeric(df['boughtInLastMonth'], errors='coerce').fillna(0).astype(int)
    
    # Renomeia as colunas para snake_case (padrão Python)
    column_mapping = {
        'asin': 'asin',
        'title': 'title',
        'imgUrl': 'img_url',
        'productURL': 'product_url',
        'stars': 'stars',
        'reviews': 'reviews',
        'price': 'price',
        'isBestSeller': 'is_best_seller',
        'boughtInLastMonth': 'bought_in_last_month',
        'categoryName': 'category_name'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Remove registos duplicados baseados no ASIN
    df = df.drop_duplicates(subset=['asin'])
    
    print(f"Dados limpos: {len(df)} produtos processados")
    return df

def import_csv_to_sqlite(csv_path: str, db_path: str, chunk_size: int = 1000):
    """Importa dados do CSV para SQLite em chunks para otimizar performance"""
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_path}")
    
    print(f"A importar dados de {csv_path} para {db_path}...")
    
    # Cria o esquema da base de dados
    create_database_schema(db_path)
    
    # Lê o CSV em chunks para otimizar memoria
    total_rows = 0
    conn = sqlite3.connect(db_path)
    
    try:
        for chunk_df in pd.read_csv(csv_path, chunksize=chunk_size):
            # Limpa os dados do chunk
            cleaned_chunk = clean_data(chunk_df)
            
            # Insere no SQLite (ignora duplicados)
            cleaned_chunk.to_sql('products', conn, if_exists='append', index=False, method='multi')
            total_rows += len(cleaned_chunk)
            print(f"Processados {total_rows} produtos...")
            
    except Exception as e:
        print(f"Erro durante a importação: {e}")
        raise
    finally:
        conn.close()
    
    print(f"Importação concluída! Total de produtos importados: {total_rows}")
    return total_rows

def get_database_stats(db_path: str):
    """Mostra estatísticas da base de dados"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total de produtos
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    
    # Produtos por categoria
    cursor.execute("""
        SELECT category_name, COUNT(*) as count 
        FROM products 
        GROUP BY category_name 
        ORDER BY count DESC
    """)
    categories = cursor.fetchall()
    
    # Estatísticas de preços
    cursor.execute("""
        SELECT 
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            COUNT(CASE WHEN is_best_seller = 1 THEN 1 END) as best_sellers
        FROM products 
        WHERE price IS NOT NULL
    """)
    price_stats = cursor.fetchone()
    
    conn.close()
    
    print("\n=== ESTATÍSTICAS DA BASE DE DADOS ===")
    print(f"Total de produtos: {total_products}")
    print(f"Best sellers: {price_stats[3]}")
    print(f"Preço mínimo: £{price_stats[0]:.2f}" if price_stats[0] else "N/A")
    print(f"Preço máximo: £{price_stats[1]:.2f}" if price_stats[1] else "N/A")
    print(f"Preço médio: £{price_stats[2]:.2f}" if price_stats[2] else "N/A")
    
    print("\nProdutos por categoria:")
    for category, count in categories[:10]:  # Top 10 categorias
        print(f"  {category}: {count}")

if __name__ == "__main__":
    # Caminhos dos arquivos
    csv_file = "amazon.csv"
    db_file = "amazon_products.db"
    
    try:
        # Importa dados do CSV para SQLite
        import_csv_to_sqlite(csv_file, db_file)
        
        # Mostra estatísticas
        get_database_stats(db_file)
        
    except Exception as e:
        print(f"Erro: {e}")
