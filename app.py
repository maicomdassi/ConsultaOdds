import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import os
import time
import pytz

from config.settings import settings

# Validar configurações
try:
    settings.validate()
except ValueError as e:
    st.error(f"Erro de configuração: {e}")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="Odds de Futebol",
    page_icon="⚽",
    layout="wide"
)

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
    placeholder_progresso = st.sidebar.empty()

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

                # Verificar se há dados na resposta
                if not dados.get('response'):
                    break

                # Adicionar dados desta página
                todas_odds.extend(dados['response'])

                # Verificar informações de paginação
                paging = dados.get('paging', {})
                current_page = paging.get('current', 1)
                total_pages = paging.get('total', 1)

                # Atualizar mensagem de progresso
                placeholder_progresso.info(f"📊 Carregado {current_page}/{total_pages} páginas")

                # Se chegou na última página, parar
                if current_page >= total_pages:
                    break

                # Próxima página
                pagina += 1

                # Pequeno delay para não sobrecarregar a API
                time.sleep(0.1)

            else:
                st.error(f"Erro ao buscar odds na página {pagina}: {resposta.status_code}")
                break

        except Exception as e:
            st.error(f"Erro na requisição de odds (página {pagina}): {str(e)}")
            break

    # Limpar mensagem de progresso
    placeholder_progresso.empty()

    # Retornar no formato esperado
    return {
        'response': todas_odds,
        'paging': {
            'current': total_pages,
            'total': total_pages
        }
    }


def converter_para_horario_brasilia(data_utc_str):
    """Converte horário UTC para horário de Brasília"""
    try:
        # Parse da data UTC
        data_utc = datetime.fromisoformat(data_utc_str.replace('Z', '+00:00'))

        # Converter para fuso horário de Brasília
        data_brasilia = data_utc.astimezone(TIMEZONE_BRASILIA)

        # Retornar formatado
        return data_brasilia.strftime('%H:%M')
    except Exception as e:
        return data_utc_str


def extrair_melhor_odd_gols(valores, tipo_time):
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

            # ID 1: Match Winner (Resultado Final)
            if id_aposta_desejado == 1:
                for valor in valores:
                    if valor.get('value') == 'Home':
                        odds_extraidas['casa'] = valor.get('odd')
                    elif valor.get('value') == 'Draw':
                        odds_extraidas['empate'] = valor.get('odd')
                    elif valor.get('value') == 'Away':
                        odds_extraidas['fora'] = valor.get('odd')

            # ID 16: Home Team Goals (Gols Casa)
            elif id_aposta_desejado == 16:
                odd, legenda = extrair_melhor_odd_gols(valores, 'casa')
                if odd:
                    odds_extraidas['gols_casa'] = odd
                    odds_extraidas['legenda_casa'] = legenda

            # ID 17: Away Team Goals (Gols Fora)
            elif id_aposta_desejado == 17:
                odd, legenda = extrair_melhor_odd_gols(valores, 'fora')
                if odd:
                    odds_extraidas['gols_fora'] = odd
                    odds_extraidas['legenda_fora'] = legenda

            break

    return odds_extraidas


def processar_dados_jogos_e_odds(dados_jogos, dados_odds, liga_selecionada=None, filtrar_sem_odds_gols=False):
    """Processa e combina dados dos jogos com suas odds"""
    if not dados_jogos or 'response' not in dados_jogos:
        return pd.DataFrame()

    if not dados_odds or 'response' not in dados_odds:
        st.warning("Dados de odds não disponíveis")
        return pd.DataFrame()

    # Criar dicionário de odds por fixture_id para acesso rápido
    mapa_odds = {}
    for odd_item in dados_odds['response']:
        fixture_id = odd_item['fixture']['id']
        mapa_odds[fixture_id] = odd_item

    lista_jogos = []

    for jogo in dados_jogos['response']:
        try:
            nome_liga = jogo['league']['name']
            pais = jogo['league']['country']

            # Filtro por liga se selecionado
            if liga_selecionada and liga_selecionada != "Todas" and nome_liga != liga_selecionada:
                continue

            id_jogo = jogo['fixture']['id']

            # Extrair horário do jogo convertido para Brasília
            horario_formatado = converter_para_horario_brasilia(jogo['fixture']['date'])

            info_jogo = {
                'id_jogo': id_jogo,
                'liga': nome_liga,
                'país': pais,
                'horario': horario_formatado,
                'time_casa': jogo['teams']['home']['name'],
                'time_fora': jogo['teams']['away']['name'],
                'status': jogo['fixture']['status']['long']
            }

            # Buscar odds para este jogo no mapa
            if id_jogo in mapa_odds:
                dados_odds_jogo = mapa_odds[id_jogo]

                # Extrair odds de resultado final (ID 1)
                odds_resultado = extrair_odds_por_id(dados_odds_jogo, 1)
                info_jogo.update({
                    'odd_casa': odds_resultado.get('casa'),
                    'odd_empate': odds_resultado.get('empate'),
                    'odd_fora': odds_resultado.get('fora')
                })

                # Extrair odds de gols casa (ID 16)
                odds_gols_casa = extrair_odds_por_id(dados_odds_jogo, 16)
                info_jogo['odd_gols_casa'] = odds_gols_casa.get('gols_casa')
                info_jogo['legenda_gols_casa'] = odds_gols_casa.get('legenda_casa')

                # Extrair odds de gols fora (ID 17)
                odds_gols_fora = extrair_odds_por_id(dados_odds_jogo, 17)
                info_jogo['odd_gols_fora'] = odds_gols_fora.get('gols_fora')
                info_jogo['legenda_gols_fora'] = odds_gols_fora.get('legenda_fora')

            # Aplicar filtro de odds de gols se solicitado
            if filtrar_sem_odds_gols:
                if not (info_jogo.get('odd_gols_casa') and info_jogo.get('odd_gols_fora')):
                    continue

            lista_jogos.append(info_jogo)

        except Exception as e:
            st.warning(f"Erro ao processar jogo {jogo.get('fixture', {}).get('id', 'desconhecido')}: {str(e)}")
            continue

    return pd.DataFrame(lista_jogos)


def main():
    st.title("⚽ Odds de Futebol")
    st.markdown("---")

    # Sidebar para filtros
    st.sidebar.header("Filtros")

    # Filtro de data
    data_selecionada = st.sidebar.date_input(
        "Selecionar Data:",
        value=date.today(),
        format="DD/MM/YYYY"
    )
    data_str = data_selecionada.strftime('%Y-%m-%d')

    # Filtro de bookmaker
    opcoes_bookmakers = list(BOOKMAKERS.keys())
    nomes_bookmakers = [f"{id} - {nome}" for id, nome in BOOKMAKERS.items()]

    indice_bookmaker = st.sidebar.selectbox(
        "Selecionar Bookmaker:",
        range(len(opcoes_bookmakers)),
        format_func=lambda x: nomes_bookmakers[x],
        index=1  # Padrão: Betano (ID 32)
    )
    id_bookmaker_selecionado = opcoes_bookmakers[indice_bookmaker]

    # Filtro para mostrar apenas jogos com odds de gols
    filtrar_sem_odds = st.sidebar.checkbox(
        "Mostrar apenas jogos com odds de gols",
        value=False
    )

    # NOVA SEÇÃO: Configurações de visualização da tabela
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Configurações da Tabela")

    # Opção para exibir todos os registros ou limitar
    mostrar_todos = st.sidebar.checkbox(
        "Mostrar todos os registros (sem paginação)",
        value=True,
        help="Quando marcado, exibe todos os jogos em uma única tabela"
    )

    # Se não mostrar todos, permitir escolher quantidade
    if not mostrar_todos:
        registros_por_pagina = st.sidebar.selectbox(
            "Máximo de registros a exibir:",
            options=[10, 25, 50, 75, 100],
            index=1  # Padrão: 25
        )
    else:
        registros_por_pagina = None

    # Controle da altura da tabela
    altura_tabela = st.sidebar.selectbox(
        "Altura da tabela:",
        options=["Auto", "Pequena (300px)", "Média (500px)", "Grande (700px)", "Extra Grande (900px)"],
        index=0,
        help="Controla a altura máxima da tabela"
    )

    # Botão para atualizar dados
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    # Mostrar informações dos filtros selecionados
    st.sidebar.markdown("---")
    st.sidebar.write(f"**Data:** {data_selecionada.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"**Bookmaker:** {BOOKMAKERS[id_bookmaker_selecionado]}")
    st.sidebar.write(f"**Fuso Horário:** Brasília (UTC-3)")

    # Carregar dados dos jogos e odds
    with st.spinner("Carregando jogos..."):
        dados_jogos = buscar_jogos_por_data(data_str)

    # Limpar indicador de carregamento de odds na sidebar
    placeholder_info = st.sidebar.empty()

    with st.spinner("Carregando todas as odds (com paginação)..."):
        dados_odds = buscar_todas_odds_por_data_e_bookmaker(data_str, id_bookmaker_selecionado)

    # Limpar informações de paginação da sidebar
    placeholder_info.empty()

    if not dados_jogos:
        st.error("Não foi possível carregar os dados dos jogos.")
        return

    # Extrair ligas disponíveis
    ligas = set()
    for jogo in dados_jogos['response']:
        ligas.add(jogo['league']['name'])

    ligas = sorted(list(ligas))
    ligas.insert(0, "Todas")

    # Filtro de liga
    liga_selecionada = st.sidebar.selectbox("Selecionar Liga:", ligas)

    # Processar dados
    with st.spinner("Processando dados..."):
        df = processar_dados_jogos_e_odds(dados_jogos, dados_odds, liga_selecionada, filtrar_sem_odds)

    if df.empty:
        st.warning("Nenhum jogo encontrado para os filtros selecionados.")
        return

    # Aplicar limite de registros se necessário
    df_exibir = df.copy()
    total_registros = len(df_exibir)

    if not mostrar_todos and registros_por_pagina:
        df_exibir = df_exibir.head(registros_por_pagina)
        registros_exibidos = len(df_exibir)
    else:
        registros_exibidos = total_registros

    # Exibir estatísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if mostrar_todos:
            st.metric("Total de Jogos", total_registros)
        else:
            st.metric("Jogos Exibidos", f"{registros_exibidos}/{total_registros}")
    with col2:
        st.metric("Ligas", df['liga'].nunique())
    with col3:
        st.metric("Países", df['país'].nunique())
    with col4:
        jogos_com_odds_gols = df[(df['odd_gols_casa'].notna()) & (df['odd_gols_fora'].notna())]
        st.metric("Com Odds de Gols", len(jogos_com_odds_gols))

    # Mostrar informações sobre as odds carregadas
    if dados_odds and 'response' in dados_odds:
        total_odds = len(dados_odds['response'])
        st.info(f"📊 **Total de odds carregadas:** {total_odds} (incluindo todas as páginas)")

    st.markdown("---")

    # Preparar dados para tabela
    df_tabela = df_exibir.copy()

    # Formatar colunas de odds com legendas
    if 'legenda_gols_casa' in df_tabela.columns:
        df_tabela['Gols Casa'] = df_tabela.apply(
            lambda row: f"{row['odd_gols_casa']} ({row['legenda_gols_casa']})"
            if pd.notna(row['odd_gols_casa']) and pd.notna(row['legenda_gols_casa'])
            else "N/A", axis=1
        )
    else:
        df_tabela['Gols Casa'] = df_tabela['odd_gols_casa'].fillna("N/A")

    if 'legenda_gols_fora' in df_tabela.columns:
        df_tabela['Gols Fora'] = df_tabela.apply(
            lambda row: f"{row['odd_gols_fora']} ({row['legenda_gols_fora']})"
            if pd.notna(row['odd_gols_fora']) and pd.notna(row['legenda_gols_fora'])
            else "N/A", axis=1
        )
    else:
        df_tabela['Gols Fora'] = df_tabela['odd_gols_fora'].fillna("N/A")

    # Selecionar e renomear colunas para exibição
    colunas_exibir = {
        'horario': 'Horário (BR)',
        'liga': 'Liga',
        'time_casa': 'Time Casa',
        'time_fora': 'Time Fora',
        'odd_casa': 'Odd Casa',
        'odd_empate': 'Odd Empate',
        'odd_fora': 'Odd Fora',
        'Gols Casa': 'Gols Casa',
        'Gols Fora': 'Gols Fora'
    }

    # Criar DataFrame final para exibição
    df_final = df_tabela[list(colunas_exibir.keys())].rename(columns=colunas_exibir)
    df_final = df_final.fillna("N/A")

    # Definir altura da tabela baseado na seleção
    altura_config = None
    if altura_tabela == "Pequena (300px)":
        altura_config = 300
    elif altura_tabela == "Média (500px)":
        altura_config = 500
    elif altura_tabela == "Grande (700px)":
        altura_config = 700
    elif altura_tabela == "Extra Grande (900px)":
        altura_config = 900

    # Exibir tabela principal
    st.subheader("📊 Tabela de Jogos e Odds")

    # Mostrar informação sobre exibição se limitado
    if not mostrar_todos:
        st.info(
            f"📋 Exibindo {registros_exibidos} de {total_registros} jogos. Para ver todos, marque 'Mostrar todos os registros' na barra lateral.")

    # Exibir tabela com configurações
    st.dataframe(
        df_final,
        use_container_width=True,
        hide_index=True,
        height=altura_config
    )

    # Informações adicionais
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.info(
            "💡 **Legendas das Odds de Gols:**\n- Mais de 0.5: Time marca pelo menos 1 gol\n- Mais de 1.0: Time marca pelo menos 2 gols\n- E assim por diante...")

    with col2:
        st.info(
            f"🏢 **Bookmaker:** {BOOKMAKERS[id_bookmaker_selecionado]}\n📅 **Data:** {data_selecionada.strftime('%d/%m/%Y')}\n🕐 **Horários:** Brasília (UTC-3)")


if __name__ == "__main__":
    main()