try:
    import streamlit as st
except ImportError:
    st = None
import re

try:
    from src.ui.base_layout import style_background_dashboard, style_base_layout
    from src.components.header import header_dashboard
    from src.components.footer import footer_dashboard
    from src.components.subject_card import subject_card
    from src.components.dialog_create_subject import create_subject_dialog
    from src.components.dialog_share_subject import share_subject_dialog
    from src.components.dialog_add_photo import add_photos_dialog
    from src.components.dialog_attendance_results import attendance_result_dialog
    from src.components.dialog_voice_attendance import voice_attendance_dialog
except ImportError:
    pass

from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects, get_attendance_for_teacher
from src.pipelines.face_pipeline import predict_attendance
import numpy as np
from datetime import datetime
from PIL import Image

try:
    import pandas as pd
except ImportError:
    pd = None

from src.database.config import supabase
def teacher_screen():

    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type=="login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()





def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {teacher_data['name']} """)
        if st.button("Logout", type='secondary', key='loginbackbtn'):
            st.session_state['is_logged_in'] = False
            del st.session_state.teacher_data 
            st.rerun()


    st.markdown("<br>", unsafe_allow_html=True)

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'
    tab1, tab2, tab3 = st.columns(3)


    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('Take Attendance',type=type1, width='stretch', icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Manage Subjects', type=type2, width='stretch', icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button('Attendance Records',type=type3, width='stretch', icon=':material/history:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()


    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    


    footer_dashboard()

def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take AI Attendance')

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []
    if 'show_add_photo_dialog' not in st.session_state:
        st.session_state.show_add_photo_dialog = False
    if 'face_uploader_key' not in st.session_state:
        st.session_state.face_uploader_key = 0

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning("You haven't created any subjects yet! Please create one under 'Manage Subjects' to begin.")
        return

    subject_options = {f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects}

    col1, col2 = st.columns([3, 1], vertical_alignment='bottom')
    with col1:
        selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()), key="attendance_subject_picker")
    with col2:
        if st.button('Add More Photos', type='secondary', icon=':material/photo_prints:', width='stretch', key='open_add_photos_btn'):
            st.session_state.show_add_photo_dialog = True

    if st.session_state.get('show_add_photo_dialog', False):
        add_photos_dialog()

    selected_subject_id = subject_options[selected_subject_label]

    st.divider()

    # Dedicated prominent tabs for AI Facial Recognition and Voice Attendance
    tab_face_att, tab_voice_att = st.tabs([
        "📸 AI Facial Recognition Attendance",
        "🎙️ Sequential Voice Attendance"
    ])

    with tab_face_att:
        st.subheader("AI Facial Recognition Attendance")
        st.caption("Capture or upload classroom photos to automatically scan and mark student attendance using deep neural networks.")

        input_mode = st.radio(
            "Classroom Photo Input Mode:",
            ["📷 Live Camera Snapshot", "📁 Upload Classroom Photos"],
            horizontal=True,
            key="face_input_mode_selector"
        )

        face_uploader_ver = st.session_state.face_uploader_key

        if input_mode == "📷 Live Camera Snapshot":
            cam_photo = st.camera_input("Point camera at classroom or student", key=f"direct_cam_attendance_{face_uploader_ver}")
            if cam_photo:
                token = getattr(cam_photo, "file_id", f"{cam_photo.name}:{cam_photo.size}")
                processed = st.session_state.setdefault("processed_direct_cam", [])
                if token not in processed:
                    cam_photo.seek(0)
                    img = Image.open(cam_photo).convert("RGB")
                    st.session_state.attendance_images.append(img)
                    processed.append(token)
                    st.toast("Classroom photo captured!", icon="📸")
        else:
            uploaded_photos = st.file_uploader(
                "Upload classroom photos",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                help="JPG, JPEG, PNG format supported",
                key=f"direct_file_upload_attendance_{face_uploader_ver}"
            )
            if uploaded_photos:
                processed = st.session_state.setdefault("processed_direct_uploads", [])
                added_count = 0
                for f in uploaded_photos:
                    tok = getattr(f, "file_id", f"{f.name}:{f.size}")
                    if tok not in processed:
                        try:
                            f.seek(0)
                            st.session_state.attendance_images.append(Image.open(f).convert("RGB"))
                            processed.append(tok)
                            added_count += 1
                        except Exception as e:
                            st.error(f"Error loading {f.name}: {e}")
                if added_count > 0:
                    st.toast(f"{added_count} new photo(s) added for face analysis!", icon="📁")

        # Display added photos
        if st.session_state.attendance_images:
            count = len(st.session_state.attendance_images)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"##### Added Photos ({count})")
            gallery_cols = st.columns(min(count, 4))
            for idx, img in enumerate(st.session_state.attendance_images):
                with gallery_cols[idx % 4]:
                    st.image(img, use_container_width=True, caption=f"Photo {idx+1}")
        else:
            st.info("💡 No classroom photos captured yet. Take a snapshot with your camera or upload classroom images above.")

        st.markdown("<br>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            if st.button("Clear All Photos", width="stretch", type="secondary", icon=":material/delete:", disabled=not st.session_state.attendance_images, key="clear_face_photos_btn"):
                st.session_state.attendance_images = []
                st.session_state.processed_attendance_captures = []
                st.session_state.processed_attendance_uploads = []
                st.session_state.processed_direct_cam = []
                st.session_state.processed_direct_uploads = []
                st.session_state.pending_attendance = None
                st.session_state.face_uploader_key += 1
                if 'dialog_photo_uploader_key' in st.session_state:
                    st.session_state.dialog_photo_uploader_key += 1
                st.toast("All classroom photos cleared!", icon="🗑️")
                st.rerun()

        with col_c2:
            if st.button("🚀 Run AI Face Analysis", width="stretch", type="primary", icon=":material/analytics:", disabled=not st.session_state.attendance_images, key="run_ai_face_analysis_btn"):
                with st.spinner("AI is scanning classroom photos & matching face embeddings..."):
                    all_detected_ids = {}
                    total_faces_found = 0

                    for idx, img in enumerate(st.session_state.attendance_images):
                        img_np = np.array(img.convert('RGB'))
                        detected, _, num_faces = predict_attendance(img_np)
                        total_faces_found += num_faces

                        if detected:
                            for sid in detected.keys():
                                student_id = int(sid)
                                all_detected_ids.setdefault(student_id, []).append(f"Photo {idx+1}")

                    enrolled_res = supabase.table('subject_students').select("*, students(*)").eq('subject_id', selected_subject_id).execute()
                    enrolled_students = enrolled_res.data or []

                    if not enrolled_students:
                        st.warning(f"No students are enrolled in '{selected_subject_label}' yet! Have students join via the QR code or link in 'Manage Subjects'.")
                    else:
                        results, attendance_to_log = [], []
                        current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                        for node in enrolled_students:
                            student = node.get('students') or {}
                            sid = student.get('student_id')
                            sources = all_detected_ids.get(int(sid), []) if sid else []
                            is_present = len(sources) > 0

                            results.append({
                                "Name": student.get('name', 'Unknown'),
                                "ID": sid or "-",
                                "Source": ", ".join(sources) if is_present else "-",
                                "Status": "✅ Present" if is_present else "❌ Absent"
                            })

                            if sid:
                                attendance_to_log.append({
                                    'student_id': sid,
                                    'subject_id': selected_subject_id,
                                    'timestamp': current_timestamp,
                                    'is_present': bool(is_present)
                                })

                        st.session_state.pending_attendance = (pd.DataFrame(results), attendance_to_log, total_faces_found)

        # Show Attendance Results directly on the screen
        if st.session_state.get('pending_attendance'):
            df_results, logs, faces_found = st.session_state.pending_attendance
            st.divider()
            st.subheader("📋 Attendance Report")
            present_count = sum(1 for log in logs if log.get('is_present'))
            total_enrolled = len(logs)
            st.caption(f"Scanned {faces_found} face(s) across photos. **{present_count} / {total_enrolled} enrolled students marked present.** Review results below before saving.")
            st.dataframe(df_results, hide_index=True, use_container_width=True)

            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button('Discard Attendance', width='stretch', key='discard_face_att'):
                    st.session_state.pending_attendance = None
                    st.rerun()
            with rc2:
                if st.button('Confirm & Save Attendance', width='stretch', type='primary', key='confirm_face_att'):
                    try:
                        from src.database.db import create_attendance
                        create_attendance(logs)
                        st.toast("Attendance successfully saved to Supabase!", icon="✅")
                        st.session_state.pending_attendance = None
                        st.session_state.attendance_images = []
                        st.session_state.processed_attendance_captures = []
                        st.session_state.processed_attendance_uploads = []
                        st.session_state.processed_direct_cam = []
                        st.session_state.processed_direct_uploads = []
                        st.session_state.face_uploader_key = st.session_state.get('face_uploader_key', 0) + 1
                        if 'dialog_photo_uploader_key' in st.session_state:
                            st.session_state.dialog_photo_uploader_key += 1
                        import time
                        time.sleep(0.8)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Save failed: {e}")

    with tab_voice_att:
        st.subheader("Sequential Voice Attendance")
        st.caption("Students sequentially record 'Present' and AI verifies them against stored voice embeddings.")
        if st.button('Open Voice Attendance Recorder', type='primary', width='stretch', icon=':material/mic:', key='voice_att_btn'):
            voice_attendance_dialog(selected_subject_id)












def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns(2)
    with col1:
        st.header('Manage Subjects', width='stretch')

    with col2:
        if st.button('Create New Subject', width='stretch'):
            create_subject_dialog(teacher_id)


    # LIST all SUBJECTS
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        cols = st.columns(2)
        for idx, sub in enumerate(subjects):
            stats = [
                ("🫂", "Students", sub['total_students']),
                ("🕰️", "Classes", sub['total_classes']),
            ]
            s_name = sub['name']
            s_code = sub['subject_code']
            s_id = sub['subject_id']

            def make_share_callback(name=s_name, code=s_code, sub_id=s_id):
                def share_btn():
                    if st.button(f"Share Code: {name}", key=f"share_{code}_{sub_id}", icon=":material/share:", width='stretch'):
                        share_subject_dialog(name, code)
                    st.markdown("<br>", unsafe_allow_html=True)
                return share_btn

            with cols[idx % 2]:
                subject_card(
                    name=s_name,
                    code=s_code,
                    section=sub['section'],
                    stats=stats,
                    footer_callback=make_share_callback()
                )
    else:
        st.info("NO SUBJECTS FOUND. CREATE ONE ABOVE")


def teacher_tab_attendance_records():
    st.header('Attendance Records')

    teacher_id = st.session_state.teacher_data['teacher_id']

    records = get_attendance_for_teacher(teacher_id)

    if not records:
        return
    
    data = []

    for r in records:
        ts = r.get('timestamp')

        data.append({
            "ts_group": ts.split(".")[0] if ts else None,
            "Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N'A",
            "Subject": r['subjects']['name'],
            "Subject Code":r['subjects']['subject_code'],
            "is_present": bool(r.get('is_present', False))
        })


    df = pd.DataFrame(data)



    summary = (
        df.groupby(['ts_group', 'Time', 'Subject', 'Subject Code'])
        .agg(
            Present_Count = ('is_present', 'sum'),
            Total_Count =('is_present', 'count')
        ).reset_index()

    )

    summary['Attendance Stats'] = (
        "✅ " + summary['Present_Count'].astype(str) + " /"
        + summary['Total_Count'].astype(str) + ' Students'
    )

    display_df = ( summary.sort_values(by='ts_group' ,ascending=False)
                  [['Time', 'Subject', 'Subject Code', 'Attendance Stats']]
                  )
    
    st.dataframe(display_df, width='stretch', hide_index=True)


def login_teacher(username, password):
    username = (username or "").strip()
    password = password or ""
    if not username or not password:
        return False, "Please enter both username and password."

    if not check_teacher_exists(username):
        return False, f"Username '{username}' not found. Please check spelling or register."

    teacher = teacher_login(username, password)

    if teacher:
        st.session_state.user_role = 'teacher'
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True, f"Welcome back, {teacher.get('name', username)}!"

    return False, "Incorrect password. Please verify your password and caps lock."


def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn'):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Login using password')
    st.markdown("<br><br>", unsafe_allow_html=True)

    with st.form("teacher_login_form", border=False):
        teacher_username = st.text_input("Enter username", placeholder='Rachel', key='login_uname')
        teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password", key='login_pwd')
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button('Login', icon=':material/passkey:', width='stretch', type='primary')

    if submitted:
        success, msg = login_teacher(teacher_username, teacher_pass)
        if success:
            st.toast(msg, icon="👋")
            st.rerun()
        else:
            st.error(msg)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button('Register Instead', icon=':material/passkey:', width='stretch', key='to_register_btn'):
        st.session_state.teacher_login_type = 'register'
        st.rerun()

    # Self-service Password Reset Expander
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔑 Forgot or want to reset password?"):
        st.caption("Reset your password by entering your registered username.")
        fp_user = st.text_input("Your Username", placeholder="e.g. Rachel", key="fp_uname")
        fp_pass = st.text_input("New Password", type="password", placeholder="Enter new password", key="fp_pwd")
        fp_pass_confirm = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password", key="fp_pwd_conf")

        if st.button("Update Password", type="secondary", key="fp_btn"):
            if not fp_user.strip() or not fp_pass:
                st.warning("Please provide username and new password.")
            elif fp_pass != fp_pass_confirm:
                st.warning("Passwords do not match!")
            elif not check_teacher_exists(fp_user.strip()):
                st.error(f"Username '{fp_user.strip()}' does not exist.")
            else:
                is_valid, v_msg = validate_password_strength(fp_pass)
                if not is_valid:
                    st.warning(v_msg)
                else:
                    from src.database.db import update_teacher_password
                    update_teacher_password(fp_user.strip(), fp_pass)
                    st.success(f"Password updated successfully for '{fp_user.strip()}'! You can now log in above.")

    footer_dashboard()


def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_+=]", password):
        return False, "Password must contain at least one special character (!@#$%^&*)."
    return True, "Valid"


def validate_username(username):
    username = username.strip()
    if len(username) < 3 or len(username) > 30:
        return False, "Username must be between 3 and 30 characters long."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, "Valid"


def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    teacher_username = teacher_username.strip() if teacher_username else ""
    teacher_name = teacher_name.strip() if teacher_name else ""

    if not teacher_username or not teacher_name or not teacher_pass or not teacher_pass_confirm:
        return False, "All fields are required!"

    # Username format validation
    is_valid_user, user_msg = validate_username(teacher_username)
    if not is_valid_user:
        return False, user_msg

    # Username uniqueness check
    try:
        if check_teacher_exists(teacher_username):
            return False, f"Username '{teacher_username}' is already taken! Please choose another."
    except Exception as e:
        return False, f"Database check failed: {str(e)}"

    # Password match check
    if teacher_pass != teacher_pass_confirm:
        return False, "Passwords do not match! Please re-type your password."

    # Password requirement criteria validation
    is_valid_pass, pass_msg = validate_password_strength(teacher_pass)
    if not is_valid_pass:
        return False, pass_msg

    try:
        created = create_teacher(teacher_username, teacher_pass, teacher_name)
        teacher_rec = created[0] if (created and isinstance(created, list)) else {"username": teacher_username, "name": teacher_name}
        return True, teacher_rec
    except Exception as e:
        return False, f"Registration failed: {str(e)}"


def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn'):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Register your teacher profile')

    st.markdown("<br><br>", unsafe_allow_html=True)

    teacher_username = st.text_input("Enter username", placeholder='ananyaroy', key='reg_uname')
    teacher_name = st.text_input("Enter name", placeholder='Ananya Roy', key='reg_name')

    teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password", key='reg_pwd')
    teacher_pass_confirm = st.text_input("Confirm your password", type='password', placeholder="Re-enter password", key='reg_pwd_conf')

    st.info(
        "🔒 **Password Requirements:**\n"
        "- At least **8 characters** long\n"
        "- At least **1 letter** (a-z, A-Z)\n"
        "- At least **1 number** (0-9)\n"
        "- At least **1 special character** (e.g. ! @ # $ % ^ & *)"
    )

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button('Register now', icon=':material/passkey:', width='stretch', key='reg_submit_btn'):
            success, result = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)
            if success:
                # Auto-login upon registration for seamless experience
                st.session_state.user_role = 'teacher'
                st.session_state.teacher_data = result
                st.session_state.is_logged_in = True
                st.toast(f"Profile Created! Welcome {teacher_name.strip()}!", icon="🎉")
                st.rerun()
            else:
                st.error(result)

    with btnc2:
        if st.button('Login Instead', type="primary", icon=':material/passkey:', width='stretch', key='to_login_btn'):
            st.session_state.teacher_login_type = 'login'
            st.rerun()

    footer_dashboard()

