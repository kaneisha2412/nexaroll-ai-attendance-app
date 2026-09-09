import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen
from src.components.dialog_auto_enroll import auto_enroll_dialog

def main():
    st.set_page_config(
        page_title='NexaRoll AI - Smart Attendance',
        page_icon="https://i.ibb.co/YTYGn5qV/logo.png"
    )
    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None

    # Track join-code query param from shareable links
    join_code = st.query_params.get('join-code')
    if join_code:
        st.session_state['pending_join_code'] = join_code
        if st.session_state.login_type != 'student':
            st.session_state.login_type = 'student'
            st.rerun()

    # Route based on login_type (compatible with Python 3.9+)
    login_type = st.session_state['login_type']
    if login_type == 'teacher':
        teacher_screen()
    elif login_type == 'student':
        student_screen()
    else:
        home_screen()

    # Trigger Yes/No auto-enroll dialog instantly when student is authenticated
    active_join_code = st.session_state.get('pending_join_code')
    if active_join_code and st.session_state.get('is_logged_in') and st.session_state.get('user_role') == 'student':
        auto_enroll_dialog(active_join_code)

if __name__ == '__main__':
    main()
