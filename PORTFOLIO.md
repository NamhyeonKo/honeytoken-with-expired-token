# 1. 프로젝트 개요 및 소개

이 프로젝트는 OAuth2 인증 환경에서 만료된 Access token을 단순 폐기하지 않고 Honeytoken으로 전환해, 유출된 토큰의 재사용 시도를 탐지하는 PoC입니다. 저장소의 `create_expired_toeken.py`와 `detect_honeytoken.py`는 만료된 JWT 생성과 API 접근 시 탐지 로직을 분리해 구현하고 있으며, `README.md`와 논문 PDF를 통해 연구 맥락(CISC-S’25 학술대회 테스트 프로젝트)이 함께 제시되어 있습니다.

팀 구성은 개인 프로젝트이며, 저장소 기준 주요 구현 언어는 Python입니다. 런타임 프레임워크는 Flask(`detect_honeytoken.py`)이고, 토큰 처리는 PyJWT(`jwt.encode`, `jwt.decode`)를 사용합니다. 인증/통신 흐름은 `Authorization: Bearer <token>` 헤더를 통해 전달된 JWT를 API에서 검증하고, 유효하지 않거나 만료된 토큰은 401로, 허니토큰으로 판별된 경우 403 경고 응답으로 분기하는 방식입니다.

핵심 기능은 첫째, 과거 `iat`/`exp`와 `jti`를 포함한 만료 JWT를 생성하는 기능(`create_expired_toeken.py`), 둘째, `/api/data`에서 Bearer token을 해석하고 허니토큰 패턴(`jti.startswith("honeytoken")`)을 탐지하는 기능(`detect_honeytoken.py`), 셋째, 탐지 로그 파일(`honeytoken_detection.log`)을 tail 방식으로 모니터링하는 기능(`log_monitoring.py`)으로 구성됩니다.

코드 구조는 단일 저장소 내 스크립트 단위 모듈 구성입니다. `create_expired_toeken.py`는 토큰 생성 전용, `detect_honeytoken.py`는 Flask API 및 로깅 전용, `log_monitoring.py`는 로그 후처리/알림 전용으로 책임이 분리되어 있어 시연 단계에서 기능별 실행과 검증이 가능합니다.

| 구성 요소 | 포트 또는 위치 | 방식 |
|---|---|---|
| Detection API (`detect_honeytoken.py`) | `127.0.0.1:5000` | Flask HTTP endpoint(`/api/data`) |
| Honeytoken Generator (`create_expired_toeken.py`) | 로컬 스크립트 실행 | PyJWT 기반 JWT 생성 |
| Log Monitor (`log_monitoring.py`) | `honeytoken_detection.log` 파일 | 파일 tail 모니터링 |

# 2. 담당 역할

## 2-1. 만료 Access token 허니토큰 생성 로직 구현

**무엇을 했는가**  
만료된 JWT를 의도적으로 생성해 공격자 재사용 시나리오를 유도하는 생성 로직을 구현했습니다.

**어떻게 구현했는가**  
`/create_expired_toeken.py`에서 `create_expired_jwt_honeytoken(user_id: str)` 함수를 작성하고, `payload`에 `sub`, `iat`, `exp`, `jti`를 포함했습니다. 특히 `iat = utcnow()-10일`, `exp = utcnow()-5일`로 설정해 생성 시점 기준 이미 만료된 토큰을 만들고, `jwt.encode(payload, SECRET_KEY, algorithm='HS256')`로 서명합니다.

**왜 그렇게 설계했는가**  
README와 논문 초록에서 제시한 “만료 토큰의 허니토큰화”를 코드로 재현하려면, 정상 형식을 유지하되 만료 상태여야 합니다. 따라서 별도 커스텀 토큰 포맷 대신 표준 JWT 필드를 유지하는 방식이 선택된 것으로 보입니다(코드/README 근거 기반 추론).

**어떤 효과가 있었는가**  
기존 JWT 처리 파이프라인과 호환되는 입력을 유지하면서도 공격 탐지용 식별자(`jti`)를 삽입해, 시뮬레이션 환경에서 “정상처럼 보이는 함정 자산”을 일관되게 생성할 수 있습니다.

## 2-2. Honeytoken 탐지 API 및 예외 분기 구현

**무엇을 했는가**  
API 요청에서 토큰을 검증하고, 허니토큰 사용 시도를 별도 경고 흐름으로 분기하는 서버 로직을 구현했습니다.

**어떻게 구현했는가**  
`/detect_honeytoken.py`에서 Flask 라우트 `@app.route('/api/data')`를 구현했습니다. `Authorization` 헤더에서 Bearer token을 추출해 `jwt.decode(..., algorithms=['HS256'])`를 수행하고, `is_honeytoken(decoded_token)`에서 `decoded_token.get("jti", "").startswith("honeytoken")` 조건으로 탐지합니다. 예외는 `ExpiredSignatureError`, `InvalidTokenError`를 분리 처리해 각각 401 응답을 반환합니다.

**왜 그렇게 설계했는가**  
`jti` prefix 기반 판별은 별도 DB 조회 없이 토큰 자체 정보만으로 탐지가 가능해 PoC 단계에서 의존성을 줄이는 선택입니다(코드 구조 기반 추론). 또한 만료/무효 토큰 예외를 라이브러리 예외 타입으로 분기해 실패 원인을 응답 레벨에서 구분할 수 있습니다.

**어떤 효과가 있었는가**  
단일 엔드포인트에서 정상/만료/무효/허니토큰 케이스가 명확히 분기되어, 탐지 시나리오 재현과 로그 축적을 반복 가능하게 만들었습니다.

## 2-3. 탐지 로그 모니터링 스크립트 구현

**무엇을 했는가**  
탐지 로그를 지속 관찰하고 반복 접근을 카운트해 경고를 올리는 후속 모니터링 로직을 구현했습니다.

**어떻게 구현했는가**  
`/log_monitoring.py`에서 `monitor_log_file()`이 `honeytoken_detection.log`를 열고 `seek(0, 2)`로 파일 끝부터 실시간 읽기를 수행합니다. `defaultdict(int)` 기반 `token_usage_counter`로 식별자별 횟수를 누적하고, 2회 이상일 때 `alert(token_id)`를 호출합니다.

**왜 그렇게 설계했는가**  
Flask 앱과 모니터링을 분리하면 API 처리 경로에 추가 부하를 주지 않고, 탐지 후속 처리 로직을 독립적으로 실험할 수 있습니다(스크립트 분리 구조 기반 추론).

**어떤 효과가 있었는가**  
탐지 이벤트를 “단발 로그”에서 “반복 행위 식별”로 확장할 수 있어, 재시도형 공격 패턴 관찰에 유리한 구조를 확보했습니다.

# 3. 기술 스택

| 분류 | 기술 | 설명 |
|---|---|---|
| Backend | Python | Flask 서버, JWT 생성/검증, 로그 모니터링 스크립트 구현 언어 (`README.md`) |
| Backend Framework | Flask 3.0.0 | 탐지 API 엔드포인트(`/api/data`) 제공 (`requirements.txt`, `detect_honeytoken.py`) |
| Authentication Token | PyJWT 2.8.0 | `jwt.encode`/`jwt.decode`로 JWT 서명·검증 (`requirements.txt`) |
| Logging | Python `logging` (stdlib) | `honeytoken_detection.log` 파일 기록 (`detect_honeytoken.py`) |
| Monitoring | Python `collections.defaultdict` (stdlib) | 토큰 사용 횟수 카운팅 (`log_monitoring.py`) |

# 4. 핵심 성과

- **만료 JWT 재활용 접근**으로 `exp`가 지난 토큰을 허니토큰 자산으로 전환하고, 동일 JWT 구조를 유지해 공격자 입장에서 구분 난도를 높이는 PoC를 구현했습니다.
- **`jti` 기반 탐지 분기**로 `/api/data` 요청을 정상/만료/무효/허니토큰 케이스로 나누어 탐지 이벤트를 API 응답과 로그에 동시에 남기도록 구성했습니다.
- **파일 기반 감사 로그 기록**(`logging.basicConfig(filename='honeytoken_detection.log')`)으로 탐지 시 IP, User-Agent를 보존해 사후 분석 가능한 증적을 남겼습니다.
- **탐지 후속 모니터링 분리**로 API와 모니터링 스크립트를 독립 실행 가능하게 구성해, 반복 접근 카운팅과 알림 로직을 별도 실험할 수 있게 했습니다.

## 사용자 확인 필요 사항

1. 논문 초록에는 “액세스 토큰 사전 재발급 시스템 도입”이 언급되지만, 현재 저장소에는 재발급/로테이션 자동화 로직이 보이지 않습니다. 해당 부분이 별도 비공개 코드 또는 데모 환경에 존재했는지 확인 부탁드립니다.  
2. `log_monitoring.py`는 `"허니토큰 사용 탐지!"` 문자열을 찾지만, `detect_honeytoken.py` 로그 메시지는 `"허니토큰 사용 탐지\n IP: ..."` 형태입니다. 실제 실험에서는 어떤 로그 포맷으로 모니터링을 수행했는지 확인 부탁드립니다.  
3. 현재 분석 문서는 저장소 코드 기준으로는 개인 단독 구현으로 확인됩니다(`git blame`: 주요 파일 작성자 `namhyun`). 포트폴리오에 이 범위를 “전체 구현 담당”으로 확정 기재해도 되는지 확인 부탁드립니다.
