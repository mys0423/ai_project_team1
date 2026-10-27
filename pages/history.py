# pages/history.py
# 처리 이력 페이지 (음성 명령 및 AI 처리 로그)

from datetime import date, datetime
import pandas as pd
import streamlit as st


def init_history_state():
    if "history" not in st.session_state:
        st.session_state.history = [
            {
                "created_at": datetime(2026, 10, 26, 14, 30),
                "input_type": "직접 녹음",
                "transcript": "내일 장보기 추가해 줘",
                "intent": "ADD_TASK",
                "status": "성공",
                "response_text": "내일 할 일에 장보기를 추가했어요.",
                "latency_ms": 2300,
                "error_message": "",
            },
            {
                "created_at": datetime(2026, 10, 26, 14, 25),
                "input_type": "텍스트",
                "transcript": "회의 준비라고 메모해 줘",
                "intent": "ADD_MEMO",
                "status": "성공",
                "response_text": "회의 준비를 메모로 저장했어요.",
                "latency_ms": 450,
                "error_message": "",
            },
            {
                "created_at": datetime(2026, 10, 26, 14, 20),
                "input_type": "파일 업로드",
                "transcript": "오늘 할 일 알려줘",
                "intent": "LIST_TASK",
                "status": "실패",
                "response_text": "잠시 후 다시 시도해 주세요.",
                "latency_ms": 1800,
                "error_message": "DB 연결에 실패했습니다.",
            },
        ]


def render_history_view():
    init_history_state()

    st.subheader('처리 이력')
    st.caption("음성·텍스트 명령의 실행 결과를 확인하세요.")

    if not st.session_state.history:
        st.info("기록된 음성 처리 이력이 없습니다.")
        return

    df = pd.DataFrame(st.session_state.history)
    df["created_at"] = pd.to_datetime(df["created_at"])

    # ── 1. 검색 · 필터 ─────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일", value=df["created_at"].min().date(),
                                   key="history_start")
    with col2:
        end_date = st.date_input("종료일", value=date.today(), key="history_end")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        input_type = st.selectbox("입력 방식", ["전체", "텍스트", "직접 녹음", "파일 업로드"],
                                  key="history_input_type")
    with col2:
        status = st.selectbox("처리 결과", ["전체", "성공", "실패"], key="history_status")

    with col3:
        keyword = st.text_input("명령 검색", placeholder="검색할 문장을 입력하세요",
                                key="history_keyword")

    if start_date > end_date:
        st.warning("종료일은 시작일 이후로 선택해 주세요.")
        filtered = df.iloc[0:0]
    else:
        dates = df["created_at"].dt.date
        filtered = df[(dates >= start_date) & (dates <= end_date)].copy()

        if input_type != "전체":
            filtered = filtered[filtered["input_type"] == input_type]

        if status != "전체":
            filtered = filtered[filtered["status"] == status]

        if keyword.strip():
            filtered = filtered[filtered["transcript"].str.contains(
                keyword.strip(), regex=False, na=False)]

        filtered = filtered.sort_values("created_at", ascending=False)

    # ── 2. 요약 카드 ──────────────────────────────────────────────
    st.divider()
    st.caption("선택한 검색 조건 기준")
    col1, col2, col3 = st.columns(3)
    col1.metric("전체", f"{len(filtered)}건")
    col2.metric("성공", f"{(filtered['status'] == '성공').sum()}건")
    col3.metric("실패", f"{(filtered['status'] == '실패').sum()}건")

    # ── 3. 목록 ───────────────────────────────────────────────────
    st.divider()
    if filtered.empty:
        st.info("조건에 맞는 처리 이력이 없습니다.")
        return

    view = filtered[["created_at", "input_type", "transcript", "intent", "status"]].copy()
    view["created_at"] = view["created_at"].dt.strftime("%m/%d %H:%M")
    view.columns = ["실행 시간", "입력 방식", "명령 문장", "의도", "결과"]
    st.dataframe(view, hide_index=True, width="stretch")

    # ── 4. 상세 보기 ──────────────────────────────────────────────
    st.subheader("기록 상세 보기")
    for row in filtered.to_dict("records"):
        icon = "🟢" if row["status"] == "성공" else "🔴"
        title = f"{icon} {row['created_at'].strftime('%m/%d %H:%M')} · {row['transcript']}"

        with st.expander(title):
            st.write("입력 방식:", row["input_type"])
            st.write("입력·인식 문장:", row["transcript"])
            st.write("분류된 의도", row["intent"])
            st.write("시스템 응답:", row["response_text"])
            st.write("처리 시간:", f"{row['latency_ms'] / 1000:.2f}초")
            if row["error_message"]:
                st.error(row["error_message"])


if __name__ == '__main__':
    st.set_page_config(page_title="처리 이력", layout="centered")
    render_history_view()