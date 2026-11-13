import datetime
import logging

import jwt

from create_expired_toeken import create_expired_jwt_honeytoken
from detect_honeytoken import SECRET_KEY, app
from log_monitoring import extract_token_id


def make_token(exp_delta, jti="normal-1", key=SECRET_KEY):
    now = datetime.datetime.utcnow()
    payload = {"sub": "user01", "iat": now, "exp": now + exp_delta, "jti": jti}
    return jwt.encode(payload, key, algorithm="HS256")


def call(token):
    return app.test_client().get("/api/data", headers={"Authorization": f"Bearer {token}"})


def test_expired_honeytoken_is_detected(caplog):
    with caplog.at_level(logging.WARNING):
        res = call(create_expired_jwt_honeytoken("attacker01@example.com"))
    assert res.status_code == 403
    line = caplog.records[-1].getMessage()
    assert "\n" not in line
    assert "허니토큰 사용 탐지!" in line
    assert extract_token_id(line) == "honeytoken-9999"


def test_valid_token_passes():
    assert call(make_token(datetime.timedelta(minutes=5))).status_code == 200


def test_expired_normal_token_is_rejected_as_expired():
    res = call(make_token(datetime.timedelta(days=-1)))
    assert res.status_code == 401
    assert res.get_json() == {"error": "만료된 토큰입니다."}


def test_forged_honeytoken_is_not_detected():
    forged = make_token(datetime.timedelta(days=-1), jti="honeytoken-9999", key="wrong-key")
    res = call(forged)
    assert res.status_code == 401
    assert res.get_json() == {"error": "유효하지 않은 토큰입니다."}
