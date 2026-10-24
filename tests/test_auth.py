"""Tests for the demo-only authentication boundary."""

from qshield.auth import (
    AUTH_SESSION_KEY,
    DEMO_PASSWORD,
    DEMO_USERNAME,
    is_authenticated,
    login_user,
    logout_user,
    verify_credentials,
)


def test_default_demo_credentials_are_valid():
    assert verify_credentials(DEMO_USERNAME, DEMO_PASSWORD) is True


def test_wrong_credentials_are_rejected_without_session_mutation():
    state = {}

    assert login_user(DEMO_USERNAME, "wrong-password", state) is False
    assert is_authenticated(state) is False
    assert AUTH_SESSION_KEY not in state


def test_successful_login_and_logout_update_session_state():
    state = {}

    assert login_user(DEMO_USERNAME, DEMO_PASSWORD, state) is True
    assert is_authenticated(state) is True
    assert state[AUTH_SESSION_KEY] == DEMO_USERNAME

    logout_user(state)
    assert is_authenticated(state) is False
    assert AUTH_SESSION_KEY not in state
