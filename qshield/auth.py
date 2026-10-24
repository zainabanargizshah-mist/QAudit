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
LOGIN_USERNAME_KEY = "qshield_login_username"
LOGIN_PASSWORD_KEY = "qshield_login_password"
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
    """Clear authentication and any retained login form values."""
    state.pop(AUTH_SESSION_KEY, None)
    state.pop(LOGIN_USERNAME_KEY, None)
    state.pop(LOGIN_PASSWORD_KEY, None)


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
            :root { color-scheme: dark; }
            .stApp {
                min-height: 100vh;
                color: #f8f7f8;
                background:
                    radial-gradient(ellipse at 50% 0%, rgba(255,16,24,0.16), transparent 48%),
                    linear-gradient(145deg, #080809 0%, #111012 52%, #080809 100%);
            }
            [data-testid="stHeader"] { background: transparent; }
            [data-testid="stSidebar"],
            [data-testid="stSidebarNav"] { display: none !important; }
            [data-testid="stAppViewContainer"] { background: transparent; }
            [data-testid="stAppViewContainer"] > .main {
                position: relative;
                min-height: 100vh;
                overflow-y: auto;
            }
            .main .block-container {
                position: relative;
                z-index: 1;
                box-sizing: border-box;
                width: 100%;
                max-width: 500px;
                min-height: 100vh;
                padding: clamp(2rem, 8vh, 5.5rem) 1.25rem 3rem;
                margin: 0 auto;
            }
            .qs-login-light {
                position: fixed;
                z-index: 0;
                top: 8vh;
                left: -14vw;
                width: min(62vw, 660px);
                aspect-ratio: 1;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(255,16,24,0.32) 0%, rgba(255,16,24,0.11) 34%, transparent 70%);
                filter: blur(42px);
                opacity: 0.72;
                pointer-events: none;
                animation: qs-login-light-drift 16s ease-in-out infinite alternate;
            }
            @keyframes qs-login-light-drift {
                0% { transform: translate3d(0, 0, 0) scale(0.92); }
                100% { transform: translate3d(62vw, 24vh, 0) scale(1.16); }
            }
            .qs-login-brand {
                display: flex;
                align-items: center;
                gap: 14px;
                margin: 0 0 clamp(2.75rem, 7vh, 4.5rem);
            }
            .qs-login-mark {
                display: grid;
                place-items: center;
                width: 48px;
                height: 48px;
                flex: 0 0 48px;
                color: #fff;
                background: #ff1018;
                border: 1px solid rgba(255,255,255,0.54);
                box-shadow: 5px 5px 0 rgba(255,255,255,0.85), 0 0 28px rgba(255,16,24,0.2);
                font-size: 1.55rem;
                font-weight: 900;
            }
            .qs-login-brand-name {
                color: #fff;
                font-size: 1rem;
                font-weight: 850;
                letter-spacing: 0.13em;
            }
            .qs-login-brand-subtitle {
                margin-top: 3px;
                color: rgba(255,255,255,0.62);
                font-size: 0.66rem;
                letter-spacing: 0.12em;
            }
            .qs-login-eyebrow {
                margin-bottom: 0.75rem;
                color: #ff4b50;
                font: 700 0.72rem/1.4 ui-monospace, SFMono-Regular, Menlo, monospace;
                letter-spacing: 0.16em;
                text-transform: uppercase;
            }
            .qs-login-heading h1 {
                margin: 0 0 0.7rem;
                color: #fff;
                font-size: clamp(2rem, 7vw, 2.65rem);
                font-weight: 850;
                letter-spacing: -0.035em;
                line-height: 1.05;
                text-transform: uppercase;
            }
            .qs-login-heading p {
                margin: 0 0 1.6rem;
                color: rgba(255,255,255,0.66);
                font-size: 0.98rem;
                line-height: 1.6;
            }
            [data-testid="stForm"] {
                position: relative;
                padding: clamp(1.15rem, 5vw, 1.65rem);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 20px;
                background: linear-gradient(145deg, rgba(255,255,255,0.105), rgba(255,255,255,0.045));
                box-shadow: 0 24px 64px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.16);
                backdrop-filter: blur(22px) saturate(1.22);
                -webkit-backdrop-filter: blur(22px) saturate(1.22);
            }
            [data-testid="stForm"] label,
            [data-testid="stForm"] [data-testid="stWidgetLabel"] p { color: rgba(255,255,255,0.82); }
            [data-testid="stForm"] [data-baseweb="input"] > div {
                min-height: 48px;
                border: 1px solid rgba(255,255,255,0.22);
                border-radius: 10px;
                background: rgba(7,7,9,0.62);
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
            }
            [data-testid="stForm"] [data-baseweb="input"] > div:focus-within {
                border-color: rgba(255,35,43,0.9);
                box-shadow: 0 0 0 3px rgba(255,16,24,0.16);
            }
            [data-testid="stForm"] input { color: #fff; }
            [data-testid="stForm"] input::placeholder { color: rgba(255,255,255,0.4); }
            [data-testid="stForm"] button[kind="primary"] {
                min-height: 48px;
                margin-top: 0.5rem;
                border: 1px solid rgba(255,115,120,0.75);
                border-radius: 10px;
                color: #fff;
                background: linear-gradient(105deg, #c9070d, #ff1018 52%, #d60a11);
                box-shadow: 0 10px 26px rgba(255,16,24,0.18), inset 0 1px 0 rgba(255,255,255,0.22);
                font-weight: 750;
                letter-spacing: 0.04em;
                transition: filter 160ms ease, transform 160ms ease, box-shadow 160ms ease;
            }
            [data-testid="stForm"] button[kind="primary"]:hover {
                filter: brightness(1.08);
                transform: translateY(-1px);
                box-shadow: 0 12px 30px rgba(255,16,24,0.25), inset 0 1px 0 rgba(255,255,255,0.24);
            }
            .qs-login-footer {
                margin-top: 1.15rem;
                color: rgba(255,255,255,0.44);
                font: 0.68rem/1.6 ui-monospace, SFMono-Regular, Menlo, monospace;
                letter-spacing: 0.05em;
                text-align: center;
            }
            @media (max-width: 520px) {
                .main .block-container { padding-inline: 1rem; }
                .qs-login-brand { margin-bottom: 2.5rem; }
                .qs-login-light { left: -38vw; width: 100vw; }
            }
            @media (prefers-reduced-motion: reduce) {
                .qs-login-light { animation: none; }
                [data-testid="stForm"] button[kind="primary"] { transition: none; }
            }
        </style>
        <div class="qs-login-light" aria-hidden="true"></div>
        <div class="qs-login-brand">
            <div class="qs-login-mark" aria-hidden="true">Q</div>
            <div>
                <div class="qs-login-brand-name">Q-SHIELD</div>
                <div class="qs-login-brand-subtitle">PQC SECURITY OPERATIONS</div>
            </div>
        </div>
        <div class="qs-login-heading">
            <div class="qs-login-eyebrow">Access portal // local session</div>
            <h1>Secure access</h1>
            <p>Sign in to continue to your quantum-readiness workspace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("qshield_login_form", clear_on_submit=True):
        username = st.text_input(
            "Username", key=LOGIN_USERNAME_KEY, autocomplete="off", placeholder="Enter your username"
        )
        password = st.text_input(
            "Password", type="password", key=LOGIN_PASSWORD_KEY, autocomplete="new-password", placeholder="Enter your password"
        )
        submitted = st.form_submit_button("Sign in to Q-Shield", type="primary", use_container_width=True)

    if submitted:
        if login_user(username, password, st.session_state):
            st.rerun()
        st.error("Invalid username or password.")

    st.markdown(
        '<div class="qs-login-footer">LOCAL DEMONSTRATION ACCESS · AUTHORIZED USERS ONLY</div>',
        unsafe_allow_html=True,
    )
    st.stop()
