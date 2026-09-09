import streamlit as st
from PIL import Image


@st.dialog("Capture or upload photos")
def add_photos_dialog():
    st.markdown("Add classroom photos to scan for attendance.")

    if 'photo_mode_choice' not in st.session_state:
        st.session_state.photo_mode_choice = "📁 Upload"

    photo_mode = st.radio(
        "Select Input Mode",
        options=["📷 Camera", "📁 Upload"],
        index=1 if st.session_state.photo_mode_choice == "📁 Upload" else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="add_photo_mode_radio"
    )
    st.session_state.photo_mode_choice = photo_mode

    st.markdown("<br>", unsafe_allow_html=True)

    if 'dialog_photo_uploader_key' not in st.session_state:
        st.session_state.dialog_photo_uploader_key = 0

    dialog_ver = st.session_state.dialog_photo_uploader_key

    if photo_mode == "📷 Camera":
        st.caption("Use your device camera to capture a classroom photo:")
        cam_photo = st.camera_input("Take a photo", key=f"dialog_camera_widget_{dialog_ver}")
        if cam_photo:
            try:
                cam_photo.seek(0)
                img = Image.open(cam_photo).convert("RGB")
                token = getattr(cam_photo, "file_id", f"{cam_photo.name}:{cam_photo.size}")
                processed = st.session_state.setdefault("processed_attendance_captures", [])
                if token not in processed:
                    st.session_state.attendance_images.append(img)
                    processed.append(token)
                    st.toast("Photo captured successfully!")
            except Exception as e:
                st.error(f"Error reading camera photo: {e}")

    else:
        st.caption("Choose image files (Drag and drop JPG or PNG images below):")
        uploaded_files = st.file_uploader(
            "Choose image files",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Limit 200MB per file • JPG, JPEG, PNG",
            key=f"dialog_uploader_widget_{dialog_ver}"
        )

        if uploaded_files:
            processed = st.session_state.setdefault("processed_attendance_uploads", [])
            added_any = False
            for f in uploaded_files:
                token = getattr(f, "file_id", f"{f.name}:{f.size}")
                if token not in processed:
                    try:
                        f.seek(0)
                        st.session_state.attendance_images.append(Image.open(f).convert("RGB"))
                        processed.append(token)
                        added_any = True
                    except Exception as e:
                        st.error(f"Failed to load {f.name}: {e}")
            if added_any:
                st.toast(f"{len(st.session_state.attendance_images)} photo(s) loaded!")

    # Live preview of loaded photos
    if st.session_state.get("attendance_images"):
        count = len(st.session_state.attendance_images)
        st.markdown("<br>", unsafe_allow_html=True)
        st.success(f"📸 **{count} photo{'s' if count != 1 else ''}** ready for face analysis.")
        preview_cols = st.columns(min(count, 4))
        for i, p_img in enumerate(st.session_state.attendance_images[-4:]):
            with preview_cols[i % 4]:
                st.image(p_img, use_container_width=True, caption=f"Photo {i+1}")

        if st.button("🗑️ Clear Photos", key="dialog_clear_btn", use_container_width=True):
            st.session_state.attendance_images = []
            st.session_state["processed_attendance_captures"] = []
            st.session_state["processed_attendance_uploads"] = []
            st.session_state["processed_direct_cam"] = []
            st.session_state["processed_direct_uploads"] = []
            st.session_state.dialog_photo_uploader_key += 1
            if 'face_uploader_key' in st.session_state:
                st.session_state.face_uploader_key += 1
            st.toast("Classroom photos cleared!", icon="🗑️")
            st.rerun()

    st.divider()
    if st.button("Done", type="primary", use_container_width=True, key="done_photo_dialog"):
        st.session_state.show_add_photo_dialog = False
        st.rerun()


