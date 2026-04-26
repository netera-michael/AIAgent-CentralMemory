import streamlit as st
import os
from api_client import CentralMemoryAPI
from theme import apply_dark_theme

API_URL = os.getenv("API_URL", "http://localhost:8000")
api = CentralMemoryAPI(API_URL)

st.set_page_config(page_title="API Keys | CentralMemory", page_icon="🔑", layout="wide")
apply_dark_theme()

st.title("🔑 API Keys")
st.caption("Manage API keys for client access and scope permissions")

# --- Create API Key ---
st.subheader("➕ Create New Key")
with st.form("create_key_form"):
    kc1, kc2 = st.columns(2)
    with kc1:
        key_name = st.text_input("Key Name *", placeholder="e.g., opencode-client, n8n-worker")
    with kc2:
        key_scopes = st.multiselect(
            "Allowed Scopes",
            ["personal", "personal_finance", "biz_finance", "biz_projects", "coding_projects", "infrastructure", "social_media_clients", "admin"],
            default=["coding_projects"]
        )

    kc3, kc4 = st.columns(2)
    with kc3:
        can_read = st.checkbox("Can Read", value=True)
    with kc4:
        can_write = st.checkbox("Can Write", value=True)

    submit_key = st.form_submit_button("🔑 Create Key", type="primary")
    if submit_key:
        if not key_name.strip():
            st.error("Key name is required!")
        elif not key_scopes:
            st.error("Select at least one scope!")
        else:
            try:
                result = api.create_api_key({
                    "name": key_name.strip(),
                    "allowed_scopes": key_scopes,
                    "can_read": can_read,
                    "can_write": can_write
                })
                plain_key = result.get("plain_key", "")
                st.success(f"Key `{key_name.strip()}` created!")
                st.warning("⚠️ Copy the key below now — it will not be shown again!")
                st.code(plain_key, language=None)
            except Exception as e:
                st.error(f"Failed to create key: {e}")

st.divider()

# --- Existing Keys ---
st.subheader("📋 Existing Keys")
try:
    keys = api.get_api_keys()
except Exception as e:
    st.error(f"Failed to fetch keys: {e}")
    keys = []

if not keys:
    st.info("No API keys created yet.")
else:
    for key in keys:
        key_id_short = str(key.get("id", ""))[:8]
        active = key.get("active", True)
        status_icon = "✅" if active else "🚫"

        scopes_str = ", ".join(key.get("allowed_scopes", []))
        perms = []
        if key.get("can_read"):
            perms.append("R")
        if key.get("can_write"):
            perms.append("W")
        perms_str = "/".join(perms) if perms else "None"

        with st.expander(f"{status_icon} **{key.get('name', 'N/A')}** — {perms_str} — {scopes_str}"):
            st.markdown(f"""
            **ID:** `{key.get('id')}`  
            **Scopes:** {scopes_str}  
            **Permissions:** {perms_str}  
            **Last Used:** {key.get('last_used_at', 'Never')}  
            **Created:** {key.get('created_at', 'N/A')}
            """)

            if active:
                if st.button(f"🚫 Revoke Key {key.get('name', key_id_short)}", key=f"revoke_{key.get('id')}"):
                    try:
                        api.revoke_api_key(key["id"])
                        st.success("Key revoked!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to revoke: {e}")
            else:
                st.warning("This key has been revoked and is inactive.")