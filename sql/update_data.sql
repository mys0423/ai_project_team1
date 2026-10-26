UPDATE tasks
SET
    title = %s,
    due_date = %s,
    content = %s,
    completed = %s,
    updated_at = now()
WHERE id = %s;