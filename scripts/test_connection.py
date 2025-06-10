import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import supabase
from config.settings import settings
import requests

def testar_conexao_supabase():
    """Testa a conexão com o Supabase"""
    print("🔄 Testando conexão com Supabase...")
    try:
        # Tentar buscar países (tabela que deve existir)
        resultado = supabase.table('paises').select("id").limit(1).execute()
        print("✅ Conexão com Supabase OK!")
        print(f"   Registros encontrados: {len(resultado.data)}")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão com Supabase: {str(e)}")
        return False

def testar_api_football():
    """Testa a conexão com a API Football"""
    print("\n🔄 Testando conexão com API Football...")
    
    if not settings.api_key:
        print("❌ API_KEY não configurada!")
        return False
    
    url = "https://v3.football.api-sports.io/status"
    headers = {
        'X-RapidAPI-Key': settings.api_key,
        'X-RapidAPI-Host': 'v3.football.api-sports.io'
    }
    
    try:
        resposta = requests.get(url, headers=headers)
        if resposta.status_code == 200:
            dados = resposta.json()
            print("✅ Conexão com API Football OK!")
            print(f"   Conta: {dados.get('response', {}).get('account', {}).get('email', 'N/A')}")
            print(f"   Requisições hoje: {dados.get('response', {}).get('requests', {}).get('current', 0)}")
            print(f"   Limite diário: {dados.get('response', {}).get('requests', {}).get('limit_day', 0)}")
            return True
        else:
            print(f"❌ Erro na API: Status {resposta.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão com API: {str(e)}")
        return False

def verificar_tabelas():
    """Verifica se as tabelas necessárias existem"""
    print("\n🔄 Verificando tabelas no banco de dados...")
    
    tabelas_necessarias = [
        'paises',
        'ligas', 
        'times',
        'times_ligas_temporada',
        'jogos',
        'estatisticas_times'
    ]
    
    tabelas_ok = 0
    for tabela in tabelas_necessarias:
        try:
            resultado = supabase.table(tabela).select("*").limit(0).execute()
            print(f"✅ Tabela '{tabela}' existe")
            tabelas_ok += 1
        except Exception as e:
            print(f"❌ Tabela '{tabela}' não encontrada ou erro: {str(e)}")
    
    print(f"\n📊 {tabelas_ok}/{len(tabelas_necessarias)} tabelas verificadas com sucesso")
    
    if tabelas_ok < len(tabelas_necessarias):
        print("\n⚠️ Execute o script SQL em 'scripts/create_tables.sql' no Supabase para criar as tabelas faltantes.")
    
    return tabelas_ok == len(tabelas_necessarias)

def main():
    """Função principal de testes"""
    print("🚀 TESTE DE CONEXÕES E CONFIGURAÇÕES")
    print("=" * 50)
    
    # Testar Supabase
    supabase_ok = testar_conexao_supabase()
    
    # Testar API Football
    api_ok = testar_api_football()
    
    # Verificar tabelas
    tabelas_ok = False
    if supabase_ok:
        tabelas_ok = verificar_tabelas()
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    print(f"   Supabase: {'✅ OK' if supabase_ok else '❌ FALHOU'}")
    print(f"   API Football: {'✅ OK' if api_ok else '❌ FALHOU'}")
    print(f"   Tabelas: {'✅ OK' if tabelas_ok else '❌ INCOMPLETO'}")
    
    if supabase_ok and api_ok and tabelas_ok:
        print("\n✅ SISTEMA PRONTO PARA USO!")
    else:
        print("\n❌ CORRIJA OS PROBLEMAS ACIMA ANTES DE USAR O SISTEMA")

if __name__ == "__main__":
    main()
