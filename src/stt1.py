# stt1.py
'''
audio.py 불러와서
faster-whisper 실행
음성 파일 전사 처리
전사 처리된 text 반환
wer, cer 반환
'''
import re
import unicodedata
from src.audio import *
from faster_whisper import WhisperModel
import tempfile
from pathlib import Path
import time
from jiwer import wer, cer

# 모델 불러오기
def load_stt_model(model_size):
    return WhisperModel(model_size, device='cpu', compute_type='int8')

# 전사 처리
def transcript_wav(audio, model_size):

    preprocess_audio, info = preprocess(audio)

    start = time.perf_counter()

    model = load_stt_model(model_size)

    elapsed = round(time.perf_counter() - start, 2)

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(preprocess_audio)
        wav_path = Path(f.name)

    try:

        segments, info = model.transcribe(
            str(wav_path),
            language='ko',
            vad_filter=True
        )

        transcript = ''.join(segment.text.strip() for segment in segments).strip()

        text = unicodedata.normalize('NFC', transcript).lower()
        text = re.sub(r'[^가-힣a-z0-9\s]', r' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        return text, elapsed

    finally:
        wav_path.unlink(missing_ok=True)

# wer, cer 반환
def evaluate_score(ref, pred):

    wer_score = wer(ref, pred)
    cer_score = cer(ref, pred)

    return {
        'WER': wer_score,
        'CER': cer_score
    }

































































