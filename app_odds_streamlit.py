import streamlit as st
import pandas as pd
from datetime import datetime, date
import pytz
import io
import xlsxwriter


# Importe apenas as funções necessárias do app.py
from app import (
    buscar_jogos_por_data,
    buscar_todas_odds_por_data_e_bookmaker,
    processar_dados_jogos_e_odds,
    buscar_estatisticas_para_jogos_selecionados,
    buscar_ou_salvar_estatisticas,
    BOOKMAKERS
)

# Importar configuração do banco
from config.database import supabase

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
    div[data-testid="stDataFrame"] tbody tr td:nth-child(6),
    div[data-testid="stDataFrame"] tbody tr td:nth-child(7) {
        background-color: rgba(76, 175, 80, 0.12) !important;
        border-left: 3px solid #4CAF50;
    }

    div[data-testid="stDataFrame"] thead tr th:nth-child(6),
    div[data-testid="stDataFrame"] thead tr th:nth-child(7) {
        background-color: rgba(76, 175, 80, 0.25) !important;
        border-left: 3px solid #4CAF50;
        font-weight: bold;
    }

    /* Time Fora (colunas 7 e 8) - Escudo e Nome */
    div[data-testid="stDataFrame"] tbody tr td:nth-child(8),
    div[data-testid="stDataFrame"] tbody tr td:nth-child(9) {
        background-color: rgba(244, 67, 54, 0.12) !important;
        border-left: 3px solid #F44336;
    }

    div[data-testid="stDataFrame"] thead tr th:nth-child(8),
    div[data-testid="stDataFrame"] thead tr th:nth-child(9) {
        background-color: rgba(244, 67, 54, 0.25) !important;
        border-left: 3px solid #F44336;
        font-weight: bold;
    }

    /* Data Editor - cores para time casa e fora */
    div[data-testid="data-editor"] [role="gridcell"]:nth-child(7),
    div[data-testid="data-editor"] [role="gridcell"]:nth-child(8) {
        background-color: rgba(76, 175, 80, 0.1) !important;
    }

    div[data-testid="data-editor"] [role="gridcell"]:nth-child(9),
    div[data-testid="data-editor"] [role="gridcell"]:nth-child(10) {
        background-color: rgba(244, 67, 54, 0.1) !important;
    }

    div[data-testid="data-editor"] [role="columnheader"]:nth-child(7),
    div[data-testid="data-editor"] [role="columnheader"]:nth-child(8) {
        background-color: rgba(76, 175, 80, 0.2) !important;
        font-weight: bold;
    }

    div[data-testid="data-editor"] [role="columnheader"]:nth-child(9),
    div[data-testid="data-editor"] [role="columnheader"]:nth-child(10) {
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

                // Time Casa (posições 5 e 6 - escudo e nome)
                if (index === 5 || index === 6 || text.includes('Casa') || text.trim() === ' ') {
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

                // Time Fora (posições 7 e 8 - escudo e nome)
                if (index === 7 || index === 8 || text.includes('Fora') || text.trim() === '  ') {
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
if 'comparacao_modal' not in st.session_state:
    st.session_state.comparacao_modal = None
if 'selecoes_manuais' not in st.session_state:
    st.session_state.selecoes_manuais = set()


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
    required_columns = ['time_casa', 'time_fora', 'team_home_id', 'team_away_id', 'league_id', 'season', 'país', 'criterio_selecao']
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


def buscar_estatisticas_temporada_completa(team_id, season):
    """Busca estatísticas agregadas da temporada completa usando a view do banco"""
    try:
        # Primeiro tentar usar a view otimizada
        resultado = supabase.table('v_estatisticas_temporada').select("*").eq('time_id', team_id).eq('temporada',
                                                                                                     season).execute()

        if resultado.data:
            # Dados já agregados pela view
            stats = resultado.data[0]
            return stats

        # Fallback: agregar manualmente se a view não existir
        resultado = supabase.table('estatisticas_times').select("*").eq('time_id', team_id).eq('temporada',
                                                                                               season).execute()

        if not resultado.data:
            return None

        # Agregar dados de todas as ligas manualmente
        stats_agregadas = {
            'jogos_total': 0,
            'vitorias_total': 0,
            'empates_total': 0,
            'derrotas_total': 0,
            'gols_marcados_total': 0,
            'gols_sofridos_total': 0,
            'jogos_sem_marcar': 0,
            'jogos_sem_sofrer': 0,
            'cartoes_amarelos': 0,
            'cartoes_vermelhos': 0,
            'penaltis_marcados': 0,
            'penaltis_perdidos': 0,
            'ligas_participando': []
        }

        for stats in resultado.data:
            stats_agregadas['jogos_total'] += stats.get('jogos_total', 0)
            stats_agregadas['vitorias_total'] += stats.get('vitorias_total', 0)
            stats_agregadas['empates_total'] += stats.get('empates_total', 0)
            stats_agregadas['derrotas_total'] += stats.get('derrotas_total', 0)
            stats_agregadas['gols_marcados_total'] += stats.get('gols_marcados_total', 0)
            stats_agregadas['gols_sofridos_total'] += stats.get('gols_sofridos_total', 0)
            stats_agregadas['jogos_sem_marcar'] += stats.get('jogos_sem_marcar', 0)
            stats_agregadas['jogos_sem_sofrer'] += stats.get('jogos_sem_sofrer', 0)
            stats_agregadas['cartoes_amarelos'] += stats.get('cartoes_amarelos', 0)
            stats_agregadas['cartoes_vermelhos'] += stats.get('cartoes_vermelhos', 0)
            stats_agregadas['penaltis_marcados'] += stats.get('penaltis_marcados', 0)
            stats_agregadas['penaltis_perdidos'] += stats.get('penaltis_perdidos', 0)
            stats_agregadas['ligas_participando'].append(stats.get('liga_id'))

        # Calcular médias e métricas derivadas
        if stats_agregadas['jogos_total'] > 0:
            stats_agregadas['media_gols_marcados'] = stats_agregadas['gols_marcados_total'] / stats_agregadas[
                'jogos_total']
            stats_agregadas['media_gols_sofridos'] = stats_agregadas['gols_sofridos_total'] / stats_agregadas[
                'jogos_total']
            stats_agregadas['aproveitamento_percentual'] = (stats_agregadas['vitorias_total'] * 3 + stats_agregadas[
                'empates_total']) / (stats_agregadas['jogos_total'] * 3) * 100
            stats_agregadas['clean_sheet_percentual'] = (stats_agregadas['jogos_sem_sofrer'] / stats_agregadas[
                'jogos_total']) * 100
            stats_agregadas['eficiencia_ofensiva_percentual'] = ((stats_agregadas['jogos_total'] - stats_agregadas[
                'jogos_sem_marcar']) / stats_agregadas['jogos_total']) * 100
        else:
            stats_agregadas['media_gols_marcados'] = 0
            stats_agregadas['media_gols_sofridos'] = 0
            stats_agregadas['aproveitamento_percentual'] = 0
            stats_agregadas['clean_sheet_percentual'] = 0
            stats_agregadas['eficiencia_ofensiva_percentual'] = 0

        stats_agregadas['total_ligas'] = len(set(stats_agregadas['ligas_participando']))
        stats_agregadas['saldo_gols'] = stats_agregadas['gols_marcados_total'] - stats_agregadas['gols_sofridos_total']

        return stats_agregadas

    except Exception as e:
        print(f"Erro ao buscar estatísticas da temporada: {str(e)}")
        return None


def buscar_nome_liga(liga_id):
    """Busca o nome da liga por ID"""
    try:
        resultado = supabase.table('ligas').select("nome").eq('id', liga_id).execute()
        if resultado.data:
            return resultado.data[0]['nome']
        return f"Liga {liga_id}"
    except:
        return f"Liga {liga_id}"


def criar_card_estatisticas(titulo, stats, cor_primaria="#007bff"):
    """Cria um card visual para exibir estatísticas"""
    if not stats:
        return f"""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    border: 1px solid #dee2e6; border-radius: 12px; padding: 20px; margin: 10px 0;">
            <h4 style="color: #6c757d; margin-bottom: 15px;">{titulo}</h4>
            <p style="color: #6c757d;">Dados não disponíveis</p>
        </div>
        """

    # Calcular aproveitamento se não estiver disponível
    aproveitamento = stats.get('aproveitamento_percentual')
    if aproveitamento is None and stats.get('jogos_total', 0) > 0:
        aproveitamento = ((stats.get('vitorias_total', 0) * 3 + stats.get('empates_total', 0)) / (
                    stats.get('jogos_total', 1) * 3)) * 100

    # Informações extras
    info_extra = ""
    if 'total_ligas' in stats and stats.get('total_ligas', 0) > 1:
        info_extra = f'<div style="margin-top: 15px; padding: 10px; background: rgba(0,123,255,0.1); border-radius: 6px; text-align: center;"><small style="color: #007bff;">🏆 Participando em {stats.get("total_ligas", 1)} liga(s) nesta temporada</small></div>'

    if 'saldo_gols' in stats:
        saldo_color = "#28a745" if stats.get('saldo_gols', 0) >= 0 else "#dc3545"
        saldo_prefix = "+" if stats.get('saldo_gols', 0) > 0 else ""
        info_extra += f'<div style="margin-top: 10px; padding: 8px; background: rgba(0,0,0,0.05); border-radius: 6px; text-align: center;"><small style="color: {saldo_color}; font-weight: 600;">Saldo: {saldo_prefix}{stats.get("saldo_gols", 0)} gols</small></div>'

    return f"""
    <div style="background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); 
                border: 1px solid {cor_primaria}; border-radius: 12px; padding: 20px; margin: 10px 0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: transform 0.2s ease;">
        <h4 style="color: {cor_primaria}; margin-bottom: 15px; font-weight: 600; 
                   border-bottom: 2px solid {cor_primaria}; padding-bottom: 8px;">{titulo}</h4>

        <!-- Resumo Principal -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <div style="text-align: center; background: rgba(0,123,255,0.1); padding: 12px; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #007bff;">{stats.get('jogos_total', 0)}</div>
                <div style="font-size: 12px; color: #6c757d;">JOGOS</div>
            </div>
            <div style="text-align: center; background: rgba(40,167,69,0.1); padding: 12px; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #28a745;">{stats.get('vitorias_total', 0)}</div>
                <div style="font-size: 12px; color: #6c757d;">VITÓRIAS</div>
            </div>
            <div style="text-align: center; background: rgba(255,193,7,0.1); padding: 12px; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #ffc107;">{stats.get('empates_total', 0)}</div>
                <div style="font-size: 12px; color: #6c757d;">EMPATES</div>
            </div>
            <div style="text-align: center; background: rgba(220,53,69,0.1); padding: 12px; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: #dc3545;">{stats.get('derrotas_total', 0)}</div>
                <div style="font-size: 12px; color: #6c757d;">DERROTAS</div>
            </div>
        </div>

        <!-- Aproveitamento em destaque -->
        {f'<div style="text-align: center; background: linear-gradient(135deg, {cor_primaria}20, {cor_primaria}10); padding: 15px; border-radius: 10px; margin-bottom: 20px;"><div style="font-size: 28px; font-weight: bold; color: {cor_primaria};">{aproveitamento:.1f}%</div><div style="font-size: 14px; color: #495057; font-weight: 500;">APROVEITAMENTO</div></div>' if aproveitamento is not None else ''}

        <!-- Gols e Médias -->
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h6 style="color: #495057; margin-bottom: 10px;">⚽ Estatísticas de Gols</h6>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; text-align: center;">
                <div>
                    <div style="font-weight: bold; color: #28a745;">{stats.get('gols_marcados_total', 0)}</div>
                    <small style="color: #6c757d;">Gols Feitos</small>
                </div>
                <div>
                    <div style="font-weight: bold; color: #dc3545;">{stats.get('gols_sofridos_total', 0)}</div>
                    <small style="color: #6c757d;">Gols Sofridos</small>
                </div>
                <div>
                    <div style="font-weight: bold; color: #17a2b8;">{stats.get('media_gols_marcados', 0):.1f}</div>
                    <small style="color: #6c757d;">Média/Jogo</small>
                </div>
                <div>
                    <div style="font-weight: bold; color: #fd7e14;">{stats.get('media_gols_sofridos', 0):.1f}</div>
                    <small style="color: #6c757d;">Sofridos/Jogo</small>
                </div>
            </div>
        </div>

        <!-- Outras Estatísticas -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div style="background: #e9ecef; padding: 12px; border-radius: 8px;">
                <h6 style="color: #495057; margin-bottom: 8px;">🎯 Eficiência</h6>
                <div style="font-size: 14px;">
                    <div>Clean Sheets: <strong>{stats.get('jogos_sem_sofrer', 0)}</strong></div>
                    <div>Não Marcou: <strong>{stats.get('jogos_sem_marcar', 0)}</strong></div>
                    {f'<div>Clean Sheet %: <strong>{stats.get("clean_sheet_percentual", 0):.1f}%</strong></div>' if 'clean_sheet_percentual' in stats else ''}
                </div>
            </div>
            <div style="background: #e9ecef; padding: 12px; border-radius: 8px;">
                <h6 style="color: #495057; margin-bottom: 8px;">🃏 Disciplina</h6>
                <div style="font-size: 14px;">
                    <div>🟨 Amarelos: <strong>{stats.get('cartoes_amarelos', 0)}</strong></div>
                    <div>🟥 Vermelhos: <strong>{stats.get('cartoes_vermelhos', 0)}</strong></div>
                    <div>⚽ Pênaltis: <strong>{stats.get('penaltis_marcados', 0)}/{stats.get('penaltis_perdidos', 0)}</strong></div>
                </div>
            </div>
        </div>

        {info_extra}
    </div>
    """


def criar_card_estatisticas_nativo(titulo, stats, cor="blue"):
    """
    Cria um card de estatísticas usando componentes nativos do Streamlit

    Args:
        titulo (str): Título do card
        stats (dict): Dados das estatísticas
        cor (str): Cor do tema (não usado, mantido para compatibilidade)
    """
    if not stats:
        st.warning(f"📊 {titulo}: Dados não disponíveis")
        return

    with st.container():
        st.markdown(f"#### 📊 {titulo}")

        # Primeira linha de métricas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Jogos", stats.get('jogos_total', 0))
        with col2:
            st.metric("Vitórias", stats.get('vitorias_total', 0))
        with col3:
            st.metric("Empates", stats.get('empates_total', 0))
        with col4:
            st.metric("Derrotas", stats.get('derrotas_total', 0))

        # Segunda linha de métricas
        col5, col6, col7, col8 = st.columns(4)

        with col5:
            st.metric("Gols Feitos", stats.get('gols_marcados_total', 0))
        with col6:
            st.metric("Gols Sofridos", stats.get('gols_sofridos_total', 0))
        with col7:
            # Calcular aproveitamento
            aproveitamento = 0
            if stats.get('jogos_total', 0) > 0:
                aproveitamento = ((stats.get('vitorias_total', 0) * 3 +
                                   stats.get('empates_total', 0)) /
                                  (stats.get('jogos_total', 1) * 3) * 100)
            st.metric("Aproveitamento", f"{aproveitamento:.1f}%")
        with col8:
            saldo = stats.get('gols_marcados_total', 0) - stats.get('gols_sofridos_total', 0)
            delta_text = "Positivo" if saldo > 0 else "Negativo" if saldo < 0 else "Neutro"
            st.metric("Saldo de Gols", saldo, delta=delta_text)

        # Terceira linha - estatísticas adicionais
        if any(stats.get(key, 0) for key in ['jogos_sem_sofrer', 'jogos_sem_marcar', 'cartoes_amarelos']):
            st.markdown("---")
            col9, col10, col11, col12 = st.columns(4)

            with col9:
                st.metric("Clean Sheets", stats.get('jogos_sem_sofrer', 0))
            with col10:
                st.metric("Não Marcou", stats.get('jogos_sem_marcar', 0))
            with col11:
                st.metric("🟨 Amarelos", stats.get('cartoes_amarelos', 0))
            with col12:
                st.metric("🟥 Vermelhos", stats.get('cartoes_vermelhos', 0))


def mostrar_modal_estatisticas(time_id, time_nome, liga_id, temporada):
    """Mostra modal com estatísticas detalhadas do time"""

    @st.dialog(f"📊 Estatísticas Detalhadas - {time_nome} (Temporada {temporada})",width="large")
    def modal_estatisticas():
        # Buscar dados da liga específica
        stats_liga = buscar_ou_salvar_estatisticas(time_id, liga_id, temporada)

        # Buscar dados da temporada completa
        stats_temporada = buscar_estatisticas_temporada_completa(time_id, temporada)

        if not stats_liga and not stats_temporada:
            st.warning("❌ Estatísticas não disponíveis para este time")
            if st.button("Fechar"):
                st.rerun()
            return

        # Abas para melhor organização
        tab1, tab2 = st.tabs(["🏆 Liga Atual", "🌍 Temporada Completa"])

        with tab1:
            st.markdown("### 📈 Desempenho na Liga Atual")
            if stats_liga:
                nome_liga = buscar_nome_liga(liga_id)
                card_html = criar_card_estatisticas(f"📈 {nome_liga}", stats_liga, "#28a745")
                st.markdown(card_html, unsafe_allow_html=True)

                # Informações adicionais da liga
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if stats_liga.get('jogos_total', 0) > 0:
                        st.metric("Aproveitamento Liga",
                                  f"{((stats_liga.get('vitorias_total', 0) * 3 + stats_liga.get('empates_total', 0)) / (stats_liga.get('jogos_total', 1) * 3) * 100):.1f}%")
                    else:
                        st.metric("Aproveitamento Liga", "0.0%")

                with col2:
                    saldo = stats_liga.get('gols_marcados_total', 0) - stats_liga.get('gols_sofridos_total', 0)
                    st.metric("Saldo de Gols", saldo,
                              delta=f"{'Positivo' if saldo > 0 else 'Negativo' if saldo < 0 else 'Neutro'}")

                with col3:
                    st.metric("Jogos em Casa", f"{stats_liga.get('jogos_casa', 0)}")

                with col4:
                    st.metric("Jogos Fora", f"{stats_liga.get('jogos_fora', 0)}")

            else:
                st.info("📝 Dados da liga atual não disponíveis")

        with tab2:
            st.markdown("### 🏅 Desempenho Geral na Temporada")
            if stats_temporada:
                card_html = criar_card_estatisticas(f"🏅 Todas as Competições {temporada}", stats_temporada, "#007bff")
                st.markdown(card_html, unsafe_allow_html=True)

                # Comparação Liga vs Temporada
                if stats_liga and stats_temporada.get('total_ligas', 0) > 1:
                    st.markdown("---")
                    st.markdown("#### ⚖️ Liga Atual vs Temporada Completa")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        liga_aproveit = ((stats_liga.get('vitorias_total', 0) * 3 + stats_liga.get('empates_total',
                                                                                                   0)) / max(
                            stats_liga.get('jogos_total', 1) * 3, 1) * 100)
                        temp_aproveit = stats_temporada.get('aproveitamento_percentual', 0)

                        st.metric(
                            "Aproveitamento",
                            f"{temp_aproveit:.1f}%",
                            delta=f"{temp_aproveit - liga_aproveit:.1f}% vs liga atual"
                        )

                    with col2:
                        st.metric(
                            "Total de Jogos",
                            stats_temporada.get('jogos_total', 0),
                            delta=f"+{stats_temporada.get('jogos_total', 0) - stats_liga.get('jogos_total', 0)} jogos a mais"
                        )

                    with col3:
                        st.metric(
                            "Gols por Jogo",
                            f"{stats_temporada.get('media_gols_marcados', 0):.1f}",
                            delta=f"{stats_temporada.get('media_gols_marcados', 0) - stats_liga.get('media_gols_marcados', 0):.1f}" if stats_liga.get(
                                'media_gols_marcados') else None
                        )

                    with col4:
                        st.metric(
                            "Competições",
                            f"{stats_temporada.get('total_ligas', 1)} liga(s)",
                            delta="múltiplas competições" if stats_temporada.get('total_ligas',
                                                                                 1) > 1 else "competição única"
                        )
            else:
                st.info("📝 Dados da temporada completa não disponíveis")

        # Botão para fechar
        st.markdown("---")
        if st.button("✅ Fechar", use_container_width=True, type="primary"):
            st.rerun()

    modal_estatisticas()


def mostrar_modal_comparacao(time_casa_id, time_casa_nome, time_fora_id, time_fora_nome, liga_id, temporada):
    """Mostra modal comparando dois times"""

    @st.dialog(f"⚔️ Comparação: {time_casa_nome} × {time_fora_nome}", width="large")
    def modal_comparacao():
        # Buscar dados dos dois times
        stats_casa_liga = buscar_ou_salvar_estatisticas(time_casa_id, liga_id, temporada)
        stats_fora_liga = buscar_ou_salvar_estatisticas(time_fora_id, liga_id, temporada)

        stats_casa_temp = buscar_estatisticas_temporada_completa(time_casa_id, temporada)
        stats_fora_temp = buscar_estatisticas_temporada_completa(time_fora_id, temporada)

        # Abas para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["🏆 Liga Atual", "🌍 Temporada Completa", "⚖️ Comparação Direta"])

        with tab1:
            nome_liga = buscar_nome_liga(liga_id)
            st.markdown(f"### 📊 Estatísticas na {nome_liga}")

            col1, col2 = st.columns(2)

            with col1:
                if stats_casa_liga:
                    criar_card_estatisticas_nativo(f"🏠 {time_casa_nome}", stats_casa_liga, "green")
                else:
                    st.warning(f"Dados de {time_casa_nome} não disponíveis")

            with col2:
                if stats_fora_liga:
                    criar_card_estatisticas_nativo(f"✈️ {time_fora_nome}", stats_fora_liga, "red")
                else:
                    st.warning(f"Dados de {time_fora_nome} não disponíveis")

        with tab2:
            st.markdown(f"### 🏅 Estatísticas da Temporada {temporada}")

            col1, col2 = st.columns(2)

            with col1:
                if stats_casa_temp:
                    criar_card_estatisticas_nativo(f"🏠 {time_casa_nome}", stats_casa_temp, "green")
                else:
                    st.warning(f"Dados de temporada de {time_casa_nome} não disponíveis")

            with col2:
                if stats_fora_temp:
                    criar_card_estatisticas_nativo(f"✈️ {time_fora_nome}", stats_fora_temp, "red")
                else:
                    st.warning(f"Dados de temporada de {time_fora_nome} não disponíveis")

        with tab3:
            st.markdown("### ⚔️ Análise Comparativa Detalhada")

            # Escolher melhor conjunto de dados disponível
            dados_casa = stats_casa_temp if stats_casa_temp else stats_casa_liga
            dados_fora = stats_fora_temp if stats_fora_temp else stats_fora_liga

            if dados_casa and dados_fora:
                # Seção de vantagens
                st.markdown("#### 🎯 Vantagens Competitivas")

                # Calcular aproveitamentos
                aproveit_casa = 0
                aproveit_fora = 0

                if 'aproveitamento_percentual' in dados_casa:
                    aproveit_casa = dados_casa.get('aproveitamento_percentual', 0)
                elif dados_casa.get('jogos_total', 0) > 0:
                    aproveit_casa = (dados_casa.get('vitorias_total', 0) * 3 + dados_casa.get('empates_total', 0)) / (
                                dados_casa.get('jogos_total', 1) * 3) * 100

                if 'aproveitamento_percentual' in dados_fora:
                    aproveit_fora = dados_fora.get('aproveitamento_percentual', 0)
                elif dados_fora.get('jogos_total', 0) > 0:
                    aproveit_fora = (dados_fora.get('vitorias_total', 0) * 3 + dados_fora.get('empates_total', 0)) / (
                                dados_fora.get('jogos_total', 1) * 3) * 100

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    melhor_aproveit = "🏠 Casa" if aproveit_casa > aproveit_fora else "✈️ Fora"
                    st.metric(
                        "Melhor Aproveitamento",
                        melhor_aproveit,
                        f"{max(aproveit_casa, aproveit_fora):.1f}%"
                    )

                with col2:
                    melhor_ataque = "🏠 Casa" if dados_casa.get('media_gols_marcados', 0) > dados_fora.get(
                        'media_gols_marcados', 0) else "✈️ Fora"
                    st.metric(
                        "Melhor Ataque",
                        melhor_ataque,
                        f"{max(dados_casa.get('media_gols_marcados', 0), dados_fora.get('media_gols_marcados', 0)):.1f} gols/jogo"
                    )

                with col3:
                    melhor_defesa = "🏠 Casa" if dados_casa.get('media_gols_sofridos', 0) < dados_fora.get(
                        'media_gols_sofridos', 0) else "✈️ Fora"
                    st.metric(
                        "Melhor Defesa",
                        melhor_defesa,
                        f"{min(dados_casa.get('media_gols_sofridos', 0), dados_fora.get('media_gols_sofridos', 0)):.1f} gols sofridos/jogo"
                    )

                with col4:
                    clean_casa = dados_casa.get('jogos_sem_sofrer', 0) / max(dados_casa.get('jogos_total', 1), 1) * 100
                    clean_fora = dados_fora.get('jogos_sem_sofrer', 0) / max(dados_fora.get('jogos_total', 1), 1) * 100

                    melhor_clean = "🏠 Casa" if clean_casa > clean_fora else "✈️ Fora"
                    st.metric(
                        "Mais Clean Sheets",
                        melhor_clean,
                        f"{max(clean_casa, clean_fora):.1f}%"
                    )

                # Tabela comparativa detalhada
                st.markdown("---")
                st.markdown("#### 📋 Comparação Detalhada")

                comparacao_data = {
                    "Estatística": [
                        "🏟️ Total de Jogos",
                        "🏆 Vitórias",
                        "🤝 Empates",
                        "😞 Derrotas",
                        "⚽ Gols Marcados",
                        "🚫 Gols Sofridos",
                        "📊 Média Gols/Jogo",
                        "📊 Média Sofre/Jogo",
                        "🎯 Clean Sheets",
                        "😔 Não Marcou",
                        "🟨 Cartões Amarelos",
                        "🟥 Cartões Vermelhos",
                        "💯 Aproveitamento (%)"
                    ],
                    f"🏠 {time_casa_nome}": [
                        dados_casa.get('jogos_total', 0),
                        dados_casa.get('vitorias_total', 0),
                        dados_casa.get('empates_total', 0),
                        dados_casa.get('derrotas_total', 0),
                        dados_casa.get('gols_marcados_total', 0),
                        dados_casa.get('gols_sofridos_total', 0),
                        f"{dados_casa.get('media_gols_marcados', 0):.1f}",
                        f"{dados_casa.get('media_gols_sofridos', 0):.1f}",
                        dados_casa.get('jogos_sem_sofrer', 0),
                        dados_casa.get('jogos_sem_marcar', 0),
                        dados_casa.get('cartoes_amarelos', 0),
                        dados_casa.get('cartoes_vermelhos', 0),
                        f"{aproveit_casa:.1f}%"
                    ],
                    f"✈️ {time_fora_nome}": [
                        dados_fora.get('jogos_total', 0),
                        dados_fora.get('vitorias_total', 0),
                        dados_fora.get('empates_total', 0),
                        dados_fora.get('derrotas_total', 0),
                        dados_fora.get('gols_marcados_total', 0),
                        dados_fora.get('gols_sofridos_total', 0),
                        f"{dados_fora.get('media_gols_marcados', 0):.1f}",
                        f"{dados_fora.get('media_gols_sofridos', 0):.1f}",
                        dados_fora.get('jogos_sem_sofrer', 0),
                        dados_fora.get('jogos_sem_marcar', 0),
                        dados_fora.get('cartoes_amarelos', 0),
                        dados_fora.get('cartoes_vermelhos', 0),
                        f"{aproveit_fora:.1f}%"
                    ]
                }

                df_comparacao = pd.DataFrame(comparacao_data)

                st.dataframe(
                    df_comparacao,
                    column_config={
                        "Estatística": st.column_config.TextColumn("Estatística", width="medium"),
                        f"🏠 {time_casa_nome}": st.column_config.TextColumn(f"🏠 {time_casa_nome}", width="medium"),
                        f"✈️ {time_fora_nome}": st.column_config.TextColumn(f"✈️ {time_fora_nome}", width="medium"),
                        "Critério": st.column_config.TextColumn("Critério", help="Critério usado: 'Gols' (ambos marcam) ou 'Resultado/Gol' (favorito + gol)", width="medium"),

                    },
                    hide_index=True,
                    use_container_width=True
                )

                # Insights da análise
                st.markdown("---")
                st.markdown("#### 💡 Insights da Análise")

                insights = []

                # Análise de aproveitamento
                if abs(aproveit_casa - aproveit_fora) > 10:
                    melhor = time_casa_nome if aproveit_casa > aproveit_fora else time_fora_nome
                    insights.append(
                        f"🎯 **{melhor}** tem aproveitamento significativamente superior ({abs(aproveit_casa - aproveit_fora):.1f}% de diferença)")

                # Análise de gols
                diff_gols = abs(dados_casa.get('media_gols_marcados', 0) - dados_fora.get('media_gols_marcados', 0))
                if diff_gols > 0.3:
                    if dados_casa.get('media_gols_marcados', 0) > dados_fora.get('media_gols_marcados', 0):
                        insights.append(
                            f"⚽ **{time_casa_nome}** tem ataque superior, marcando {diff_gols:.1f} gols a mais por jogo")
                    else:
                        insights.append(
                            f"⚽ **{time_fora_nome}** tem ataque superior, marcando {diff_gols:.1f} gols a mais por jogo")

                # Análise de defesa
                diff_def = abs(dados_casa.get('media_gols_sofridos', 0) - dados_fora.get('media_gols_sofridos', 0))
                if diff_def > 0.3:
                    if dados_casa.get('media_gols_sofridos', 0) < dados_fora.get('media_gols_sofridos', 0):
                        insights.append(
                            f"🛡️ **{time_casa_nome}** tem defesa mais sólida, sofrendo {diff_def:.1f} gols a menos por jogo")
                    else:
                        insights.append(
                            f"🛡️ **{time_fora_nome}** tem defesa mais sólida, sofrendo {diff_def:.1f} gols a menos por jogo")

                # Análise de disciplina
                cartoes_casa = dados_casa.get('cartoes_amarelos', 0) + dados_casa.get('cartoes_vermelhos', 0) * 2
                cartoes_fora = dados_fora.get('cartoes_amarelos', 0) + dados_fora.get('cartoes_vermelhos', 0) * 2

                if abs(cartoes_casa - cartoes_fora) > 5:
                    if cartoes_casa > cartoes_fora:
                        insights.append(
                            f"🟨 **{time_casa_nome}** tem mais problemas disciplinares ({cartoes_casa - cartoes_fora} cartões a mais)")
                    else:
                        insights.append(
                            f"🟨 **{time_fora_nome}** tem mais problemas disciplinares ({cartoes_fora - cartoes_casa} cartões a mais)")

                # Análise de clean sheets
                if abs(clean_casa - clean_fora) > 10:
                    melhor_clean_nome = time_casa_nome if clean_casa > clean_fora else time_fora_nome
                    insights.append(
                        f"🎯 **{melhor_clean_nome}** mantém a meta inviolada com mais frequência ({abs(clean_casa - clean_fora):.1f}% de diferença)")

                if insights:
                    for insight in insights:
                        st.write(f"• {insight}")
                else:
                    st.info("• Os times apresentam desempenho equilibrado nas principais métricas analisadas")

            else:
                st.warning("⚠️ Dados insuficientes para comparação completa")

                if not dados_casa:
                    st.write(f"❌ Dados de **{time_casa_nome}** não disponíveis")
                if not dados_fora:
                    st.write(f"❌ Dados de **{time_fora_nome}** não disponíveis")

        # Botão para fechar
        st.markdown("---")
        if st.button("✅ Fechar Comparação", use_container_width=True, type="primary"):
            st.rerun()

    modal_comparacao()


def exportar_para_excel(df):
    """Exporta DataFrame para Excel com formatação melhorada incluindo coluna Critério"""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Jogos e Estatísticas', index=False)

        # Obter o objeto workbook e worksheet
        workbook = writer.book
        worksheet = writer.sheets['Jogos e Estatísticas']

        # ===== FORMATOS DE FORMATAÇÃO =====

        # Formato do cabeçalho
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BD',
            'border': 1,
            'font_size': 11
        })

        # Formato para time casa (verde claro)
        home_format = workbook.add_format({
            'bg_color': '#E8F5E9',
            'border': 1,
            'align': 'center'
        })

        # Formato para time fora (vermelho claro)
        away_format = workbook.add_format({
            'bg_color': '#FFEBEE',
            'border': 1,
            'align': 'center'
        })

        # NOVOS FORMATOS PARA COLUNA CRITÉRIO
        criterio_gols_format = workbook.add_format({
            'bg_color': '#FFF3E0',  # Laranja claro para "Gols"
            'border': 1,
            'bold': True,
            'align': 'center',
            'font_color': '#E65100'  # Texto laranja escuro
        })

        criterio_resultado_format = workbook.add_format({
            'bg_color': '#E3F2FD',  # Azul claro para "Resultado/Gol"
            'border': 1,
            'bold': True,
            'align': 'center',
            'font_color': '#0D47A1'  # Texto azul escuro
        })

        # Formato para células normais
        normal_format = workbook.add_format({
            'border': 1,
            'align': 'center'
        })

        # Formato para números (odds)
        number_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'num_format': '0.00'
        })

        # ===== IDENTIFICAR COLUNAS IMPORTANTES =====

        col_casa = None
        col_fora = None
        col_criterio = None
        col_pais = None
        colunas_odds = []  # Para formatar odds como números

        for idx, col in enumerate(df.columns):
            col_lower = col.lower()

            # Identificar colunas de times
            if 'casa' in col_lower and ('time' in col_lower or col.strip() == ' '):
                col_casa = idx
            elif 'fora' in col_lower and ('time' in col_lower or col.strip() == '  '):
                col_fora = idx
            # Identificar coluna critério
            elif 'critério' in col_lower or 'criterio' in col_lower:
                col_criterio = idx
            # Identificar coluna país
            elif 'país' in col_lower or 'pais' in col_lower:
                col_pais = idx
            # Identificar colunas de odds (para formatação numérica)
            elif any(word in col_lower for word in ['odd', 'casa', 'fora', 'gols']) and 'time' not in col_lower:
                if col not in ['Time Casa', 'Time Fora', 'Gols Casa', 'Gols Fora']:
                    colunas_odds.append(idx)

        # ===== FORMATAÇÃO DO CABEÇALHO =====

        for col_num, value in enumerate(df.columns.values):
            # Cabeçalho especial para coluna critério
            if col_num == col_criterio:
                criterio_header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#FFE0B2',  # Laranja mais claro
                    'border': 2,
                    'font_size': 11,
                    'font_color': '#E65100'
                })
                worksheet.write(0, col_num, value, criterio_header_format)
            # Cabeçalho especial para coluna país
            elif col_num == col_pais:
                pais_header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#E1F5FE',  # Azul claro
                    'border': 2,
                    'font_size': 11
                })
                worksheet.write(0, col_num, value, pais_header_format)
            else:
                worksheet.write(0, col_num, value, header_format)

        # ===== FORMATAÇÃO DAS CÉLULAS DE DADOS =====

        for row_num in range(1, len(df) + 1):
            for col_num in range(len(df.columns)):
                value = df.iloc[row_num - 1, col_num]

                # Formatação especial para coluna Critério
                if col_num == col_criterio:
                    if value == 'Gols':
                        worksheet.write(row_num, col_num, value, criterio_gols_format)
                    elif value == 'Resultado/Gol':
                        worksheet.write(row_num, col_num, value, criterio_resultado_format)
                    else:
                        # Célula vazia ou outro valor
                        worksheet.write(row_num, col_num, value, normal_format)

                # Formatação para time casa (verde)
                elif col_num == col_casa:
                    worksheet.write(row_num, col_num, value, home_format)

                # Formatação para time fora (vermelho)
                elif col_num == col_fora:
                    worksheet.write(row_num, col_num, value, away_format)

                # Formatação para colunas de odds (numéricas)
                elif col_num in colunas_odds:
                    try:
                        # Tentar converter para float se for numérico
                        numeric_value = float(value) if pd.notna(value) and str(value).replace('.', '').replace(',',
                                                                                                                '').isdigit() else value
                        worksheet.write(row_num, col_num, numeric_value, number_format)
                    except (ValueError, TypeError):
                        worksheet.write(row_num, col_num, value, normal_format)

                # Formatação padrão para outras células
                else:
                    worksheet.write(row_num, col_num, value, normal_format)

        # ===== AJUSTAR LARGURA DAS COLUNAS =====

        for i, col in enumerate(df.columns):
            # Largura especial para algumas colunas
            if i == col_criterio:
                worksheet.set_column(i, i, 15)  # Critério um pouco mais largo
            elif 'Time' in col:
                worksheet.set_column(i, i, 18)  # Times mais largos
            elif col.strip() in [' ', '  ']:  # Colunas de escudo
                worksheet.set_column(i, i, 5)  # Escudos pequenos
            elif any(word in col.lower() for word in ['odd', 'gols']):
                worksheet.set_column(i, i, 12)  # Odds médias
            else:
                # Largura automática baseada no conteúdo
                column_len = max(
                    df[col].astype(str).str.len().max() if not df[col].empty else 0,
                    len(col)
                ) + 3
                worksheet.set_column(i, i, min(column_len, 25))  # Máximo 25 caracteres

        # ===== ADICIONAR FILTROS =====

        # Adicionar filtro automático
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)

        # ===== CONGELAR PAINÉIS =====

        # Congelar primeira linha (cabeçalho) e primeiras 3 colunas (Horário, País, Liga)
        worksheet.freeze_panes(1, 3)

        # ===== ADICIONAR TOTAIS/ESTATÍSTICAS =====

        # Adicionar linha de totais se houver coluna critério
        if col_criterio is not None:
            total_row = len(df) + 2

            # Contar critérios
            criterios_count = df.iloc[:, col_criterio].value_counts()

            # Escrever estatísticas
            worksheet.write(total_row, 0, 'TOTAIS:', workbook.add_format({'bold': True, 'bg_color': '#F5F5F5'}))

            col_atual = 1
            for criterio, count in criterios_count.items():
                if criterio == 'Gols':
                    format_total = workbook.add_format({'bold': True, 'bg_color': '#FFF3E0', 'border': 1})
                elif criterio == 'Resultado/Gol':
                    format_total = workbook.add_format({'bold': True, 'bg_color': '#E3F2FD', 'border': 1})
                else:
                    format_total = workbook.add_format({'bold': True, 'bg_color': '#F5F5F5', 'border': 1})

                worksheet.write(total_row, col_atual, f'{criterio}: {count}', format_total)
                col_atual += 1

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
    st.session_state.comparacao_modal = None
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
    st.session_state.time_selecionado_modal = None
    st.session_state.comparacao_modal = None

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
                f"• Critério 1 (Resultado/Gol): Time casa odd ≥ 1.5 E Time fora marca gol (Over 0.5) ≥ 1.5\n"
                f"• Critério 2 (Resultado/Gol): Time fora odd ≥ 1.5 E Time casa marca gol (Over 0.5) ≥ 1.5\n"
                f"• Critério 3 (Gols): Time casa marca gol (Over 0.5) ≥ 1.5 E Time fora marca gol (Over 0.5) ≥ 1.5\n"
                f"\n🏷️ Veja a coluna 'Critério' para identificar qual regra foi aplicada")

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
            st.write("🏁 = Coluna País antes da Liga")
            st.write("🏷️ = Coluna Critério identifica a regra usada")  # ← NOVA INFORMAÇÃO
        with col2:
            st.write("**Critérios de Seleção Automática:**")
            st.write("1️⃣ Casa ≥1.5 E Fora marca(0.5) ≥1.5 → 'Resultado/Gol'")  # ← ATUALIZADO
            st.write("2️⃣ Fora ≥1.5 E Casa marca(0.5) ≥1.5 → 'Resultado/Gol'")  # ← ATUALIZADO
            st.write("3️⃣ Casa marca(0.5) ≥1.5 E Fora marca(0.5) ≥1.5 → 'Gols'")  # ← ATUALIZADO
            st.write("✓ = Marque jogos para buscar estatísticas")
            st.write("🔗 = Clique nas linhas para ver estatísticas")

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
        'Selecionar', 'id_jogo', 'horario', 'país', 'liga',  # ← PAÍS ADICIONADO
        'escudo_casa', 'Time Casa', 'escudo_fora', 'Time Fora',
        'odd_casa', 'odd_empate', 'odd_fora',
        'Gols Casa', 'Gols Fora',
        'criterio_selecao', 'selecao_automatica'  # ← CRITÉRIO ADICIONADO
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
            'criterio_selecao': 'Critério',
            'escudo_casa': ' ',
            'escudo_fora': '  ',
            'país': 'País',  # ← ADICIONAR ESTA LINHA
        }),
        column_config={
            # ... outras configurações ...
            "País": st.column_config.TextColumn(  # ← NOVA CONFIGURAÇÃO
                "País",
                help="País da liga",
                width="small"
            ),
            "liga": st.column_config.TextColumn("Liga", help="Liga/Competição", width="medium"),
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
                width="medium"
            ),
            "  ": st.column_config.ImageColumn(
                "  ",  # Escudo fora
                help="Escudo do time de fora",
                width="small"
            ),
            "Time Fora": st.column_config.TextColumn(
                "Time Fora",
                help="Time de fora - Clique na linha para ver estatísticas",
                width="medium"
            ),
            "odd_casa": st.column_config.NumberColumn("Odd Casa", format="%.2f", width="small"),
            "odd_empate": st.column_config.NumberColumn("Odd X", format="%.2f", width="small"),
            "odd_fora": st.column_config.NumberColumn("Odd Fora", format="%.2f", width="small"),
            "Gols Casa": st.column_config.TextColumn("Gols Casa", width="medium"),
            "Gols Fora": st.column_config.TextColumn("Gols Fora", width="medium"),
            "Critério": st.column_config.TextColumn(
                "Critério",
                help="Tipo de critério: 'Gols' ou 'Resultado/Gol'",
                width="small"
            ),
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

            col1, col2, col3 = st.columns(3)
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

            with col3:
                if st.button(f"⚔️ Comparar Times", use_container_width=True, type="primary"):
                    st.session_state.comparacao_modal = {
                        'time_casa_id': selected_row['team_home_id'],
                        'time_casa_nome': selected_row['time_casa'],
                        'time_fora_id': selected_row['team_away_id'],
                        'time_fora_nome': selected_row['time_fora'],
                        'liga_id': selected_row['league_id'],
                        'temporada': selected_row['season']
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
        'id_jogo', 'horario', 'país', 'liga',
        'escudo_casa', 'Time Casa', 'escudo_fora', 'Time Fora',
        'odd_casa', 'odd_empate', 'odd_fora', 'Gols Casa', 'Gols Fora',
        'criterio_selecao'
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
        'id_jogo': 'ID',
        'horario': 'Horário',
        'país': 'País',
        'liga': 'Liga',
        'escudo_casa': ' ',  # Espaço para escudo casa
        'escudo_fora': '  ',  # Dois espaços para escudo fora
        'odd_casa': 'Odd Casa',
        'odd_empate': 'Odd X',
        'odd_fora': 'Odd Fora',
        'criterio_selecao': 'Critério',
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
                label="📥 Baixar Excel Completo",
                data=excel_file,
                file_name=f"odds_estatisticas_criterios_{data_selecionada.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Excel com formatação especial para critérios e estatísticas completas"
            )

        with col_export2:
            # Botão adicional para exportar apenas jogos selecionados
            if st.session_state.jogos_selecionados:
                df_selecionados_raw = df_final_display[
                    df_final_display['id_jogo'].isin(st.session_state.jogos_selecionados)]
                colunas_para_mostrar_selecionados = [col for col in colunas_basicas + colunas_estatisticas if
                                                     col in df_selecionados_raw.columns]
                df_selecionados = df_selecionados_raw[colunas_para_mostrar_selecionados].rename(columns={
                    'horario': 'Horário',
                    'país': 'País',
                    'liga': 'Liga',
                    'escudo_casa': ' ',
                    'escudo_fora': '  ',
                    'odd_casa': 'Odd Casa',
                    'odd_empate': 'Odd X',
                    'odd_fora': 'Odd Fora',
                    'criterio_selecao': 'Critério',
                    'jogos': 'Jogos (C-F)',
                    'vitorias': 'Vitórias (C-F)',
                    'derrotas': 'Derrotas (C-F)',
                    'gols_marcados': 'Gols Marc. (C-F)',
                    'gols_sofridos': 'Gols Sofr. (C-F)',
                    'jogos_sem_marcar': 'J.S.Marcar (C-F)'
                }).fillna("N/A")

                if not df_selecionados.empty:
                    excel_selecionados = exportar_para_excel(df_selecionados)
                    st.download_button(
                        label="📋 Apenas Selecionados",
                        data=excel_selecionados,
                        file_name=f"jogos_selecionados_{data_selecionada.strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Excel apenas com jogos selecionados"
                    )

        with col_export3:
            # Mostrar estatísticas rápidas
            if 'Critério' in df_final_renamed.columns:
                criterios_stats = df_final_renamed['Critério'].value_counts()
                st.write("**Resumo dos Critérios:**")
                for criterio, count in criterios_stats.items():
                    if criterio:  # Não mostrar valores vazios
                        if criterio == 'Gols':
                            st.write(f"⚽ {criterio}: {count} jogos")
                        elif criterio == 'Resultado/Gol':
                            st.write(f"🎯 {criterio}: {count} jogos")

    # Mostrar tabela final
    st.markdown("### 📋 Resultados Finais")

    # Configurar exibição da tabela final
    column_config_final = {
        "ID": st.column_config.NumberColumn("ID", width="small"),
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

            col1, col2, col3 = st.columns(3)
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

            with col3:
                if st.button(f"⚔️ Comparar Ambos", use_container_width=True, key="final_comparar", type="primary"):
                    st.session_state.comparacao_modal = {
                        'time_casa_id': selected_row['team_home_id'],
                        'time_casa_nome': selected_row['time_casa'],
                        'time_fora_id': selected_row['team_away_id'],
                        'time_fora_nome': selected_row['time_fora'],
                        'liga_id': selected_row['league_id'],
                        'temporada': selected_row['season']
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
            "- 📊 Clique nas linhas para ver estatísticas individuais\n"
            "- ⚔️ Use 'Comparar Times' para análise lado a lado\n"
            "- ✓ Marque jogos para análise comparativa em lote"
        )
    with col_info2:
        st.info(
            f"🏢 **Bookmaker:** {BOOKMAKERS[id_bookmaker]}\n"
            f"📅 **Data:** {data_selecionada.strftime('%d/%m/%Y')}\n"
            f"🕐 **Horários:** Brasília (UTC-3)\n"
            f"📊 **Jogos selecionados:** {len(st.session_state.jogos_selecionados)}"
        )

    if st.session_state.estatisticas_carregadas:
        st.success(
            "✅ Estatísticas carregadas! Clique nas linhas da tabela para ver detalhes individuais ou usar 'Comparar Times' para análise completa.")

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

# Verificar se há comparação selecionada para mostrar modal
if st.session_state.comparacao_modal:
    comp = st.session_state.comparacao_modal
    mostrar_modal_comparacao(
        comp['time_casa_id'],
        comp['time_casa_nome'],
        comp['time_fora_id'],
        comp['time_fora_nome'],
        comp['liga_id'],
        comp['temporada']
    )
    st.session_state.comparacao_modal = None