import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import os
import time
import pytz
from collections import defaultdict

from config.settings import settings

# Validar configurações (manter aqui, pois é uma validação de backend)
try:
    settings.validate()
except ValueError as e:
    # Se app.py for importado, st.error pode não ser ideal aqui.
    # Mas para fins de validação inicial do token, podemos mantê-lo.
    st.error(f"Erro de configuração: {e}")
    st.stop() # Interrompe a execução do script

# Token da API
TOKEN_API = settings.api_key
URL_BASE = "https://v3.football.api-sports.io"

# Headers para requisições
cabecalhos = {
    'X-RapidAPI-Key': TOKEN_API,
    'X-RapidAPI-Host': 'v3.football.api-sports.io'
}

# Lista de bookmakers comuns
BOOKMAKERS = {
    8: "Bet365",
    32: "Betano",
    3: "Betfair"
}

# Fuso horário de Brasília
TIMEZONE_BRASILIA = pytz.timezone('America/Sao_Paulo')


def obter_temporada_atual(data_selecionada):
    """Determina a temporada atual baseada na data selecionada"""
    ano = data_selecionada.year
    mes = data_selecionada.month

    if mes <= 7:
        return ano - 1
    else:
        return ano


@st.cache_data(ttl=300)  # Cache por 5 minutos
def buscar_jogos_por_data(data_selecionada):
    """Obtém os jogos de uma data específica"""
    url = f"{URL_BASE}/fixtures"
    parametros = {
        'date': data_selecionada,
        'status': 'NS'  # Not Started
    }

    try:
        resposta = requests.get(url, headers=cabecalhos, params=parametros)
        if resposta.status_code == 200:
            return resposta.json()
        else:
            st.error(f"Erro ao buscar jogos: {resposta.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro na requisição: {str(e)}")
        return None


@st.cache_data(ttl=300)
def buscar_todas_odds_por_data_e_bookmaker(data_selecionada, id_bookmaker):
    """Obtém todas as odds de uma data específica e bookmaker (com paginação)"""
    url = f"{URL_BASE}/odds"
    todas_odds = []
    pagina = 1
    total_pages = 1
    # st.sidebar.empty() não deve estar aqui, pois esta função é chamada do app_odds_streamlit.py
    # O placeholder_progresso deve ser passado como argumento ou gerenciado na UI.
    # Por simplicidade, vou usar um st.empty() genérico aqui, mas o ideal seria a UI gerenciar.
    placeholder_progresso = st.empty() # temporário para evitar erro aqui se executado isolado

    while True:
        parametros = {
            'date': data_selecionada,
            'bookmaker': id_bookmaker,
            'page': pagina
        }

        try:
            resposta = requests.get(url, headers=cabecalhos, params=parametros)
            if resposta.status_code == 200:
                dados = resposta.json()

                if not dados.get('response'):
                    break

                todas_odds.extend(dados['response'])

                paging = dados.get('paging', {})
                current_page = paging.get('current', 1)
                total_pages = paging.get('total', 1)

                placeholder_progresso.info(f"📊 Carregado {current_page}/{total_pages} páginas de odds")

                if current_page >= total_pages:
                    break

                pagina += 1
                time.sleep(0.1)

            else:
                st.error(f"Erro ao buscar odds na página {pagina}: {resposta.status_code}")
                break

        except Exception as e:
            st.error(f"Erro na requisição de odds (página {pagina}): {str(e)}")
            break

    placeholder_progresso.empty()

    return {
        'response': todas_odds,
        'paging': {
            'current': total_pages,
            'total': total_pages
        }
    }


@st.cache_data(ttl=1800)  # Cache por 30 minutos (estatísticas mudam menos)
def buscar_estatisticas_por_liga(league_id, season):
    """Busca estatísticas de todos os times de uma liga específica"""
    url = f"{URL_BASE}/teams/statistics"
    estatisticas_liga = {}

    url_teams = f"{URL_BASE}/teams"
    parametros_teams = {
        'league': league_id,
        'season': season
    }

    try:
        resposta_teams = requests.get(url_teams, headers=cabecalhos, params=parametros_teams)
        if resposta_teams.status_code != 200:
            st.warning(f"Erro ao buscar teams da liga {league_id}: {resposta_teams.status_code}")
            return estatisticas_liga

        dados_teams = resposta_teams.json()
        teams = dados_teams.get('response', [])

        if not teams:
            return estatisticas_liga

        total_teams = len(teams)
        progress_placeholder = st.empty()

        for idx, team_data in enumerate(teams):
            team_id = team_data['team']['id']
            team_name = team_data['team']['name']

            progress_placeholder.info(f"📊 Carregando estatísticas da liga: {idx + 1}/{total_teams} times")

            parametros = {
                'team': team_id,
                'league': league_id,
                'season': season
            }

            try:
                resposta = requests.get(url, headers=cabecalhos, params=parametros)
                if resposta.status_code == 200:
                    dados = resposta.json()
                    if dados.get('response'):
                        estatisticas_liga[team_id] = dados['response']

                time.sleep(0.05)

            except Exception as e:
                st.warning(f"Erro ao buscar estatísticas do time {team_name} (ID: {team_id}): {str(e)}")
                continue

        progress_placeholder.empty()

        return estatisticas_liga

    except Exception as e:
        st.warning(f"Erro ao buscar times da liga {league_id}: {str(e)}")
        return estatisticas_liga


def extrair_estatisticas_time(stats_data):
    """Extrai e formata as estatísticas relevantes do time como inteiros"""
    if not stats_data:
        return {
            'jogos': 0,
            'vitorias': 0,
            'derrotas': 0,
            'gols_marcados': 0,
            'gols_sofridos': 0,
            'jogos_sem_marcar': 0
        }

    try:
        fixtures = stats_data.get('fixtures', {})
        goals = stats_data.get('goals', {})
        jogos_total = fixtures.get('played', {}).get('total', 0)
        vitorias = fixtures.get('wins', {}).get('total', 0)
        derrotas = fixtures.get('loses', {}).get('total', 0)
        gols_marcados = goals.get('for', {}).get('total', {}).get('total', 0)
        gols_sofridos = goals.get('against', {}).get('total', {}).get('total', 0)
        failed_to_score = stats_data.get('failed_to_score', {})
        jogos_sem_marcar = failed_to_score.get('total', 0) if failed_to_score else 0

        return {
            'jogos': int(jogos_total or 0),
            'vitorias': int(vitorias or 0),
            'derrotas': int(derrotas or 0),
            'gols_marcados': int(gols_marcados or 0),
            'gols_sofridos': int(gols_sofridos or 0),
            'jogos_sem_marcar': int(jogos_sem_marcar or 0)
        }
    except Exception as e:
        st.warning(f"Erro ao extrair estatísticas: {str(e)}")
        return {
            'jogos': 0,
            'vitorias': 0,
            'derrotas': 0,
            'gols_marcados': 0,
            'gols_sofridos': 0,
            'jogos_sem_marcar': 0
        }


def converter_para_horario_brasilia(data_utc_str):
    """Converte horário UTC para horário de Brasília"""
    try:
        data_utc = datetime.fromisoformat(data_utc_str.replace('Z', '+00:00'))
        data_brasilia = data_utc.astimezone(TIMEZONE_BRASILIA)
        return data_brasilia.strftime('%H:%M')
    except Exception as e:
        return data_utc_str


def extrair_melhor_odd_gols(valores):
    """Extrai a melhor odd de gols disponível (Over 0.5, 1.0, 1.5, etc.)"""
    opcoes_over = ['Over 0.5', 'Over 1.0', 'Over 1.5', 'Over 2.0', 'Over 2.5']

    for opcao in opcoes_over:
        for valor in valores:
            valor_str = str(valor.get('value', ''))
            if opcao in valor_str:
                legenda = f"Mais de {opcao.split(' ')[1]}"
                return valor.get('odd'), legenda
    return None, None


def extrair_odds_por_id(dados_odds, id_aposta_desejado):
    """Extrai odds específicas por ID da aposta"""
    odds_extraidas = {}

    if not dados_odds or 'bookmakers' not in dados_odds:
        return odds_extraidas

    casas_apostas = dados_odds['bookmakers']
    if not casas_apostas:
        return odds_extraidas

    apostas = casas_apostas[0]['bets']

    for aposta in apostas:
        if aposta.get('id') == id_aposta_desejado:
            valores = aposta.get('values', [])

            if id_aposta_desejado == 1: # Match Winner
                for valor in valores:
                    if valor.get('value') == 'Home':
                        odds_extraidas['casa'] = valor.get('odd')
                    elif valor.get('value') == 'Draw':
                        odds_extraidas['empate'] = valor.get('odd')
                    elif valor.get('value') == 'Away':
                        odds_extraidas['fora'] = valor.get('odd')

            elif id_aposta_desejado == 16: # Home Team Goals
                odd, legenda = extrair_melhor_odd_gols(valores)
                if odd:
                    odds_extraidas['gols_casa'] = odd
                    odds_extraidas['legenda_casa'] = legenda

            elif id_aposta_desejado == 17: # Away Team Goals
                odd, legenda = extrair_melhor_odd_gols(valores)
                if odd:
                    odds_extraidas['gols_fora'] = odd
                    odds_extraidas['legenda_fora'] = legenda
            break
    return odds_extraidas


def verificar_selecao_automatica(row):
    """Verifica se uma linha deve ser selecionada automaticamente"""
    try:
        odd_casa = row.get('odd_casa')
        if not odd_casa or float(odd_casa) <= 1.5:
            return False

        odd_gols_fora = row.get('odd_gols_fora')
        legenda_gols_fora = row.get('legenda_gols_fora')

        if not odd_gols_fora or not legenda_gols_fora:
            return False

        if "0.5" not in legenda_gols_fora or float(odd_gols_fora) <= 1.5:
            return False

        return True
    except (ValueError, TypeError):
        return False


def processar_dados_jogos_e_odds(dados_jogos, dados_odds, liga_selecionada=None, filtrar_sem_odds_gols=False):
    """Processa e combina dados dos jogos com suas odds (SEM estatísticas inicialmente)"""
    if not dados_jogos or 'response' not in dados_jogos:
        return pd.DataFrame()

    if not dados_odds or 'response' not in dados_odds:
        # Removendo st.warning aqui para que a UI em app_odds_streamlit.py gerencie
        return pd.DataFrame()

    mapa_odds = {}
    for odd_item in dados_odds['response']:
        fixture_id = odd_item['fixture']['id']
        mapa_odds[fixture_id] = odd_item

    lista_jogos = []

    for jogo in dados_jogos['response']:
        try:
            nome_liga = jogo['league']['name']
            pais = jogo['league']['country']

            if liga_selecionada and liga_selecionada != "Todas" and nome_liga != liga_selecionada:
                continue

            id_jogo = jogo['fixture']['id']
            horario_formatado = converter_para_horario_brasilia(jogo['fixture']['date'])

            info_jogo = {
                'id_jogo': id_jogo,
                'liga': nome_liga,
                'país': pais,
                'season': jogo['league']['season'],
                'league_id': jogo['league']['id'],
                'team_home_id': jogo['teams']['home']['id'],
                'team_away_id': jogo['teams']['away']['id'],
                'horario': horario_formatado,
                'time_casa': jogo['teams']['home']['name'],
                'time_fora': jogo['teams']['away']['name'],
                'status': jogo['fixture']['status']['long'],
                'odd_casa': None,
                'odd_empate': None,
                'odd_fora': None,
                'odd_gols_casa': None,
                'legenda_gols_casa': None,
                'odd_gols_fora': None,
                'legenda_gols_fora': None
            }

            if id_jogo in mapa_odds:
                dados_odds_jogo = mapa_odds[id_jogo]

                odds_resultado = extrair_odds_por_id(dados_odds_jogo, 1)
                info_jogo.update({
                    'odd_casa': odds_resultado.get('casa'),
                    'odd_empate': odds_resultado.get('empate'),
                    'odd_fora': odds_resultado.get('fora')
                })

                #info_jogo.update(odds_resultado) # Adiciona odd_casa, odd_empate, odd_fora

                odds_gols_casa = extrair_odds_por_id(dados_odds_jogo, 16)
                info_jogo['odd_gols_casa'] = odds_gols_casa.get('gols_casa')
                info_jogo['legenda_gols_casa'] = odds_gols_casa.get('legenda_casa')

                odds_gols_fora = extrair_odds_por_id(dados_odds_jogo, 17)
                info_jogo['odd_gols_fora'] = odds_gols_fora.get('gols_fora')
                info_jogo['legenda_gols_fora'] = odds_gols_fora.get('legenda_fora')

            if filtrar_sem_odds_gols:
                if not (info_jogo['odd_gols_casa'] and info_jogo['odd_gols_fora']):
                    continue

            info_jogo['selecao_automatica'] = verificar_selecao_automatica(info_jogo)

            lista_jogos.append(info_jogo)

        except Exception as e:
            st.warning(f"Erro ao processar jogo {jogo.get('fixture', {}).get('id', 'desconhecido')}: {str(e)}")
            continue

    return pd.DataFrame(lista_jogos)


@st.cache_data(ttl=3600) # Cache mais longo para estatísticas
def buscar_estatisticas_para_jogos_selecionados(df_jogos_original, jogos_selecionados):
    """Busca e adiciona estatísticas aos jogos selecionados no DataFrame original."""
    if not jogos_selecionados:
        return df_jogos_original.assign(
            jogos='N/A', vitorias='N/A', derrotas='N/A',
            gols_marcados='N/A', gols_sofridos='N/A', jogos_sem_marcar='N/A'
        )

    # Criar uma cópia do DataFrame original para modificação
    df_com_stats = df_jogos_original.copy()

    # Garantir que as colunas de estatísticas existam, inicializando com N/A
    for col in ['jogos', 'vitorias', 'derrotas', 'gols_marcados', 'gols_sofridos', 'jogos_sem_marcar']:
        if col not in df_com_stats.columns:
            df_com_stats[col] = 'N/A'

    # Identificar ligas únicas dos jogos selecionados
    ligas_para_buscar = {}
    for _, jogo in df_jogos_original[df_jogos_original['id_jogo'].isin(jogos_selecionados)].iterrows():
        league_id = jogo['league_id']
        season = jogo['season']
        nome_liga = jogo['liga']

        if league_id not in ligas_para_buscar:
            ligas_para_buscar[league_id] = {'nome': nome_liga, 'season': season}

    st.info(f"🔄 Carregando estatísticas de {len(ligas_para_buscar)} liga(s) para {len(jogos_selecionados)} jogo(s) selecionado(s)...")

    cache_estatisticas = {}
    for league_id, info_liga in ligas_para_buscar.items():
        season = info_liga['season']
        nome_liga = info_liga['nome']
        with st.spinner(f"Carregando estatísticas da liga: {nome_liga} (Temporada {season})"):
            estatisticas_liga = buscar_estatisticas_por_liga(league_id, season)
            cache_estatisticas.update(estatisticas_liga)
        time.sleep(0.1)

    for index, row in df_com_stats.iterrows():
        if row['id_jogo'] in jogos_selecionados:
            team_home_id = row['team_home_id']
            team_away_id = row['team_away_id']

            stats_home = cache_estatisticas.get(team_home_id)
            stats_home_formatted = extrair_estatisticas_time(stats_home)

            stats_away = cache_estatisticas.get(team_away_id)
            stats_away_formatted = extrair_estatisticas_time(stats_away)

            df_com_stats.loc[index, 'jogos'] = f"{stats_home_formatted['jogos']} - {stats_away_formatted['jogos']}"
            df_com_stats.loc[index, 'vitorias'] = f"{stats_home_formatted['vitorias']} - {stats_away_formatted['vitorias']}"
            df_com_stats.loc[index, 'derrotas'] = f"{stats_home_formatted['derrotas']} - {stats_away_formatted['derrotas']}"
            df_com_stats.loc[index, 'gols_marcados'] = f"{stats_home_formatted['gols_marcados']} - {stats_away_formatted['gols_marcados']}"
            df_com_stats.loc[index, 'gols_sofridos'] = f"{stats_home_formatted['gols_sofridos']} - {stats_away_formatted['gols_sofridos']}"
            df_com_stats.loc[index, 'jogos_sem_marcar'] = f"{stats_home_formatted['jogos_sem_marcar']} - {stats_away_formatted['jogos_sem_marcar']}"
        else:
            # Para jogos NÃO selecionados, garantir que as colunas de estatísticas sejam 'N/A'
            df_com_stats.loc[index, ['jogos', 'vitorias', 'derrotas',
                                      'gols_marcados', 'gols_sofridos',
                                      'jogos_sem_marcar']] = 'N/A'

    return df_com_stats