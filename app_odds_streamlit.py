import streamlit as st
import pandas as pd
from datetime import datetime, date
import pytz

# Importe apenas as funções necessárias do app.py
from app import (
    buscar_jogos_por_data,
    buscar_todas_odds_por_data_e_bookmaker,
    processar_dados_jogos_e_odds,
    buscar_estatisticas_para_jogos_selecionados, # Nova função importada
    BOOKMAKERS # Importa o dicionário de bookmakers
)

# Configuração da página (DEVE SER A PRIMEIRA CHAMADA STREAMLIT)
st.set_page_config(
    page_title="Odds de Futebol",
    page_icon="⚽",
    layout="wide"
)

# Fuso horário de Brasília (re-declarado aqui para uso na UI, se necessário)
TIMEZONE_BRASILIA = pytz.timezone('America/Sao_Paulo')

# Inicializar controles no session_state
if 'dados_carregados' not in st.session_state:
    st.session_state.dados_carregados = False
if 'dados_jogos' not in st.session_state:
    st.session_state.dados_jogos = None
if 'dados_odds' not in st.session_state:
    st.session_state.dados_odds = None
if 'df_processado' not in st.session_state:
    st.session_state.df_processado = pd.DataFrame()
if 'jogos_selecionados' not in st.session_state:
    st.session_state.jogos_selecionados = []
if 'estatisticas_carregadas' not in st.session_state:
    st.session_state.estatisticas_carregadas = False


st.title("⚽ Odds de Futebol - Seleção de Estatísticas")
st.markdown("---")

# Sidebar para filtros
st.sidebar.header("🔧 Configurações e Filtros")

# Filtros de entrada
data_selecionada = st.sidebar.date_input("Selecionar Data:", value=date.today(), format="DD/MM/YYYY")
data_str = data_selecionada.strftime('%Y-%m-%d')

opcoes_bookmakers = list(BOOKMAKERS.keys())
nomes_bookmakers = [f"{id} - {nome}" for id, nome in BOOKMAKERS.items()]
indice_bookmaker = st.sidebar.selectbox("Selecionar Bookmaker:", range(len(opcoes_bookmakers)),
                                        format_func=lambda x: nomes_bookmakers[x], index=1)
id_bookmaker = opcoes_bookmakers[indice_bookmaker]

filtrar_sem_odds = st.sidebar.checkbox("Mostrar apenas jogos com odds de gols", value=True)
mostrar_todos = st.sidebar.checkbox("Mostrar todos os registros (sem paginação)", value=True)
registros_por_pagina = None
if not mostrar_todos:
    registros_por_pagina = st.sidebar.selectbox("Máximo de registros:", [10, 25, 50, 100], index=1)

altura_tabela = st.sidebar.selectbox("Altura da Tabela:", ["Auto", "Pequena (300px)", "Média (500px)",
                                                           "Grande (700px)", "Extra Grande (900px)"], index=0)

if st.sidebar.button("🗑️ Limpar Cache"):
    st.cache_data.clear()
    st.session_state.dados_carregados = False
    st.session_state.dados_jogos = None
    st.session_state.dados_odds = None
    st.session_state.df_processado = pd.DataFrame()
    st.session_state.jogos_selecionados = []
    st.session_state.estatisticas_carregadas = False
    st.sidebar.success("Cache limpo! Reiniciando a aplicação.")
    st.rerun() # Necessário para resetar o estado da UI

st.sidebar.markdown("---")
st.sidebar.write(f"**Data:** {data_selecionada.strftime('%d/%m/%Y')}")
st.sidebar.write(f"**Bookmaker:** {BOOKMAKERS[id_bookmaker]}")
st.sidebar.write("**Fuso Horário:** Brasília (UTC-3)")


# Botão para carregar dados
st.subheader("🎮 Controle de Consultas")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.info("💡 Configure os filtros acima e clique no botão para buscar os dados da API.")
with col2:
    btn_buscar_dados = st.button("🔍 Buscar Jogos e Odds", type="primary", use_container_width=True)
with col3:
    if st.session_state.dados_carregados:
        st.success("✅ Dados carregados")
    else:
        st.warning("⏳ Dados não carregados")

# Consultar dados ao clicar no botão
if btn_buscar_dados:
    st.session_state.dados_carregados = False
    st.session_state.estatisticas_carregadas = False # Resetar estatísticas ao buscar novos dados
    st.session_state.jogos_selecionados = [] # Limpar seleções

    with st.spinner("🔄 Carregando jogos..."):
        dados_jogos = buscar_jogos_por_data(data_str)
        st.session_state.dados_jogos = dados_jogos

    if not dados_jogos:
        st.error("❌ Não foi possível carregar os dados dos jogos.")
        st.stop()

    with st.spinner("🔄 Carregando todas as odds (com paginação)..."):
        # A função buscar_todas_odds_por_data_e_bookmaker tem um st.empty() para progresso.
        # Se você quiser um controle mais fino na UI, pode passar um placeholder para ela.
        dados_odds = buscar_todas_odds_por_data_e_bookmaker(data_str, id_bookmaker)
        st.session_state.dados_odds = dados_odds

    if not dados_odds or not dados_odds.get('response'):
        st.warning("⚠️ Não foi possível carregar os dados de odds para este bookmaker e data.")
        # Não precisa st.stop() aqui, apenas exibe a mensagem

    with st.spinner("🔄 Processando dados..."):
        df = processar_dados_jogos_e_odds(st.session_state.dados_jogos, st.session_state.dados_odds, None, filtrar_sem_odds)
        st.session_state.df_processado = df

    # Inicializar seleções automáticas na primeira carga de dados
    selecoes_automaticas = df[df['selecao_automatica'] == True]['id_jogo'].tolist()
    st.session_state.jogos_selecionados = selecoes_automaticas
    if selecoes_automaticas:
        st.info(f"🎯 {len(selecoes_automaticas)} jogo(s) selecionado(s) automaticamente baseado nos critérios: Odd casa > 1.5 e Odd gols fora > 1.5 (Over 0.5)")


    st.session_state.dados_carregados = True
    st.rerun() # Recarregar a página para exibir os dados e o estado atualizados

# Se dados já estiverem carregados
if st.session_state.dados_carregados:
    df_base = st.session_state.df_processado.copy()

    if df_base.empty:
        st.warning("⚠️ Nenhum jogo encontrado para os filtros selecionados.")
        st.stop()

    ligas = sorted(df_base['liga'].unique().tolist())
    ligas.insert(0, "Todas")
    liga_selecionada = st.selectbox("🏆 Filtrar por Liga:", ligas, key="filtro_liga")

    # Aplicar filtro de liga
    if liga_selecionada != "Todas":
        df_filtrado_exibicao = df_base[df_base['liga'] == liga_selecionada].copy()
    else:
        df_filtrado_exibicao = df_base.copy()

    # Exibir estatísticas gerais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Jogos Encontrados", len(df_base))
    with col2:
        st.metric("Ligas Únicas", df_base['liga'].nunique())
    with col3:
        st.metric("Países Únicos", df_base['país'].nunique())
    with col4:
        jogos_com_odds_gols = df_base[(df_base['odd_gols_casa'].notna()) & (df_base['odd_gols_fora'].notna())]
        st.metric("Jogos com Odds de Gols", len(jogos_com_odds_gols))

    st.markdown("---")
    st.subheader("📈 Seleção de Jogos para Estatísticas")

    # Adicionar coluna de checkbox para seleção interativa
    df_filtrado_exibicao['Selecionar'] = df_filtrado_exibicao['id_jogo'].isin(st.session_state.jogos_selecionados)

    # Paginação para a tabela de exibição
    total_registros_exibicao = len(df_filtrado_exibicao)
    if not mostrar_todos and registros_por_pagina:
        df_para_data_editor = df_filtrado_exibicao.head(registros_por_pagina)
        registros_exibidos = len(df_para_data_editor)
    else:
        df_para_data_editor = df_filtrado_exibicao.copy()
        registros_exibidos = total_registros_exibicao

    st.info(f"Mostrando {registros_exibidos} de {total_registros_exibicao} jogos para seleção.")

    # Tabela interativa para seleção de jogos
    df_interativo = st.data_editor(
        df_para_data_editor[[
            'id_jogo', 'horario', 'liga', 'time_casa', 'time_fora',
            'odd_casa', 'odd_empate', 'odd_fora', 'odd_gols_casa',
            'legenda_gols_casa', 'odd_gols_fora', 'legenda_gols_fora',
            'selecao_automatica', # Manter para visualização do critério
            'Selecionar'
        ]].rename(columns={'selecao_automatica': 'Auto Seleção'}), # Renomear para melhor visualização
        column_config={
            "Selecionar": st.column_config.CheckboxColumn("Selecionar", help="Marque os jogos para buscar estatísticas"),
            "id_jogo": "ID Jogo",
            "horario": "Horário",
            "liga": "Liga",
            "time_casa": "Casa",
            "time_fora": "Fora",
            "odd_casa": "Odd Casa",
            "odd_empate": "Odd Empate",
            "odd_fora": "Odd Fora",
            "odd_gols_casa": "Odd Gols Casa",
            "legenda_gols_casa": "Legenda Gols Casa",
            "odd_gols_fora": "Odd Gols Fora",
            "legenda_gols_fora": "Legenda Gols Fora",
            "Auto Seleção": st.column_config.CheckboxColumn("Auto Seleção", help="Jogo selecionado automaticamente pelos critérios iniciais", disabled=True)
        },
        use_container_width=True,
        hide_index=True,
        key="tabela_selecao_jogos"
    )

    # Atualizar lista de jogos selecionados com base na interação do usuário
    # É importante reconstruir a lista a partir do df_interativo
    st.session_state.jogos_selecionados = df_interativo[df_interativo['Selecionar']]['id_jogo'].tolist()


    # Botões de ação para seleção
    col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)
    with col_sel1:
        if st.button("✅ Selecionar Todos Exibidos"):
            # Seleciona apenas os jogos atualmente exibidos na tabela interativa
            st.session_state.jogos_selecionados = df_para_data_editor['id_jogo'].tolist()
            st.rerun()
    with col_sel2:
        if st.button("❌ Desmarcar Todos Exibidos"):
            # Desmarca apenas os jogos atualmente exibidos na tabela interativa
            current_displayed_ids = df_para_data_editor['id_jogo'].tolist()
            st.session_state.jogos_selecionados = [
                id_jogo for id_jogo in st.session_state.jogos_selecionados
                if id_jogo not in current_displayed_ids
            ]
            st.rerun()
    with col_sel3:
        btn_buscar_stats = st.button("🔍 Buscar Estatísticas dos Selecionados", type="primary", use_container_width=True)
    with col_sel4:
        qtd_selecionados = len(st.session_state.jogos_selecionados)
        st.metric("Total Selecionados", qtd_selecionados)

    # Processamento para adicionar estatísticas
    if btn_buscar_stats:
        if st.session_state.jogos_selecionados:
            with st.spinner("🚀 Buscando e adicionando estatísticas aos jogos selecionados..."):
                # Use df_base aqui, que contém todos os jogos, para que a busca de estatísticas
                # não se limite apenas aos que estão sendo exibidos na tabela filtrada.
                df_com_stats = buscar_estatisticas_para_jogos_selecionados(df_base, st.session_state.jogos_selecionados)
                st.session_state.df_processado_com_stats = df_com_stats
            st.session_state.estatisticas_carregadas = True
            st.rerun() # Recarregar para exibir a tabela com estatísticas
        else:
            st.warning("⚠️ Nenhum jogo selecionado! Marque os jogos que deseja ver as estatísticas.")

    # Exibir a tabela final (com ou sem estatísticas)
    st.markdown("---")
    st.subheader(
        "📊 Tabela de Jogos com Estatísticas Detalhadas" if st.session_state.estatisticas_carregadas else "📊 Tabela de Jogos e Odds"
    )

    df_final_display = None
    if st.session_state.estatisticas_carregadas and 'df_processado_com_stats' in st.session_state:
        # Filtrar para exibir apenas os jogos que foram de fato selecionados E tiveram estatísticas buscadas
        df_final_display = st.session_state.df_processado_com_stats[
            st.session_state.df_processado_com_stats['id_jogo'].isin(st.session_state.jogos_selecionados)
        ].copy()

        if df_final_display.empty:
            st.warning("Nenhuma estatística encontrada para os jogos selecionados após o filtro. Ajuste suas seleções.")
            df_final_display = st.session_state.df_processado_com_stats.copy() # Mostra o dataframe completo se não houver seleção
            st.session_state.estatisticas_carregadas = False # Reseta a flag para evitar looping

    else:
        df_final_display = df_filtrado_exibicao.copy() # Exibe o dataframe filtrado sem estatísticas


    # Formatar colunas de odds com legendas (se existirem)
    if 'legenda_gols_casa' in df_final_display.columns:
        df_final_display['Gols Casa'] = df_final_display.apply(
            lambda row: f"{row['odd_gols_casa']} ({row['legenda_gols_casa']})"
            if pd.notna(row['odd_gols_casa']) and pd.notna(row['legenda_gols_casa'])
            else "N/A", axis=1
        )
    else:
        df_final_display['Gols Casa'] = df_final_display['odd_gols_casa'].fillna("N/A")

    if 'legenda_gols_fora' in df_final_display.columns:
        df_final_display['Gols Fora'] = df_final_display.apply(
            lambda row: f"{row['odd_gols_fora']} ({row['legenda_gols_fora']})"
            if pd.notna(row['odd_gols_fora']) and pd.notna(row['legenda_gols_fora'])
            else "N/A", axis=1
        )
    else:
        df_final_display['Gols Fora'] = df_final_display['odd_gols_fora'].fillna("N/A")

    # Colunas a serem exibidas na tabela final
    colunas_basicas = {
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

    colunas_estatisticas = {
        'jogos': 'Jogos (C-F)',
        'vitorias': 'Vitórias (C-F)',
        'derrotas': 'Derrotas (C-F)',
        'gols_marcados': 'Gols Marcados (C-F)',
        'gols_sofridos': 'Gols Sofridos (C-F)',
        'jogos_sem_marcar': 'J S/M (C-F)'
    }

    # Decide quais colunas mostrar baseado se as estatísticas foram carregadas
    if st.session_state.estatisticas_carregadas:
        todas_colunas = {**colunas_basicas, **colunas_estatisticas}
    else:
        todas_colunas = colunas_basicas

    colunas_para_mostrar = [col for col in todas_colunas.keys() if col in df_final_display.columns]

    df_final_renamed = df_final_display[colunas_para_mostrar].rename(columns=todas_colunas).fillna("N/A")


    altura_config = None
    if altura_tabela == "Pequena (300px)": altura_config = 300
    elif altura_tabela == "Média (500px)": altura_config = 500
    elif altura_tabela == "Grande (700px)": altura_config = 700
    elif altura_tabela == "Extra Grande (900px)": altura_config = 900

    st.dataframe(df_final_renamed, use_container_width=True, height=altura_config)


    # Informações adicionais
    st.markdown("---")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(
            "💡 **Legendas das Odds de Gols:**\n"
            "- Mais de 0.5: Time marca pelo menos 1 gol\n"
            "- Mais de 1.0: Time marca pelo menos 2 gols\n"
            "- E assim por diante..."
        )
    with col_info2:
        st.info(
            f"🏢 **Bookmaker:** {BOOKMAKERS[id_bookmaker]}\n"
            f"📅 **Data:** {data_selecionada.strftime('%d/%m/%Y')}\n"
            f"🕐 **Horários:** Brasília (UTC-3)"
        )

    if st.session_state.estatisticas_carregadas:
        st.success("✅ Estatísticas carregadas e exibidas para os jogos selecionados. As colunas como 'Jogos (C-F)' representam 'Casa - Fora'.")
        if not mostrar_todos and registros_por_pagina:
             st.info(f"⚠️ A tabela de exibição de estatísticas mostra apenas os jogos que foram *selecionados* e os resultados da busca de estatísticas. A paginação na tabela superior não afeta esta tabela.")

else:
    st.info("👆 Clique em 'Buscar Jogos e Odds' para carregar os dados e começar a seleção.")