import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import time
from datetime import datetime
from config.database import supabase
from config.settings import settings

# Headers para requisições
cabecalhos = {
    'X-RapidAPI-Key': settings.api_key,
    'X-RapidAPI-Host': 'v3.football.api-sports.io'
}

def buscar_ligas_ativas():
    """Busca todas as ligas ativas com temporada atual"""
    try:
        print("🔄 Buscando ligas ativas do banco...")
        resultado = supabase.table('ligas').select("id, nome, temporada_atual, pais_id").eq('ativo', True).execute()
        ligas = resultado.data
        print(f"✅ {len(ligas)} ligas ativas encontradas")
        return ligas
    except Exception as e:
        print(f"❌ Erro ao buscar ligas: {str(e)}")
        return []

def buscar_times_liga_api(liga_id, temporada):
    """Busca todos os times de uma liga específica na temporada atual"""
    url = "https://v3.football.api-sports.io/teams"
    parametros = {
        'league': liga_id,
        'season': temporada
    }
    
    try:
        resposta = requests.get(url, headers=cabecalhos, params=parametros)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            times = dados.get('response', [])
            return times
        else:
            print(f"❌ Erro ao buscar times da liga {liga_id}: {resposta.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erro na requisição para liga {liga_id}: {str(e)}")
        return []

def buscar_times_banco():
    """Busca todos os times do banco de dados"""
    try:
        resultado = supabase.table('times').select("*").execute()
        times = resultado.data
        # Criar dicionário com id como chave
        times_dict = {time['id']: time for time in times}
        return times_dict
    except Exception as e:
        print(f"❌ Erro ao buscar times do banco: {str(e)}")
        return {}

def buscar_vinculos_times_ligas():
    """Busca todos os vínculos existentes entre times e ligas"""
    try:
        resultado = supabase.table('times_ligas_temporada').select("*").execute()
        vinculos = resultado.data
        # Criar conjunto de chaves únicas (time_id, liga_id, temporada)
        vinculos_set = {(v['time_id'], v['liga_id'], v['temporada']) for v in vinculos}
        return vinculos_set
    except Exception as e:
        print(f"❌ Erro ao buscar vínculos: {str(e)}")
        return set()

def inserir_ou_atualizar_time(time_data, times_banco):
    """Insere um novo time ou atualiza se já existir"""
    time_info = time_data.get('team', {})
    time_id = time_info.get('id')
    time_nome = time_info.get('name')
    time_codigo = time_info.get('code')
    time_logo = time_info.get('logo')
    time_fundacao = time_info.get('founded')
    
    if not time_id or not time_nome:
        return False
    
    dados_time = {
        'nome': time_nome,
        'codigo': time_codigo,
        'logo_url': time_logo,
        'ano_fundacao': time_fundacao,
        'ativo': True,
        'atualizado_em': datetime.now().isoformat()
    }
    
    try:
        if time_id in times_banco:
            # Atualizar time existente se houver mudanças
            time_banco = times_banco[time_id]
            if (time_banco.get('nome') != time_nome or
                time_banco.get('codigo') != time_codigo or
                time_banco.get('logo_url') != time_logo):
                
                supabase.table('times').update(dados_time).eq('id', time_id).execute()
                print(f"📝 Time atualizado: {time_nome}")
        else:
            # Inserir novo time
            dados_time['id'] = time_id
            supabase.table('times').insert(dados_time).execute()
            print(f"✅ Novo time inserido: {time_nome}")
            times_banco[time_id] = dados_time  # Atualizar cache local
        
        return True
    except Exception as e:
        print(f"❌ Erro ao processar time {time_nome}: {str(e)}")
        return False

def criar_vinculo_time_liga(time_id, liga_id, temporada, vinculos_existentes):
    """Cria vínculo entre time e liga para a temporada"""
    if (time_id, liga_id, temporada) in vinculos_existentes:
        return False  # Vínculo já existe
    
    try:
        supabase.table('times_ligas_temporada').insert({
            'time_id': time_id,
            'liga_id': liga_id,
            'temporada': temporada,
            'ativo': True,
            'criado_em': datetime.now().isoformat(),
            'atualizado_em': datetime.now().isoformat()
        }).execute()
        
        # Adicionar ao cache local
        vinculos_existentes.add((time_id, liga_id, temporada))
        return True
    except Exception as e:
        print(f"❌ Erro ao criar vínculo time {time_id} x liga {liga_id}: {str(e)}")
        return False

def sincronizar_times():
    """Sincroniza times de todas as ligas ativas"""
    print("\n🚀 Iniciando sincronização de times...")
    
    # Buscar dados iniciais
    ligas = buscar_ligas_ativas()
    times_banco = buscar_times_banco()
    vinculos_existentes = buscar_vinculos_times_ligas()
    
    if not ligas:
        print("❌ Nenhuma liga ativa encontrada")
        return
    
    # Estatísticas
    total_times_novos = 0
    total_times_atualizados = 0
    total_vinculos_criados = 0
    ligas_processadas = 0
    
    print(f"\n📊 Processando {len(ligas)} ligas...")
    
    for liga in ligas:
        liga_id = liga['id']
        liga_nome = liga['nome']
        temporada = liga['temporada_atual']
        
        if not temporada:
            print(f"⚠️ Liga {liga_nome} sem temporada atual definida")
            continue
        
        print(f"\n🏆 Processando liga: {liga_nome} (ID: {liga_id}, Temporada: {temporada})")
        
        # Buscar times da liga
        times_api = buscar_times_liga_api(liga_id, temporada)
        
        if not times_api:
            print(f"  ⚠️ Nenhum time encontrado para esta liga")
            continue
        
        print(f"  📋 {len(times_api)} times encontrados")
        
        times_novos_liga = 0
        vinculos_novos_liga = 0
        
        for time_data in times_api:
            time_info = time_data.get('team', {})
            time_id = time_info.get('id')
            
            if not time_id:
                continue
            
            # Inserir ou atualizar time
            time_existia = time_id in times_banco
            if inserir_ou_atualizar_time(time_data, times_banco):
                if not time_existia:
                    times_novos_liga += 1
                    total_times_novos += 1
                else:
                    total_times_atualizados += 1
            
            # Criar vínculo time x liga x temporada
            if criar_vinculo_time_liga(time_id, liga_id, temporada, vinculos_existentes):
                vinculos_novos_liga += 1
                total_vinculos_criados += 1
        
        print(f"  ✅ {times_novos_liga} novos times, {vinculos_novos_liga} novos vínculos")
        ligas_processadas += 1
        
        # Delay entre requisições para não sobrecarregar a API
        time.sleep(0.5)
    
    # Resumo final
    print("\n📊 Resumo da sincronização:")
    print(f"✅ {ligas_processadas} ligas processadas")
    print(f"✅ {total_times_novos} novos times inseridos")
    print(f"📝 {total_times_atualizados} times atualizados")
    print(f"🔗 {total_vinculos_criados} novos vínculos criados")
    print(f"📁 Total de times no banco: {len(times_banco)}")
    print(f"📁 Total de vínculos: {len(vinculos_existentes)}")

if __name__ == "__main__":
    sincronizar_times()
