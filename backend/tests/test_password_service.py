from app.services.password_service import hash_password, verify_password


def test_password_hashing_and_verification_work():
    password = 'farmer-secret-123'
    hashed = hash_password(password)

    assert hashed
    assert verify_password(password, hashed) is True
    assert verify_password('wrong-password', hashed) is False
