import streamlit as st
import os
import json
import pandas as pd
from api_client import CentralMemoryAPI
from theme import apply_dark_theme, status_badge, type_icon

API_URL = os.getenv("API_URL", "http://localhost:8000")
api = CentralMemoryAPI(API_URL)

st.set_page_config(page_title="Memories | CentralMemory", page_icon="🧠", layout="wide")
apply_dark_theme()

st.title("🧠 Memories")
st.caption("Browse, inspect, and manage the memory store")

# --- Sidebar Filters ---
st.sidebar.header("Filters")
include_scratch = st.sidebar.checkbox("Include Scratch", value=True)
status_filter = st.sidebar.multiselect(
    "Status Filter",
    ["scratch", "reviewed", "canonical", "stale", "conflicted", "archived"],
    default=["scratch", "reviewed", "canonical"]
)
scope_filter = st.sidebar.text_input("Scope (exact match)", placeholder="e.g., coding_projects")
type_filter = st.sidebar.text_input("Type (exact match)", placeholder="e.g., fact, preference")
text_search = st.sidebar.text_input("🔍 Text Search", placeholder="Search in content, title, summary...")
date_from = st.sidebar.date_input("Created After")
date_to = st.sidebar.date_input("Created Before")
page_size = st.sidebar.slider("Page Size", 10, 200, 50)

# Fetch Memories
try:
    with st.spinner("Fetching memories..."):
        memories = api.get_memories(limit=500, include_scratch=include_scratch)
except Exception as e:
    st.error(f"Failed to fetch memories: {e}")
    memories = []

# Apply client-side filters
if status_filter:
    memories = [m for m in memories if m.get("status") in status_filter]
if scope_filter:
    memories = [m for m in memories if m.get("scope") == scope_filter]
if type_filter:
    memories = [m for m in memories if m.get("type") == type_filter]
if text_search:
    q = text_search.lower()
    memories = [m for m in memories if q in (m.get("content", "") or "").lower() or q in (m.get("title", "") or "").lower() or q in (m.get("summary", "") or "").lower()]
if date_from:
    memories = [m for m in memories if m.get("created_at") and str(m.get("created_at", ""))[:10] >= str(date_from)]
if date_to:
    memories = [m for m in memories if m.get("created_at") and str(m.get("created_at", ""))[:10] <= str(date_to)]

# Pagination
total = len(memories)
page_num = st.sidebar.number_input("Page", min_value=1, value=1, step=1)
start = (page_num - 1) * page_size
end = start + page_size
page_memories = memories[start:end]
total_pages = max(1, (total + page_size - 1) // page_size)

st.sidebar.caption(f"Page {page_num}/{total_pages} — {total} total memories")

if not page_memories:
    st.info("No memories found matching filters.")
else:
    scratch_count = sum(1 for m in memories if m.get("status") == "scratch")
    if scratch_count > 0:
        if st.button(f"⚠️ {scratch_count} scratch memories need review → Go to Review Queue", use_container_width=True):
            st.switch_page("pages/2_Review_Queue.py")

    # Build display dataframe
    df = pd.DataFrame(page_memories)
    cols_order = ['id', 'status', 'type', 'scope', 'title', 'content', 'created_at']
    df = df[[c for c in cols_order if c in df.columns] + [c for c in df.columns if c not in cols_order]]

    # Shorten content for display
    if 'content' in df.columns:
        df['content'] = df['content'].apply(lambda x: (x[:300] + "...") if isinstance(x, str) and len(x) > 300 else x)

    # Truncate UUIDs for readability
    if 'id' in df.columns:
        df['id_short'] = df['id'].apply(lambda x: str(x)[:8] + "..." if isinstance(x, str) else str(x)[:8] + "...")

    # Add type icons
    if 'type' in df.columns:
        df['type'] = df['type'].apply(type_icon)

    display_cols = [c for c in ['id_short', 'status', 'type', 'scope', 'title', 'content', 'created_at'] if c in df.columns]
    st.dataframe(
        df[display_cols],
        column_config={
            "id_short": st.column_config.TextColumn("ID", width="small"),
            "status": st.column_config.TextColumn("Status"),
            "type": st.column_config.TextColumn("Type"),
            "scope": st.column_config.TextColumn("Scope"),
            "title": st.column_config.TextColumn("Title"),
            "content": st.column_config.TextColumn("Content", width="large"),
            "created_at": st.column_config.TextColumn("Created")
        },
        hide_index=True,
        height=400
    )

    # --- Export Buttons ---
    st.divider()
    st.subheader("📥 Export")
    ec1, ec2 = st.columns(2)
    all_df = pd.DataFrame(memories)
    with ec1:
        st.download_button(
            "Export as JSON",
            data=all_df.to_json(orient="records", indent=2),
            file_name="memories.json",
            mime="application/json",
            use_container_width=True
        )
    with ec2:
        st.download_button(
            "Export as CSV",
            data=all_df.to_csv(index=False),
            file_name="memories.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.divider()

    # --- Inspect & Edit Memory ---
    st.subheader("✏️ Inspect & Edit Memory")

    memory_options = {f"{m.get('title') or m['id'][:8]} [{m.get('status')}] ({m.get('type')} | {m.get('scope')})": m for m in page_memories}
    selected_label = st.selectbox("Select Memory:", options=[""] + list(memory_options.keys()))

    if selected_label:
        memory = memory_options[selected_label]
        mem_id = memory['id']

        # Status badge display
        st.markdown(f"**Status:** {status_badge(memory['status'])} | **Type:** {memory.get('type', 'N/A')} | **Scope:** {memory.get('scope', 'N/A')}", unsafe_allow_html=True)

        with st.form(key=f"edit_memory_{mem_id}"):
            new_title = st.text_input("Title", value=memory.get('title') or "")
            new_summary = st.text_area("Summary", value=memory.get('summary') or "", height=100)
            new_content = st.text_area("Content", value=memory.get('content', ''), height=200)
            new_status = st.selectbox(
                "Status",
                options=["scratch", "reviewed", "canonical", "stale", "conflicted", "archived"],
                index=["scratch", "reviewed", "canonical", "stale", "conflicted", "archived"].index(memory['status'])
            )

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                submit = st.form_submit_button("💾 Update Memory", type="primary")
            with col_b:
                archive = st.form_submit_button("📦 Archive")
            with col_c:
                purge = st.form_submit_button("🗑️ Purge (Hard Delete)", type="secondary")

            if submit:
                try:
                    update_payload = {}
                    if new_title != (memory.get('title') or ""):
                        update_payload["title"] = new_title
                    if new_summary != (memory.get('summary') or ""):
                        update_payload["summary"] = new_summary
                    if new_content != memory.get('content', ''):
                        update_payload["content"] = new_content
                    if new_status != memory['status']:
                        update_payload["status"] = new_status
                    if update_payload:
                        api.update_memory(mem_id, update_payload)
                        st.success(f"Memory {mem_id[:8]} updated!")
                        st.rerun()
                    else:
                        st.info("No changes detected.")
                except Exception as e:
                    st.error(f"Failed to update: {e}")

            if archive:
                try:
                    api.archive_memory(mem_id)
                    st.success(f"Memory {mem_id[:8]} archived!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to archive: {e}")

            if purge:
                st.warning(f"⚠️ This will permanently delete memory `{mem_id[:8]}`. This cannot be undone.")
                if st.checkbox(f"I understand — permanently delete memory {mem_id[:8]}", key=f"confirm_purge_{mem_id}"):
                    try:
                        api.purge_memory(mem_id)
                        st.success(f"Memory {mem_id[:8]} permanently deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to purge: {e}")