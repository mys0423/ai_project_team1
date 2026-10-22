# audio.py
# 음성 전처리,

import hashlib
import io
import soundfile as sf
import librosa
import numpy as np
import wave # WAV 파일 헤더와 PCM 형식 검사
from pathlib import Path # 파일 경로 처리
import pandas as pd

TARGET_SR = 16000
test = Path(__file__).resolve().parent.parent / 'data'
audio_data = Path(__file__).resolve().parent.parent / 'data' / 'clip04.wav'

# wav 파일 검사
def validate_wav(audio):

    try:
        with wave.open(io.BytesIO(audio), 'rb') as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            compression = wav.getcomptype()
            frames = wav.getnframes()
            hash = hashlib.sha256(audio).hexdigest()
    except (wave.Error, EOFError, OSError) as e:
        raise ValueError('유효한 비압축 PCM WAV 파일을 입력해 주세요') from e

    if compression != 'NONE' or channels not in (1, 2) or sample_rate <= 0 or frames <= 0:
        raise ValueError('모노/스테레오 비압축 PCM WAV 파일이 필요합니다')

    return {
        'hash_value': hash,
        'channels': channels,
        'sample_rate': sample_rate,
        'duration': frames / sample_rate
    }

# 모노 변환 / 16000 통일 / 무음 구간 정리
def prepare(audio):

    try:
        y, sr = sf.read(io.BytesIO(audio), dtype='float32')
    except ValueError as e:
        raise ValueError('음성 데이터를 읽을 수 없습니다') from e

    mono = librosa.to_mono(y) if y.ndim == 2 else y

    resampled = librosa.resample(
        mono,
        orig_sr = sr,
        target_sr = TARGET_SR
    )

    if y.size == 0 or not np.isfinite(y).all():
        raise ValueError('유효하지 않은 음성 데이터입니다')

    if resampled.size == 0 or np.max(np.abs(resampled)) < 1e-6:
        raise ValueError('녹음된 소리가 없습니다')

    trimmed, interval = librosa.effects.trim(
        resampled,
        top_db=25
    )

    if not trimmed.size:
        raise ValueError('처리 가능한 구간이 없습니다')

    output = io.BytesIO(audio)

    return trimmed, interval, output

# 전처리
def preprocess(audio):
    info = validate_wav(audio)
    trim, interval, output = prepare(audio)
    prepared = sf.write(output, trim, TARGET_SR, format='WAV', subtype='PCM_16')

    return output.getvalue(), info, interval, prepared


# 중복 데이터 제거
def delete_duplicate(audio_list):

    rows = []

    for name, audio in audio_list:
        info = validate_wav(audio)
        info['filename'] = name
        rows.append(info)
    if not rows:
        return pd.DataFrame(columns=['filename','hash_value', 'channels', 'sample_rate', 'duration'])
    return pd.DataFrame(rows).drop_duplicates(subset=['hash_value'], keep='first')





























