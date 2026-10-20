-- ID로 지정한 할 일 수정
UPDATE tasks
SET title = %s,
    due_date = %s,
    content = %s,
    completed = %s,
    updated_at = now()
WHERE id = %s
RETURNING id, title, due_date, content,
          completed, created_at, updated_at;