# stt.py
# 음성 전처리,

import hashlib
import io
import tempfile
import librosa
import numpy as np
import wave # WAV 파일 헤더와 PCM 형식 검사
from pathlib import Path # 파일 경로 처리

TARGET_SR = 16000


def inspect(audio):

    try:
        with wave.open(io.BytesIO(audio), 'rb') as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            compression = wav.getcomptype()
            frames = wav.getnframes()
    except (wave.Error, EOFError, OSError) as e:
        raise ValueError('유효한 비압축 PCM WAV 파일을 입력해 주세요') from e

    if compression != 'NONE' or channels not in (1, 2) or sample_rate <= 0 or frames <= 0:
        raise ValueError('모노/스테레오 비압축 PCM WAV 파일이 필요합니다')

    return audio

# 모노 / 16000 통일 / 무음 구간 정리
def prepare(y, sr):

    mono = librosa.to_mono(y) if y.ndim == 2 else y

    resampled = librosa.resample(
        mono,
        orig_sr = sr,
        target_sr = TARGET_SR
    )

    if resampled.size == 0 or np.max(np.abs(resampled)) < 1e-6:
        raise ValueError('녹음된 소리가 없습니다')

    trimmed, interval = librosa.effects.trim(
        resampled,
        top_db=25
    )

    if not trimmed.size:
        raise ValueError('처리 가능한 구간이 없습니다')

    return trimmed, interval

# 중복 데이터 확인
def duplicate(audio):

    hash_value = hashlib.sha256(audio).hexdigest()



























































































































