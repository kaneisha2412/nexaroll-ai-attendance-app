import streamlit as st
import io
import segno
import socket
from src.database.db import create_subject


def get_network_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "localhost"


import os

def get_public_url():
    env_url = os.environ.get("PUBLIC_URL", "").strip()
    if env_url.startswith("http"):
        return env_url
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        candidate = os.path.join(cur_dir, ".tunnel_url")
        if os.path.exists(candidate):
            try:
                with open(candidate, "r") as f:
                    url = f.read().strip()
                    if url.startswith("http"):
                        return url
            except Exception:
                pass
        cur_dir = os.path.dirname(cur_dir)
    return None


@st.dialog("Create New Subject")
def create_subject_dialog(teacher_id):
    # If the subject was just created in this dialog session, show the 3 sharing options
    if "just_created_subject" in st.session_state and st.session_state.just_created_subject:
        subj = st.session_state.just_created_subject
        sub_code = subj["code"]
        sub_name = subj["name"]
        sub_section = subj["section"]

        lan_ip = get_network_ip()
        network_url = f"http://{lan_ip}:8501/?join-code={sub_code}"
        local_url = f"http://localhost:8501/?join-code={sub_code}"
        public_url = get_public_url()

        st.success(f"🎉 Subject **{sub_name}** ({sub_code} - Sec {sub_section}) created successfully!")
        st.markdown("Share this course with your students using any of the options below:")

        if public_url:
            public_join_url = f"{public_url.rstrip('/')}/?join-code={sub_code}"
            tab_online, tab_wifi, tab_local = st.tabs([
                "🌐 Online Mobile QR (Works Anywhere)",
                "📶 Same Wi-Fi Network",
                "💻 Localhost"
            ])

            with tab_online:
                col1, col2 = st.columns(2, gap="medium")
                with col1:
                    st.subheader("📱 Scan with Phone")
                    qr = segno.make(public_join_url)
                    out = io.BytesIO()
                    qr.save(out, kind="png", scale=8, border=2)
                    st.image(out.getvalue(), caption=f"Scan to join {sub_code}", width=210)
                    st.caption("✨ Works from any phone (Wi-Fi or Mobile Data) and enables camera access.")
                with col2:
                    st.subheader("🏷️ Subject Code")
                    st.markdown(f"### `{sub_code}`")
                    st.caption("Students can enter this code manually in their Student Portal.")
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("##### 🌐 Online HTTPS Link")
                    st.code(public_join_url, language="text")

            with tab_wifi:
                col1, col2 = st.columns(2, gap="medium")
                with col1:
                    st.subheader("📱 Wi-Fi QR Code")
                    qr = segno.make(network_url)
                    out = io.BytesIO()
                    qr.save(out, kind="png", scale=8, border=2)
                    st.image(out.getvalue(), caption=f"Scan to join {sub_code}", width=210)
                    st.caption("✨ Phone and Mac must be connected to the exact same Wi-Fi.")
                with col2:
                    st.subheader("🏷️ Subject Code")
                    st.markdown(f"### `{sub_code}`")
                    st.caption("Students can enter this code manually in their Student Portal.")
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("##### 📶 Local Network Link")
                    st.code(network_url, language="text")

            with tab_local:
                st.subheader("💻 Localhost Link (Testing on this Mac)")
                st.code(local_url, language="text")

        else:
            st.divider()
            col1, col2 = st.columns(2, gap="medium")
            with col1:
                st.subheader("📱 Mobile QR Code")
                qr = segno.make(network_url)
                out = io.BytesIO()
                qr.save(out, kind="png", scale=8, border=2)
                st.image(out.getvalue(), caption=f"Scan to join {sub_code}", width=210)
                st.caption("✨ Phone must be connected to the same Wi-Fi network.")

            with col2:
                st.subheader("🏷️ Subject Code")
                st.markdown(f"### `{sub_code}`")
                st.caption("Students can enter this code manually in their Student Portal.")
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### 🌐 Network Link (Same Wi-Fi)")
                st.code(network_url, language="text")

            st.divider()
            st.subheader("💻 Localhost Link (Testing on this Mac)")
            st.code(local_url, language="text")

        st.divider()

        if st.button("Done & View Subjects", type="primary", width="stretch"):
            del st.session_state.just_created_subject
            st.rerun()

        return

    # Default Form State
    st.write("Enter the details of the new subject:")
    sub_id = st.text_input("Subject Code", placeholder="e.g. CS111").strip().upper()
    sub_name = st.text_input("Subject Name", placeholder="e.g. Intro to Machine Learning").strip()
    sub_section = st.text_input("Section", placeholder="e.g. A").strip()

    if st.button("Create Subject Now", type="primary", width="stretch"):
        if sub_id and sub_name and sub_section:
            try:
                create_subject(sub_id, sub_name, sub_section, teacher_id)
                st.session_state.just_created_subject = {
                    "code": sub_id,
                    "name": sub_name,
                    "section": sub_section,
                }
                st.rerun()
            except Exception as e:
                st.error(f"Error creating subject: {str(e)}")
        else:
            st.warning("Please fill in all the fields (Code, Name, Section).")
