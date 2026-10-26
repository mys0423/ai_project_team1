# app_home.py
# UI
# python -m streamlit run app_home.py

from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar
from src.core import process_text
from src.stt import transcript_wav
import time


st.set_page_config(
    '나만의 AI 음성 비서',
    '🎙️',
    'centered'
)

st.title('나만의 AI 음성 비서')

if 'history' not in st.session_state:
    st.session_state.history = []

if "edited_text" not in st.session_state:
    st.session_state.edited_text = ""

if "stt_time" not in st.session_state:
    st.session_state.stt_time = 0.0

if "result" not in st.session_state:
    st.session_state.result = None


def main():

    tab1, tab2, tab3, tab4 = st.tabs([
        '음성 비서 홈',
        '메모 관리',
        '할 일 관리',
        '처리 이력'
    ])

    with tab1:
        st.header('음성 비서 홈')

        input_type = st.radio(
            '입력 방식',
            ['녹음/텍스트 입력', '파일 업로드'],
            horizontal=True
        )
        if input_type == '녹음/텍스트 입력':
            prompt = st.chat_input(
                '멸령어를 입력하거나 음성 녹음을 실행하세요',
                accept_audio=True,
                key='voice_prompt'
            )
            if prompt:
                if prompt.text:
                    st.session_state.edited_text = prompt.text
                    st.session_state.stt_time = 0.0

                if prompt.audio:
                    st.audio(prompt.audio)

                    with st.spinner('처리 중...'):
                        text, elapsed = transcript_wav(prompt.audio.getvalue())

                    st.session_state.edited_text = text
                    st.session_state.stt_time = elapsed


        if input_type == '파일 업로드':

            wav_file = st.file_uploader(
                'wav파일을 업로드하세요',
                type=['wav']
            )

            if wav_file is not None:
                st.audio(wav_file)

            if st.button('처리'):
                if wav_file is None:
                    st.warning('파일을 먼저 업로드해주세요')
                else:
                    with st.spinner('처리 중...'):
                        text, elapsed = transcript_wav(wav_file.getvalue())

                    st.session_state.edited_text = text
                    st.session_state.stt_time = elapsed

        st.divider()

        st.subheader('문장 미리보기 및 수정')

        st.text_area(
            '인식된 문장을 확인하고 수정하세요',
            key = 'edited_text',
            height=120
        )

        if st.button('저장', type='primary'):

            text = st.session_state.edited_text.strip()

            if not text:
                st.warning('음성녹음/텍스트 입력, 파일업로드를 먼저 해주세요')
            else:
                start = time.perf_counter()

                try:
                    with st.spinner('처리 중...'):

                        result = process_text(text)

                    count_time = round(time.perf_counter() - start, 3)

                except Exception as e:
                    count_time = round(time.perf_counter() - start, 3)

                    result = {
                        'intent': 'UNKNOWN',
                        'status': '실패',
                        'response': str(e)
                    }

                st.session_state.result = result

                st.session_state.history.append({
                    '실행 시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '인식 문장': text,
                    '의도': result.get('intent', 'UNKNOWN'),
                    '처리결과': result.get('status', '실패'),
                    'STT 시간': st.session_state.stt_time,
                    '명령 처리 시간': count_time,
                    '응답': result.get('response', '')
                })

        if st.session_state.result is not None:
            result = st.session_state.result

            if result['status'] == '성공':
                st.success(result['response'])
            else:
                st.error(result['response'])

    with tab4:
        st.header('처리 이력')

        history = st.session_state.history

        if history:
            total = len(history)
            success = sum(
                1 for row in history
                if row['처리 결과'] == '성공'
            )
            failure = total - success

            col1, col2, col3 = st.columns(3)

            col1.metric('전체 처리 건수: ', total)
            col2.metric('성공 건수: ', success)
            col3.metric('실패 건수: ', failure)

            st.divider()

            st.subheader('명령 처리 기록')

if __name__ == '__main__':
    main()



























