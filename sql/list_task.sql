-- 지정한 날짜의 할 일을 최신순으로 조회
SELECT id, title, due_data, completed, created_at, content, updated_at
FROM tasks
WHERE due_data = %s OR due_data IS NULL
ORDER BY due_data ASC, created_at DESC;