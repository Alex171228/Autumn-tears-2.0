from datetime import datetime, timedelta

from jose import jwt

from python_microservices.shared import auth_core


def test_hash_and_verify_password_round_trip():
    password = "strong-password-123"

    hashed = auth_core.hash_password(password)

    assert hashed != password
    assert auth_core.verify_password(password, hashed) is True
    assert auth_core.verify_password("wrong-password", hashed) is False


def test_create_access_token_contains_claims_and_exp():
    token = auth_core.create_access_token(
        {"sub": "alice", "is_admin": True},
        expires_delta=timedelta(minutes=5),
    )

    payload = jwt.decode(token, auth_core.SECRET_KEY, algorithms=[auth_core.ALGORITHM])

    assert payload["sub"] == "alice"
    assert payload["is_admin"] is True
    assert payload["exp"] > int(datetime.utcnow().timestamp())


def test_brute_force_blocks_user_after_repeated_failures():
    protection = auth_core.BruteForceProtection()
    ip = "127.0.0.1"
    username = "tester"

    for _ in range(protection.MAX_ATTEMPTS_PER_USER):
        protection.check_and_record_attempt(ip, username, False)

    allowed, message = protection.is_allowed(ip, username)

    assert allowed is False
    assert isinstance(message, str)
    assert message


def test_brute_force_success_resets_counters():
    protection = auth_core.BruteForceProtection()
    ip = "127.0.0.1"
    username = "tester"

    protection.check_and_record_attempt(ip, username, False)
    protection.check_and_record_attempt(ip, username, True)

    assert protection.failed_attempts_by_ip[ip] == []
    assert protection.failed_attempts_by_user[username] == []


def test_admin_session_invalidates_on_ip_mismatch():
    manager = auth_core.AdminSessionManager()
    token = "token-value"
    manager.create_session(token, "10.0.0.1", "test-agent", "admin")

    is_valid, message = manager.validate_session(token, "10.0.0.2", "test-agent")

    assert is_valid is False
    assert isinstance(message, str)
    assert message


def test_admin_session_expires_after_timeout():
    manager = auth_core.AdminSessionManager()
    token = "token-value"
    token_hash = manager.create_session(token, "10.0.0.1", "test-agent", "admin")
    manager.admin_sessions[token_hash]["last_activity"] = datetime.now() - timedelta(seconds=manager.SESSION_TIMEOUT + 1)

    is_valid, message = manager.validate_session(token, "10.0.0.1", "test-agent")

    assert is_valid is False
    assert isinstance(message, str)
    assert message
