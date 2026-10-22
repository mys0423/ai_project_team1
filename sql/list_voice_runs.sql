SELECT id, transcript, intent, response_text, status, latency_ms, created_at
FROM voice_runs
ORDER BY created_at DESC