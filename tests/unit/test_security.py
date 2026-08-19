from app.core.security import hash_password, verify_password


def test_hash_password_does_not_return_plaintext():
    password = "super-secret-password"

    hashed_password = hash_password(password)

    assert hashed_password != password


def test_verify_password_accepts_correct_password():
    password = "super-secret-password"

    hashed_password = hash_password(password)

    assert verify_password(
        password,
        hashed_password,
    )


def test_verify_password_rejects_wrong_password():
    password = "super-secret-password"

    hashed_password = hash_password(password)

    assert not verify_password(
        "wrong-password",
        hashed_password,
    )


def test_same_password_generates_different_hashes():
    password = "super-secret-password"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash