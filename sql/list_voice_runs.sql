SELECT id, created_at, transcript, intent, status, response_text,
       latency_ms, error_message
FROM voice_runs
ORDER BY created_at DESC, id DESC
LIMIT %s;
