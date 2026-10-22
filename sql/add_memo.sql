-- 메모 추가
INSERT INTO memos (content)
VALUES (%s)
RETURNING id;