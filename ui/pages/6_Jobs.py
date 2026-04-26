import streamlit as st
import os
from api_client import CentralMemoryAPI
from theme import apply_dark_theme, status_badge

API_URL = os.getenv("API_URL", "http://localhost:8000")
api = CentralMemoryAPI(API_URL)

st.set_page_config(page_title="Ingestion Jobs | CentralMemory", page_icon="⚙️", layout="wide")
apply_dark_theme()

st.title("⚙️ Ingestion Jobs")
st.caption("Monitor and manage background embedding/chunking jobs")

status_filter = st.sidebar.selectbox("Filter by Status", ["all", "pending", "running", "completed", "failed"], index=0)
limit = st.sidebar.slider("Limit", 10, 200, 50)

try:
    with st.spinner("Fetching jobs..."):
        jobs = api.get_ingestion_jobs(limit=limit, status=None if status_filter == "all" else status_filter)
except Exception as e:
    st.error(f"Failed to fetch jobs: {e}")
    jobs = []

if not jobs:
    st.info(f"No ingestion jobs found for filter: {status_filter}")
else:
    status_counts = {}
    for j in jobs:
        s = j.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⏳ Pending", status_counts.get("pending", 0))
    with col2:
        st.metric("🔄 Running", status_counts.get("running", 0))
    with col3:
        st.metric("✅ Completed", status_counts.get("completed", 0))
    with col4:
        st.metric("❌ Failed", status_counts.get("failed", 0))

    if status_counts.get("failed", 0) > 0:
        st.error(f"⚠️ {status_counts['failed']} failed job(s) need attention!")

    st.divider()

    for job in jobs:
        job_id_short = str(job.get("id", ""))[:8]
        status = job.get("status", "unknown")
        badge = status_badge(status)

        icon = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌"}.get(status, "•")
        header = f"{icon} {job.get('job_type', 'N/A')} — Memory `{job.get('memory_id', 'N/A')[:8]}...` [{status}]"

        with st.expander(header, expanded=(status == "failed")):
            st.markdown(f"""
            **Job ID:** `{job.get('id')}`  
            **Job Type:** {job.get('job_type', 'N/A')}  
            **Memory ID:** `{job.get('memory_id', 'N/A')}`  
            **Status:** {badge}  
            **Attempts:** {job.get('attempt_count', 0)}  
            **Created:** {job.get('created_at', 'N/A')}  
            **Started:** {job.get('started_at', 'N/A')}  
            **Completed:** {job.get('completed_at', 'N/A')}
            """, unsafe_allow_html=True)

            if status == "failed" and job.get("last_error"):
                st.error(f"**Error:** {job['last_error']}")

            if status in ("failed", "pending"):
                if st.button(f"🔄 Retry Job {job_id_short}", key=f"retry_{job.get('id')}"):
                    try:
                        api.retry_ingestion_job(job["id"])
                        st.success("Job queued for retry!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to retry: {e}")