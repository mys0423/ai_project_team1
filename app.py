# app.py
# 실행: python -m streamlit run app.py

import streamlit as st

# 페이지별 뷰 모듈 불러오기
from pages.home import render_home_view
from pages.memo import render_memo_view, init_memo_state
from pages.todo import render_todo_view, init_task_state
from pages.history import render_history_view, init_history_state
from pages.model_evaluate import render_evaluate_view

# 0. 전역 페이지 설정
st.set_page_config(
    page_title='나만의 AI 음성 비서',
    page_icon='🎙️',
    layout='centered'
)

st.title('나만의 AI 음성 비서')

# 1. 공통 세션 상태 초기화
if "edited_text" not in st.session_state:
    st.session_state.edited_text = ""
if "stt_time" not in st.session_state:
    st.session_state.stt_time = 0.0
if "result" not in st.session_state:
    st.session_state.result = None

init_memo_state()
init_task_state()
init_history_state()


# 2. 사이드바 메뉴 크기 시원하게 확대하는 CSS
st.markdown("""
<style>
/* 사이드바 네비게이션 글씨 및 버튼 크기 시원하게 확대 */
[data-testid="stSidebarNav"] span,
[data-testid="stSidebar"] a span,
section[data-testid="stSidebar"] li span {
    font-size: 1.15rem !important;
    font-weight: 600 !important;
}

[data-testid="stSidebarNav"] a,
section[data-testid="stSidebar"] a {
    padding-top: 12px !important;
    padding-bottom: 12px !important;
    padding-left: 14px !important;
    margin-bottom: 8px !important;
    border-radius: 10px !important;
    transition: all 0.2s ease-in-out;
}

[data-testid="stSidebarNav"] a:hover,
section[data-testid="stSidebar"] a:hover {
    transform: translateX(4px);
}
</style>
""", unsafe_allow_html=True)

# 3. 사이드바 네비게이션 정의 (한글 이름 및 아이콘 설정)
pages = [
    st.Page(render_home_view, title="음성 비서 홈", icon="🎙️", default=True),
    st.Page(render_memo_view, title="메모 관리", icon="📝"),
    st.Page(render_todo_view, title="할 일 관리", icon="📅"),
    st.Page(render_history_view, title="처리 이력", icon="📊"),
    st.Page(render_evaluate_view, title="모델 평가", icon="📈"),
]

pg = st.navigation(pages)

# 4. 선택된 페이지 화면 렌더링
pg.run()