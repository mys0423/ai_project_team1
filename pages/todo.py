# views/todo.py
# 할 일 관리 페이지 (FullCalendar & 할 일 목록 탭 구성)

from datetime import date, datetime, time
import streamlit as st

PALETTE = ['#c7b8f5', '#b8e6c9', '#ffd9a8', '#f7c6d9', '#b8d8f7']   # 달력 칩 색상
DONE_COLOR = '#d9d9d9'


def tasks_to_events(tasks):
    """할 일 목록 → FullCalendar 이벤트 변환"""
    events = []
    for i, t in enumerate(tasks):
        due = t.get('due_date')
        if not due:
            continue
        due_time = t.get('due_time')
        event = {
            'title': t.get('content', '할 일'),
            'color': DONE_COLOR if t.get('is_done') else PALETTE[i % len(PALETTE)],
            'textColor': '#1E1B4B',
        }
        if due_time:
            event['start'] = datetime.combine(due, due_time).isoformat()
        else:
            event['start'] = due.isoformat() if isinstance(due, (date, datetime)) else str(due)
            event['allDay'] = True
        events.append(event)
    return events


def render_calendar(tasks, key='task_calendar'):
    """FullCalendar 렌더링"""
    from streamlit_calendar import calendar as full_cal

    today_str = date.today().isoformat()
    options = {
        'initialView': 'dayGridMonth',
        'initialDate': today_str,
        'locale': 'ko',
        'firstDay': 0,
        'contentHeight': 620,
        'headerToolbar': {'left': 'prev,next today', 'center': 'title', 'right': ''},
        'displayEventTime': True,
    }
    return full_cal(events=tasks_to_events(tasks), options=options, key=key)


def _demo_tasks():
    today = date.today()
    return [
        {'content': '팀 회의', 'due_date': today, 'due_time': time(10, 0), 'is_done': False},
        {'content': '보고서 작성', 'due_date': today, 'due_time': time(14, 0), 'is_done': True},
        {'content': '병원 예약', 'due_date': today.replace(day=min(today.day + 1, 28)), 'due_time': time(15, 0), 'is_done': False},
        {'content': '운동하기', 'due_date': today.replace(day=min(today.day + 3, 28)), 'due_time': None, 'is_done': False},
    ]


def init_task_state():
    if "tasks" not in st.session_state:
        st.session_state.tasks = _demo_tasks()


def render_todo_view():
    init_task_state()

    st.subheader('할 일 관리')

    # 새 일정 등록 간이 폼
    with st.expander("➕ 새 일정 등록", expanded=False):
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            new_title = st.text_input("일정 내용", placeholder="예: 치과 검진", key="new_task_content")
        with c2:
            new_due = st.date_input("날짜", value=date.today(), key="new_task_due")
        with c3:
            st.write("")
            st.write("")
            if st.button("추가", type="primary", key="btn_add_task"):
                if new_title.strip():
                    st.session_state.tasks.append({
                        'content': new_title.strip(),
                        'due_date': new_due,
                        'due_time': None,
                        'is_done': False
                    })
                    st.toast("일정을 등록했습니다.", icon="📅")
                    st.rerun()

    tab_cal, tab_list = st.tabs(["📅 캘린더", "📋 할 일 목록"])

    with tab_cal:
        render_calendar(st.session_state.tasks)

    with tab_list:
        if not st.session_state.tasks:
            st.info("등록된 할 일이 없습니다. 새 일정을 추가해보세요!")
        else:
            filter_status = st.segmented_control(
                "필터",
                ["전체", "미완료", "완료"],
                default="전체",
                label_visibility="collapsed"
            )

            tasks = st.session_state.tasks
            if filter_status == "미완료":
                displayed = [(i, t) for i, t in enumerate(tasks) if not t.get('is_done')]
            elif filter_status == "완료":
                displayed = [(i, t) for i, t in enumerate(tasks) if t.get('is_done')]
            else:
                displayed = [(i, t) for i, t in enumerate(tasks)]

            if not displayed:
                st.info(f"{filter_status} 상태의 할 일이 없습니다.")
            else:
                for idx, t in displayed:
                    col_check, col_content, col_date, col_del = st.columns([1, 6, 3, 1], vertical_alignment="center")
                    is_done = t.get('is_done', False)

                    with col_check:
                        checked = st.checkbox("완료 여부", value=is_done, key=f"chk_task_{idx}", label_visibility="collapsed")
                        if checked != is_done:
                            t['is_done'] = checked
                            st.rerun()

                    with col_content:
                        if is_done:
                            st.markdown(f"<span style='text-decoration: line-through; color: #94A3B8; font-size: 1rem;'>{t.get('content', '')}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<span style='font-weight: 600; color: #1E293B; font-size: 1rem;'>{t.get('content', '')}</span>", unsafe_allow_html=True)

                    with col_date:
                        due = t.get('due_date')
                        if due:
                            due_str = due.strftime("%Y-%m-%d") if hasattr(due, 'strftime') else str(due)
                            today = date.today()
                            if isinstance(due, (date, datetime)) and due == today:
                                st.markdown("<span style='background: #FEE2E2; color: #DC2626; padding: 3px 8px; border-radius: 6px; font-size: 0.82rem; font-weight: 700;'>🚨 오늘 마감</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='color: #64748B; font-size: 0.85rem;'>📅 {due_str}</span>", unsafe_allow_html=True)

                    with col_del:
                        if st.button("🗑️", key=f"btn_del_{idx}", help="삭제", type="tertiary"):
                            st.session_state.tasks.pop(idx)
                            st.toast("할 일을 삭제했습니다.", icon="🗑️")
                            st.rerun()
