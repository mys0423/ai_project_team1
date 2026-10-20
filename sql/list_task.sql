SELECT id, title, content, due_date, completed, created_at
FROM tasks
WHERE due_date >= %s OR due_date IS NULL
ORDER BY due_date ASC