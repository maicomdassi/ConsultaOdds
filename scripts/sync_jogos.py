import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime, date
import time
from config.database import supabase
from config.settings import settings

# Headers para requisições
cabecalhos = {
    'X-RapidAPI-Key': settings.api_key,
    'X-RapidAPI-Host': 'v3.football.api-sports.io'
}


def verificar_time_existe(time_id):
    """Verifica se um time existe no banco de dados"""
    try:
        resultado = supabase.table('times').select("id").eq('id', time_id).execute()
        return len(resultado.data) > 0
    except Exception as e:
        print(f"❌ Erro ao verificar time {time_id}: {str(e)}")
        return False


def buscar_time_api(time_id):
    """Busca informações de um time específico na API"""
    url = "https://v3.football.api-sports.io/teams"
    parametros = {
        'id': time_id
    }

    try:
        resposta = requests.get(url, headers=cabecalhos, params=parametros)
        if resposta.status_code == 200:
            dados = resposta.json()
            times = dados.get('response', [])
            if times:
                return times[0]  # Retorna o primeiro (e único) time
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar time {time_id} da API: {str(e)}")
        return None


def salvar_time_banco(time_data):
    """Salva um time no banco de dados"""
    try:
        time_info = time_data.get('team', {})

        dados_time = {
            'id': time_info.get('id'),
            'nome': time_info.get('name'),
            'codigo': time_info.get('code'),
            'logo_url': time_info.get('logo'),
            'ano_fundacao': time_info.get('founded'),
            'ativo': True,
            'atualizado_em': datetime.now().isoformat()
        }

        # Verificar se já existe (pode ter sido criado por outro processo)
        if not verificar_time_existe(dados_time['id']):
            supabase.table('times').insert(dados_time).execute()
            print(f"   ✅ Time {dados_time['nome']} (ID: {dados_time['id']}) salvo no banco")
            return True
        return False
    except Exception as e:
        print(f"   ❌ Erro ao salvar time: {str(e)}")
        return False


def garantir_time_existe(time_id, time_nome=None):
    """Garante que um time existe no banco, buscando da API se necessário"""
    if verificar_time_existe(time_id):
        return True

    print(f"   ⚠️ Time {time_nome if time_nome else time_id} não encontrado no banco. Buscando na API...")

    # Buscar time da API
    time_data = buscar_time_api(time_id)
    if time_data:
        # Salvar no banco
        if salvar_time_banco(time_data):
            time.sleep(0.2)  # Pequeno delay para não sobrecarregar a API
            return True

    print(f"   ❌ Não foi possível obter dados do time {time_id}")
    return False


def verificar_liga_existe(liga_id):
    """Verifica se uma liga existe no banco de dados"""
    try:
        resultado = supabase.table('ligas').select("id").eq('id', liga_id).execute()
        return len(resultado.data) > 0
    except Exception as e:
        print(f"❌ Erro ao verificar liga {liga_id}: {str(e)}")
        return False


def salvar_liga_banco(league_data, country_name="World"):
    """Salva uma liga no banco de dados"""
    try:
        # Buscar ID do país
        pais_id = None
        if country_name and country_name != "World":
            resultado = supabase.table('paises').select("id").eq('nome', country_name).execute()
            if resultado.data:
                pais_id = resultado.data[0]['id']

        dados_liga = {
            'id': league_data.get('id'),
            'nome': league_data.get('name'),
            'tipo': league_data.get('type'),
            'logo_url': league_data.get('logo'),
            'pais_id': pais_id,
            'ativo': True,
            'atualizado_em': datetime.now().isoformat()
        }

        supabase.table('ligas').insert(dados_liga).execute()
        print(f"   ✅ Liga {dados_liga['nome']} (ID: {dados_liga['id']}) salva no banco")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao salvar liga: {str(e)}")
        return False


def verificar_jogos_existentes(data_busca):
    """Verifica se já existem jogos salvos para a data especificada"""
    try:
        resultado = supabase.table('jogos').select("id").eq('data', data_busca).execute()
        return len(resultado.data)
    except Exception as e:
        print(f"❌ Erro ao verificar jogos existentes: {str(e)}")
        return 0


def buscar_jogos_api(data_busca):
    """Busca todos os jogos de uma data específica na API"""
    url = "https://v3.football.api-sports.io/fixtures"
    parametros = {
        'date': data_busca
    }

    try:
        print(f"🔄 Buscando jogos da API para {data_busca}...")
        resposta = requests.get(url, headers=cabecalhos, params=parametros)

        if resposta.status_code == 200:
            dados = resposta.json()
            jogos = dados.get('response', [])
            print(f"✅ {len(jogos)} jogos encontrados na API")
            return jogos
        else:
            print(f"❌ Erro ao buscar jogos: {resposta.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")
        return []


def salvar_jogos_banco(jogos, data_busca):
    """Salva os jogos no banco de dados"""
    jogos_salvos = 0
    jogos_atualizados = 0
    jogos_com_erro = 0
    times_novos = 0
    ligas_novas = 0

    print(f"\n📝 Processando {len(jogos)} jogos...")

    for idx, jogo in enumerate(jogos):
        try:
            fixture = jogo['fixture']
            teams = jogo['teams']
            league = jogo['league']
            venue = jogo.get('fixture', {}).get('venue', {})
            score = jogo.get('score', {})
            country = jogo.get('league', {}).get('country', 'World')

            # IDs dos times e liga
            time_casa_id = teams['home']['id']
            time_fora_id = teams['away']['id']
            liga_id = league['id']

            # Verificar e criar liga se necessário
            if not verificar_liga_existe(liga_id):
                print(f"\n   📋 Liga {league['name']} não encontrada. Criando...")
                if salvar_liga_banco(league, country):
                    ligas_novas += 1

            # Verificar e buscar times se necessário
            time_casa_nome = teams['home']['name']
            time_fora_nome = teams['away']['name']

            if not verificar_time_existe(time_casa_id):
                if garantir_time_existe(time_casa_id, time_casa_nome):
                    times_novos += 1
                else:
                    print(f"   ❌ Pulando jogo {fixture['id']} - Time casa não encontrado")
                    jogos_com_erro += 1
                    continue

            if not verificar_time_existe(time_fora_id):
                if garantir_time_existe(time_fora_id, time_fora_nome):
                    times_novos += 1
                else:
                    print(f"   ❌ Pulando jogo {fixture['id']} - Time fora não encontrado")
                    jogos_com_erro += 1
                    continue

            # Determinar status mais detalhado
            status_short = fixture.get('status', {}).get('short', 'NS')
            status_long = fixture.get('status', {}).get('long', 'Not Started')

            # Extrair gols se o jogo já foi jogado
            gols_casa = None
            gols_fora = None
            if status_short in ['FT', 'AET', 'PEN', 'SUSP', 'INT']:  # Jogo finalizado ou suspenso
                gols_casa = score.get('fulltime', {}).get('home')
                gols_fora = score.get('fulltime', {}).get('away')
                # Se não tiver fulltime, tentar halftime
                if gols_casa is None:
                    gols_casa = score.get('halftime', {}).get('home')
                    gols_fora = score.get('halftime', {}).get('away')

            dados_jogo = {
                'id': fixture['id'],
                'data': data_busca,
                'horario': fixture['date'],
                'time_casa_id': time_casa_id,
                'time_fora_id': time_fora_id,
                'liga_id': liga_id,
                'temporada': league['season'],
                'status': status_short,
                'rodada': league.get('round'),
                'arbitro': fixture.get('referee'),
                'estadio': venue.get('name'),
                'cidade': venue.get('city'),
                'gols_casa': gols_casa,
                'gols_fora': gols_fora,
                'atualizado_em': datetime.now().isoformat()
            }

            # Verificar se o jogo já existe
            existe = supabase.table('jogos').select("id").eq('id', fixture['id']).execute()

            if existe.data:
                # Atualizar jogo existente
                supabase.table('jogos').update(dados_jogo).eq('id', fixture['id']).execute()
                jogos_atualizados += 1
            else:
                # Inserir novo jogo
                supabase.table('jogos').insert(dados_jogo).execute()
                jogos_salvos += 1

            # Mostrar progresso a cada 10 jogos
            if (idx + 1) % 10 == 0:
                print(f"   📊 Progresso: {idx + 1}/{len(jogos)} jogos processados")

        except Exception as e:
            print(f"❌ Erro ao salvar jogo {fixture.get('id')}: {str(e)}")
            jogos_com_erro += 1

    return jogos_salvos, jogos_atualizados, jogos_com_erro, times_novos, ligas_novas


def sincronizar_jogos_data(data_busca=None):
    """Sincroniza jogos de uma data específica"""
    if data_busca is None:
        data_busca = date.today().strftime('%Y-%m-%d')

    print(f"\n🚀 Iniciando sincronização de jogos para {data_busca}...")

    # Verificar se já existem jogos para esta data
    jogos_existentes = verificar_jogos_existentes(data_busca)
    if jogos_existentes > 0:
        print(f"ℹ️ Já existem {jogos_existentes} jogos salvos para esta data.")
        resposta = input("Deseja atualizar os dados? (s/n): ")
        if resposta.lower() != 's':
            print("❌ Sincronização cancelada.")
            return

    # Buscar jogos da API
    jogos = buscar_jogos_api(data_busca)

    if not jogos:
        print("❌ Nenhum jogo encontrado para esta data.")
        return

    # Salvar no banco
    salvos, atualizados, erros, times_novos, ligas_novas = salvar_jogos_banco(jogos, data_busca)

    # Resumo
    print("\n📊 Resumo da sincronização:")
    print(f"✅ {salvos} novos jogos salvos")
    print(f"📝 {atualizados} jogos atualizados")
    print(f"❌ {erros} jogos com erro")
    print(f"👥 {times_novos} novos times adicionados")
    print(f"🏆 {ligas_novas} novas ligas adicionadas")
    print(f"📁 Total processado: {len(jogos)} jogos")

    if erros > 0:
        print(f"\n⚠️ Alguns jogos não foram salvos devido a erros. Verifique os logs acima.")


if __name__ == "__main__":
    # Permitir passar data como argumento
    if len(sys.argv) > 1:
        data_param = sys.argv[1]
        try:
            # Validar formato da data
            datetime.strptime(data_param, '%Y-%m-%d')
            sincronizar_jogos_data(data_param)
        except ValueError:
            print("❌ Formato de data inválido. Use YYYY-MM-DD (ex: 2025-01-06)")
    else:
        # Usar data de hoje
        sincronizar_jogos_data()