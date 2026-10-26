# model_evaluate.py

import streamlit as st
import pandas as pd
from models.model import train_model, REPORT_PATH

def render_evaluate_view():
    st.subheader('📃 모델 평가')

    if st.button('모델 평가 실행', type='primary'):
        with st.spinner('평가 중...'):
            train_model()

        st.success('모델 평가가 완료되었습니다')


        metrics_path = REPORT_PATH / 'intent_metrics.csv'
        cm_path = REPORT_PATH / 'confusion_matrix.png'
        errors_path = REPORT_PATH / 'intent_errors.csv'

        if metrics_path.exists():
            df = pd.read_csv(metrics_path)

            st.subheader('의도별 평가 지표')
            st.dataframe(df, use_container_width=True, hide_index=True)

        if errors_path.exists():
            errors = pd.read_csv(errors_path)

            st.subheader('대표 오류 사례')

            if errors.empty:
                st.info('오분류 사례가 없습니다')
            else:
                st.dataframe(errors, use_container_width=True, hide_index=True)

        if cm_path.exists():
            st.subheader('혼동 행렬')
            st.image(str(cm_path), use_container_width=True)




















































