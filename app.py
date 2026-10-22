# app.py
# UI
import pandas as pd
import streamlit as st

from src.audio1 import *
from src.db import *

st.set_page_config('테스트')

def main():

    st.title('테스트')
    if not DATABASE_URL:
        st.error("DATABASE_URL을 설정하세요.")
        st.stop()

    try:
        create_table()
        with st.form('memo'):
            # memo = st.file_uploader('메모 음성 파일', type=['wav'])
            memo = st.text_input('메모 음성 파일')
            submitted = st.form_submit_button('메모 저장')
        if submitted:
            if not memo:
                st.warning('음성파일을 올려주세요')
            else:
                add_memo(memo)

        with st.form('task'):
            # task = st.file_uploader('할 일 음성 파일', type=['wav'])
            title = st.text_input('할 일 제목')
            content = st.text_input('할 일 내용')
            due_date = st.date_input('기간')
            submitted = st.form_submit_button('할일 저장')

        if submitted:
            if not title or not content:
                st.warning('음성파일을 올려주세요')
            else:
                add_task(
                    title = title.strip(),
                    content = content.strip(),
                    due_date = due_date,
                )

        st.subheader('메모')
        rows = list_memo()
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )
        st.subheader('할 일')
        row = list_all_task()
        st.dataframe(
            pd.DataFrame(row),
            use_container_width=True,
            hide_index=True
        )

    except psycopg.Error as e:
        st.error(f'{e}')


if __name__ == "__main__":
    main()








































