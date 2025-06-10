-- Tabela de países (já existe, mas incluindo para referência)
-- CREATE TABLE IF NOT EXISTS paises (
--     id INTEGER PRIMARY KEY,
--     nome VARCHAR(255) NOT NULL,
--     codigo VARCHAR(10),
--     flag_url VARCHAR(500),
--     ativo BOOLEAN DEFAULT true,
--     atualizado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
-- );

-- Tabela de ligas
CREATE TABLE IF NOT EXISTS ligas (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(50),
    logo_url VARCHAR(500),
    pais_id INTEGER,
    temporada_atual INTEGER,
    data_inicio DATE,
    data_fim DATE,
    temporada_corrente BOOLEAN DEFAULT false,
    ativo BOOLEAN DEFAULT true,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (pais_id) REFERENCES paises(id)
);

-- Tabela de times
CREATE TABLE IF NOT EXISTS times (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    codigo VARCHAR(10),
    logo_url VARCHAR(500),
    ano_fundacao INTEGER,
    ativo BOOLEAN DEFAULT true,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Tabela de ligação times x ligas x temporada
CREATE TABLE IF NOT EXISTS times_ligas_temporada (
    id SERIAL PRIMARY KEY,
    time_id INTEGER NOT NULL,
    liga_id INTEGER NOT NULL,
    temporada INTEGER NOT NULL,
    ativo BOOLEAN DEFAULT true,
    criado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (time_id) REFERENCES times(id),
    FOREIGN KEY (liga_id) REFERENCES ligas(id),
    UNIQUE(time_id, liga_id, temporada)
);

-- Tabela de jogos
CREATE TABLE IF NOT EXISTS jogos (
    id INTEGER PRIMARY KEY,
    data DATE NOT NULL,
    horario TIMESTAMP WITH TIME ZONE NOT NULL,
    time_casa_id INTEGER NOT NULL,
    time_fora_id INTEGER NOT NULL,
    liga_id INTEGER NOT NULL,
    temporada INTEGER NOT NULL,
    status VARCHAR(50),
    rodada VARCHAR(50),
    arbitro VARCHAR(255),
    estadio VARCHAR(255),
    cidade VARCHAR(255),
    gols_casa INTEGER,
    gols_fora INTEGER,
    criado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (time_casa_id) REFERENCES times(id),
    FOREIGN KEY (time_fora_id) REFERENCES times(id),
    FOREIGN KEY (liga_id) REFERENCES ligas(id)
);

-- Índice para busca rápida por data
CREATE INDEX IF NOT EXISTS idx_jogos_data ON jogos(data);

-- Tabela de estatísticas dos times
CREATE TABLE IF NOT EXISTS estatisticas_times (
    id SERIAL PRIMARY KEY,
    time_id INTEGER NOT NULL,
    liga_id INTEGER NOT NULL,
    temporada INTEGER NOT NULL,
    data_referencia DATE,
    -- Estatísticas de jogos
    jogos_total INTEGER DEFAULT 0,
    jogos_casa INTEGER DEFAULT 0,
    jogos_fora INTEGER DEFAULT 0,
    -- Resultados
    vitorias_total INTEGER DEFAULT 0,
    vitorias_casa INTEGER DEFAULT 0,
    vitorias_fora INTEGER DEFAULT 0,
    empates_total INTEGER DEFAULT 0,
    empates_casa INTEGER DEFAULT 0,
    empates_fora INTEGER DEFAULT 0,
    derrotas_total INTEGER DEFAULT 0,
    derrotas_casa INTEGER DEFAULT 0,
    derrotas_fora INTEGER DEFAULT 0,
    -- Gols
    gols_marcados_total INTEGER DEFAULT 0,
    gols_marcados_casa INTEGER DEFAULT 0,
    gols_marcados_fora INTEGER DEFAULT 0,
    gols_sofridos_total INTEGER DEFAULT 0,
    gols_sofridos_casa INTEGER DEFAULT 0,
    gols_sofridos_fora INTEGER DEFAULT 0,
    -- Médias
    media_gols_marcados DECIMAL(5,2) DEFAULT 0,
    media_gols_sofridos DECIMAL(5,2) DEFAULT 0,
    -- Estatísticas especiais
    jogos_sem_marcar INTEGER DEFAULT 0,
    jogos_sem_sofrer INTEGER DEFAULT 0,
    jogos_ambos_marcam INTEGER DEFAULT 0,
    -- Cartões
    cartoes_amarelos INTEGER DEFAULT 0,
    cartoes_vermelhos INTEGER DEFAULT 0,
    -- Escanteios
    escanteios_favor INTEGER DEFAULT 0,
    escanteios_contra INTEGER DEFAULT 0,
    -- Sequências
    maior_sequencia_vitorias INTEGER DEFAULT 0,
    maior_sequencia_invicto INTEGER DEFAULT 0,
    sequencia_atual VARCHAR(50),
    -- Forma recente (últimos 5 jogos)
    forma_recente VARCHAR(10),
    -- Outros
    penaltis_marcados INTEGER DEFAULT 0,
    penaltis_perdidos INTEGER DEFAULT 0,
    penaltis_sofridos INTEGER DEFAULT 0,
    -- Controle
    criado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (time_id) REFERENCES times(id),
    FOREIGN KEY (liga_id) REFERENCES ligas(id),
    UNIQUE(time_id, liga_id, temporada)
);

-- Índices para otimização
CREATE INDEX IF NOT EXISTS idx_estatisticas_time_liga ON estatisticas_times(time_id, liga_id);
CREATE INDEX IF NOT EXISTS idx_estatisticas_temporada ON estatisticas_times(temporada);
