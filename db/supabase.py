import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_settings(user_id, settings):
    existing = supabase.table("settings").select("*").eq("user_id", user_id).execute()
    if existing.data:
        supabase.table("settings").update(settings).eq("user_id", user_id).execute()
    else:
        supabase.table("settings").insert(settings).execute()

def get_settings(user_id):
    result = supabase.table("settings").select("*").eq("user_id", user_id).execute()
    return result.data[0] if result.data else {}
