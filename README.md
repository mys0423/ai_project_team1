# 🎙️ 나만의 AI 음성 비서 — 한국어 음성 명령 기반 메모·할 일 관리 서비스

## 1. 프로젝트 개요
- **팀원 및 담당 기능**:
  - **문윤성 (팀장)**: 프로젝트 기획 총괄, End-to-End 파이프라인 통합, 협업 및 WBS 관리
  - **최준혁 (AI 모델)**: TF-IDF + LinearSVC 의도 분류 모델(9개 의도) 학습, 슬롯 추출 규칙 엔진 구축, 모델 성능 평가
  - **엄기훈 (서비스·DB)**: Neon PostgreSQL 클라우드 DB 연동, 할 일·메모·이력 CRUD 트랜잭션, 비즈니스 예외 처리
  - **이태규 (데이터)**: 음성 데이터 전처리(16kHz Mono 리샘플링), 학습/평가 데이터셋 구축, STT 오류 분석
  - **정유아 (UI·배포)**: Streamlit 멀티페이지 UI(홈/할일/메모/이력/평가), Altair 시각화 차트, Streamlit Cloud 배포 파이프라인
- **주요 사용자 시나리오**: 
  1. 사용자가 마이크에 “내일 할 일에 발표 준비 추가해 줘”라고 말하거나 오디오 파일을 업로드합니다.
  2. 시스템이 STT로 사용자의 음성을 한국어 텍스트로 고정밀 전사합니다 (사용자 직접 수정 가능).
  3. 핵심 AI 기능이 전사된 텍스트의 의도를 `ADD_TASK`로 분류하고, 규칙 기반 슬롯 파싱을 통해 날짜(`내일`)와 내용(`발표 준비`)을 추출합니다.
  4. TTS가 "내일 할 일에 발표 준비를 추가했습니다."라고 음성 피드백을 제공합니다.
  5. 추출된 할 일 데이터와 실행 메트릭(소요 시간 등)을 Cloud PostgreSQL에 실시간 저장합니다.
- **서비스 화면**:

| 🏠 음성 비서 홈 (음성 입력 및 실시간 전사) | 📌 명령어 사용 가이드 (의도별 발화 예시) |
|:---:|:---:|
| ![음성 비서 홈](assets/ui_home.png) | ![명령어 가이드](assets/ui_guide.png) |

| 📅 할 일 관리 (캘린더 뷰 및 DB 실시간 동기화) | 📝 메모 관리 (키워드 검색 및 간편 저장) |
|:---:|:---:|
| ![할 일 관리](assets/ui_calendar.png) | ![메모 관리](assets/ui_memo.png) |

| 📜 처리 이력 (명령어 통계 및 처리 로그) | 📊 AI 모델 성능 평가 (혼동 행렬 시각화) |
|:---:|:---:|
| ![처리 이력](assets/ui_history.png) | ![모델 평가](reports/confusion_matrix.png) |

## 2. 기능
- **STT**: `faster-whisper` (base 모델)를 활용한 고정밀 한국어 음성 전사 및 전사 텍스트 실시간 수정 기능
- **핵심 AI**: `TfidfVectorizer` + `LinearSVC` 기반 9개 의도 분류(정확도 97.2%) 및 구어체 지원 규칙 기반 슬롯 추출
- **TTS**: `gTTS` / `edge-tts`를 활용한 3종 음성 피드백 생성 및 브라우저 즉시 재생
- **DB**: Cloud PostgreSQL(Neon Serverless)을 활용한 실시간 할 일, 메모 및 처리 이력(`voice_runs`) 영구 관리

## 3. 실행 환경
- **Python**: 3.12 (3.10 이상 권장)
- **운영체제**: Windows 11 / Linux (Streamlit Cloud Debian)
- **외부 API 및 비용/접근 조건**:
  - 유료 API 키 불필요 (오픈소스 라이브러리 및 On-Device 모델 활용)
  - Neon PostgreSQL Free Tier 사용 (인터넷 연결 필요, 미연결 시 세션 데모 모드 자동 폴백)

## 4. 설치
```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 5. 환경변수 및 DB
1. `.env.example`을 참고해 `.env` 파일에 실제 DB 접속 정보를 설정합니다.
2. `sql/schema.sql` 테이블 스키마가 최초 실행 시 자동 적용됩니다.
3. **환경변수 이름과 의미**:
   - `DATABASE_URL`: Neon PostgreSQL 연결 문자열 (형식: `postgresql://user:password@host/dbname?sslmode=require`)
   - *(미설정 시 앱 크래시 없이 세션 메모리 데모 모드로 안전하게 동작합니다.)*

## 6. 실행
```bash
streamlit run app.py
```

## 7. 테스트·평가 재현
- **단위/통합 테스트 명령**:
  ```bash
  python tests/test_app_run.py
  ```
- **의도 분류 모델 재학습 및 평가 명령**:
  ```bash
  python models/model.py
  ```
  *(실행 시 `reports/intent_metrics.csv` 및 `reports/confusion_matrix.png` 자동 생성)*
- **데이터셋 출처**:
  - `data/commands_RE.csv`: 팀 자체 수집 및 교차 검증을 거친 음성 비서 발화 데이터셋 (180건, 9개 의도 균등 분할)

## 8. 주의사항·제약
- **음성 데이터 저장 정책**: 사용자의 개인정보 보호를 위해 원본 음성 파일은 서버에 영구 보관하지 않으며, 전사 처리 후 메모리에서 즉시 폐기됩니다. (텍스트 전사문 및 처리 메타데이터만 이력에 보관)
- **알려진 한계**: 한글 수사 발음("삼십일" 등) 및 1문장 2의도 복합 명령은 단일 의도 분류 특성상 제한되며, 향후 경량 LLM 도입을 통해 고도화 예정입니다.
- **배포 링크**: 
  - [https://aiprojectteam1-g72cg98mdypu9kfeqhuklt.streamlit.app/](https://aiprojectteam1-g72cg98mdypu9kfeqhuklt.streamlit.app/)
