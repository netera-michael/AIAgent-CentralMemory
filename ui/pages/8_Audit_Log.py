import streamlit as st
import os
import pandas as pd
from api_client import CentralMemoryAPI
from theme import apply_dark_theme

API_URL = os.getenv("API_URL", "http://localhost:8000")
api = CentralMemoryAPI(API_URL)

st.set_page_config(page_title="Audit Log | CentralMemory", page_icon="📜", layout="wide")
apply_dark_theme()

st.title("📜 Audit Log")
st.caption("View system-level audit trail of API actions")

limit = st.sidebar.slider("Entries", 20, 500, 100)

try:
    with st.spinner("Fetching audit logs..."):
        logs = api.get_audit_logs(limit=limit)
except Exception as e:
    st.error(f"Failed to fetch audit logs: {e}")
    logs = []

if not logs:
    st.info("No audit logs found.")
else:
    st.metric("Total Entries Loaded", len(logs))

    df = pd.DataFrame(logs)

    display_cols = [c for c in ['created_at', 'action', 'route', 'scope', 'api_key_id'] if c in df.columns]

    if 'created_at' in df.columns:
        df['created_at'] = df['created_at'].apply(lambda x: str(x)[:19] if x else x)

    if 'api_key_id' in df.columns:
        df['api_key_id'] = df['api_key_id'].apply(lambda x: str(x)[:8] + "..." if x else "—")

    if 'route' in df.columns:
        df['route'] = df['route'].apply(lambda x: str(x)[:60] if x else "—")

    st.dataframe(
        df[display_cols],
        column_config={
            "created_at": st.column_config.TextColumn("Time", width="medium"),
            "action": st.column_config.TextColumn("Action", width="small"),
            "route": st.column_config.TextColumn("Route", width="medium"),
            "scope": st.column_config.TextColumn("Scope", width="small"),
            "api_key_id": st.column_config.TextColumn("API Key", width="small"),
        },
        hide_index=True,
        height=600
    )

    # Export
    st.divider()
    st.subheader("📥 Export")
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button(
            "Export as JSON",
            data=df.to_json(orient="records", indent=2),
            file_name="audit_log.json",
            mime="application/json",
            use_container_width=True
        )
    with ec2:
        st.download_button(
            "Export as CSV",
            data=df.to_csv(index=False),
            file_name="audit_log.csv",
            mime="text/csv",
            use_container_width=True
        )