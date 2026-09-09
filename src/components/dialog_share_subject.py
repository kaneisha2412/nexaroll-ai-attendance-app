import streamlit as st
import segno
import io
import socket


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


@st.dialog("Share Class Details")
def share_subject_dialog(subject_name, subject_code):
    lan_ip = get_network_ip()
    network_url = f"http://{lan_ip}:8501/?join-code={subject_code}"
    local_url = f"http://localhost:8501/?join-code={subject_code}"
    public_url = get_public_url()

    st.markdown(f"Share **{subject_name}** (`{subject_code}`) with your students:")

    if public_url:
        public_join_url = f"{public_url.rstrip('/')}/?join-code={subject_code}"
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
                st.image(out.getvalue(), caption=f"Scan to join {subject_code}", width=210)
                st.caption("✨ Works from any phone (Wi-Fi or Mobile Data) and enables camera access.")
            with col2:
                st.subheader("🏷️ Subject Code")
                st.markdown(f"### `{subject_code}`")
                st.caption("Students can enter this code manually under 'Enroll in Subject'.")
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
                st.image(out.getvalue(), caption=f"Scan to join {subject_code}", width=210)
                st.caption("✨ Phone must be connected to the exact same Wi-Fi.")
            with col2:
                st.subheader("🏷️ Subject Code")
                st.markdown(f"### `{subject_code}`")
                st.caption("Students can enter this code manually under 'Enroll in Subject'.")
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
            st.image(out.getvalue(), caption=f"Scan to join {subject_code}", width=210)
            st.caption("✨ Phone must be connected to the same Wi-Fi network.")

        with col2:
            st.subheader("🏷️ Subject Code")
            st.markdown(f"### `{subject_code}`")
            st.caption("Students can enter this code manually under 'Enroll in Subject'.")
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 🌐 Network Link (Same Wi-Fi)")
            st.code(network_url, language="text")

        st.divider()
        st.subheader("💻 Localhost Link (Testing on this Mac)")
        st.code(local_url, language="text")

    st.divider()

    if st.button("Done", type="primary", width="stretch", key=f"done_share_{subject_code}"):
        st.rerun()
