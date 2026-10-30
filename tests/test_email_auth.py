import pytest

import db
import remotetech_data as data


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "SQLITE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(db, "USE_POSTGRES", False)
    data.init_db()


def test_unverified_account_email_verification_is_single_use():
    assert data.register_user(
        "Learner Example", "learner_example", "learner@example.test",
        "ExamplePass123!", "🚀", email_verified=False,
    )
    assert data.login_user("learner_example", "ExamplePass123!")["email_verified"] is False

    token = data.create_email_verification_token("learner_example", "learner@example.test")
    assert token
    assert data.verify_email_token(token) is True
    assert data.verify_email_token(token) is False
    assert data.login_user("learner_example", "ExamplePass123!")["email_verified"] is True


def test_password_recovery_works_for_school_admin_role():
    assert data.register_user(
        "Teacher Example", "teacher_example", "teacher@example.test",
        "ExamplePass123!", "🧑‍🏫", role="admin", email_verified=True,
    )
    token = data.create_password_reset_token("teacher_example", "teacher@example.test")
    assert token
    assert data.verify_reset_token(token) == "teacher_example"
    assert data.consume_reset_token(token, "ReplacementPass123!") is True
    assert data.consume_reset_token(token, "AnotherPass123!") is False
    assert data.login_user("teacher_example", "ReplacementPass123!") is not None


def test_verification_requires_matching_username_and_email():
    assert data.register_user(
        "Learner Example", "another_learner", "another@example.test",
        "ExamplePass123!", "🚀", email_verified=False,
    )
    assert data.create_email_verification_token("another_learner", "wrong@example.test") is None
