INSERT INTO voice_runs
    (transcript, intent, response_text, status, latency_ms)
VALUES (%s, %s, %s, %s, %s)
RETURNING ID;