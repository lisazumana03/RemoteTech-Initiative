import pytest
import db
import remotetech_data as data

@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "SQLITE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(db, "USE_POSTGRES", False)
    data.init_db()

def test_registration_allows_immediate_login_without_email_verification():
    assert data.register_user(
        "Learner Example", "learner_example", "learner@example.test",
        "ExamplePass123!", "🚀",
    )
    user = data.login_user("learner_example", "ExamplePass123!")
    assert user is not None
    assert user["username"] == "learner_example"
    assert "email_verified" not in user

def test_wrong_password_is_rejected():
    assert data.register_user(
        "Learner Example", "learner_example", "learner@example.test",
        "ExamplePass123!", "🚀",
    )
    assert data.login_user("learner_example", "WrongPassword123!") is None

def test_password_recovery_still_works_for_school_admin_role():
    assert data.register_user(
        "Teacher Example", "teacher_example", "teacher@example.test",
        "ExamplePass123!", "🧑‍🏫", role="admin",
    )
    token = data.create_password_reset_token("teacher_example", "teacher@example.test")
    assert token
    assert data.verify_reset_token(token) == "teacher_example"
    assert data.consume_reset_token(token, "ReplacementPass123!") is True
    assert data.consume_reset_token(token, "AnotherPass123!") is False
    assert data.login_user("teacher_example", "ReplacementPass123!") is not None
