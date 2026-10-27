# src/tts.py
# 팀원 작성 기반 edge-tts 음성 합성 모듈 (선희, 인준, 현수 3종 목소리 지원)

import asyncio
import concurrent.futures
import time
import edge_tts

VOICES = {
    '선희(여성)': 'ko-KR-SunHiNeural',
    '인준(남성)': 'ko-KR-InJoonNeural',
    '현수(남성)': 'ko-KR-HyunsuNeural'
}


async def generate(text: str, voice: str) -> bytes:
    """edge-tts Communicate 스트림을 통해 mp3 바이트 생성"""
    communicate = edge_tts.Communicate(text=text, voice=voice)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            audio.extend(chunk['data'])
    return bytes(audio)


def text_to_speech(text: str, voice: str = 'ko-KR-SunHiNeural') -> bytes:
    """
    텍스트를 edge-tts를 통해 mp3 음성 바이트로 변환합니다.

    Args:
        text: 음성으로 변환할 텍스트
        voice: edge-tts 보이스 (기본: ko-KR-SunHiNeural)
    Returns:
        audio_bytes (bytes)
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError('변환할 텍스트가 없습니다')

    # 보이스 값 검증 및 키/값 상호 호환
    if voice not in VOICES.values():
        if voice in VOICES:
            voice = VOICES[voice]
        else:
            raise ValueError('지원하지않는 목소리입니다')

    clean_text = text.strip()
    # 이모지 정리
    clean_text = clean_text.replace("✅", "").replace("❌", "").replace("📌", "")
    clean_text = clean_text.replace("📅", "").replace("📝", "").replace("⚡", "").strip()

    # Streamlit 스레드 내 이미 실행 중인 이벤트 루프와의 충돌 방지
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, generate(clean_text, voice)).result(timeout=15)
    else:
        return asyncio.run(generate(clean_text, voice))


if __name__ == "__main__":
    sample_text = "내일 3시 치과 예약 일정을 등록했습니다."
    print(f"TTS 변환 테스트 시작: '{sample_text}'")
    for name, v_id in VOICES.items():
        t0 = time.perf_counter()
        data = text_to_speech(sample_text, voice=v_id)
        sec = time.perf_counter() - t0
        print(f"[{name}] 성공: {len(data):,} bytes ({sec:.3f}초)")
