-- 음성 명령 처리 이력 저장
INSERT INTO voice_runs (
    transcript,
    intent,
    status,
    response_text,
    latency_ms,
    error_message
)
FROM voice_runs
ORDER BY created_at DESC
LIMIT %s;