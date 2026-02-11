import jwt
import datetime

#   JWT 서명에 사용할 비밀 키 (서버와 공유된 key)
SECRET_KEY = 'supersecret_honeytoken_key'

#   허니토큰 JWT 생성 함수
#   access token 유효기간 5일짜리
def create_expired_jwt_honeytoken(user_id: str):
    payload = {
        "sub": user_id,                 # 사용자 ID (공격자 유인용)
        "iat": datetime.datetime.utcnow() - datetime.timedelta(days=10),  # 발급일 10일 전
        "exp": datetime.datetime.utcnow() - datetime.timedelta(days=5),   # 만료일 5일 전
        "jti": "honeytoken-9999"        # 고유 식별자 (탐지용 필드)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

# 예시 사용
honey_token = create_expired_jwt_honeytoken("attacker01@example.com")
print(f"🪤 생성된 만료된 Access Token (Honeytoken):\n{honey_token}")