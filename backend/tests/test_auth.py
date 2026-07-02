from utils.password import hash_password, verify_password


def test_password_hashing():
    password = "StrongPass123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
