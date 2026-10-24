"""Demo-only session authentication for the Streamlit application.

This module provides a small local login gate for demos and judge
presentations. It is not a production identity system: credentials are local,
there are no user accounts or roles, and the default account is public by
design.
"""

from __future__ import annotations

import hmac
import os
from collections.abc import MutableMapping


AUTH_SESSION_KEY = "qshield_authenticated_user"
DEMO_USERNAME = os.environ.get("QSHIELD_DEMO_USERNAME", "judge")
DEMO_PASSWORD = os.environ.get("QSHIELD_DEMO_PASSWORD", "qshield-demo")


def verify_credentials(username: str, password: str) -> bool:
    """Return whether the supplied demo credentials are valid."""
    return hmac.compare_digest(str(username).strip(), DEMO_USERNAME) and hmac.compare_digest(
        str(password), DEMO_PASSWORD
    )


def is_authenticated(state: MutableMapping[str, object]) -> bool:
    """Return whether a Streamlit-like session mapping is authenticated."""
    return bool(state.get(AUTH_SESSION_KEY))


def login_user(username: str, password: str, state: MutableMapping[str, object]) -> bool:
    """Authenticate the demo user and persist the username in session state."""
    if not verify_credentials(username, password):
        return False
    state[AUTH_SESSION_KEY] = DEMO_USERNAME
    return True


def logout_user(state: MutableMapping[str, object]) -> None:
    """Clear the authenticated user from session state."""
    state.pop(AUTH_SESSION_KEY, None)


def render_auth_sidebar() -> None:
    """Render the authenticated user's identity and logout action."""
    import streamlit as st

    username = st.session_state.get(AUTH_SESSION_KEY)
    if not username:
        return
    st.caption(f"Signed in as **{username}** · demo account")
    if st.button("Log out", use_container_width=True):
        logout_user(st.session_state)
        st.rerun()


def require_login() -> None:
    """Render the login screen and stop the current page when unauthenticated."""
    import streamlit as st

    if is_authenticated(st.session_state):
        return

    st.markdown(
        """
        <style>
            .login-card {
                max-width: 520px;
                margin: 8vh auto 0 auto;
                padding: 2rem;
                border: 1px solid #dbe3ef;
                border-radius: 14px;
                background: linear-gradient(145deg, #ffffff, #f5f8fc);
                box-shadow: 0 12px 30px rgba(18, 33, 59, 0.12);
            }
            .login-card h1 { color: #1a1f36; margin-bottom: 0.25rem; }
            .login-card p { color: #64748b; }
        </style>
        <div class="login-card">
            <h1>🛡️ Q-Shield</h1>
            <p>Sign in to the local quantum-readiness planning demo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("qshield_login_form"):
        username = st.text_input("Username", autocomplete="username")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

    if submitted:
        if login_user(username, password, st.session_state):
            st.rerun()
        st.error("Invalid demo username or password.")

    st.info(
        f"Demo credentials: username `{DEMO_USERNAME}`, password `{DEMO_PASSWORD}`. "
        "This built-in account is for local demonstrations only, not production security."
    )
    st.stop()
