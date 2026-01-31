import streamlit as st
from database import authenticate_user as db_authenticate
from database import create_user as db_create



def authenticate_user(username, password):
    """
    Called by app.py to verify login credentials.
    Returns the User object if successful, None otherwise.
    """
    return db_authenticate(username, password)

def create_user(username, email, password, role="user"):
    """
    Called by app.py to register a new user.
    Returns True if successful, False if username exists.
    """
    return db_create(username, email, password, role)


def logout_user():
    """Clears session state for logout."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]