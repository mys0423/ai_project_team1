# views/home.py
# 음성 비서 홈 페이지 (입력, STT, 문장 수정, AI 의도 분석 연동)

import time
import uuid
from datetime import date, datetime
import streamlit as st
import pandas as pd
from src.stt import transcript_wav
from src.core import process_text as core_process_text
from src.tts import text_to_speech, VOICES, evaluate_tts
from src.db import has_database_url
from pages.todo import init_task_state
from pages.memo import init_memo_state


TASK_INTENTS = {'ADD_TASK', 'UPDATE_TASK', 'COMPLETE_TASK', 'DELETE_TASK'}
MEMO_INTENTS = {'ADD_MEMO', 'DELETE_MEMO'}


def _sync_from_db(intent):
    """[수정] 처리 성공 시 DB 기준으로 세션 목록을 다시 불러옴
    - 기존: 제목 '포함' 여부로 세션을 직접 수정 → 같은 이름(날짜만 다른) 할 일/메모가 모두 삭제·완료되어 보임
    - 변경: DB에서 실제로 바뀐 결과만 반영 (메모/할 일 페이지와 항상 일치)
    """
    if not has_database_url():
        return False
    try:
        if intent in TASK_INTENTS:
            init_task_state(force=True)
        elif intent in MEMO_INTENTS:
            init_memo_state(force=True)
        return True
    except Exception:
        return False


def handle_process_text(text: str, input_type: str = "직접 녹음"):
    result = core_process_text(text, input_type=input_type)  # [수정] 입력 방식을 처리 이력에 전달
    intent = result.get('intent', 'UNKNOWN')
    slots = result.get('slots', {})
    status = result.get('status', '실패')
    response_msg = result.get('response', '')
    latency_ms = result.get('latency_ms', 0)

    # 1. 이력 세션 상태 동기화
    if "history" not in st.session_state:
        st.session_state.history = []

    st.session_state.history.insert(0, {
        "id": result.get('run_id'),  # [수정] 처리 이력 페이지에서 DB 이력과 중복 표시 방지
        "transcript": text,
        "input_type": input_type,
        "intent": intent,
        "status": status,
        "latency_ms": latency_ms,
        "created_at": datetime.now(),
        "response": response_msg,
        "response_text": response_msg,
        "error_message": "" if status == '성공' else response_msg
    })

    # 2. 메모 / 할 일 세션 상태 동기화 (성공 시)
    #    [수정] DB가 연결되어 있으면 DB 결과로 다시 불러오고, 아니면 core가 돌려준 id 기준으로만 반영
    if status == '성공' and not _sync_from_db(intent):
        if "memos" not in st.session_state:
            st.session_state.memos = []
        if "tasks" not in st.session_state:
            st.session_state.tasks = []

        is_already_exists = result.get('data', {}).get('already_exists', False) if isinstance(result.get('data'), dict) else False

        if intent == 'ADD_MEMO':
            if not is_already_exists:
                content = slots.get('MEMO_CONTENT', text)
                memo_id = result.get('data', {}).get('id') if isinstance(result.get('data'), dict) else str(uuid.uuid4())
                st.session_state.memos.insert(0, {
                    "id": str(memo_id),
                    "content": content,
                    "created_at": datetime.now()
                })

        elif intent == 'ADD_TASK':
            if not is_already_exists:
                title = slots.get('TITLE', text)
                due_str = slots.get('DUE_DATE')
                try:
                    due_date = date.fromisoformat(due_str) if due_str else date.today()
                except Exception:
                    due_date = date.today()

                task_id = result.get('data', {}).get('id') if isinstance(result.get('data'), dict) else str(uuid.uuid4())
                st.session_state.tasks.append({
                    'id': str(task_id),
                    'content': title,
                    'due_date': due_date,
                    'due_time': None,
                    'is_done': False
                })

        # [수정] 제목 '포함' 비교 대신 실제 처리된 id만 반영 (같은 이름의 다른 날짜 항목은 건드리지 않음)
        data = result.get('data') if isinstance(result.get('data'), dict) else {}
        target_ids = {str(i) for i in (data.get('ids') or ([data['id']] if data.get('id') else []))}

        if intent == 'COMPLETE_TASK':
            for t in st.session_state.tasks:
                if str(t.get('id')) in target_ids:
                    t['is_done'] = True

        elif intent == 'UPDATE_TASK':
            new_title = slots.get('NEW_TITLE')
            new_due = slots.get('NEW_DUE_DATE')
            for t in st.session_state.tasks:
                if str(t.get('id')) in target_ids:
                    if new_title:
                        t['content'] = new_title
                    if new_due:
                        t['due_date'] = date.fromisoformat(new_due)

        elif intent == 'DELETE_TASK':
            st.session_state.tasks = [t for t in st.session_state.tasks if str(t.get('id')) not in target_ids]

        elif intent == 'DELETE_MEMO':
            st.session_state.memos = [m for m in st.session_state.memos if str(m.get('id')) not in target_ids]

    return result


def render_home_view():
    st.title('🎙️ 나만의 AI 음성 비서')
    st.caption('한국어 음성 명령으로 메모와 일정을 간편하게 관리하세요.')

    tab1, tab2 = st.tabs(['녹음/텍스트입력', '파일 업로드'])

    if "recorded_audio" not in st.session_state:
        st.session_state.recorded_audio = None

    with tab1:
        prompt = st.chat_input(
            '명령어를 입력하거나 음성 녹음을 실행하세요',
            accept_audio=True,
            key='voice_prompt'
        )
        if prompt:
            if prompt.text:
                st.session_state.edited_text = prompt.text
                st.session_state.stt_time = 0.0
                st.session_state.recorded_audio = None
                st.session_state.current_input_type = '텍스트'
                st.rerun()

            if prompt.audio:
                audio_bytes = prompt.audio.getvalue()
                st.session_state.recorded_audio = audio_bytes
                st.session_state.current_input_type = '직접 녹음'
                with st.spinner('음성 인식 처리 중...'):
                    text, elapsed = transcript_wav(audio_bytes)
                st.session_state.edited_text = text
                st.session_state.stt_time = elapsed
                st.rerun()

        if st.session_state.get('recorded_audio'):
            st.caption("🎙️ 녹음된 음성 확인:")
            st.audio(st.session_state.recorded_audio, format="audio/wav")

    with tab2:
        wav_file = st.file_uploader(
            '음성 파일을 업로드하세요 (WAV, MP3)',
            type=['wav', 'mp3']
        )

        if wav_file is not None:
            st.audio(wav_file)

        if st.button('파일 음성 변환 처리 🎧'):
            if wav_file is None:
                st.warning('파일을 먼저 업로드해주세요')
            else:
                st.session_state.current_input_type = '파일 업로드'

                # [수정] 무음 파일 업로드 안내
                try:
                    with st.spinner('파일 분석 중...'):
                        text, elapsed = transcript_wav(wav_file.getvalue())
                    if not text.strip():
                        st.warning('무음 파일입니다. 파일을 다시 확인해주세요')
                    else:
                        st.session_state.edited_text = text
                        st.session_state.stt_time = elapsed
                        st.toast(f"전사 완료 ({elapsed}초)", icon="✨")
                        st.rerun()
                except ValueError as e:
                    st.warning(str(e))

    st.divider()

    st.subheader('문장 미리보기 및 수정')

    # 저장 후 텍스트 안전 초기화
    if st.session_state.get('clear_edited_text'):
        st.session_state.edited_text = ""
        st.session_state.clear_edited_text = False

    with st.expander('📌 사용 가능한 명령어 예시'):
        st.info('예시에 맞게 문장을 수정하세요')
        st.markdown("""
        **📅 할 일 관리**

        **1. 할 일 추가**
        - 할 일에 장보기 추가해
        - 내일 회의 등록해
        - 29일 할 일에 발표 준비 추가해
        - 할 일 추가: 운동하기

        **2. 할 일 조회**
        - 오늘 할 일 알려줘
        - 30일 할 일 알려줘
        - 내일 미완료 할 일 보여줘
        - 완료한 할 일 보여줘

        **3. 할 일 수정**
        - 장보기 이름을 마트 가기로 바꿔
        - 회의 날짜를 내일로 변경해
        - 30일 운동 날짜를 31일로 바꿔 (같은 이름이 여러 날짜에 있으면 날짜를 앞에)

        **4. 할 일 완료**
        - 장보기 완료
        - 30일 운동 다 했어
        - 할 일 중에 회의 완료
        - 운동 모두 완료 (같은 이름 전체)

        **5. 할 일 삭제**
        - 할 일에서 장보기 삭제
        - 29일 운동 할 일 지워
        - 장보기 모두 삭제 (같은 이름 전체)

        ---

        **📝 메모 관리**

        **1. 메모 추가**
        - 우유 사기 메모해
        - 메모 추가: 회의 준비
        - 회의 준비라고 메모해
        - 메모장에 운동 계획 적어

        **2. 메모 조회**
        - 메모 목록 보여줘
        - 회의 관련 메모 보여줘

        **3. 메모 삭제**
        - 회의 관련 메모 삭제해
        - 최근 메모 삭제해
        - 회의 관련 메모 모두 삭제해
        - 메모 삭제해 (삭제할 후보를 보여 드려요)
        """)

    edited_text = st.text_area(
        '인식된 문장을 확인하고 수정하세요',
        key='edited_text',
        height=120
    )

    if st.session_state.stt_time > 0:
        st.caption(f"⚡ STT 소요 시간: {st.session_state.stt_time:.3f}초")

    if st.button('저장', type='primary', use_container_width=True):
        text = edited_text.strip()

        if not text:
            st.warning('음성녹음/텍스트 입력, 파일업로드를 먼저 해주세요')
        else:
            input_type = st.session_state.get('current_input_type', '텍스트')
            with st.spinner('AI 의도 분석 및 등록 중...'):
                result = handle_process_text(text, input_type=input_type)
            st.session_state.result = result
            st.session_state.clear_edited_text = True
            st.session_state.last_tts_audio = None
            st.session_state.current_input_type = '텍스트'
            st.rerun()

    if st.session_state.result is not None:
        result = st.session_state.result
        if result['status'] == '성공':
            st.success(result['response'])
        elif result.get('needs_input'):
            # [수정] 중복·대상 없음 등 다시 말해야 하는 경우는 오류가 아닌 안내로 표시
            st.warning(result['response'], icon='💬')
        else:
            st.error(result['response'])

    voice_name = st.selectbox(
        '목소리 선택',
        list(VOICES.keys())
    )

    voice = VOICES[voice_name]

    if st.button('음성 재생'):
        if st.session_state.get('result') is None:
            st.warning('작업을 먼저 실행해주세요')
        else:
            with st.spinner('음성 생성 중...'):
                try:
                    t0 = time.perf_counter()
                    audio_bytes = text_to_speech(
                        st.session_state.result['response'],
                        voice=voice
                    )
                    tts_sec = time.perf_counter() - t0
                    st.session_state.last_tts_audio = audio_bytes
                    st.session_state.last_tts_sec = tts_sec
                except Exception as e:
                    st.error(f'음성 생성에 실패했습니다: {e}')

    if st.session_state.get('last_tts_audio'):
        st.audio(st.session_state.last_tts_audio, format="audio/mp3")
        if st.session_state.get('last_tts_sec'):
            st.caption(f"⚡ TTS 소요 시간: {st.session_state.last_tts_sec:.3f}초")

    st.divider()

    # ─────────────────────────────────────────────────────────────
    # TTS 생성 성능 (평가 상단으로 위치 이동)
    # ─────────────────────────────────────────────────────────────
    st.subheader("TTS 생성 성능")

    stats = evaluate_tts()

    c1, c2, c3 = st.columns(3)
    c1.metric("생성 시도", f"{stats['total']}건")
    c2.metric("평균 생성 시간", f"{stats['avg_elapsed_sec']:.2f}초")
    c3.metric("실패율", f"{stats['failure_rate']:.1f}%")

    st.divider()

    # ─────────────────────────────────────────────────────────────
    # TTS 청취 평가
    # ─────────────────────────────────────────────────────────────
    st.subheader('TTS 청취 평가')
    st.caption('청취자의 주관적인 평가입니다 (1~5점)')

    default_evals = [
        {'평가자': '문윤성', '자연스러움': 5, '명확도': 5},
        {'평가자': '이태규', '자연스러움': 5, '명확도': 4},
        {'평가자': '최준혁', '자연스러움': 4, '명확도': 5},
        {'평가자': '엄기훈', '자연스러움': 4, '명확도': 5},
    ]

    if 'tts_evaluation' not in st.session_state or len(st.session_state.tts_evaluation) <= 1:
        st.session_state.tts_evaluation = list(default_evals)

    with st.form('tts_eval_form'):
        evaluator = st.text_input('평가자 ID', placeholder='예) 사용자 이름 또는 아이디', key='input_evaluator')

        naturalness = st.number_input(
            '자연스러움',
            min_value=1,
            max_value=5,
            step=1,
            value=3
        )

        clarity = st.number_input(
            '명확도',
            min_value=1,
            max_value=5,
            step=1,
            value=3
        )
        submitted = st.form_submit_button('평가 저장', type='primary')

        if submitted:
            evaluator = evaluator.strip()

            if not evaluator:
                st.warning('평가자의 ID를 입력해주세요')
            elif any(row['평가자'] == evaluator for row in st.session_state.tts_evaluation):
                st.warning('이미 평가한 ID 입니다')
            else:
                st.session_state.tts_evaluation.append({
                    '평가자': evaluator,
                    '자연스러움': naturalness,
                    '명확도': clarity
                })
                st.success('평가를 성공적으로 저장했습니다')

    evaluation = st.session_state.tts_evaluation

    if len(evaluation) >= 1:
        st.write(f'👥 청취 평가 참여자 수: {len(evaluation)}명')
        df = pd.DataFrame(evaluation)
        m1, m2 = st.columns(2)
        m1.metric("평균 자연스러움", f"{df['자연스러움'].mean():.2f} / 5.0")
        m2.metric("평균 명료도", f"{df['명확도'].mean():.2f} / 5.0")
        st.dataframe(df, hide_index=True, use_container_width=True)