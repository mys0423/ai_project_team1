# model1.py

from functools import lru_cache
from pathlib import Path
from datetime import date, timedelta
import re
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score, precision_recall_fscore_support,
                             ConfusionMatrixDisplay)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from util.print_util import pp

BASE = Path(__file__).resolve().parent.parent
CSV_PATH = BASE / 'data' / 'commands_RE.csv'
REPORT_PATH = BASE / 'reports'
TOKEN_PATTERN = r'(?u)\b\w+\b'

@lru_cache(maxsize=1)
def train_model(csv_path=CSV_PATH):
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    X, y = df['text'], df['intent']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.25, random_state=42, stratify=y_train
    )

    logistic = Pipeline([
        ('tfidf', TfidfVectorizer(token_pattern=TOKEN_PATTERN, ngram_range=(1, 2))),
        ('model', LogisticRegression(max_iter=1000, random_state=42))
    ])
    linear = Pipeline([
        ('tfidf', TfidfVectorizer(token_pattern=TOKEN_PATTERN, ngram_range=(1, 2))),
        ('model', LinearSVC(max_iter=1000, random_state=42, dual=False))
    ])

    results = []
    for name, candidate in [('LogisticRegression', logistic), ('LinearSVC', linear)]:
        candidate.fit(X_train, y_train)
        pred = candidate.predict(X_val)
        results.append({
            'model': name,
            'Accuracy': accuracy_score(y_val, pred),
            'Precision': precision_score(y_val, pred, average='macro', zero_division=0),
            'Recall': recall_score(y_val, pred, average='macro', zero_division=0),
            'F1': f1_score(y_val, pred, average='macro', zero_division=0)
        })

    pp('[검증 데이터 모델 비교]')
    pp(pd.DataFrame(results).round(4).to_string(index=False))

    best = max(results, key=lambda r: (r['Accuracy'], r['F1']))
    model_name = best['model']
    model = logistic if model_name == 'LogisticRegression' else linear
    pp('선택 모델:', model_name)

    predicted = model.predict(X_test)
    pp('테스트 Accuracy:', round(accuracy_score(y_test, predicted), 4))
    pp('테스트 Macro F1:', round(f1_score(y_test, predicted, average='macro'), 4))

    p, r, f, support = precision_recall_fscore_support(
        y_test, predicted, labels=model.classes_, zero_division=0
    )
    pp('\n[의도별 테스트 성능]')
    pp(pd.DataFrame({
        'intent': model.classes_, 'Precision': p, 'Recall': r,
        'F1': f, 'count': support
    }).round(4).to_string(index=False))

    REPORT_PATH.mkdir(parents=True, exist_ok=True)
    ConfusionMatrixDisplay.from_predictions(y_test, predicted, xticks_rotation=90)
    plt.tight_layout()
    plt.savefig(REPORT_PATH / 'confusion_matrix.png', bbox_inches='tight')
    plt.close()

    errors = pd.DataFrame({
        'text': X_test.to_numpy(), 'intent': y_test.to_numpy(), 'predict': predicted
    })
    errors = errors[errors['intent'] != errors['predict']]
    pp('\n오분류 건수:', len(errors))
    if not errors.empty:
        pp(errors.to_string(index=False))

    model.fit(X, y)
    return model, model_name

WEEKDAYS = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
DATE_PATTERN = re.compile(
    r'\d{4}[-./]\d{1,2}[-./]\d{1,2}|'
    r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일|'
    r'(?:다음\s*달|이번\s*달)\s*\d{1,2}일|'
    r'\d{1,2}월\s*\d{1,2}일|'
    r'(?:이번\s*주|다음\s*주|지난\s*주)\s*[월화수목금토일]요일|'
    r'오늘|내일|모레|어제|그저께|방금'
)

def convert_date(date_text, today=None):
    today = today or date.today()
    s = re.sub(r'\s+', '', date_text)
    offsets = {'그저께': -2, '어제': -1, '오늘': 0,
               '방금': 0, '내일': 1, '모레': 2}
    if s in offsets:
        return (today + timedelta(days=offsets[s])).isoformat()

    m = re.fullmatch(r'(이번주|다음주|지난주)([월화수목금토일])요일', s)
    if m:
        week_offset = {'지난주': -1, '이번주': 0, '다음주': 1}[m.group(1)]
        monday = today - timedelta(days=today.weekday())
        return (monday + timedelta(weeks=week_offset, days=WEEKDAYS[m.group(2)])).isoformat()

    m = re.fullmatch(r'(이번달|다음달)(\d{1,2})일', s)
    if m:
        year, month = today.year, today.month
        if m.group(1) == '다음달':
            month += 1
            if month == 13:
                year, month = year + 1, 1
        try:
            return date(year, month, int(m.group(2))).isoformat()
        except ValueError:
            return None

    m = re.fullmatch(r'(\d{4})년(\d{1,2})월(\d{1,2})일', s)
    if not m:
        m = re.fullmatch(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})', s)
    if m:
        try:
            return date(*map(int, m.groups())).isoformat()
        except ValueError:
            return None

    m = re.fullmatch(r'(\d{1,2})월(\d{1,2})일', s)
    if m:
        month, day = map(int, m.groups())
        try:
            result = date(today.year, month, day)
            if result < today:
                result = date(today.year + 1, month, day)
            return result.isoformat()
        except ValueError:
            return None
    return None

def clean_title(value):
    value = value.strip(' ,，.!?')
    value = re.sub(r'^(?:할\s*일(?:에|에서|중에|로)?|메모(?:에|장에)?)\s*', '', value)
    value = re.sub(r'^(?:에|를|을|은|는)\s+', '', value)
    value = re.sub(r'\s*(?:을|를|은|는|이|가|에|로|으로|까지)$', '', value)
    return value.strip(' ,，.!?')

def extract_slots(text, intent):
    slots = {}
    working = text.strip()
    dates = list(DATE_PATTERN.finditer(text))

    if intent in {'ADD_TASK', 'LIST_TASK', 'UPDATE_TASK', 'COMPLETE_TASK', 'DELETE_TASK'}:
        if intent == 'UPDATE_TASK':
            if dates:
                if len(dates) >= 2:
                    slots['DUE_DATE'] = convert_date(dates[0].group())
                    slots['NEW_DUE_DATE'] = convert_date(dates[-1].group())
                else:
                    slots['NEW_DUE_DATE'] = convert_date(dates[0].group())
        elif dates:
            slots['DUE_DATE'] = convert_date(dates[0].group())
    elif intent in {'LIST_MEMO', 'DELETE_MEMO'} and dates:
        slots['MEMO_DATE'] = convert_date(dates[0].group())

    working = DATE_PATTERN.sub(' ', working)
    working = re.sub(r'\s+', ' ', working).strip()
    working = re.sub(r'^(?:까지|에|부터)\s+', '', working)

    if intent == 'HELP':
        return {}

    if intent == 'LIST_TASK':
        m = re.search(r'안\s*끝낸|미완료|완료한|완료된', working)
        if m:
            slots['STATUS'] = m.group()
        return {k: v for k, v in slots.items() if v is not None}

    if intent in {'LIST_MEMO', 'DELETE_MEMO'}:
        m = re.search(r'^(.+?)\s*(?:관련|들어간)?\s*메모', working)
        if m:
            keyword = clean_title(m.group(1))
            if keyword and keyword not in {'쓴', '적어 둔', '작성한', '방금'}:
                slots['KEYWORD'] = keyword
        return {k: v for k, v in slots.items() if v is not None}

    if intent == 'ADD_MEMO':
        patterns = [
            r'^(.+?)\s*이라고\s*(?:메모|적어)',
            r'^메모\s*추가\s*[,，:]\s*(.+)$',
            r'^메모장에\s*(.+?)\s*(?:남겨|적어|써)',
            r'^(.+?)\s*[,，]?\s*메모해',
            r'^(.+?)\s*메모(?:해|로\s*남겨|에\s*적어)'
        ]
        for pattern in patterns:
            m = re.search(pattern, working)
            if m:
                slots['MEMO_CONTENT'] = clean_title(m.group(1))
                break
        return slots

    if intent == 'UPDATE_TASK':
        m = re.search(r'^(.+?)\s*(?:이름을|제목을|을|를)\s*(.+?)(?:로|으로)\s*(?:바꿔|수정해|변경해)', working)
        if m and 'NEW_DUE_DATE' not in slots:
            slots['TITLE'] = clean_title(m.group(1))
            slots['NEW_TITLE'] = clean_title(m.group(2))
        else:
            m = re.match(r'^(.+?)\s*(?:마감을|날짜를|기한을|일정을|로\s*미뤄|옮겨|바꿔|수정해)', working)
            if m:
                slots['TITLE'] = clean_title(m.group(1))
            elif 'NEW_DUE_DATE' in slots:
                title = re.sub(r'\s*(?:마감을|날짜를|기한을|일정을|로|으로|바꿔|옮겨|미뤄|수정해|변경해).*$', '', working)
                if clean_title(title):
                    slots['TITLE'] = clean_title(title)
        return {k: v for k, v in slots.items() if v is not None}

    if intent == 'ADD_TASK':
        patterns = [
            r'할\s*일(?:에|로)?\s*(.+?)\s*(?:추가해|넣어|등록해)',
            r'^(.+?)\s*(?:해야\s*돼|끝내야).*?(?:할\s*일에|등록해|넣어)',
            r'^(.+?)\s*(?:할\s*일로\s*)?(?:등록해|추가해|넣어)',
            r'^할\s*일\s*추가\s*[,，:]\s*(.+)$'
        ]
    elif intent == 'COMPLETE_TASK':
        patterns = [
            r'할\s*일\s*중에\s*(.+?)\s*(?:완료|끝)',
            r'^(.+?)\s*(?:완료|끝났어|다\s*했어)',
            r'^(.+?)\s*(?:완료로|완료\s*처리)'
        ]
    elif intent == 'DELETE_TASK':
        patterns = [
            r'할\s*일에서\s*(.+?)\s*(?:지워|삭제|빼)',
            r'^(.+?)\s*할\s*일\s*(?:삭제|지워|뺴줘)',
            r'^(.+?)\s*(?:안\s*해도\s*돼|삭제|지워|빼)'
        ]
    else:
        patterns = []

    for pattern in patterns:
        m = re.search(pattern, working)
        if m:
            title = clean_title(m.group(1))
            if title:
                slots['TITLE'] = title
                break
    return {k: v for k, v in slots.items() if v is not None}

def predict_intent(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('텍스트를 입력하세요')
    model, model_name = train_model()
    intent = model.predict([text])[0]
    if model_name == 'LogisticRegression':
        score = model.predict_proba([text]).max()
        score_type = 'probability'
    else:
        score = model.decision_function([text]).max()
        score_type = 'decision_score'
    return {
        'model_name': model_name,
        'intent': intent,
        'confidence_or_score': float(score),
        'score_type': score_type,
        'slots': extract_slots(text, intent)
    }

if __name__ == '__main__':
    samples = [
        '내일 할 일에 운동 추가해 줘',
        '10월 30일까지 택배 보내기 할 일에 넣어 줘',
        '다음 주 월요일 할 일 뭐 있어?',
        '운동 마감을 이번 주 금요일로 바꿔 줘',
        '보고서 작성 완료했어',
        '과제 제출 할 일 삭제해 줘',
        '메모 추가, 프린터 잉크 사야 함',
        '과제 관련 메모 보여 줘',
        '시험 관련 메모 지워 줘',
        '사용할 수 있는 명령 알려 줘',
        '운동 빼 줘'
    ]
    for text in samples:
        pp('\n', text, '\n', predict_intent(text))
