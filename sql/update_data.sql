UPDATE tasks
SET
    due_date = %s,
    content = %s,
    completed = %s,
    updated_at = now()
WHERE id = %s;