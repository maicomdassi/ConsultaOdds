import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime
from config.database import supabase
from config.settings import settings

# Headers para requisições
cabecalhos = {
    'X-RapidAPI-Key': settings.api_key,
    'X-RapidAPI-Host': 'v3.football.api-sports.io'
}

def buscar_paises_api():
    """Busca todos os países da API"""
    url = "https://v3.football.api-sports.io/countries"
    
    try:
        print("🔄 Buscando países da API...")
        resposta = requests.get(url, headers=cabecalhos)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            paises = dados.get('response', [])
            print(f"✅ {len(paises)} países encontrados na API")
            return paises
        else:
            print(f"❌ Erro ao buscar países: {resposta.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")
        return []

def buscar_paises_banco():
    """Busca todos os países do banco de dados"""
    try:
        print("🔄 Buscando países do banco de dados...")
        resultado = supabase.table('paises').select("*").execute()
        paises = resultado.data
        print(f"✅ {len(paises)} países encontrados no banco")
        
        # Criar dicionário com nome como chave para facilitar comparação
        paises_dict = {pais['nome']: pais for pais in paises}
        return paises_dict
    except Exception as e:
        print(f"❌ Erro ao buscar países do banco: {str(e)}")
        return {}

def sincronizar_paises():
    """Sincroniza países da API com o banco de dados"""
    print("\n🚀 Iniciando sincronização de países...")
    
    # Buscar dados
    paises_api = buscar_paises_api()
    paises_banco = buscar_paises_banco()
    
    if not paises_api:
        print("❌ Nenhum país retornado da API")
        return
    
    # Estatísticas
    novos_paises = []
    paises_atualizados = []
    
    for pais_api in paises_api:
        nome = pais_api.get('name')
        codigo = pais_api.get('code')
        flag_url = pais_api.get('flag')
        
        if not nome:
            continue
        
        # Verificar se o país já existe no banco
        if nome in paises_banco:
            pais_banco = paises_banco[nome]
            # Verificar se precisa atualizar
            if (pais_banco.get('codigo') != codigo or 
                pais_banco.get('flag_url') != flag_url):
                
                try:
                    supabase.table('paises').update({
                        'codigo': codigo,
                        'flag_url': flag_url,
                        'atualizado_em': datetime.now().isoformat()
                    }).eq('nome', nome).execute()
                    
                    paises_atualizados.append(nome)
                    print(f"📝 País atualizado: {nome}")
                except Exception as e:
                    print(f"❌ Erro ao atualizar {nome}: {str(e)}")
        else:
            # País novo - inserir
            try:
                # Buscar próximo ID disponível (se não for auto-incremento)
                # Se a tabela já tem auto-incremento, remova o campo 'id' do insert
                max_id_result = supabase.table('paises').select('id').order('id', desc=True).limit(1).execute()
                next_id = 1 if not max_id_result.data else max_id_result.data[0]['id'] + 1
                
                supabase.table('paises').insert({
                    'id': next_id,
                    'nome': nome,
                    'codigo': codigo,
                    'flag_url': flag_url,
                    'ativo': True,
                    'atualizado_em': datetime.now().isoformat()
                }).execute()
                
                novos_paises.append(nome)
                print(f"✅ Novo país inserido: {nome}")
            except Exception as e:
                print(f"❌ Erro ao inserir {nome}: {str(e)}")
    
    # Resumo
    print("\n📊 Resumo da sincronização:")
    print(f"✅ {len(novos_paises)} novos países inseridos")
    print(f"📝 {len(paises_atualizados)} países atualizados")
    print(f"📁 Total de países no banco: {len(paises_banco) + len(novos_paises)}")
    
    if novos_paises:
        print("\n🆕 Novos países:")
        for pais in novos_paises[:10]:  # Mostrar apenas os 10 primeiros
            print(f"  - {pais}")
        if len(novos_paises) > 10:
            print(f"  ... e mais {len(novos_paises) - 10} países")

if __name__ == "__main__":
    sincronizar_paises()
