# db.py
# 프로젝트 DB

import os
import psycopg
from psycopg.rows import dict_row # 조회한 행들을 딕셔너리로 가져오는 함수
from dotenv import load_dotenv # .env 로딩 라이브러리
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parent.parent / 'sql'
if not SQL_DIR.exists():
    SQL_DIR.mkdir(parents=True, exist_ok=True)

# sql 불러오기
def load_sql(filename):
    path = (SQL_DIR / filename).resolve()
    if path.parent != SQL_DIR.resolve() or path.suffix != '.sql':
        raise ValueError('sql폴더의 .sql파일명만 지정하세요')
    return path.read_text(encoding='utf-8')

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def has_database_url():
    return bool(DATABASE_URL)

def get_connection():
    if not has_database_url():
        raise ValueError('DATABASE_URL이 설정되지 않았습니다')
    return psycopg.connect(DATABASE_URL)

# 테이블 생성
def create_table():
    sql = load_sql('schema.sql')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

# 메모 입력
def add_memo(content):
    sql = load_sql('add_memo.sql')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (content,))
            return cur.fetchone()[0]

# 할 일 생성
def add_task(title, content, due_date=None):
    sql = load_sql('add_task.sql')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (title, content, due_date,))
            return cur.fetchone()[0]

# 최근 메모 조회
def list_memo():
    sql = load_sql('list_memo.sql')
    with get_connection() as conn:
        # row_factory=dict_row : 행들을 딕셔너리로 가져옴
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            return cur.fetchall()


# 날짜별 조회
def list_task(due_date):
    sql = load_sql('list_task.sql')
    with get_connection() as conn:
        # row_factory=dict_row : 행들을 딕셔너리로 가져옴
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (due_date,))
            return cur.fetchall()

# 수정
def update_data(data_id, due_date, content, completed):
    sql = load_sql('update_data.sql')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (due_date, content, completed, data_id))
            return cur.rowcount

# 메모 삭제
def delete_memo(data_id):
    sql = load_sql('delete_memo.sql')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (data_id,))
            return cur.rowcount

# task 삭제
def delete_task(data_id):
    sql = load_sql('delete_task.sql')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (data_id,))
            return cur.rowcount
























































































































































