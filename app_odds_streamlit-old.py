import streamlit as st
import pandas as pd
from datetime import datetime, date
import pytz
import io
import xlsxwriter
import base64
import streamlit.components.v1 as components

# Importe apenas as funções necessárias do app.py
from app import (
    buscar_jogos_por_data,
    buscar_todas_odds_por_data_e_bookmaker,
    processar_dados_jogos_e_odds,
    buscar_estatisticas_para_jogos_selecionados,
    buscar_ou_salvar_estatisticas,
    BOOKMAKERS
)

# Configuração da página (DEVE SER A PRIMEIRA CHAMADA STREAMLIT)
st.set_page_config(
    page_title="Odds de Futebol",
    page_icon="⚽",
    layout="wide"
)

# CSS personalizado para melhorar a exibição
st.markdown("""
<style>
    /* Cores para colunas de times no DataFrame */

    /* Cores para colunas de times no DataFrame */

    /* Time Casa (colunas 5 e 6) - Escudo e Nome */
    div[data-testid="stDataFrame"] tbody tr td:nth-child(5),
    div[data-testid="stDataFrame"] tbody tr td:nth-child(6) {
        background-color: rgba(76, 175, 80, 0.12) !important;
        border-left: 3px solid #4CAF50;
    }

    div[data-testid="stDataFrame"] thead tr th:nth-child(5),
    div[data-testid="stDataFrame"] thead tr th:nth-child(6) {
        background-color: rgba(76, 175, 80, 0.25) !important;
        border-left: 3px solid #4CAF50;
        font-weight: bold;
    }

    /* Time Fora (colunas 7 e 8) - Escudo e Nome */
    div[data-testid="stDataFrame"] tbody tr td:nth-child(7),
    div[data-testid="stDataFrame"] tbody tr td:nth-child(8) {
        background-color: rgba(244, 67, 54, 0.12) !important;
        border-left: 3px solid #F44336;
    }

    div[data-testid="stDataFrame"] thead tr th:nth-child(7),
    div[data-testid="stDataFrame"] thead tr th:nth-child(8) {
        background-color: rgba(244, 67, 54, 0.25) !important;
        border-left: 3px solid #F44336;
        font-weight: bold;
    }

    /* Data Editor - cores para time casa e fora */
    div[data-testid="data-editor"] [role="gridcell"]:nth-child(6),
    div[data-testid="data-editor"] [role="gridcell"]:nth-child(7) {
        background-color: rgba(76, 175, 80, 0.1) !important;
    }

    div[data-testid="data-editor"] [role="gridcell"]:nth-child(8),
    div[data-testid="data-editor"] [role="gridcell"]:nth-child(9) {
        background-color: rgba(244, 67, 54, 0.1) !important;
    }

    div[data-testid="data-editor"] [role="columnheader"]:nth-child(6),
    div[data-testid="data-editor"] [role="columnheader"]:nth-child(7) {
        background-color: rgba(76, 175, 80, 0.2) !important;
        font-weight: bold;
    }

    div[data-testid="data-editor"] [role="columnheader"]:nth-child(8),
    div[data-testid="data-editor"] [role="columnheader"]:nth-child(9) {
        background-color: rgba(244, 67, 54, 0.2) !important;
        font-weight: bold;
    }

    /* Ajustes gerais */
    .dataframe tbody th {
        display: none;
    }

    .dataframe td {
        min-height: 35px;
        vertical-align: middle;
    }

    /* Melhorar aparência dos escudos */
    div[data-testid="stDataFrame"] img,
    div[data-testid="data-editor"] img {
        width: 24px;
        height: 24px;
        object-fit: contain;
        border-radius: 3px;
    }
</style>

<script>
// Função para aplicar cores nas tabelas
function applyTableColors() {
    setTimeout(() => {
        // Para DataFrames
        const dataframes = document.querySelectorAll('[data-testid="stDataFrame"]');
        dataframes.forEach(df => {
            const headers = df.querySelectorAll('thead th');
            const rows = df.querySelectorAll('tbody tr');

            // Identificar colunas por posição ou conteúdo
            headers.forEach((header, index) => {
                const text = header.textContent || '';

                // Time Casa (posições 4 e 5 - escudo e nome)
                if (index === 4 || index === 5 || text.includes('Casa') || text.trim() === ' ') {
                    header.style.backgroundColor = 'rgba(76, 175, 80, 0.25)';
                    header.style.borderLeft = '3px solid #4CAF50';
                    header.style.fontWeight = 'bold';

                    // Aplicar nas células correspondentes
                    rows.forEach(row => {
                        const cell = row.cells[index];
                        if (cell) {
                            cell.style.backgroundColor = 'rgba(76, 175, 80, 0.12)';
                            cell.style.borderLeft = '3px solid #4CAF50';
                        }
                    });
                }

                // Time Fora (posições 6 e 7 - escudo e nome)
                if (index === 6 || index === 7 || text.includes('Fora') || text.trim() === '  ') {
                    header.style.backgroundColor = 'rgba(244, 67, 54, 0.25)';
                    header.style.borderLeft = '3px solid #F44336';
                    header.style.fontWeight = 'bold';

                    // Aplicar nas células correspondentes
                    rows.forEach(row => {
                        const cell = row.cells[index];
                        if (cell) {
                            cell.style.backgroundColor = 'rgba(244, 67, 54, 0.12)';
                            cell.style.borderLeft = '3px solid #F44336';
                        }
                    });
                }
            });
        });

        // Para Data Editors
        const dataEditors = document.querySelectorAll('[data-testid="data-editor"]');
        dataEditors.forEach(editor => {
            const headers = editor.querySelectorAll('[role="columnheader"]');

            headers.forEach((header, index) => {
                const text = header.textContent || '';

                // Time Casa (índices 4 e 5)
                if (text.includes('Casa') || text.trim() === ' ' || index === 4 || index === 5) {
                    header.style.backgroundColor = 'rgba(76, 175, 80, 0.25)';
                    header.style.fontWeight = 'bold';

                    // Aplicar nas células
                    const cells = editor.querySelectorAll(`[role="gridcell"][aria-colindex="${index + 1}"]`);
                    cells.forEach(cell => {
                        cell.style.backgroundColor = 'rgba(76, 175, 80, 0.1)';
                    });
                }

                // Time Fora (índices 6 e 7)
                if (text.includes('Fora') || text.trim() === '  ' || index === 6 || index === 7) {
                    header.style.backgroundColor = 'rgba(244, 67, 54, 0.25)';
                    header.style.fontWeight = 'bold';

                    // Aplicar nas células
                    const cells = editor.querySelectorAll(`[role="gridcell"][aria-colindex="${index + 1}"]`);
                    cells.forEach(cell => {
                        cell.style.backgroundColor = 'rgba(244, 67, 54, 0.1)';
                    });
                }
            });
        });
    }, 100);
}

// Observer para mudanças no DOM
const observer = new MutationObserver(() => {
    applyTableColors();
});

observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true
});

// Aplicar inicialmente e periodicamente
applyTableColors();
setInterval(applyTableColors, 500);
</script>
""", unsafe_allow_html=True)

# Fuso horário de Brasília
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
if 'time_selecionado_modal' not in st.session_state:
    st.session_state.time_selecionado_modal = None
if 'selecoes_manuais' not in st.session_state:
    st.session_state.selecoes_manuais = set()


def criar_celula_time_com_logo(nome_time, logo_url, tipo_time="home"):
    """Retorna apenas o nome do time, sem emojis"""
    return nome_time


def safe_format_odd(odd_value):
    """Formata odds de forma segura"""
    try:
        if pd.isna(odd_value) or odd_value is None or odd_value == '':
            return "N/A"

        # Converter para float se necessário
        if isinstance(odd_value, str):
            odd_value = float(odd_value)

        if isinstance(odd_value, (int, float)) and odd_value > 0:
            return f"{odd_value:.2f}"
        else:
            return "N/A"
    except (ValueError, TypeError):
        return "N/A"


def processar_dataframe_para_exibicao(df):
    """Processa o DataFrame para exibição com logos e formatação adequada"""
    if df.empty:
        return df

    df_display = df.copy()

    # Verificar se as colunas necessárias existem
    required_columns = ['time_casa', 'time_fora', 'team_home_id', 'team_away_id', 'league_id', 'season']
    missing_columns = [col for col in required_columns if col not in df_display.columns]
    if missing_columns:
        st.warning(f"Colunas ausentes no DataFrame: {missing_columns}")
        return df_display

    # Criar coluna de escudos (sem título) para casa
    df_display['escudo_casa'] = df_display['time_casa_logo'].fillna('')

    # Criar coluna de escudos (sem título) para fora
    df_display['escudo_fora'] = df_display['time_fora_logo'].fillna('')

    # Manter apenas os nomes dos times (sem emojis)
    df_display['Time Casa'] = df_display['time_casa']
    df_display['Time Fora'] = df_display['time_fora']

    # Criar URLs para tornar os nomes clicáveis (usando query params)
    df_display['Link Casa'] = df_display.apply(
        lambda
            row: f"?team_id={row['team_home_id']}&league_id={row['league_id']}&season={row['season']}&team_name={row['time_casa']}",
        axis=1
    )

    df_display['Link Fora'] = df_display.apply(
        lambda
            row: f"?team_id={row['team_away_id']}&league_id={row['league_id']}&season={row['season']}&team_name={row['time_fora']}",
        axis=1
    )

    # Formatar odds com legendas - com verificação de tipo
    def formatar_odd_gols(odd_value, legenda_value):
        """Formata odds de gols com verificação de tipo"""
        try:
            if pd.notna(odd_value) and pd.notna(legenda_value):
                # Converter para float se for string
                if isinstance(odd_value, str):
                    odd_value = float(odd_value)
                if isinstance(odd_value, (int, float)) and odd_value != 0:
                    return f"{odd_value:.2f} ({legenda_value})"
            return "N/A"
        except (ValueError, TypeError):
            return "N/A"

    if 'legenda_gols_casa' in df_display.columns:
        df_display['Gols Casa'] = df_display.apply(
            lambda row: formatar_odd_gols(row.get('odd_gols_casa'), row.get('legenda_gols_casa')),
            axis=1
        )
    else:
        # Se não tiver legenda, usar apenas a odd
        df_display['Gols Casa'] = df_display.apply(
            lambda row: safe_format_odd(row.get('odd_gols_casa')), axis=1
        )

    if 'legenda_gols_fora' in df_display.columns:
        df_display['Gols Fora'] = df_display.apply(
            lambda row: formatar_odd_gols(row.get('odd_gols_fora'), row.get('legenda_gols_fora')),
            axis=1
        )
    else:
        # Se não tiver legenda, usar apenas a odd
        df_display['Gols Fora'] = df_display.apply(
            lambda row: safe_format_odd(row.get('odd_gols_fora')), axis=1
        )

    return df_display


def mostrar_modal_estatisticas(time_id, time_nome, liga_id, temporada):
    """Mostra modal com estatísticas detalhadas do time"""

    @st.dialog(f"📊 Estatísticas Detalhadas - {time_nome}")
    def modal_estatisticas():
        stats = buscar_ou_salvar_estatisticas(time_id, liga_id, temporada)

        if stats:
            # Container principal
            st.markdown("### 📈 Resumo da Temporada")

            # Primeira linha - Informações principais
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("🏟️ Total de Jogos", stats.get('jogos_total', 0))
            with col2:
                st.metric("⚽ Total de Gols", stats.get('gols_marcados_total', 0))
            with col3:
                st.metric("🚫 Gols Sofridos", stats.get('gols_sofridos_total', 0))
            with col4:
                st.metric("😔 Jogos sem Marcar", stats.get('jogos_sem_marcar', 0))

            st.markdown("---")

            # Segunda linha - Resultados detalhados
            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader("🏆 Resultados")
                st.metric("Vitórias", stats.get('vitorias_total', 0),
                          f"Casa: {stats.get('vitorias_casa', 0)} | Fora: {stats.get('vitorias_fora', 0)}")
                st.metric("Empates", stats.get('empates_total', 0),
                          f"Casa: {stats.get('empates_casa', 0)} | Fora: {stats.get('empates_fora', 0)}")
                st.metric("Derrotas", stats.get('derrotas_total', 0),
                          f"Casa: {stats.get('derrotas_casa', 0)} | Fora: {stats.get('derrotas_fora', 0)}")

            with col2:
                st.subheader("⚽ Gols Detalhados")
                st.metric("Gols Marcados", stats.get('gols_marcados_total', 0),
                          f"Casa: {stats.get('gols_marcados_casa', 0)} | Fora: {stats.get('gols_marcados_fora', 0)}")
                st.metric("Gols Sofridos", stats.get('gols_sofridos_total', 0),
                          f"Casa: {stats.get('gols_sofridos_casa', 0)} | Fora: {stats.get('gols_sofridos_fora', 0)}")
                st.metric("Média Gols/Jogo", f"{stats.get('media_gols_marcados', 0):.2f}",
                          f"Sofridos: {stats.get('media_gols_sofridos', 0):.2f}")

            with col3:
                st.subheader("📈 Estatísticas Especiais")
                st.metric("Jogos sem Sofrer Gol", stats.get('jogos_sem_sofrer', 0))
                st.metric("Ambos Marcam", stats.get('jogos_ambos_marcam', 0) if 'jogos_ambos_marcam' in stats else 0)
                forma = stats.get('forma_recente', '')
                if forma:
                    forma_colorida = forma.replace('W', '🟢').replace('D', '🟡').replace('L', '🔴')
                    st.write(f"**Forma Recente:** {forma_colorida}")

            # Terceira linha - Cartões e Pênaltis
            if stats.get('cartoes_amarelos', 0) > 0 or stats.get('cartoes_vermelhos', 0) > 0:
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("🟨 Cartões Amarelos", stats.get('cartoes_amarelos', 0))
                with col2:
                    st.metric("🟥 Cartões Vermelhos", stats.get('cartoes_vermelhos', 0))
                with col3:
                    st.metric("⚽ Pênaltis Marcados", stats.get('penaltis_marcados', 0))
                with col4:
                    st.metric("❌ Pênaltis Perdidos", stats.get('penaltis_perdidos', 0))

            if st.button("Fechar", use_container_width=True):
                st.rerun()
        else:
            st.warning("Estatísticas não disponíveis para este time")
            if st.button("Fechar"):
                st.rerun()

    modal_estatisticas()


def exportar_para_excel(df):
    """Exporta DataFrame para Excel com formatação"""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Jogos e Estatísticas', index=False)

        # Obter o objeto workbook e worksheet
        workbook = writer.book
        worksheet = writer.sheets['Jogos e Estatísticas']

        # Adicionar formatação
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BD',
            'border': 1
        })

        # Formato para time casa (verde claro)
        home_format = workbook.add_format({
            'bg_color': '#E8F5E9',
            'border': 1
        })

        # Formato para time fora (vermelho claro)
        away_format = workbook.add_format({
            'bg_color': '#FFEBEE',
            'border': 1
        })

        # Formatar cabeçalho
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Identificar colunas de times
        col_casa = None
        col_fora = None
        for idx, col in enumerate(df.columns):
            if 'Casa' in col or '🏠' in col:
                col_casa = idx
            elif 'Fora' in col or '✈️' in col:
                col_fora = idx

        # Aplicar formatação nas células
        for row_num in range(1, len(df) + 1):
            for col_num in range(len(df.columns)):
                value = df.iloc[row_num - 1, col_num]

                if col_num == col_casa:
                    worksheet.write(row_num, col_num, value, home_format)
                elif col_num == col_fora:
                    worksheet.write(row_num, col_num, value, away_format)
                else:
                    worksheet.write(row_num, col_num, value)

        # Ajustar largura das colunas
        for i, col in enumerate(df.columns):
            column_len = df[col].astype(str).str.len().max()
            column_len = max(column_len, len(col)) + 2
            worksheet.set_column(i, i, min(column_len, 50))  # Limitar largura máxima

    output.seek(0)
    return output


# Interface principal
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
    st.session_state.selecoes_manuais = set()
    st.session_state.time_selecionado_modal = None
    st.sidebar.success("Cache limpo! Reiniciando a aplicação.")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write(f"**Data:** {data_selecionada.strftime('%d/%m/%Y')}")
st.sidebar.write(f"**Bookmaker:** {BOOKMAKERS[id_bookmaker]}")
st.sidebar.write("**Fuso Horário:** Brasília (UTC-3)")

# Verificar query parameters para abrir modal
query_params = st.query_params
if 'team_id' in query_params:
    try:
        team_id = int(query_params['team_id'])
        league_id = int(query_params['league_id'])
        season = int(query_params['season'])
        team_name = query_params['team_name']

        st.session_state.time_selecionado_modal = {
            'id': team_id,
            'liga_id': league_id,
            'temporada': season,
            'nome': team_name
        }
        # Limpar query params
        st.query_params.clear()
    except:
        pass

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
    st.session_state.estatisticas_carregadas = False
    st.session_state.jogos_selecionados = []
    st.session_state.selecoes_manuais = set()

    with st.spinner("🔄 Carregando jogos..."):
        dados_jogos = buscar_jogos_por_data(data_str)
        st.session_state.dados_jogos = dados_jogos

    if not dados_jogos:
        st.error("❌ Não foi possível carregar os dados dos jogos.")
        st.stop()

    with st.spinner("🔄 Carregando todas as odds (com paginação)..."):
        dados_odds = buscar_todas_odds_por_data_e_bookmaker(data_str, id_bookmaker)
        st.session_state.dados_odds = dados_odds

    if not dados_odds or not dados_odds.get('response'):
        st.warning("⚠️ Não foi possível carregar os dados de odds para este bookmaker e data.")

    with st.spinner("🔄 Processando dados..."):
        df = processar_dados_jogos_e_odds(st.session_state.dados_jogos, st.session_state.dados_odds, None,
                                          filtrar_sem_odds)
        st.session_state.df_processado = df

    # Inicializar seleções automáticas na primeira carga de dados
    selecoes_automaticas = df[df['selecao_automatica'] == True]['id_jogo'].tolist()
    st.session_state.jogos_selecionados = selecoes_automaticas
    if selecoes_automaticas:
        st.info(f"🎯 {len(selecoes_automaticas)} jogo(s) selecionado(s) automaticamente baseado nos critérios:\n"
                f"• Time casa odd ≥ 1.5 E Time fora marca gol (Over 0.5) ≥ 1.5\n"
                f"• Time fora odd ≥ 1.5 E Time casa marca gol (Over 0.5) ≥ 1.5")

    st.session_state.dados_carregados = True
    st.rerun()

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

    # Mostrar legenda dos indicadores
    with st.expander("ℹ️ Legenda e Instruções", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Indicadores visuais:**")
            st.write("📸 = Escudos dos times (colunas sem título)")
            st.write("🟢 = Cor de fundo verde para time casa")
            st.write("🔴 = Cor de fundo vermelho para time fora")
        with col2:
            st.write("**Instruções:**")
            st.write("✓ = Marque os jogos para buscar estatísticas")
            st.write("🔗 = Clique nas linhas para ver estatísticas dos times")
            st.write("📊 = Clique em 'Buscar Estatísticas' após selecionar")

    # Processar DataFrame para exibição melhorada
    df_display = processar_dataframe_para_exibicao(df_filtrado_exibicao)

    # Adicionar coluna de checkbox para seleção interativa
    df_display['Selecionar'] = df_display['id_jogo'].isin(st.session_state.jogos_selecionados)

    # Paginação
    total_registros_exibicao = len(df_display)
    if not mostrar_todos and registros_por_pagina:
        df_para_exibir = df_display.head(registros_por_pagina)
        registros_exibidos = len(df_para_exibir)
    else:
        df_para_exibir = df_display.copy()
        registros_exibidos = total_registros_exibicao

    st.info(f"Mostrando {registros_exibidos} de {total_registros_exibicao} jogos para seleção.")

    # Preparar colunas para exibição
    colunas_exibir = [
        'Selecionar', 'id_jogo', 'horario', 'liga',
        'escudo_casa', 'Time Casa', 'escudo_fora', 'Time Fora',
        'odd_casa', 'odd_empate', 'odd_fora',
        'Gols Casa', 'Gols Fora',
        'selecao_automatica'
    ]

    # Configurar altura da tabela
    altura_config = None
    if altura_tabela == "Pequena (300px)":
        altura_config = 300
    elif altura_tabela == "Média (500px)":
        altura_config = 500
    elif altura_tabela == "Grande (700px)":
        altura_config = 700
    elif altura_tabela == "Extra Grande (900px)":
        altura_config = 900

    # Tabela interativa melhorada com on_select
    event = st.dataframe(
        df_para_exibir[colunas_exibir].rename(columns={
            'selecao_automatica': 'Auto',
            'escudo_casa': ' ',  # Espaço para escudo casa
            'escudo_fora': '  ',  # Dois espaços para escudo fora
        }),
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(
                "✓",
                help="Marque os jogos para buscar estatísticas",
                width="small"
            ),
            "id_jogo": st.column_config.NumberColumn("ID", width="small"),
            "horario": st.column_config.TextColumn("Horário", width="small"),
            "liga": st.column_config.TextColumn("Liga", width="medium"),
            " ": st.column_config.ImageColumn(
                " ",  # Escudo casa
                help="Escudo do time da casa",
                width="small"
            ),
            "Time Casa": st.column_config.TextColumn(
                "Time Casa",
                help="Time da casa - Clique na linha para ver estatísticas",
                width="large"
            ),
            "  ": st.column_config.ImageColumn(
                "  ",  # Escudo fora
                help="Escudo do time de fora",
                width="small"
            ),
            "Time Fora": st.column_config.TextColumn(
                "Time Fora",
                help="Time de fora - Clique na linha para ver estatísticas",
                width="large"
            ),
            "odd_casa": st.column_config.NumberColumn("Odd Casa", format="%.2f", width="small"),
            "odd_empate": st.column_config.NumberColumn("Odd X", format="%.2f", width="small"),
            "odd_fora": st.column_config.NumberColumn("Odd Fora", format="%.2f", width="small"),
            "Gols Casa": st.column_config.TextColumn("Gols Casa", width="medium"),
            "Gols Fora": st.column_config.TextColumn("Gols Fora", width="medium"),
            "Auto": st.column_config.CheckboxColumn(
                "Auto",
                help="Seleção automática pelos critérios",
                disabled=True,
                width="small"
            )
        },
        use_container_width=True,
        hide_index=True,
        height=altura_config,
        on_select="rerun",
        selection_mode=["multi-row"],
        key="tabela_principal"
    )

    # Detectar seleções de linhas para abrir modal de estatísticas
    if event.selection and 'rows' in event.selection and event.selection['rows']:
        # Pegar a primeira linha selecionada para abrir modal
        row_index = event.selection['rows'][0]
        if row_index < len(df_para_exibir):
            selected_row = df_para_exibir.iloc[row_index]

            # Mostrar opções para ver estatísticas dos times
            st.markdown("---")
            st.markdown("### 🔍 Time Selecionado - Escolha uma opção:")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📊 Ver Estatísticas - {selected_row['time_casa']}", use_container_width=True):
                    st.session_state.time_selecionado_modal = {
                        'id': selected_row['team_home_id'],
                        'liga_id': selected_row['league_id'],
                        'temporada': selected_row['season'],
                        'nome': selected_row['time_casa']
                    }
                    st.rerun()

            with col2:
                if st.button(f"📊 Ver Estatísticas - {selected_row['time_fora']}", use_container_width=True):
                    st.session_state.time_selecionado_modal = {
                        'id': selected_row['team_away_id'],
                        'liga_id': selected_row['league_id'],
                        'temporada': selected_row['season'],
                        'nome': selected_row['time_fora']
                    }
                    st.rerun()

    # Detectar mudanças nas seleções para análise de estatísticas
    df_editado = df_para_exibir[df_para_exibir['Selecionar'] == True]
    novas_selecoes = set(df_editado['id_jogo'].tolist()) if not df_editado.empty else set()
    selecoes_anteriores = set(st.session_state.jogos_selecionados)

    if novas_selecoes != selecoes_anteriores:
        st.session_state.jogos_selecionados = list(novas_selecoes)
        st.session_state.selecoes_manuais = novas_selecoes

    # Botões de ação para seleção
    col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)
    with col_sel1:
        if st.button("✅ Selecionar Todos Exibidos"):
            todos_ids_exibidos = df_para_exibir['id_jogo'].tolist()
            st.session_state.jogos_selecionados = list(set(st.session_state.jogos_selecionados + todos_ids_exibidos))
            st.rerun()
    with col_sel2:
        if st.button("❌ Desmarcar Todos Exibidos"):
            current_displayed_ids = df_para_exibir['id_jogo'].tolist()
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
                df_com_stats = buscar_estatisticas_para_jogos_selecionados(df_base, st.session_state.jogos_selecionados)
                st.session_state.df_processado_com_stats = df_com_stats
            st.session_state.estatisticas_carregadas = True
            st.rerun()
        else:
            st.warning("⚠️ Nenhum jogo selecionado! Marque os jogos que deseja ver as estatísticas.")

    # Exibir a tabela final (com ou sem estatísticas)
    st.markdown("---")
    st.subheader(
        "📊 Tabela de Jogos com Estatísticas Detalhadas" if st.session_state.estatisticas_carregadas else "📊 Tabela de Jogos e Odds"
    )

    df_final_display = None
    if st.session_state.estatisticas_carregadas and 'df_processado_com_stats' in st.session_state:
        df_final_display = st.session_state.df_processado_com_stats[
            st.session_state.df_processado_com_stats['id_jogo'].isin(st.session_state.jogos_selecionados)
        ].copy()

        if df_final_display.empty:
            st.warning("Nenhuma estatística encontrada para os jogos selecionados após o filtro.")
            df_final_display = st.session_state.df_processado_com_stats.copy()
            st.session_state.estatisticas_carregadas = False
    else:
        df_final_display = df_display.copy()

    # Processar DataFrame final para exibição
    df_final_display = processar_dataframe_para_exibicao(df_final_display)

    # Verificar se as colunas processadas existem antes de usá-las
    if 'Gols Casa' not in df_final_display.columns:
        df_final_display['Gols Casa'] = df_final_display.apply(
            lambda row: safe_format_odd(row.get('odd_gols_casa')), axis=1
        )

    if 'Gols Fora' not in df_final_display.columns:
        df_final_display['Gols Fora'] = df_final_display.apply(
            lambda row: safe_format_odd(row.get('odd_gols_fora')), axis=1
        )

    # Colunas a serem exibidas na tabela final
    colunas_basicas = [
        'horario', 'liga', 'escudo_casa', 'Time Casa', 'escudo_fora', 'Time Fora',
        'odd_casa', 'odd_empate', 'odd_fora', 'Gols Casa', 'Gols Fora'
    ]

    colunas_estatisticas = [
        'jogos', 'vitorias', 'derrotas', 'gols_marcados', 'gols_sofridos', 'jogos_sem_marcar'
    ]

    if st.session_state.estatisticas_carregadas:
        todas_colunas = colunas_basicas + [col for col in colunas_estatisticas if col in df_final_display.columns]
    else:
        todas_colunas = colunas_basicas

    colunas_para_mostrar = [col for col in todas_colunas if col in df_final_display.columns]
    df_final_renamed = df_final_display[colunas_para_mostrar].rename(columns={
        'horario': 'Horário',
        'liga': 'Liga',
        'escudo_casa': ' ',  # Espaço para escudo casa
        'escudo_fora': '  ',  # Dois espaços para escudo fora
        'odd_casa': 'Odd Casa',
        'odd_empate': 'Odd X',
        'odd_fora': 'Odd Fora',
        'jogos': 'Jogos (C-F)',
        'vitorias': 'Vitórias (C-F)',
        'derrotas': 'Derrotas (C-F)',
        'gols_marcados': 'Gols Marc. (C-F)',
        'gols_sofridos': 'Gols Sofr. (C-F)',
        'jogos_sem_marcar': 'J.S.Marcar (C-F)'
    }).fillna("N/A")

    # Adicionar botão de exportação
    if st.session_state.estatisticas_carregadas and not df_final_renamed.empty:
        col_export1, col_export2, col_export3 = st.columns([1, 1, 3])
        with col_export1:
            excel_file = exportar_para_excel(df_final_renamed)
            st.download_button(
                label="📥 Baixar Excel",
                data=excel_file,
                file_name=f"odds_estatisticas_{data_selecionada.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Mostrar tabela final
    st.markdown("### 📋 Resultados Finais")

    # Configurar exibição da tabela final
    column_config_final = {
        " ": st.column_config.ImageColumn(
            " ",
            help="Escudo do time da casa",
            width="small"
        ),
        "  ": st.column_config.ImageColumn(
            "  ",
            help="Escudo do time de fora",
            width="small"
        ),
        "Time Casa": st.column_config.TextColumn(
            "Time Casa",
            help="Time da casa - Clique na linha para ver opções de estatísticas",
            width="large"
        ),
        "Time Fora": st.column_config.TextColumn(
            "Time Fora",
            help="Time de fora - Clique na linha para ver opções de estatísticas",
            width="large"
        ),
        "Odd Casa": st.column_config.NumberColumn("Odd Casa", format="%.2f"),
        "Odd X": st.column_config.NumberColumn("Odd X", format="%.2f"),
        "Odd Fora": st.column_config.NumberColumn("Odd Fora", format="%.2f")
    }

    final_event = st.dataframe(
        df_final_renamed,
        column_config=column_config_final,
        use_container_width=True,
        hide_index=True,
        height=altura_config,
        on_select="rerun",
        selection_mode=["single-row"],
        key="tabela_final"
    )

    # Detectar seleção na tabela final para abrir estatísticas
    if final_event.selection and 'rows' in final_event.selection and final_event.selection['rows']:
        row_index = final_event.selection['rows'][0]
        if row_index < len(df_final_display):
            selected_row = df_final_display.iloc[row_index]

            st.markdown("---")
            st.markdown("### 🔍 Linha Selecionada - Ver Estatísticas:")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📊 {selected_row['time_casa']}", use_container_width=True, key="final_casa"):
                    st.session_state.time_selecionado_modal = {
                        'id': selected_row['team_home_id'],
                        'liga_id': selected_row['league_id'],
                        'temporada': selected_row['season'],
                        'nome': selected_row['time_casa']
                    }
                    st.rerun()

            with col2:
                if st.button(f"📊 {selected_row['time_fora']}", use_container_width=True, key="final_fora"):
                    st.session_state.time_selecionado_modal = {
                        'id': selected_row['team_away_id'],
                        'liga_id': selected_row['league_id'],
                        'temporada': selected_row['season'],
                        'nome': selected_row['time_fora']
                    }
                    st.rerun()

    # Informações adicionais
    st.markdown("---")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(
            "💡 **Como usar:**\n"
            "- 📸 Escudos dos times nas colunas sem título\n"
            "- 🟢 Verde = Dados do time casa\n"
            "- 🔴 Vermelho = Dados do time fora\n"
            "- 🔗 Clique nas linhas para ver estatísticas dos times\n"
            "- ✓ Marque jogos para análise comparativa"
        )
    with col_info2:
        st.info(
            f"🏢 **Bookmaker:** {BOOKMAKERS[id_bookmaker]}\n"
            f"📅 **Data:** {data_selecionada.strftime('%d/%m/%Y')}\n"
            f"🕐 **Horários:** Brasília (UTC-3)\n"
            f"📊 **Jogos selecionados:** {len(st.session_state.jogos_selecionados)}"
        )

    if st.session_state.estatisticas_carregadas:
        st.success("✅ Estatísticas carregadas! Clique nas linhas da tabela para ver detalhes dos times.")

else:
    st.info("👆 Clique em 'Buscar Jogos e Odds' para carregar os dados e começar a seleção.")

# Verificar se há time selecionado para mostrar modal
if st.session_state.time_selecionado_modal:
    time = st.session_state.time_selecionado_modal
    mostrar_modal_estatisticas(
        time['id'],
        time['nome'],
        time['liga_id'],
        time['temporada']
    )
    st.session_state.time_selecionado_modal = None