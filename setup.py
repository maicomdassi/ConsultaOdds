#!/usr/bin/env python
"""
Script de setup inicial do projeto
"""

import os
import sys
import subprocess

def criar_estrutura_pastas():
    """Cria a estrutura de pastas necessária"""
    pastas = ['config', 'scripts']
    
    print("📁 Criando estrutura de pastas...")
    for pasta in pastas:
        if not os.path.exists(pasta):
            os.makedirs(pasta)
            print(f"   ✅ Pasta '{pasta}' criada")
        else:
            print(f"   ℹ️ Pasta '{pasta}' já existe")
    
    # Criar __init__.py na pasta config
    init_file = os.path.join('config', '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# Config module\n")
        print("   ✅ Arquivo config/__init__.py criado")

def criar_env_file():
    """Cria o arquivo .env se não existir"""
    if not os.path.exists('.env'):
        print("\n📄 Criando arquivo .env...")
        
        if os.path.exists('.env.example'):
            # Copiar de .env.example
            with open('.env.example', 'r') as src:
                with open('.env', 'w') as dst:
                    dst.write(src.read())
            print("   ✅ Arquivo .env criado a partir de .env.example")
            print("   ⚠️ IMPORTANTE: Edite o arquivo .env e adicione sua API_KEY!")
        else:
            # Criar .env básico
            conteudo_env = """# API Football
API_KEY=sua_chave_api_aqui

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://zpauppwkolrbbyzszyrf.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwYXVwcHdrb2xyYmJ5enN6eXJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg5MDkwMTYsImV4cCI6MjA2NDQ4NTAxNn0.pPXnnY7m9QDoTPLwOv5RvIbllRgDqccOxHinVMN2afE

# Debug
DEBUG=False
"""
            with open('.env', 'w') as f:
                f.write(conteudo_env)
            print("   ✅ Arquivo .env criado")
            print("   ⚠️ IMPORTANTE: Edite o arquivo .env e adicione sua API_KEY!")
    else:
        print("\n📄 Arquivo .env já existe")

def instalar_dependencias():
    """Instala as dependências do projeto"""
    print("\n📦 Instalando dependências...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("   ✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("   ❌ Erro ao instalar dependências")
        return False

def exibir_proximos_passos():
    """Exibe os próximos passos para configuração"""
    print("\n" + "=" * 60)
    print("🎉 SETUP INICIAL CONCLUÍDO!")
    print("=" * 60)
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("\n1. Configure sua API Key:")
    print("   - Edite o arquivo .env")
    print("   - Adicione sua chave da API-Football no campo API_KEY")
    
    print("\n2. Configure o banco de dados:")
    print("   - Acesse o Supabase e execute o script SQL:")
    print("   - scripts/create_tables.sql")
    
    print("\n3. Execute os scripts de sincronização na ordem:")
    print("   a) python scripts/sync_paises.py")
    print("   b) python scripts/sync_ligas.py")
    print("   c) python scripts/sync_times.py")
    print("   d) python scripts/sync_jogos.py")
    
    print("\n4. Teste as conexões:")
    print("   python scripts/test_connection.py")
    
    print("\n5. Execute a aplicação:")
    print("   streamlit run app_odds_streamlit.py")
    
    print("\n📚 Consulte o README.md para mais informações!")

def main():
    """Função principal do setup"""
    print("🚀 INICIANDO SETUP DO PROJETO")
    print("=" * 60)
    
    # Criar estrutura de pastas
    criar_estrutura_pastas()
    
    # Criar arquivo .env
    criar_env_file()
    
    # Instalar dependências
    resposta = input("\n🤔 Deseja instalar as dependências agora? (s/n): ")
    if resposta.lower() == 's':
        instalar_dependencias()
    else:
        print("   ℹ️ Execute 'pip install -r requirements.txt' para instalar as dependências")
    
    # Exibir próximos passos
    exibir_proximos_passos()

if __name__ == "__main__":
    main()
