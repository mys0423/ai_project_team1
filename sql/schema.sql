-- 1팀 SQL 초안: 팀 설계에 맞게 수정하세요.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS memos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS tasks ( -- content 넣어야되고
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    due_date DATE,
    completed BOOLEAN NOT NULL DEFAULT FALSE, -- 이게 is_done 이고
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS voice_runs ( -- error_message 빠져있고
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript TEXT,
    intent TEXT,
    response_text TEXT,
    status TEXT NOT NULL,
    latency_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
