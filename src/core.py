# core.py
# 답변생성

from models.model import predict_intent
from src.db import *

HELP_TEXT = (
    '할 일 추가, 조회, 수정, 완료, 삭제 /'
    '메모 추가, 조회, 삭제 명령을 사용할 수 있습니다'
)

# 할 일 전체 조회
def task_matches(title, due_date=None):

    rows = list_all_task()
    matches = [row for row in rows if row['title'] == title]

    if due_date:
        matches = [row for row in matches if row['due_date'] and
                   str(row['due_date']) == due_date]

    return matches

# 메모 조회
def memo_matches(keyword=None, memo_date=None):

    rows = list_memo()
    if keyword:
        rows = [row for row in rows if keyword in row['content']]
    if memo_date:
        rows = [row for row in rows if str(row['created_at'].date()) == memo_date]

    return rows

def select_one(rows):
    if not rows:
        return None
    if len(rows) > 1:
        return None
    return rows[0], None

def execute(intent, slots):
    title = slots.get('TITLE')
    due_date = slots.get('DUE_DATE')

    if intent == 'HELP':
        return HELP_TEXT

    if intent == 'ADD_TASK':
        if not title:
            return '추가 할 일의 제목을 말씀해주세요'

        task_id = add_task(title, title, due_date)
        return f'할 일: {title}을 추가했습니다', {'id': str(task_id)}

    if intent == 'LIST_TASK':
        tasks = list_all_task()
        if due_date:
            tasks = [row for row in tasks if row['due_date'] and
                     str(row['due_date']) == due_date]
        status = slots.get('STATUS', '')
        if status in ('완료한', '완료된'):
            tasks = [row for row in tasks if row['completed']]
        elif status in ('안 끝낸', '미완료'):
            tasks = [row for row in tasks if not row['completed']]
        if not tasks:
            return '조회된 할 일이 없습니다', []
        lines = [f"{row['title']} ({'완료' if row['completed'] else '미완료'}, "
                 f"마감: {row['due_date'] or ' '})" for row in tasks]
        return '\n'.join(lines), tasks

    if intent in ('UPDATE_TASK', 'COMPLETE_TASK', 'DELETE_TASK'):
        if not title:
            return '처리할 할 일의 제목을 말씀해 주세요'
        row, error = select_one(task_matches(title, due_date), '할 일')
        if error:
            return error
        if intent == 'DELETE_TASK':
            count = delete_task(row['id'])
            if count:
                f'할 일: {title}을 삭제했습니다', count
            return '삭제할 할 일이 없습니다', count
        new_title = (
            slots.get('NEW_TITLE')
            if intent == 'UPDATE_TASK'
            else None
        )

        new_due = (
            slots.get('NEW_DUE_DATE')
            if intent == 'UPDATE_TASK'
            else None
        )

        if intent == 'UPDATE_TASK' and not (new_title and new_due):
            return '변경할 제목, 마감일을 입력해주세요'

        changed = update_data(
            row['id'],
            new_title or row['title'],
            new_due or row['due_date'],
            row['content'],
            True if intent == 'COMPLETE_TASK' else row['completed']
        )

        if not changed:
            return '변경에 실패했습니다'
        if intent == 'COMPLETE_TASK':
            return f'할 일: {title}을 완료 처리 했습니다'

        if new_title and new_due:
            return (
                f'할 일 {title}을 {new_title}로, '
                f'마감일을 {new_due}로 변경했습니다'
            )

        if new_title:
            return f'할 일 {title}을 {new_title}로 수정했습니다'

        if new_due:
            return f'{title}의 마감일을 {new_due}로 변경했습니다'

    if intent == 'ADD_MEMO':
        content = slots.get('MEMO_CONTENT')

        if not content:
            return '메모 내용을 입력해주세요', None

        memo_id = add_memo(content)

        return '메모를 저장했습니다', {'id': str(memo_id)}

    if intent in ('LIST_MEMO', 'DELETE_MEMO'):
        keyword  = slots.get('KEYWORD')
        memo_date = slots.get('MEMO_DATE')

        if intent == 'DELETE_MEMO' and not (keyword or memo_date):
            return '삭제할 메모의 내용이나 날짜를 알려주세요', None

        memos = memo_matches(keyword, memo_date)

        if intent == 'LIST_MEMO':
            if not memos:
                return '조회할 메모가 없습니다', None

            return '\n'.join(f'{row['content']}' for row in memos)

        row, error = select_one(memos, '메모')

        if error:
            return error

        count = delete_memo(row['id'])

        if count:
            return f'{count}개 메모를 삭제했습니다'

        return '메모 삭제에 실패했습니다'

    return f'작업을 수행할 수 없습니다: {intent}'


def process_text(text):
    result = predict_intent(text)

    intent = result['intent']
    slots = result['slots']

    try:
        response, data = execute(intent, slots)
        status = '성공'

    except Exception as e:
        response = f'DB 처리 중 오류 발생, {e}'
        data = None
        status = '실패'

    return {
        **result,
        'text': text,
        'response': response,
        'data': data,
        'status': status
    }

if __name__ == '__main__':
    text = input('명령을 입력하세요: ')
    print(process_text(text))



















































































































