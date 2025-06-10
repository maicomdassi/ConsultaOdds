-- View para agregar estatísticas de times por temporada (todas as ligas)
-- Esta view soma os dados de todas as ligas que um time participou em uma temporada específica

CREATE OR REPLACE VIEW v_estatisticas_temporada AS
SELECT 
    time_id,
    temporada,
    
    -- Contagem de ligas participantes
    COUNT(DISTINCT liga_id) as total_ligas,
    STRING_AGG(DISTINCT liga_id::text, ',') as ligas_participantes,
    
    -- Agregação de jogos
    SUM(jogos_total) as jogos_total,
    SUM(jogos_casa) as jogos_casa,
    SUM(jogos_fora) as jogos_fora,
    
    -- Agregação de resultados
    SUM(vitorias_total) as vitorias_total,
    SUM(vitorias_casa) as vitorias_casa,
    SUM(vitorias_fora) as vitorias_fora,
    
    SUM(empates_total) as empates_total,
    SUM(empates_casa) as empates_casa,
    SUM(empates_fora) as empates_fora,
    
    SUM(derrotas_total) as derrotas_total,
    SUM(derrotas_casa) as derrotas_casa,
    SUM(derrotas_fora) as derrotas_fora,
    
    -- Agregação de gols
    SUM(gols_marcados_total) as gols_marcados_total,
    SUM(gols_marcados_casa) as gols_marcados_casa,
    SUM(gols_marcados_fora) as gols_marcados_fora,
    
    SUM(gols_sofridos_total) as gols_sofridos_total,
    SUM(gols_sofridos_casa) as gols_sofridos_casa,
    SUM(gols_sofridos_fora) as gols_sofridos_fora,
    
    -- Cálculo de médias (baseado no total de jogos)
    CASE 
        WHEN SUM(jogos_total) > 0 THEN 
            ROUND(SUM(gols_marcados_total)::numeric / SUM(jogos_total)::numeric, 2)
        ELSE 0 
    END as media_gols_marcados,
    
    CASE 
        WHEN SUM(jogos_total) > 0 THEN 
            ROUND(SUM(gols_sofridos_total)::numeric / SUM(jogos_total)::numeric, 2)
        ELSE 0 
    END as media_gols_sofridos,
    
    -- Estatísticas especiais agregadas
    SUM(jogos_sem_marcar) as jogos_sem_marcar,
    SUM(jogos_sem_sofrer) as jogos_sem_sofrer,
    
    -- Disciplina agregada
    SUM(cartoes_amarelos) as cartoes_amarelos,
    SUM(cartoes_vermelhos) as cartoes_vermelhos,
    SUM(penaltis_marcados) as penaltis_marcados,
    SUM(penaltis_perdidos) as penaltis_perdidos,
    
    -- Cálculo do aproveitamento (%)
    CASE 
        WHEN SUM(jogos_total) > 0 THEN 
            ROUND(((SUM(vitorias_total) * 3 + SUM(empates_total))::numeric / (SUM(jogos_total) * 3)::numeric) * 100, 1)
        ELSE 0 
    END as aproveitamento_percentual,
    
    -- Saldo de gols
    (SUM(gols_marcados_total) - SUM(gols_sofridos_total)) as saldo_gols,
    
    -- Eficiência de clean sheets (%)
    CASE 
        WHEN SUM(jogos_total) > 0 THEN 
            ROUND((SUM(jogos_sem_sofrer)::numeric / SUM(jogos_total)::numeric) * 100, 1)
        ELSE 0 
    END as clean_sheet_percentual,
    
    -- Eficiência ofensiva (% de jogos que marcou)
    CASE 
        WHEN SUM(jogos_total) > 0 THEN 
            ROUND(((SUM(jogos_total) - SUM(jogos_sem_marcar))::numeric / SUM(jogos_total)::numeric) * 100, 1)
        ELSE 0 
    END as eficiencia_ofensiva_percentual,
    
    -- Informações de atualização
    MAX(atualizado_em) as ultima_atualizacao,
    COUNT(*) as registros_origem

FROM estatisticas_times 
GROUP BY time_id, temporada
ORDER BY temporada DESC, aproveitamento_percentual DESC;

-- Índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_v_estatisticas_temporada_time_season 
ON estatisticas_times(time_id, temporada);

CREATE INDEX IF NOT EXISTS idx_v_estatisticas_temporada_season 
ON estatisticas_times(temporada);

-- Comentários na view
COMMENT ON VIEW v_estatisticas_temporada IS 
'View que agrega estatísticas de times por temporada, somando dados de todas as ligas participantes';

COMMENT ON COLUMN v_estatisticas_temporada.time_id IS 
'ID do time';

COMMENT ON COLUMN v_estatisticas_temporada.temporada IS 
'Ano da temporada';

COMMENT ON COLUMN v_estatisticas_temporada.total_ligas IS 
'Número total de ligas/competições que o time participou na temporada';

COMMENT ON COLUMN v_estatisticas_temporada.aproveitamento_percentual IS 
'Percentual de aproveitamento de pontos na temporada (considerando 3 pontos por vitória)';

COMMENT ON COLUMN v_estatisticas_temporada.saldo_gols IS 
'Diferença entre gols marcados e sofridos na temporada';

-- Query de exemplo para testar a view
/*
-- Estatísticas agregadas de um time específico na temporada 2024
SELECT * FROM v_estatisticas_temporada 
WHERE time_id = 85 AND temporada = 2024;

-- Top 10 times com melhor aproveitamento na temporada 2024
SELECT 
    t.nome as time_nome,
    vt.total_ligas,
    vt.jogos_total,
    vt.vitorias_total,
    vt.empates_total,
    vt.derrotas_total,
    vt.aproveitamento_percentual,
    vt.media_gols_marcados,
    vt.saldo_gols
FROM v_estatisticas_temporada vt
JOIN times t ON vt.time_id = t.id
WHERE vt.temporada = 2024
ORDER BY vt.aproveitamento_percentual DESC
LIMIT 10;

-- Times que participaram de múltiplas competições na temporada
SELECT 
    t.nome as time_nome,
    vt.total_ligas,
    vt.ligas_participantes,
    vt.jogos_total,
    vt.aproveitamento_percentual
FROM v_estatisticas_temporada vt
JOIN times t ON vt.time_id = t.id
WHERE vt.temporada = 2024 AND vt.total_ligas > 1
ORDER BY vt.total_ligas DESC, vt.aproveitamento_percentual DESC;
*/