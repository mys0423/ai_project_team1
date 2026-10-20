-- 할 일 추가
INSERT INTO tasks (title, due_data, content)
VALUES (%s, %s, %s)
RETURNING id, title, due_data, completed, created_at, content;