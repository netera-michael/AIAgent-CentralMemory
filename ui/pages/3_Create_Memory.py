import streamlit as st
import os
from api_client import CentralMemoryAPI
from theme import apply_dark_theme

API_URL = os.getenv("API_URL", "http://localhost:8000")
api = CentralMemoryAPI(API_URL)

st.set_page_config(page_title="Create Memory | CentralMemory", page_icon="📝", layout="wide")
apply_dark_theme()

st.title("📝 Create Memory")
st.caption("Add a new memory to the store. New memories start as 'scratch' status by default.")

SCOPES = [
    "personal",
    "personal_finance",
    "biz_finance",
    "biz_projects",
    "coding_projects",
    "infrastructure",
    "social_media_clients",
]

TYPES = [
    "fact",
    "preference",
    "decision",
    "workflow",
    "project_note",
]

SENSITIVITY_LEVELS = ["internal", "confidential", "restricted"]

with st.form("create_memory_form"):
    st.subheader("Memory Content")
    content = st.text_area("Content *", placeholder="Enter the memory content...", height=200, help="The main factual content to store")
    title = st.text_input("Title", placeholder="Short descriptive title (optional)")
    summary = st.text_area("Summary", placeholder="Brief summary of the content (optional)", height=80)

    st.divider()
    st.subheader("Classification")
    col1, col2, col3 = st.columns(3)

    with col1:
        mem_type = st.selectbox("Type *", TYPES, index=0, help="What kind of memory is this?")
    with col2:
        scope = st.selectbox("Scope *", SCOPES, index=4, help="Which domain does this memory belong to?")
    with col3:
        sensitivity = st.selectbox("Sensitivity", SENSITIVITY_LEVELS, index=0, help="Access sensitivity level")

    st.divider()
    st.subheader("Optional Metadata")

    col4, col5 = st.columns(2)
    with col4:
        observed_at = st.date_input("Observed At", value=None, help="When was this fact observed?")
    with col5:
        entity_name = st.text_input("Entity Name", placeholder="e.g., Contabo VPS, iPhone 16 (optional)")

    col_entity_type, col_conf = st.columns(2)
    with col_entity_type:
        entity_type = st.selectbox("Entity Type", ["person", "project", "server", "device", "service", "company"], index=0, help="Type for auto-created entity")
    with col_conf:
        confidence = st.slider("Confidence", 0.0, 1.0, value=1.0, step=0.1, help="How confident are you about this memory?")

    submitted = st.form_submit_button("💾 Create Memory", type="primary")

if submitted:
    if not content.strip():
        st.error("Content is required!")
    else:
        payload = {
            "content": content.strip(),
            "type": mem_type,
            "scope": scope,
            "sensitivity": sensitivity,
            "confidence": round(confidence, 2),
        }
        if title.strip():
            payload["title"] = title.strip()
        if summary.strip():
            payload["summary"] = summary.strip()
        if observed_at:
            payload["observed_at"] = str(observed_at) + "T00:00:00Z"

        # Create entity if specified
        if entity_name.strip():
            try:
                entity = api.create_entity({
                    "name": entity_name.strip(),
                    "type": entity_type,
                    "description": f"Auto-created entity for memory: {title.strip() or content.strip()[:50]}"
                })
                payload["entity_id"] = str(entity["id"])
            except Exception as e:
                st.warning(f"Could not create/link entity: {e}")

        try:
            result = api.create_memory(payload)
            mem_id = result.get('id', 'unknown')
            status = result.get('status', 'scratch')
            st.success(f"Memory created! ID: `{mem_id}` — Status: **{status}**")
            st.json(result)
            st.info("Memory starts as 'scratch'. Use the Memories page or Review Queue to promote it.")
        except Exception as e:
            st.error(f"Failed to create memory: {e}")