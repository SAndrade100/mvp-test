#!/usr/bin/env python3
"""
Script principal para configurar e executar a aplicação Amazon Products API
"""

import os
import sys
import subprocess
from data.csv_to_sqlite import import_csv_to_sqlite, get_database_stats

def setup_project():
    """Configura o projeto e importa os dados"""
    print("=== CONFIGURAÇÃO DO PROJETO AMAZON PRODUCTS API ===\n")
    
    # Verifica se o arquivo CSV existe
    csv_file = "data/amazon.csv"
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo {csv_file} não encontrado!")
        print("Certifique-se de que o arquivo amazon.csv está na pasta 'data/'")
        return False
    
    print(f"✅ Arquivo CSV encontrado: {csv_file}")
    
    # Importa dados para SQLite
    db_file = "amazon_products.db"
    
    try:
        print("\n📊 A importar dados do CSV para SQLite...")
        import_csv_to_sqlite(csv_file, db_file)
        
        print("\n📈 Estatísticas da base de dados:")
        get_database_stats(db_file)
        
        print(f"\n✅ Base de dados criada com sucesso: {db_file}")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a configuração: {e}")
        return False

def start_api():
    """Inicia o servidor da API"""
    print("\n🚀 A iniciar servidor da API...")
    print("A API estará disponível em: http://localhost:8000")
    print("Documentação automática em: http://localhost:8000/docs")
    print("Pressione Ctrl+C para parar o servidor\n")
    
    try:
        import uvicorn
        from api import app
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n👋 Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar o servidor: {e}")

def main():
    """Função principal"""
    print("Amazon Products API - Sistema de Análise de Dados\n")
    
    # Verifica se a base de dados já existe
    db_file = "amazon_products.db"
    
    if not os.path.exists(db_file):
        print("Base de dados não encontrada. A configurar projeto...")
        if not setup_project():
            print("❌ Falha na configuração. A terminar.")
            sys.exit(1)
    else:
        print(f"✅ Base de dados encontrada: {db_file}")
        
        # Mostra estatísticas existentes
        try:
            get_database_stats(db_file)
        except Exception as e:
            print(f"⚠️  Aviso: Erro ao ler estatísticas: {e}")
    
    # Pergunta se quer iniciar a API
    while True:
        choice = input("\nDeseja iniciar o servidor da API? (s/n): ").lower().strip()
        
        if choice in ['s', 'sim', 'y', 'yes']:
            start_api()
            break
        elif choice in ['n', 'não', 'nao', 'no']:
            print("👋 Configuração concluída. Execute 'python main.py' para iniciar a API mais tarde.")
            break
        else:
            print("Por favor, responda 's' para sim ou 'n' para não.")

if __name__ == "__main__":
    main()
