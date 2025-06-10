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

def buscar_ligas_api():
    """Busca todas as ligas da API"""
    url = "https://v3.football.api-sports.io/leagues"
    
    try:
        print("🔄 Buscando ligas da API...")
        resposta = requests.get(url, headers=cabecalhos)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            ligas = dados.get('response', [])
            print(f"✅ {len(ligas)} ligas encontradas na API")
            return ligas
        else:
            print(f"❌ Erro ao buscar ligas: {resposta.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")
        return []

def buscar_ligas_banco():
    """Busca todas as ligas do banco de dados"""
    try:
        print("🔄 Buscando ligas do banco de dados...")
        resultado = supabase.table('ligas').select("*").execute()
        ligas = resultado.data
        print(f"✅ {len(ligas)} ligas encontradas no banco")
        
        # Criar dicionário com id como chave
        ligas_dict = {liga['id']: liga for liga in ligas}
        return ligas_dict
    except Exception as e:
        print(f"❌ Erro ao buscar ligas do banco: {str(e)}")
        return {}

def buscar_pais_id(nome_pais):
    """Busca o ID do país pelo nome"""
    if nome_pais == "World":
        return None  # Ligas mundiais não têm país específico
    
    try:
        resultado = supabase.table('paises').select("id").eq('nome', nome_pais).execute()
        if resultado.data:
            return resultado.data[0]['id']
        else:
            print(f"⚠️ País não encontrado: {nome_pais}")
            return None
    except Exception as e:
        print(f"❌ Erro ao buscar país {nome_pais}: {str(e)}")
        return None

def obter_temporada_atual(seasons):
    """Obtém a temporada mais recente (atual) da lista de temporadas"""
    if not seasons:
        return None
    
    # Filtrar temporadas com ano válido
    temporadas_validas = [s for s in seasons if s.get('year')]
    
    if not temporadas_validas:
        return None
    
    # Ordenar por ano (decrescente) e pegar a primeira
    temporada_atual = sorted(temporadas_validas, key=lambda x: x['year'], reverse=True)[0]
    
    return temporada_atual

def sincronizar_ligas():
    """Sincroniza ligas da API com o banco de dados"""
    print("\n🚀 Iniciando sincronização de ligas...")
    
    # Buscar dados
    ligas_api = buscar_ligas_api()
    ligas_banco = buscar_ligas_banco()
    
    if not ligas_api:
        print("❌ Nenhuma liga retornada da API")
        return
    
    # Estatísticas
    novas_ligas = []
    ligas_atualizadas = []
    ligas_com_erro = []
    
    for item in ligas_api:
        liga = item.get('league', {})
        pais = item.get('country', {})
        temporadas = item.get('seasons', [])
        
        liga_id = liga.get('id')
        liga_nome = liga.get('name')
        liga_tipo = liga.get('type')
        liga_logo = liga.get('logo')
        pais_nome = pais.get('name')
        
        if not liga_id or not liga_nome:
            continue
        
        # Obter temporada atual
        temporada_atual = obter_temporada_atual(temporadas)
        if not temporada_atual:
            print(f"⚠️ Liga sem temporada válida: {liga_nome}")
            continue
        
        # Buscar ID do país
        pais_id = buscar_pais_id(pais_nome) if pais_nome else None
        
        # Dados da liga para inserir/atualizar
        dados_liga = {
            'nome': liga_nome,
            'tipo': liga_tipo,
            'logo_url': liga_logo,
            'pais_id': pais_id,
            'temporada_atual': temporada_atual['year'],
            'data_inicio': temporada_atual.get('start'),
            'data_fim': temporada_atual.get('end'),
            'temporada_corrente': temporada_atual.get('current', False),
            'ativo': True,
            'atualizado_em': datetime.now().isoformat()
        }
        
        # Verificar se a liga já existe no banco
        if liga_id in ligas_banco:
            liga_banco = ligas_banco[liga_id]
            
            # Verificar se a temporada mudou ou se há outras atualizações
            if (liga_banco.get('temporada_atual') != temporada_atual['year'] or
                liga_banco.get('data_inicio') != temporada_atual.get('start') or
                liga_banco.get('data_fim') != temporada_atual.get('end') or
                liga_banco.get('temporada_corrente') != temporada_atual.get('current', False)):
                
                try:
                    supabase.table('ligas').update(dados_liga).eq('id', liga_id).execute()
                    ligas_atualizadas.append(f"{liga_nome} ({pais_nome})")
                    print(f"📝 Liga atualizada: {liga_nome} - Temporada {temporada_atual['year']}")
                except Exception as e:
                    print(f"❌ Erro ao atualizar {liga_nome}: {str(e)}")
                    ligas_com_erro.append(liga_nome)
        else:
            # Liga nova - inserir
            try:
                dados_liga['id'] = liga_id
                supabase.table('ligas').insert(dados_liga).execute()
                novas_ligas.append(f"{liga_nome} ({pais_nome})")
                print(f"✅ Nova liga inserida: {liga_nome} ({pais_nome}) - Temporada {temporada_atual['year']}")
            except Exception as e:
                print(f"❌ Erro ao inserir {liga_nome}: {str(e)}")
                ligas_com_erro.append(liga_nome)
    
    # Resumo
    print("\n📊 Resumo da sincronização:")
    print(f"✅ {len(novas_ligas)} novas ligas inseridas")
    print(f"📝 {len(ligas_atualizadas)} ligas atualizadas")
    print(f"❌ {len(ligas_com_erro)} ligas com erro")
    print(f"📁 Total de ligas processadas: {len(ligas_api)}")
    
    if novas_ligas:
        print("\n🆕 Novas ligas (primeiras 10):")
        for liga in novas_ligas[:10]:
            print(f"  - {liga}")
        if len(novas_ligas) > 10:
            print(f"  ... e mais {len(novas_ligas) - 10} ligas")
    
    if ligas_atualizadas:
        print("\n📝 Ligas atualizadas (primeiras 10):")
        for liga in ligas_atualizadas[:10]:
            print(f"  - {liga}")
        if len(ligas_atualizadas) > 10:
            print(f"  ... e mais {len(ligas_atualizadas) - 10} ligas")

if __name__ == "__main__":
    sincronizar_ligas()
