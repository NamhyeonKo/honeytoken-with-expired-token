from flask import Flask, request, jsonify
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
import logging

app = Flask(__name__)
SECRET_KEY = 'supersecret_honeytoken_key'

# 로깅 설정
logging.basicConfig(
    filename='honeytoken_detection.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# 허니토큰 탐지 함수
def is_honeytoken(decoded_token):
    return decoded_token.get("jti", "").startswith("honeytoken")

# API 엔드포인트 예시
@app.route('/api/data', methods=['GET'])
def protected_api():
    auth_header = request.headers.get('Authorization', None)

    if not auth_header:
        return jsonify({"error": "토큰이 없습니다."}), 401

    try:
        token = auth_header.split(" ")[1]  # 'Bearer <token>' 형식
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        # 허니토큰 탐지
        if is_honeytoken(decoded):
            logging.warning(f"허니토큰 사용 탐지\n IP: {request.remote_addr}, User-Agent: {request.headers.get('User-Agent')}")
            return jsonify({"warning": "허니토큰 접근이 탐지되었습니다. 이 시도는 기록됩니다."}), 403

        return jsonify({"message": "정상적인 접근입니다.", "user": decoded["sub"]})

    except ExpiredSignatureError:
        return jsonify({"error": "만료된 토큰입니다."}), 401
    except InvalidTokenError:
        return jsonify({"error": "유효하지 않은 토큰입니다."}), 401

# Flask 앱 실행
if __name__ == '__main__':
    app.run(debug=True, port=5000)