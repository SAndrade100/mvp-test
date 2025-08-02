import sqlite3
import random
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializa o Faker para gerar dados realistas
fake = Faker(['pt_PT', 'en_US'])

class UserDataGenerator:
    def __init__(self, db_path="amazon_products.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Conecta à base de dados"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def disconnect(self):
        """Desconecta da base de dados"""
        if self.conn:
            self.conn.close()
            
    def create_user_tables(self):
        """Cria as tabelas para usuários e interações"""
        cursor = self.conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                gender TEXT,
                country TEXT,
                city TEXT,
                join_date DATE,
                total_orders INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0.0,
                preferred_categories TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de avaliações de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_ratings (
                rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                rating REAL NOT NULL,
                review_text TEXT,
                helpful_votes INTEGER DEFAULT 0,
                rating_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (id),
                UNIQUE(user_id, product_id)
            )
        ''')
        
        # Tabela de histórico de compras
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_history (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                price_paid REAL,
                purchase_date DATE,
                order_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Tabela de visualizações de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_views (
                view_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                view_date DATE,
                view_duration_seconds INTEGER,
                came_from TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Tabela de carrinho de compras (produtos adicionados mas não comprados)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart_abandonment (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                added_date DATE,
                removed_date DATE,
                quantity INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Criar índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_ratings_user ON user_ratings(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_ratings_product ON user_ratings(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchase_user ON purchase_history(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchase_product ON purchase_history(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_views_user ON product_views(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_views_product ON product_views(product_id)')
        
        self.conn.commit()
        logger.info("Tabelas de usuários criadas com sucesso!")
        
    def get_product_sample(self, limit=None):
        """Obtém uma amostra de produtos da base de dados"""
        cursor = self.conn.cursor()
        
        if limit:
            cursor.execute("SELECT id, asin, title, category_name, price, stars FROM products WHERE price IS NOT NULL ORDER BY RANDOM() LIMIT ?", (limit,))
        else:
            cursor.execute("SELECT id, asin, title, category_name, price, stars FROM products WHERE price IS NOT NULL")
            
        return cursor.fetchall()
    
    def get_categories(self):
        """Obtém lista de categorias"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT category_name FROM products WHERE category_name IS NOT NULL")
        return [row[0] for row in cursor.fetchall()]
    
    def generate_users(self, num_users=10000):
        """Gera usuários sintéticos"""
        logger.info(f"A gerar {num_users} usuários...")
        
        categories = self.get_categories()
        users_data = []
        
        for i in range(num_users):
            # Dados demográficos realistas
            gender = random.choice(['M', 'F', 'Other'])
            age = np.random.normal(35, 12)  # Idade média 35, desvio 12
            age = max(18, min(80, int(age)))  # Entre 18 e 80 anos
            
            # Preferências de categoria (usuários têm 1-4 categorias preferidas)
            preferred_cats = random.sample(categories, k=random.randint(1, min(4, len(categories))))
            
            # Data de registo (últimos 3 anos)
            join_date = fake.date_between(start_date='-3y', end_date='today')
            
            user_data = (
                fake.user_name(),
                fake.email(),
                fake.first_name(),
                fake.last_name(),
                age,
                gender,
                fake.country(),
                fake.city(),
                join_date,
                ','.join(preferred_cats[:3])  # Máximo 3 categorias
            )
            users_data.append(user_data)
            
            if (i + 1) % 1000 == 0:
                logger.info(f"Gerados {i + 1} usuários...")
        
        # Inserir usuários na base de dados
        cursor = self.conn.cursor()
        cursor.executemany('''
            INSERT INTO users (username, email, first_name, last_name, age, gender, country, city, join_date, preferred_categories)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', users_data)
        
        self.conn.commit()
        logger.info(f"✅ {num_users} usuários inseridos com sucesso!")
        
    def generate_ratings(self, num_ratings=100000, products_sample_size=50000):
        """Gera avaliações de produtos pelos usuários"""
        logger.info(f"A gerar {num_ratings} avaliações...")
        
        # Obter usuários
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, preferred_categories FROM users")
        users = cursor.fetchall()
        
        # Obter amostra de produtos
        products = self.get_product_sample(limit=products_sample_size)
        
        ratings_data = []
        
        for i in range(num_ratings):
            user = random.choice(users)
            product = random.choice(products)
            
            user_id = user[0]
            preferred_categories = user[1].split(',') if user[1] else []
            
            # Bias: usuários tendem a avaliar produtos das suas categorias preferidas
            if product[3] in preferred_categories:
                # Maior probabilidade de rating alto para categorias preferidas
                rating = np.random.beta(4, 1.5) * 5  # Enviesado para ratings altos
            else:
                # Rating mais neutro para outras categorias
                rating = np.random.beta(2, 2) * 5
            
            rating = max(1, min(5, round(rating, 1)))  # Entre 1 e 5
            
            # Texto da review (ocasional)
            review_text = None
            if random.random() < 0.3:  # 30% das avaliações têm texto
                review_text = fake.text(max_nb_chars=500)
            
            # Data da avaliação
            rating_date = fake.date_between(start_date='-2y', end_date='today')
            
            helpful_votes = max(0, int(np.random.exponential(2)))  # Distribuição exponencial
            
            ratings_data.append((
                user_id,
                product[0],  # product_id
                rating,
                review_text,
                helpful_votes,
                rating_date
            ))
            
            if (i + 1) % 10000 == 0:
                logger.info(f"Geradas {i + 1} avaliações...")
        
        # Inserir avaliações (ignorar duplicados)
        cursor.executemany('''
            INSERT OR IGNORE INTO user_ratings (user_id, product_id, rating, review_text, helpful_votes, rating_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ratings_data)
        
        self.conn.commit()
        inserted = cursor.rowcount
        logger.info(f"✅ {inserted} avaliações inseridas com sucesso!")
        
    def generate_purchases(self, num_purchases=50000, products_sample_size=30000):
        """Gera histórico de compras"""
        logger.info(f"A gerar {num_purchases} compras...")
        
        # Obter usuários
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, preferred_categories FROM users")
        users = cursor.fetchall()
        
        # Obter amostra de produtos
        products = self.get_product_sample(limit=products_sample_size)
        
        purchases_data = []
        order_counter = 1
        
        for i in range(num_purchases):
            user = random.choice(users)
            product = random.choice(products)
            
            user_id = user[0]
            preferred_categories = user[1].split(',') if user[1] else []
            
            # Quantidade (a maioria compra 1, alguns compram mais)
            if random.random() < 0.8:
                quantity = 1
            else:
                quantity = random.randint(2, 5)
            
            # Preço pago (pode ter desconto)
            original_price = product[4] if product[4] else 50.0
            if random.random() < 0.2:  # 20% têm desconto
                price_paid = original_price * random.uniform(0.7, 0.95)
            else:
                price_paid = original_price
                
            price_paid = round(price_paid, 2)
            
            # Data da compra
            purchase_date = fake.date_between(start_date='-2y', end_date='today')
            
            # Order ID (alguns produtos podem estar na mesma encomenda)
            if random.random() < 0.1:  # 10% chance de estar na mesma encomenda que a anterior
                order_id = f"ORD-{order_counter-1:06d}"
            else:
                order_id = f"ORD-{order_counter:06d}"
                order_counter += 1
            
            purchases_data.append((
                user_id,
                product[0],  # product_id
                quantity,
                price_paid,
                purchase_date,
                order_id
            ))
            
            if (i + 1) % 5000 == 0:
                logger.info(f"Geradas {i + 1} compras...")
        
        # Inserir compras
        cursor.executemany('''
            INSERT INTO purchase_history (user_id, product_id, quantity, price_paid, purchase_date, order_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', purchases_data)
        
        self.conn.commit()
        logger.info(f"✅ {num_purchases} compras inseridas com sucesso!")
        
    def generate_views(self, num_views=200000, products_sample_size=100000):
        """Gera visualizações de produtos"""
        logger.info(f"A gerar {num_views} visualizações...")
        
        # Obter usuários
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # Obter amostra de produtos
        products = self.get_product_sample(limit=products_sample_size)
        product_ids = [p[0] for p in products]
        
        views_data = []
        sources = ['search', 'category_browse', 'recommendation', 'homepage', 'ad', 'direct']
        
        for i in range(num_views):
            user_id = random.choice(user_ids)
            product_id = random.choice(product_ids)
            
            # Duração da visualização (distribuição log-normal)
            duration = max(5, int(np.random.lognormal(3, 1)))  # 5 segundos mínimo
            
            view_date = fake.date_between(start_date='-1y', end_date='today')
            came_from = random.choice(sources)
            
            views_data.append((
                user_id,
                product_id,
                view_date,
                duration,
                came_from
            ))
            
            if (i + 1) % 20000 == 0:
                logger.info(f"Geradas {i + 1} visualizações...")
        
        # Inserir visualizações
        cursor.executemany('''
            INSERT INTO product_views (user_id, product_id, view_date, view_duration_seconds, came_from)
            VALUES (?, ?, ?, ?, ?)
        ''', views_data)
        
        self.conn.commit()
        logger.info(f"✅ {num_views} visualizações inseridas com sucesso!")
        
    def update_user_stats(self):
        """Atualiza estatísticas dos usuários baseado nas compras"""
        logger.info("A atualizar estatísticas dos usuários...")
        
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET total_orders = (
                SELECT COUNT(DISTINCT order_id) 
                FROM purchase_history 
                WHERE purchase_history.user_id = users.user_id
            ),
            total_spent = (
                SELECT COALESCE(SUM(price_paid * quantity), 0.0)
                FROM purchase_history 
                WHERE purchase_history.user_id = users.user_id
            )
        ''')
        
        self.conn.commit()
        logger.info("✅ Estatísticas dos usuários atualizadas!")
        
    def get_generation_stats(self):
        """Mostra estatísticas dos dados gerados"""
        cursor = self.conn.cursor()
        
        # Estatísticas de usuários
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Estatísticas de avaliações
        cursor.execute("SELECT COUNT(*), AVG(rating), MIN(rating), MAX(rating) FROM user_ratings")
        rating_stats = cursor.fetchone()
        
        # Estatísticas de compras
        cursor.execute("SELECT COUNT(*), SUM(quantity), AVG(price_paid) FROM purchase_history")
        purchase_stats = cursor.fetchone()
        
        # Estatísticas de visualizações
        cursor.execute("SELECT COUNT(*), AVG(view_duration_seconds) FROM product_views")
        view_stats = cursor.fetchone()
        
        # Top 5 usuários por gastos
        cursor.execute('''
            SELECT username, total_orders, total_spent 
            FROM users 
            ORDER BY total_spent DESC 
            LIMIT 5
        ''')
        top_users = cursor.fetchall()
        
        # Top 5 produtos mais avaliados
        cursor.execute('''
            SELECT p.title, COUNT(ur.rating) as num_ratings, AVG(ur.rating) as avg_rating
            FROM products p
            JOIN user_ratings ur ON p.id = ur.product_id
            GROUP BY p.id, p.title
            ORDER BY num_ratings DESC
            LIMIT 5
        ''')
        top_rated_products = cursor.fetchall()
        
        print("\n" + "="*60)
        print("📊 ESTATÍSTICAS DOS DADOS GERADOS")
        print("="*60)
        
        print(f"\n👥 USUÁRIOS: {total_users:,}")
        
        print(f"\n⭐ AVALIAÇÕES: {rating_stats[0]:,}")
        print(f"   Média: {rating_stats[1]:.2f}")
        print(f"   Min/Max: {rating_stats[2]}/{rating_stats[3]}")
        
        print(f"\n🛒 COMPRAS: {purchase_stats[0]:,}")
        print(f"   Total itens: {purchase_stats[1]:,}")
        print(f"   Preço médio: £{purchase_stats[2]:.2f}")
        
        print(f"\n👀 VISUALIZAÇÕES: {view_stats[0]:,}")
        print(f"   Duração média: {view_stats[1]:.1f}s")
        
        print(f"\n🏆 TOP 5 USUÁRIOS (por gastos):")
        for user in top_users:
            print(f"   {user[0]}: {user[1]} encomendas, £{user[2]:.2f}")
            
        print(f"\n📱 TOP 5 PRODUTOS (por avaliações):")
        for product in top_rated_products:
            title = product[0][:50] + "..." if len(product[0]) > 50 else product[0]
            print(f"   {title}: {product[1]} avaliações (⭐{product[2]:.1f})")
        
        print("\n" + "="*60)


def main():
    """Função principal"""
    print("🚀 GERADOR DE DADOS SINTÉTICOS - Amazon Products")
    print("="*60)
    
    generator = UserDataGenerator()
    
    try:
        generator.connect()
        
        # Criar tabelas
        generator.create_user_tables()
        
        # Gerar dados (ajuste os números conforme necessário)
        print("\n📋 A gerar dados sintéticos...")
        generator.generate_users(num_users=5000)           # 5K usuários
        generator.generate_ratings(num_ratings=50000)      # 50K avaliações
        generator.generate_purchases(num_purchases=25000)  # 25K compras
        generator.generate_views(num_views=100000)         # 100K visualizações
        
        # Atualizar estatísticas
        generator.update_user_stats()
        
        # Mostrar estatísticas
        generator.get_generation_stats()
        
        print("\n✅ Geração de dados concluída com sucesso!")
        print("💡 Agora pode criar modelos de recomendação baseados nos dados de usuários!")
        
    except Exception as e:
        logger.error(f"Erro durante a geração: {e}")
        raise
    finally:
        generator.disconnect()


if __name__ == "__main__":
    main()
