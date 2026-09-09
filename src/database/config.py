import os

supabase_url = None
supabase_key = None

# 1. Check Streamlit secrets
try:
    import streamlit as st
    if hasattr(st, "secrets") and "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
except Exception:
    pass

# 2. Check environment variables
if not supabase_url or not supabase_key:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

# 3. Connect to Supabase Cloud or Local Adapter
is_placeholder = (
    not supabase_key 
    or supabase_key.startswith("PASTE_") 
    or "your-" in supabase_key.lower() 
    or "placeholder" in supabase_key.lower()
)

if supabase_url and supabase_key and not is_placeholder:
    try:
        from supabase import create_client, Client
        test_client = create_client(supabase_url, supabase_key)
        # Verify tables exist on Supabase Cloud
        test_client.table("teachers").select("*").limit(1).execute()
        supabase: Client = test_client
    except Exception as e:
        from src.database.local_db import get_local_client
        supabase = get_local_client()
else:
    from src.database.local_db import get_local_client
    supabase = get_local_client()