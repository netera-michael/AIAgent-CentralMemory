import streamlit as st
import os
from datetime import datetime
from api_client import CentralMemoryAPI
from theme import apply_dark_theme

API_URL = os.getenv("API_URL", "http://localhost:8000")
api = CentralMemoryAPI(API_URL)

st.set_page_config(page_title="CentralMemory Dashboard", page_icon="🧠", layout="wide")
apply_dark_theme()

st.title("🧠 CentralMemory")
st.caption("Centralized memory platform for AI agents")

# Auto-refresh
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
if auto_refresh:
    st.empty()

api_connected = False
health = {}
try:
    health = api.get_health()
    api_connected = health.get("status") == "ok"
except Exception:
    pass

if api_connected:
    st.success("🟢 API Connected — Database healthy")
else:
    st.error(f"🔴 API Error — Cannot connect to {API_URL}")
    st.stop()

st.divider()

# Fetch data
with st.spinner("Loading stats..."):
    try:
        all_memories = api.get_memories(limit=500, include_scratch=True)
    except Exception as e:
        st.error(f"Failed to fetch memories: {e}")
        all_memories = []

    try:
        stats = api.get_stats()
    except Exception:
        stats = None

    try:
        review_items = api.get_review_items(status="pending")
    except Exception:
        review_items = []

    try:
        entities = api.get_entities(limit=200)
    except Exception:
        entities = []

    try:
        jobs = api.get_ingestion_jobs(limit=50)
    except Exception:
        jobs = []

# --- Status Breakdown ---
if stats:
    total = stats.get("total", len(all_memories))
    by_status = stats.get("by_status", {})
    by_scope = stats.get("by_scope", {})
    by_type = stats.get("by_type", {})
    total_entities = stats.get("total_entities", len(entities))
    pending_reviews = stats.get("pending_reviews", len(review_items))
    pending_jobs = stats.get("pending_jobs", 0)
else:
    total = len(all_memories)
    by_status = {}
    by_scope = {}
    by_type = {}
    for m in all_memories:
        by_status[m.get("status", "unknown")] = by_status.get(m.get("status", "unknown"), 0) + 1
        by_scope[m.get("scope", "unknown")] = by_scope.get(m.get("scope", "unknown"), 0) + 1
        by_type[m.get("type", "unknown")] = by_type.get(m.get("type", "unknown"), 0) + 1
    total_entities = len(entities)
    pending_reviews = len(review_items)
    pending_jobs = 0

canonical = by_status.get("canonical", 0)
reviewed = by_status.get("reviewed", 0)
scratch = by_status.get("scratch", 0)
failed_jobs = by_status.get("failed", 0)
failed_job_count = sum(1 for j in jobs if j.get("status") == "failed")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Memories", total)
with col2:
    st.metric("👑 Canonical", canonical)
with col3:
    st.metric("✅ Reviewed", reviewed)
with col4:
    st.metric("⚠️ Scratch", scratch)
    if scratch > 0:
        if st.button("Review Scratch →", key="go_scratch", use_container_width=True):
            st.switch_page("pages/2_Review_Queue.py")
with col5:
    st.metric("⚖️ Pending Reviews", pending_reviews)
    if pending_reviews > 0:
        if st.button("Resolve Items →", key="go_reviews", use_container_width=True):
            st.switch_page("pages/2_Review_Queue.py")

st.divider()

# --- Timeline Chart ---
st.subheader("📈 Memory Timeline")
if all_memories:
    from collections import Counter
    date_counts = Counter()
    scope_date_counts = {}
    for m in all_memories:
        created = m.get("created_at", "")
        if created:
            day = str(created)[:10]
            date_counts[day] += 1
            scope = m.get("scope", "unknown")
            if scope not in scope_date_counts:
                scope_date_counts[scope] = Counter()
            scope_date_counts[scope][day] += 1

    if date_counts:
        sorted_dates = sorted(date_counts.keys())
        chart_data = {"date": sorted_dates, "total": [date_counts.get(d, 0) for d in sorted_dates]}
        for scope in sorted(scope_date_counts.keys()):
            chart_data[scope] = [scope_date_counts[scope].get(d, 0) for d in sorted_dates]

        st.bar_chart(chart_data, x="date", height=300)
    else:
        st.info("No dated memories for timeline.")
else:
    st.info("No memories to plot.")

st.divider()

# --- Scope & Type Distribution ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📋 By Scope")
    if by_scope:
        for scope, count in sorted(by_scope.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total else 0
            st.markdown(f"**{scope}** — {count} ({pct:.0f}%)")
            st.progress(min(pct / 100, 1.0))
    else:
        st.info("No memories yet")

with col_right:
    st.subheader("🗂️ By Type")
    if by_type:
        for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total else 0
            st.markdown(f"**{t}** — {count} ({pct:.0f}%)")
            st.progress(min(pct / 100, 1.0))
    else:
        st.info("No memories yet")

st.divider()

# --- Ingestion Jobs Status ---
st.subheader("⚙️ Ingestion Jobs")
job_col1, job_col2, job_col3 = st.columns(3)
job_status_counts = {}
for j in jobs:
    s = j.get("status", "unknown")
    job_status_counts[s] = job_status_counts.get(s, 0) + 1

with job_col1:
    st.metric("⏳ Pending", job_status_counts.get("pending", 0))
with job_col2:
    st.metric("✅ Completed", job_status_counts.get("completed", 0))
with job_col3:
    st.metric("❌ Failed", job_status_counts.get("failed", 0))

if failed_job_count > 0:
    if st.button(f"⚠️ {failed_job_count} failed job(s) — View Jobs", use_container_width=True):
        st.switch_page("pages/6_Jobs.py")

st.divider()

# --- Quick Actions ---
st.subheader("⚡ Quick Actions")
qa_col1, qa_col2, qa_col3, qa_col4, qa_col5, qa_col6 = st.columns(6)

with qa_col1:
    if st.button("📝 Create", use_container_width=True):
        st.switch_page("pages/3_Create_Memory.py")
with qa_col2:
    if st.button("🔍 Search", use_container_width=True):
        st.switch_page("pages/4_Search.py")
with qa_col3:
    if st.button("🏛️ Entities", use_container_width=True):
        st.switch_page("pages/5_Entities.py")
with qa_col4:
    if st.button("⚙️ Jobs", use_container_width=True):
        st.switch_page("pages/6_Jobs.py")
with qa_col5:
    if st.button("🔑 API Keys", use_container_width=True):
        st.switch_page("pages/7_API_Keys.py")
with qa_col6:
    if st.button("📜 Audit Log", use_container_width=True):
        st.switch_page("pages/8_Audit_Log.py")

st.divider()

if entities:
    with st.expander(f"🏛️ Entities ({len(entities)})", expanded=False):
        for ent in entities[:20]:
            st.markdown(f"- **{ent.get('name', 'N/A')}** ({ent.get('type', 'N/A')}) — {ent.get('description', 'No description')}")

st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')} — Total: {total} memories, {total_entities} entities")

# Auto-refresh handling
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()