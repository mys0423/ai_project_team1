
from pathlib import Path
import time

import pandas as pd
from faster_whisper import WhisperModel
from jiwer import wer, cer

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "stt_test"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# 파일명과 실제 녹음한 문장
REFERENCES = {
    "ADD_MEMO.wav": "다음발표주제는 음성인식이라고 적어줘",
    "ADD_TASK1.wav": "오늘할일에 장보기 추가해줘",
    "ADD_TASK2.wav": "과제 제출을 다음주 월요일 할일로 등록해주세요",
    "LIST_MEMO.wav": "그저께 쓴 메모 알려줘",
    "LIST_TASK.wav": "완료한 할일목록 읽어줘",
    "LIST_TASK2.wav": "끝난 할일 목록 읽어줘",
    "T00_ADD_MEMO.wav": "메모에 우유사기라고 적어줘",
    "T01_ADD_MEMO.wav": "장보기 목록 메모해줘",
    "T02_ADD_MEMO.wav": "회의 준비라고 메모해줘",
    "T03_LIST_MEMO.wav": "저장된 메모 보여줘",
    "T04_ADD_TASK.wav": "오늘 할일에 운도 추가해줘",
    "T05_LIST_TASK.wav": "내일 할일 알려줘",
}

def main():
    model = WhisperModel(
        "base",
        device="cpu",
        compute_type="int8",
        cpu_threads=2,
    )

    results = []

    for beam_size in range(1, 11):
        print(f"\n===== BEAM SIZE {beam_size} =====")

        for filename, reference in REFERENCES.items():
            path = AUDIO_DIR / filename

            if not path.exists():
                print(f"파일 없음: {path}")
                continue

            start = time.perf_counter()

            segments, info = model.transcribe(
                str(path),
                language="ko",
                beam_size=beam_size,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 300,
                },
                condition_on_previous_text=False,
                temperature=0,
            )

            prediction = " ".join(
                segment.text.strip() for segment in segments
            ).strip()

            latency = time.perf_counter() - start
            duration = info.duration

            result = {
                "beam_size": beam_size,
                "file": filename,
                "reference": reference,
                "prediction": prediction,
                "WER": wer(reference, prediction),
                "CER": cer(reference, prediction),
                "Latency": latency,
                "RTF": latency / duration if duration > 0 else 0,
            }

            results.append(result)

            print(f"파일: {filename}")
            print(f"정답: {reference}")
            print(f"인식: {prediction}")
            print(f"WER: {result['WER']:.2%}")
            print(f"CER: {result['CER']:.2%}")
            print(f"처리시간: {latency:.2f}초")

    if not results:
        print("테스트할 음성 파일이 없습니다.")
        return

    df = pd.DataFrame(results)

    summary = (
        df.groupby("beam_size", as_index=False)
        .agg(
            WER=("WER", "mean"),
            CER=("CER", "mean"),
            Latency=("Latency", "mean"),
            RTF=("RTF", "mean"),
        )
        .sort_values(["CER", "RTF"])
    )

    print("\n===== 최종 비교 결과 =====")
    print(summary.to_string(index=False))

    df.to_csv(
        REPORT_DIR / "stt_beam_details.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        REPORT_DIR / "stt_beam_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("\n결과 저장 완료!")

if __name__ == "__main__":
    main()
