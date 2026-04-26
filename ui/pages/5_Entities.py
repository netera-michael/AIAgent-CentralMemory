import streamlit as st
import os
import pandas as pd
from api_client import CentralMemoryAPI
from theme import apply_dark_theme

API_URL = os.getenv("API_URL", "http://localhost:8000")
api = CentralMemoryAPI(API_URL)

st.set_page_config(page_title="Entities | CentralMemory", page_icon="🏛️", layout="wide")
apply_dark_theme()

st.title("🏛️ Entities")
st.caption("Manage entities that memories can be attached to (people, projects, servers, etc.)")

# Fetch entities
try:
    with st.spinner("Fetching entities..."):
        entities = api.get_entities(limit=200)
except Exception as e:
    st.error(f"Failed to fetch entities: {e}")
    entities = []

# --- Create Entity ---
st.subheader("➕ Create Entity")
with st.form("create_entity_form"):
    ec1, ec2 = st.columns(2)
    with ec1:
        entity_name = st.text_input("Name *", placeholder="e.g., Contabo VPS, Echo Dubai, Michael")
    with ec2:
        entity_type = st.selectbox("Type *", ["person", "project", "server", "device", "service", "company", "auto"], index=6)

    entity_desc = st.text_area("Description", placeholder="Optional description of this entity", height=80)

    submit_entity = st.form_submit_button("🏛️ Create Entity", type="primary")
    if submit_entity:
        if not entity_name.strip():
            st.error("Entity name is required!")
        else:
            try:
                result = api.create_entity({
                    "name": entity_name.strip(),
                    "type": entity_type,
                    "description": entity_desc.strip() if entity_desc.strip() else None
                })
                st.success(f"Entity '{entity_name.strip()}' created! ID: `{result.get('id', 'unknown')}`")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create entity: {e}")

st.divider()

# --- Entity List ---
st.subheader(f"📋 Existing Entities ({len(entities)})")

if not entities:
    st.info("No entities created yet.")
else:
    type_counts = {}
    for e in entities:
        t = e.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    # Summary row
    summary_cols = st.columns(min(len(type_counts), 6))
    for i, (t, count) in enumerate(sorted(type_counts.items())):
        if i < len(summary_cols):
            with summary_cols[i]:
                st.metric(t, count)

    st.divider()

    # Display as expandable list
    for ent in entities:
        ent_id_short = str(ent.get('id', ''))[:8]
        with st.expander(f"**{ent.get('name', 'N/A')}** ({ent.get('type', 'N/A')})"):
            st.markdown(f"""
            **ID:** `{ent.get('id')}`  
            **Normalized Name:** {ent.get('normalized_name', 'N/A')}  
            **Description:** {ent.get('description') or 'No description'}  
            **Created:** {ent.get('created_at', 'N/A')}  
            **Updated:** {ent.get('updated_at', 'N/A')}
            """)