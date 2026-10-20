# db.py

import os
import psycopg
from psycopg.rows import dict_row # 조회한 행들을 딕셔너리로 가져오는 함수
from dotenv import load_dotenv # .env 로딩 라이브러리
from pathlib import Path

# SQL 파일들 저장 디렉토리
SQL_DIR = Path(__file__).resolve().parent / 'sql'
if not SQL_DIR.exists(): # 디렉토리 없다면
    SQL_DIR.mkdir(parents=True, exist_ok=True) # 새로 생성

# 파일명에 해당하는 SQL 문자열을 리턴하는 함수
def load_sql(filename):
    path = (SQL_DIR / filename).resolve() # SQL파일의 서버상의 실제경로
    # 생성된 sql디렉토리에 SQL파일이 없거나 SQL파일의 확장자가 sql이 아니라면
    if path.parent != SQL_DIR.resolve() or path.suffix != '.sql':
        raise ValueError('sql폴더의 .sql파일명만 지정하세요.')
    return path.read_text(encoding='utf-8') # SQL파일내의 문자열을 리턴

# .env 파일의 환경변수를 로딩
load_dotenv()

# 메모리에 로딩된 .env파일의 DATABASE_URL 환경변수의 값 저장
DATABASE_URL = os.getenv("DATABASE_URL")
# pp(DATABASE_URL)

# DATABASE_URL 유효여부 확인하는 함수
def has_database_url():
    return bool(DATABASE_URL)

# Connection 획득 함수
def get_connection():
    if not has_database_url():
        raise ValueError('DATABASE_URL이 설정되지 않았습니다!')
    return psycopg.connect(DATABASE_URL)

# 테이블 생성 함수
def create_table():
    sql = load_sql('create_table.sql')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

# 입력
def save_voice_data(speaker, transcript, language, file_name):
    sql = load_sql('save_voice_data.sql')
    params = (speaker, transcript, language, file_name or None)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()[0]

# 검색 조회
def load_voice_data(keyword = ''):
    sql = load_sql('load_voice_data.sql')
    params = (f'%{keyword.strip()}%',) # %는 0개 이상의 문자열
    with get_connection() as conn:
        # row_factory=dict_row() : 행들을 딕셔너리로 가져오는 커서
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

# 수정
def update_voice_data(data_id, transcript, language):
    sql = load_sql('update_voice_data.sql')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (transcript, language, data_id))
            return cur.rowcount

# 삭제
def delete_voice_data(data_id):
    sql = load_sql('delete_voice_data.sql')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (data_id,))
            return cur.rowcount