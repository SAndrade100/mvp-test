import sqlite3
import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
import pickle

# Caminho do banco de dados
DB_PATH = 'data/amazon_products.db'
MODEL_PATH = 'recommender_model.pkl'

# 1. Carregar dados de avaliações do banco SQLite
def load_ratings(db_path):
    conn = sqlite3.connect(db_path)
    query = '''
        SELECT user_id, product_id, rating
        FROM user_ratings
        WHERE rating IS NOT NULL
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def train_recommender(df):
    # 2. Preparar dados para Surprise
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df[['user_id', 'product_id', 'rating']], reader)
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

    # 3. Treinar modelo SVD
    algo = SVD()
    algo.fit(trainset)

    # 4. Avaliar (opcional)
    predictions = algo.test(testset)
    from surprise import accuracy
    print('RMSE:', accuracy.rmse(predictions))

    return algo

def save_model(model, path):
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    print(f'Modelo salvo em: {path}')

if __name__ == '__main__':
    print('Lendo avaliações do banco de dados...')
    df = load_ratings(DB_PATH)
    print(f'Total de avaliações: {len(df)}')
    print('Treinando modelo de recomendação...')
    model = train_recommender(df)
    save_model(model, MODEL_PATH)
    print('Pronto!')
