import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase
import time


@st.dialog("Join Course Invitation")
def auto_enroll_dialog(subject_code):
    if "student_data" not in st.session_state or not st.session_state.student_data:
        return

    student_id = st.session_state.student_data.get("student_id") or st.session_state.student_data.get("id")

    code_clean = str(subject_code).strip()
    try:
        res = supabase.table("subjects").select("*").ilike("subject_code", code_clean).execute()
        if not res.data:
            res = supabase.table("subjects").select("*").eq("subject_code", code_clean).execute()
    except Exception:
        res = supabase.table("subjects").select("*").eq("subject_code", code_clean).execute()

    if not res.data:
        st.error(f"Subject with code '{subject_code}' not found!")
        if st.button("Close", type="secondary", width="stretch"):
            st.query_params.clear()
            st.session_state.pop("pending_join_code", None)
            st.rerun()
        return

    subject = res.data[0]
    subject_db_id = subject.get("subject_id") or subject.get("id")

    # Check if student is already enrolled
    check = supabase.table("subject_students").select("*").eq("subject_id", subject_db_id).eq("student_id", student_id).execute()
    if check.data:
        st.info(f"You are already enrolled in **{subject.get('name')}** ({subject_code})!")
        if st.button("Go to My Subjects", type="primary", width="stretch"):
            st.query_params.clear()
            st.session_state.pop("pending_join_code", None)
            st.rerun()
        return

    st.markdown(
        f"### 🎓 Join this course?\n"
        f"You opened the invite link for:\n\n"
        f"- **Subject**: **{subject.get('name')}**\n"
        f"- **Code**: `{subject_code}`\n"
        f"- **Section**: {subject.get('section', 'A')}\n\n"
        f"Would you like to enroll right now?"
    )

    st.divider()

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        if st.button("No", type="secondary", width="stretch"):
            st.query_params.clear()
            st.session_state.pop("pending_join_code", None)
            st.rerun()

    with col2:
        if st.button("Yes", type="primary", width="stretch"):
            try:
                enroll_student_to_subject(student_id, subject_db_id)
                st.success(f"🎉 Successfully joined **{subject.get('name')}**!")
                st.query_params.clear()
                st.session_state.pop("pending_join_code", None)
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to join: {str(e)}")
