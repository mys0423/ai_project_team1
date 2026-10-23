# model_fit_predict.py

from functools import lru_cache
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, ConfusionMatrixDisplay, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
import pandas as pd
from pathlib import Path
from util.print_util import pp



BASE = Path(__file__).resolve().parent.parent
CSV_PATH =  BASE / "data" / 'commands_RE.csv'
REPORT_PATH = BASE / 'reports'
token_pattern = r'(?u)\b\w+\b'

@lru_cache(maxsize=1)
def train_model(csv_path=CSV_PATH):
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    X = df['text']
    y = df['intent']

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train,
        y_train,
        test_size=0.25,
        random_state=42,
        stratify=y_train
    )

    logistic_model = Pipeline([
        ('tfid', TfidfVectorizer(
            token_pattern=token_pattern,
            ngram_range=(1, 2),
            analyzer='word'
        )),
        ('logistic', LogisticRegression(max_iter=1000, random_state=42))
    ])

    logistic_model.fit(X_train, y_train)
    logistic_acc = accuracy_score(y_val, logistic_model.predict(X_val))
    logistic_f1 = f1_score(y_val, logistic_model.predict(X_val), average='macro')
    logistic_precision = precision_score(y_val, logistic_model.predict(X_val), average='macro')
    logistic_recall = recall_score(y_val, logistic_model.predict(X_val), average='macro')

    pp('정확도: ', round(logistic_acc, 2))
    pp('F1 score: ', logistic_f1)

    linear_model = Pipeline([
        ('tfid', TfidfVectorizer(
            token_pattern=token_pattern,
            ngram_range=(1, 2),
            analyzer='word'
        )),
        ('linear', LinearSVC(max_iter=1000, random_state=42, dual=False))
    ])

    linear_model.fit(X_train, y_train)
    linear_acc = accuracy_score(y_val, linear_model.predict(X_val))
    linear_f1 = f1_score(y_val, linear_model.predict(X_val), average='macro')
    linear_precision = precision_score(y_val, logistic_model.predict(X_val), average='macro')
    linear_recall = recall_score(y_val, logistic_model.predict(X_val), average='macro')

    compare_df = pd.DataFrame({
        'model': ['logistic', 'linear'],
        'Accuracy': [logistic_acc, linear_acc],
        'F1 score': [logistic_f1, linear_f1],
        'Precision': [logistic_precision, linear_precision],
        'Recall': [logistic_recall, linear_recall]
    })

    pp(compare_df.round(4))

    pp('LinearSVC 정확도: ', round(linear_acc, 2))
    pp('LinearSVC F1 score: ', linear_f1)

    if logistic_acc > linear_acc:
        model = logistic_model
        model_name = 'Tfid, Logistic'
    else:
        model = linear_model
        model_name = 'Tfid, LinearSVC'

    pp('선택모델', model_name)

    predicted = model.predict(X_test)

    test_acc = accuracy_score(y_test, predicted)
    test_f1 = f1_score(y_test, predicted, average='macro')

    pp('테스트 정확도:', round(test_acc, 4))
    pp('테스트 F1:', round(test_f1, 4))

    REPORT_PATH.mkdir(parents=True, exist_ok=True)
    ConfusionMatrixDisplay.from_predictions(
        y_test,
        predicted,
        xticks_rotation= 90
    )
    plt.tight_layout()
    plt.savefig(REPORT_PATH / 'confusion_matrix.png', bbox_inches='tight')
    plt.close()

    error = pd.DataFrame({
        'model': model_name,
        'text': X_test.to_numpy(),
        'intent': y_test.to_numpy(),
        'predict': predicted
    })
    error = error[error['intent'] != error['predict']]
    pp('오류 건수: \n', len(error))

    if not error.empty:
        pp(error.to_string(index=False))

    model.fit(X, y)

    return model, model_name

# return -> intent: 의도, confidenc_or_score
def predict_intent(text):
    if not text.strip():
        raise ValueError('텍스트를 입력하세요')

    model, model_name = train_model()

    intent = model.predict([text])[0]

    if model_name == 'Tfid, Logistic':
        confidence_or_score = model.predict_proba([text]).max()
        score_type = 'probability'
    else:
        confidence_or_score = model.decision_function([text]).max()
        score_type = 'decision_score'

    return {
        'model_name': model_name,
        'intent': intent,
        'confidence_or_score': float(confidence_or_score),
        'score_type': score_type
    }

if __name__ == '__main__':
    samples = [
        '내일 운동 추가해줘',
        '할 일 목록 보여줘',
        '회의 일정 수정해줘',
        '운동 완료했어',
        '할 일 삭제해줘',
        '메모에 발표 작성해줘',
        '이건 뭐야'
    ]
    for text in samples:
        pp(text, predict_intent(text))































































































































































