import time
from collections import defaultdict

# 모니터링할 로그 파일 경로
LOG_FILE_PATH = 'honeytoken_detection.log'

# 토큰 사용 횟수 저장 (jti 또는 전체 토큰 스트링)
token_usage_counter = defaultdict(int)

def monitor_log_file():
    print("[탐지 시작] 로그 파일을 모니터링 중...")

    with open(LOG_FILE_PATH, 'r') as log_file:
        # 파일 끝으로 이동
        log_file.seek(0, 2)

        while True:
            line = log_file.readline()

            if not line:
                time.sleep(1)
                continue

            # 특정 토큰 ID 혹은 jti 파싱 (간단한 예시)
            if "허니토큰 사용 탐지!" in line:
                # 예: jti 정보 포함된 라인이면 추출
                # 여기서는 IP 또는 식별자로 대체 가능
                # 고급 처리: 정규표현식 사용 가능
                token_id = extract_token_id(line)  # 사용자 정의 함수 또는 위치 기반 파싱

                if token_id:
                    token_usage_counter[token_id] += 1

                    if token_usage_counter[token_id] == 2:
                        print(f"\n[허니토큰 판별] 토큰 ID '{token_id}'이(가) 2회 이상 사용됨 → 허니토큰으로 간주합니다.")
                        alert(token_id)

def extract_token_id(log_line):
    # 간단 예시: 로그에 'jti=honeytoken-9999' 형태로 포함돼 있다고 가정
    if "jti=" in log_line:
        parts = log_line.strip().split("jti=")
        return parts[1].split()[0]
    return None

def alert(token_id):
    print(f"[경고] 반복 사용된 허니토큰 감지됨\n 토큰 ID: {token_id}")

if __name__ == "__main__":
    monitor_log_file()