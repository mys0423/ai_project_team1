-- 메모 목록을 최신순으로 조회
SELECT id, content, created_at
FROM memos
ORDER BY created_at DESC LIMIT %s;