-- Schema do banco de dados para Sistema de Documentos Perdidos e Achados

-- Tabela de usuários
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de documentos perdidos
CREATE TABLE documentos_perdidos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    tipo_documento VARCHAR(50) NOT NULL, -- RG, CPF, CNH, Passaporte, etc
    numero_documento VARCHAR(100),
    nome_documento VARCHAR(255), -- Nome que aparece no documento
    cpf_documento VARCHAR(14), -- CPF que aparece no documento
    data_perda DATE,
    local_perda TEXT,
    descricao TEXT,
    foto_url TEXT,
    status VARCHAR(20) DEFAULT 'perdido', -- perdido, encontrado, recuperado
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de documentos achados
CREATE TABLE documentos_achados (
    id SERIAL PRIMARY KEY,
    encontrador_id INTEGER REFERENCES usuarios(id),
    tipo_documento VARCHAR(50) NOT NULL,
    numero_documento VARCHAR(100),
    nome_documento VARCHAR(255),
    cpf_documento VARCHAR(14),
    data_encontrado DATE,
    local_encontrado TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    descricao TEXT,
    foto_url TEXT,
    status VARCHAR(20) DEFAULT 'disponivel', -- disponivel, devolvido
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de matches (quando encontramos correspondências)
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    documento_perdido_id INTEGER REFERENCES documentos_perdidos(id),
    documento_achado_id INTEGER REFERENCES documentos_achados(id),
    score_similaridade DECIMAL(5, 2), -- 0 a 100
    notificacao_enviada BOOLEAN DEFAULT FALSE,
    data_notificacao TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pendente', -- pendente, confirmado, rejeitado
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de logs de notificações
CREATE TABLE notificacoes (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    usuario_id INTEGER REFERENCES usuarios(id),
    tipo VARCHAR(20), -- email, sms, push
    destinatario VARCHAR(255),
    assunto TEXT,
    mensagem TEXT,
    enviado BOOLEAN DEFAULT FALSE,
    data_envio TIMESTAMP,
    erro TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhorar performance
CREATE INDEX idx_documentos_perdidos_tipo ON documentos_perdidos(tipo_documento);
CREATE INDEX idx_documentos_perdidos_numero ON documentos_perdidos(numero_documento);
CREATE INDEX idx_documentos_perdidos_cpf ON documentos_perdidos(cpf_documento);
CREATE INDEX idx_documentos_perdidos_status ON documentos_perdidos(status);

CREATE INDEX idx_documentos_achados_tipo ON documentos_achados(tipo_documento);
CREATE INDEX idx_documentos_achados_numero ON documentos_achados(numero_documento);
CREATE INDEX idx_documentos_achados_cpf ON documentos_achados(cpf_documento);
CREATE INDEX idx_documentos_achados_status ON documentos_achados(status);

CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_notificacao ON matches(notificacao_enviada);
