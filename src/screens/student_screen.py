import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
import pandas as pd
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import get_all_students, create_student, get_student_subjects, get_student_attendance, unenroll_student_to_subject
from src.database.config import supabase
import time

from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card


def render_student_subjects(student_id, subjects, stats_map):
    st.header('Your Enrolled Subjects')

    if not subjects:
        st.info('You are not enrolled in any subjects yet. Use “Enroll in Subject” to join one.')
        return

    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']
        stats = stats_map.get(sid, {"total": 0, "attended": 0})
        enrollment_id = sub_node.get('id', i)

        def unenroll_button(subject_id=sid, subject_name=sub['name'], button_key=f"unenroll_{student_id}_{enrollment_id}"):
            if st.button(
                "Unenroll from this course",
                type='tertiary',
                width='stretch',
                icon=':material/delete_forever:',
                key=button_key,
            ):
                unenroll_student_to_subject(student_id, subject_id)
                st.toast(f"Unenrolled from {subject_name} successfully!")
                st.rerun()

        with cols[i % 2]:
            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub['section'],
                stats=[
                    ('📅', 'Classes', stats['total']),
                    ('✅', 'Attended', stats['attended']),
                ],
                footer_callback=unenroll_button,
            )


def render_student_attendance(subjects, logs):
    st.header('Attendance Records')

    total_classes = len(logs)
    attended_classes = sum(1 for log in logs if log.get('is_present'))
    attendance_rate = round((attended_classes / total_classes) * 100) if total_classes else 0

    metric_cols = st.columns(3)
    metric_cols[0].metric('Total Classes', total_classes)
    metric_cols[1].metric('Classes Attended', attended_classes)
    metric_cols[2].metric('Attendance Rate', f'{attendance_rate}%')

    if not subjects:
        st.info('Enroll in a subject to start building your attendance record.')
        return

    subject_options = {'All Subjects': None}
    for sub_node in subjects:
        subject = sub_node['subjects']
        label = f"{subject['name']} ({subject['subject_code']})"
        subject_options[label] = subject['subject_id']

    selected_label = st.selectbox(
        'Filter by subject',
        list(subject_options.keys()),
        key='student_attendance_subject_filter',
    )
    selected_subject_id = subject_options[selected_label]
    filtered_logs = [
        log for log in logs
        if selected_subject_id is None or log['subject_id'] == selected_subject_id
    ]

    if not filtered_logs:
        st.info('No attendance has been recorded for this selection yet.')
        return

    records = []
    for log in filtered_logs:
        subject = log.get('subjects') or {}
        timestamp = pd.to_datetime(log.get('timestamp'), errors='coerce')
        records.append({
            'Date': timestamp.strftime('%d %b %Y') if not pd.isna(timestamp) else '—',
            'Time': timestamp.strftime('%I:%M %p') if not pd.isna(timestamp) else '—',
            'Subject': subject.get('name', 'Unknown subject'),
            'Code': subject.get('subject_code', '—'),
            'Section': subject.get('section', '—'),
            'Status': 'Present' if log.get('is_present') else 'Absent',
            '_sort_time': timestamp,
        })

    records.sort(
        key=lambda record: record['_sort_time'] if not pd.isna(record['_sort_time']) else pd.Timestamp.min,
        reverse=True,
    )
    records_df = pd.DataFrame(records).drop(columns=['_sort_time'])
    st.dataframe(records_df, hide_index=True, width='stretch')

def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {student_data['name']} """)
        if st.button("Logout", type='secondary', key='loginbackbtn'):
            st.session_state['is_logged_in'] = False
            del st.session_state.student_data 
            st.rerun()


    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs:
        sid = log['subject_id']

        if sid not in stats_map:
            stats_map[sid] = {"total":0, "attended": 0}

        stats_map[sid]['total'] +=1

        if log.get('is_present'):
            stats_map[sid]['attended'] += 1


    if 'current_student_tab' not in st.session_state:
        st.session_state.current_student_tab = 'subjects'

    st.markdown("<br>", unsafe_allow_html=True)
    nav_subjects, nav_records, nav_enroll = st.columns(3)
    with nav_subjects:
        subjects_type = 'primary' if st.session_state.current_student_tab == 'subjects' else 'tertiary'
        if st.button('My Subjects', type=subjects_type, width='stretch', icon=':material/book_ribbon:', key='student_nav_subjects'):
            st.session_state.current_student_tab = 'subjects'
            st.rerun()
    with nav_records:
        records_type = 'primary' if st.session_state.current_student_tab == 'records' else 'tertiary'
        if st.button('Attendance Records', type=records_type, width='stretch', icon=':material/history:', key='student_nav_records'):
            st.session_state.current_student_tab = 'records'
            st.rerun()
    with nav_enroll:
        if st.button('Enroll in Subject', type='tertiary', width='stretch', icon=':material/add_circle:', key='student_nav_enroll'):
            enroll_dialog()

    st.divider()

    if st.session_state.current_student_tab == 'records':
        render_student_attendance(subjects, logs)
    else:
        render_student_subjects(student_id, subjects, stats_map)

    footer_dashboard()


def student_screen():
    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state:
        student_dashboard()
        return
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn'):
            st.session_state['login_type'] = None
            st.rerun()

    pending_join_code = st.session_state.get('pending_join_code')

    if pending_join_code:
        try:
            sub_res = supabase.table("subjects").select("name, section").eq("subject_code", pending_join_code).execute()
            if sub_res.data:
                sub_info = sub_res.data[0]
                st.info(f"🎓 **Course Invite**: You've been invited to join **{sub_info['name']}** (`{pending_join_code}` - Section {sub_info.get('section', 'A')})!\nPlease enter your student details below to register, or sign in if you already have a profile.")
            else:
                st.info(f"🎓 **Course Invite**: Code `{pending_join_code}`. Please enter your student details below to register, or sign in if you already have a profile.")
        except Exception:
            st.info(f"🎓 **Course Invite**: Code `{pending_join_code}`. Please enter your student details below.")

        tab_reg, tab_login = st.tabs(["📝 Register Student Details", "📷 Existing Student Login"])
    else:
        st.header('Student Portal')
        tab_login, tab_reg = st.tabs(["📷 Existing Student Login", "📝 Register New Profile"])

    with tab_reg:
        with st.container(border=True):
            st.subheader('Register Profile Details')
            new_name = st.text_input("Full Name *", placeholder='E.g. Akash Sharma', key='reg_name_input')

            st.markdown("##### 📸 Face Biometric (Required)")
            st.caption("AI uses your facial features for instant attendance logging.")
            photo_source_type = st.radio("Choose photo input:", ["📷 Take Photo with Camera", "📁 Upload Photo"], horizontal=True, key='photo_source_type')

            photo_source = None
            if photo_source_type == "📷 Take Photo with Camera":
                photo_source = st.camera_input("Position your face in the center", key='reg_camera_input')
            else:
                photo_source = st.file_uploader("Upload a clear photo containing your face", type=['jpg', 'jpeg', 'png'], key='reg_file_upload')

            st.markdown("##### 🎙️ Voice Enrollment (Optional)")
            st.caption("Enroll a voice sample for voice attendance support.")

            audio_data = None
            try:
                audio_data = st.audio_input('Record a short phrase (e.g., "I am present, my name is ...")', key='reg_audio_input')
            except Exception:
                pass

            st.markdown("<br>", unsafe_allow_html=True)
            reg_btn_label = "Register & Proceed to Course ➡️" if pending_join_code else "Create Profile"
            if st.button(reg_btn_label, type='primary', width='stretch', key='reg_submit_btn'):
                if not new_name.strip():
                    st.warning('Please enter your full name!')
                elif not photo_source:
                    st.warning('Please capture or upload a face photo!')
                else:
                    with st.spinner('Analyzing facial features & creating profile...'):
                        try:
                            img = np.array(Image.open(photo_source))
                            encodings = get_face_embeddings(img)
                            if encodings:
                                face_emb = encodings[0].tolist()

                                voice_emb = None
                                if audio_data:
                                    voice_emb = get_voice_embedding(audio_data.read())

                                response_data = create_student(new_name.strip(), face_embedding=face_emb, voice_embedding=voice_emb)

                                if response_data:
                                    train_classifier()
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_role = 'student'
                                    st.session_state.student_data = response_data[0]
                                    st.toast(f"Profile Created! Welcome {new_name.strip()}!")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Failed to save profile. Please try again.")
                            else:
                                st.error("Couldn't detect facial features. Please ensure your face is well-lit and clearly visible.")
                        except Exception as e:
                            st.error(f"Registration error: {str(e)}")

    with tab_login:
        subtab_face, subtab_manual = st.tabs(["📷 FaceID Login", "👤 Sign In by Name / Student ID"])

        with subtab_face:
            st.subheader('Login using FaceID')
            face_input_type = st.radio("Choose photo input:", ["📷 Take Photo with Camera", "📁 Upload Photo"], horizontal=True, key='student_login_photo_type')

            login_photo = None
            if face_input_type == "📷 Take Photo with Camera":
                login_photo = st.camera_input("Position your face in the center", key='login_cam_input')
            else:
                login_photo = st.file_uploader("Upload your face photo", type=['jpg', 'jpeg', 'png'], key='login_upload_input')

            if login_photo:
                img = np.array(Image.open(login_photo))

                with st.spinner('AI is scanning...'):
                    try:
                        detected, all_ids, num_faces = predict_attendance(img)

                        if num_faces == 0:
                            st.warning('Face not found! Please check lighting and face the camera directly.')
                        elif num_faces > 1:
                            st.warning('Multiple faces detected! Please ensure only you are visible.')
                        else:
                            if detected:
                                student_id = list(detected.keys())[0]
                                all_students = get_all_students()
                                student = next((s for s in all_students if s['student_id'] == student_id), None)

                                if student:
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_role = 'student'
                                    st.session_state.student_data = student
                                    st.toast(f"Welcome Back {student['name']}")
                                    time.sleep(0.5)
                                    st.rerun()
                            else:
                                st.warning('Face not recognized! Try with better lighting, or switch to the **Sign In by Name / Student ID** tab above.')
                    except Exception as e:
                        st.error(f"FaceID error: {str(e)}")

        with subtab_manual:
            st.subheader('Sign In with Registered Profile')
            st.caption("Select your profile to authenticate directly.")
            try:
                registered_students = get_all_students()
            except Exception:
                registered_students = []

            if registered_students:
                student_options = {f"{s['name']} (ID: {s['student_id']})": s for s in registered_students}
                chosen_student_label = st.selectbox("Select Your Profile", options=list(student_options.keys()), key="student_manual_select")

                manual_btn_label = "Sign In & Join Course ➡️" if pending_join_code else "Sign In"
                if st.button(manual_btn_label, type="primary", width="stretch", key="student_manual_login_btn"):
                    selected_student = student_options[chosen_student_label]
                    st.session_state.is_logged_in = True
                    st.session_state.user_role = 'student'
                    st.session_state.student_data = selected_student
                    st.toast(f"Welcome Back {selected_student['name']}!")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.info("No registered students found yet. Please register your profile first under 'Register Profile Details'.")

    footer_dashboard()
