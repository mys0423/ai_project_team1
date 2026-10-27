# tts.py

import asyncio
import time

import edge_tts

VOICES = {
    "선희(여성)": "ko-KR-SunHiNeural",
    "인준(남성)": "ko-KR-InJoonNeural",
    "현수(남성)": "ko-KR-HyunsuNeural"
}

tts_record = []

async def generate(text, voice):
    communicate = edge_tts.Communicate(text=text, voice=voice)

    audio = bytearray()

    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            audio.extend(chunk['data'])

    return bytes(audio)

def text_to_speech(text, voice='ko-KR-SunHiNeural'):

    start = time.perf_counter()
    try:
        if not isinstance(text, str) or not text.strip():
            raise ValueError('변환할 텍스트가 없습니다')

        if voice not in VOICES.values():
            raise ValueError('지원하지않는 목소리입니다')

        audio = asyncio.run(generate(text.strip(), voice))

        if not audio:
            raise ValueError('음성 데이터가 없습니다')

        elapsed = time.perf_counter() - start

        tts_record.append({
            'voice': voice,
            'elapsed': elapsed,
            'success': True
        })

        return audio

    except Exception:
        elapsed = time.perf_counter() - start

        tts_record.append({
            'voice': voice,
            'elapsed': elapsed,
            'success': True
        })
        raise


def evaluate_tts():
    total = len(tts_record)
    fail = sum(not r['success'] for r in tts_record)

    return {
        'total': total,
        'failures': fail,
        'failure_rate': fail / total * 100 if total else 0,
        'avg_elapsed_sec': (
            sum(r['elapsed_sec'] for r in tts_record) / total
            if total else 0
        )
    }


































































