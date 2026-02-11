# 만료된 Access Token의 허니토큰화: 능동형 비인가 탐지 시스템
> **디셉션(Deception) 기반의 비인가 접근 탐지 기법 연구**

## 📌 프로젝트 개요
본 프로젝트는 **"만료된 Access Token의 허니토큰화: 디셉션 기반 비인가 탐지 기법 연구"** 논문을 입증하기 위한 PoC(Proof of Concept) 구현체입니다.

> **관련 논문**: [CISC-S_25_paper_146.pdf](CISC-S_25_paper_146.pdf)  
> **발표**: CISC-S'25 (2025 정보보호학회 하계학술대회)

기존 OAuth 2.0 환경에서는 만료된 액세스 토큰이 단순히 폐기되거나 거부됩니다. 본 프로젝트는 이러한 만료된 토큰을 **허니토큰(Honeytoken)**으로 전환하는 **사이버 디셉션(Cyber Deception)** 전략을 제안합니다. 이를 통해 탈취된 만료 자격 증명을 재사용하려는 공격자를 능동적으로 탐지하고 추적하며, 수동적인 방어 메커니즘을 적극적인 위협 인텔리전스 수집 수단으로 전환합니다.

### 핵심 목표 (Key Objectives)
- **허니토큰 전환 (Honeytoken Transformation)**: 특정 만료 토큰을 자동으로 탐지용 함정(Trap)으로 전환합니다.
- **능동적 탐지 (Active Detection)**: 허니토큰을 이용한 악의적인 재사용(Replay) 공격을 식별합니다.
- **구분 불가능성 (Indistinguishability)**: 공격자를 속이기 위해 허니토큰을 정상 토큰과 동일한 형태로 유지합니다.

---

## 🚀 주요 기능 (Key Features)

### 1. 허니토큰 생성 (`create_expired_toeken.py`)
- 정상적인 형식을 갖추었으나, 의도적으로 과거의 만료 날짜(`exp`)를 가진 JWT를 생성합니다.
- 공격자가 눈치채지 못하도록 고유 식별자(`jti`)를 심어 일반 트래픽과 구분하고 추적합니다.

### 2. 능동 탐지 API (`detect_honeytoken.py`)
- 보호된 자원 서버(Resource Server) 역할을 수행합니다.
- 표준 유효성 검증 실패 이전에 요청을 가로챕니다.
- 토큰이 알려진 허니토큰인지 확인합니다. 일치할 경우 단순한 401 오류 대신 경고를 트리거하고 접근 시도에 대한 주요 정보(IP, User-Agent)를 기록합니다.

### 3. 실시간 위협 모니터링 (`log_monitoring.py`)
- 탐지 트리거에 대한 접근 로그를 지속적으로 모니터링합니다.
- 반복적인 접근 시도를 식별하고 경고(Alert) 수준을 높일 수 있습니다.

---

## 🛠️ 기술 스택 (Technology Stack)
- **Language**: Python 3.x
- **Framework**: Flask (마이크로서비스 API 시뮬레이션)
- **Security**: PyJWT (토큰 서명 및 검증)
- **Logging**: Python Standard Logging (파일 기반 감사 추적)

---

## 📦 설치 및 사용법 (Installation & Usage)

### 1. 레포지토리 클론
```bash
git clone https://github.com/your-username/honeytoken-detection.git
cd honeytoken-detection
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 탐지 서버 실행
```bash
python detect_honeytoken.py
```
*서버는 `http://127.0.0.1:5000`에서 실행됩니다.*

### 4. 허니토큰 생성 (공격자 시뮬레이션용)
새 터미널을 열고 다음을 실행합니다:
```bash
python create_expired_toeken.py
```
*생성된 토큰 문자열을 복사하세요.*

### 5. 공격 시뮬레이션 (Attack Simulation)
생성된 허니토큰을 사용하여 서버에 요청을 보냅니다:
```bash
curl -H "Authorization: Bearer <YOUR_HONEY_TOKEN>" http://127.0.0.1:5000/api/data
```
서버는 탐지 경고로 응답하며, 해당 이벤트는 로그에 기록됩니다.

### 6. 로그 모니터링
```bash
python log_monitoring.py
```

---

## 🔮 향후 계획 및 확장성 (Future Roadmap & Scalability)

본 PoC를 엔터프라이즈급 보안 솔루션으로 발전시키기 위해 다음과 같은 로드맵을 제안합니다:

### 1. 중앙 집중식 토큰 관리 (Redis/Memcached)
- **현재**: 토큰 검증이 로컬 또는 하드코딩 방식으로 이루어짐.
- **미래**: 고성능 키-값 저장소(Redis)를 도입하여 분산 환경에서 허니토큰의 생명주기(유효/만료/허니토큰 상태)를 관리합니다. 이를 통해 대용량 트래픽 API에서도 낮은 지연 시간으로 검증이 가능합니다.

### 2. 고도화된 이상 탐지 (AI/ML)
- **현재**: `jti` 기반의 단순 패턴 매칭.
- **미래**: 머신러닝 모델을 통합하여 허니토큰과 관련된 접근 패턴(사용 시간, 지리적 이상 징후, 불가능한 여행 등)을 분석합니다. 이를 통해 오탐(False Positive)을 줄이고 정교한 APT 공격을 탐지합니다.

### 3. 엔터프라이즈 로깅 연동 (ELK Stack)
- **현재**: 로컬 파일 로깅.
- **미래**: 로그를 **Elasticsearch, Logstash, Kibana (ELK)** 또는 Splunk로 전송합니다. 보안 팀은 이를 통해 공격 흐름을 시각화하고, 다른 보안 이벤트와 연관 분석하여 종합적인 대시보드를 구축할 수 있습니다.

### 4. 자동화된 사고 대응 (SOAR)
- **현재**: 수동 로그 확인.
- **미래**: Slack, MS Teams, PagerDuty API와 연동하여 실시간 알림을 전송합니다. 더 나아가 SOAR 플랫폼과 연동하여 탐지 즉시 방화벽 레벨에서 IP를 차단하는 등 대응을 자동화합니다.

### 5. 컨테이너화 및 오케스트레이션
- **미래**: 애플리케이션을 Dockerize하고 Kubernetes 배포를 위한 Helm 차트를 제공하여, 마이크로서비스 아키텍처 환경에서 능동형 기만 레이어가 동적으로 확장될 수 있도록 지원합니다.

---

## 📄 라이선스 (License)
[MIT License](LICENSE)
