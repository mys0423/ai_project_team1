SELECT id, title, content, due_date, completed, created_at
FROM tasks
WHERE due_date >= %s
ORDER BY due_date DESC