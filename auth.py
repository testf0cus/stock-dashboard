import streamlit as st

def check_password():
    """Returns `True` if the user had a correct password."""

    # Check if secrets are configured
    if "passwords" not in st.secrets:
        st.error("❌ **Configuration Error**: Secrets not found.")
        st.info("To fix this in Streamlit Cloud:\n1. Click 'Manage App' (bottom right).\n2. Click 'Settings' (three dots) > 'Secrets'.\n3. Paste the content of your local `.streamlit/secrets.toml` file.")
        st.stop()  # Stop execution to prevent KeyError

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["passwords"]["admin"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True
