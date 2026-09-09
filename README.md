# NexaRoll AI — Smart Biometric Attendance System

NexaRoll AI is an enterprise-grade AI-powered classroom attendance platform featuring multi-modal biometric identification (Facial Recognition and Voice ID). Designed for modern educators and students, it eliminates roll-call overhead and manual sign-in sheets with real-time neural verification.
 
- **Product Showcase & Landing Page**: [https://nexaroll-ai-attendance-landing.vercel.app](https://nexaroll-ai-attendance-landing.vercel.app)
- **Latest Deployment Snapshot**: [https://nexaroll-ai-attendance-landing-lydg6dlhw-kans1.vercel.app](https://nexaroll-ai-attendance-landing-lydg6dlhw-kans1.vercel.app)

---

## Key Features

- **📸 Multi-Face Classroom Scanning**: High-speed deep neural face detection and 128-dimensional embedding matching from single or multi-angle classroom photos.
- **🎙️ Sequential Voice ID**: Voice verification pipeline matching 256-dimensional acoustic embeddings against enrolled voice signatures.
- **📱 Instant Mobile QR & Link Enrollment**: One-scan subject enrollment with automatic URL routing, query parameter detection, and confirmation modal.
- **⚡ Dual-Mode Connectivity**: Built-in support for both local Wi-Fi networks and secure online Cloudflare Edge tunnels for remote/mobile data access.
- **📊 Real-Time Teacher Analytics**: Subject creation, student roster management, CSV export, confidence metrics, and editable attendance records.
- **🎓 Student Self-Service Portal**: Biometric profile setup, multi-subject enrollment, and personal attendance tracking dashboard.

---

## Tech Stack

- **Frontend & Interface**: Streamlit with custom CSS design system
- **Computer Vision**: Deep learning facial recognition, 128-D Euclidean distance & cosine similarity
- **Acoustic Verification**: 256-D voice embedding extraction & verification
- **Database & Storage**: Supabase (PostgreSQL) with SQLite local fallback support
- **Networking**: Cloudflare Quick Tunnels, QR generation (Segno), socket-level network discovery

---

## Getting Started

### Prerequisites
- Python 3.9+
- Virtual environment (`venv`)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/kaneisha2412/nexaroll-ai-attendance-app.git
   cd nexaroll-ai-attendance-app
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env` and provide your Supabase credentials:
   ```bash
   cp .env.example .env
   ```

5. Launch the application:
   ```bash
   streamlit run app.py
   ```
