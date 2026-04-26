import streamlit as st
import os
from api_client import CentralMemoryAPI
from theme import apply_dark_theme, status_badge, TYPE_ICONS

API_URL = os.getenv("API_URL", "http://localhost:8000")
api = CentralMemoryAPI(API_URL)

st.set_page_config(page_title="Review Queue | CentralMemory", page_icon="⚖️", layout="wide")
apply_dark_theme()

st.title("⚖️ Review Queue")
st.caption("Resolve duplicates, conflicts, and promote scratch memories")

page = st.sidebar.radio("Section", ["Scratch Memories", "Review Items"])
status_filter = st.sidebar.selectbox("Status", ["pending", "resolved"], index=0)

if page == "Review Items":
    try:
        with st.spinner("Fetching review items..."):
            items = api.get_review_items(status=status_filter)
    except Exception as e:
        st.error(f"Failed to fetch review items: {e}")
        items = []

    if not items:
        if status_filter == "pending":
            st.success("✅ No pending review items — all clear!")
        else:
            st.info(f"No {status_filter} review items.")
    else:
        st.info(f"Found {len(items)} {status_filter} review item{'s' if len(items) != 1 else ''}")

        for item in items:
            mem_id_short = str(item['memory_id'])[:8]
            candidate_short = str(item.get('candidate_memory_id', ''))[:8] if item.get('candidate_memory_id') else 'N/A'

            with st.expander(f"{item['review_type'].upper()} — Memory {mem_id_short}... (Candidate: {candidate_short})", expanded=(status_filter == "pending")):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Review Type:** `{item['review_type']}`  
                    **Target Memory:** `{item['memory_id']}`  
                    **Candidate Memory:** `{item.get('candidate_memory_id') or 'N/A'}`  
                    **Reason:** {item.get('reason') or 'N/A'}  
                    **Created:** {item['created_at']}
                    """)

                    # Side-by-side diff for duplicate/conflict reviews
                    if item.get('candidate_memory_id'):
                        try:
                            target_mem = api.get_memory(item['memory_id'])
                            candidate_mem = api.get_memory(item['candidate_memory_id'])

                            st.divider()
                            st.subheader("Side-by-Side Comparison")

                            diff_col1, diff_col2 = st.columns(2)
                            with diff_col1:
                                t_icon = TYPE_ICONS.get(target_mem.get('type', ''), '📄')
                                st.markdown(f"### {t_icon} Target Memory")
                                st.markdown(f"**Title:** {target_mem.get('title') or 'N/A'}")
                                st.markdown(f"**Status:** {status_badge(target_mem.get('status', ''))}")
                                st.markdown(f"**Type:** {target_mem.get('type', 'N/A')} | **Scope:** {target_mem.get('scope', 'N/A')}")
                                if target_mem.get('summary'):
                                    st.markdown(f"**Summary:** {target_mem['summary']}")
                                st.text_area("Content", value=target_mem.get('content', ''), height=150, disabled=True, key=f"target_{item['id']}")

                            with diff_col2:
                                c_icon = TYPE_ICONS.get(candidate_mem.get('type', ''), '📄')
                                st.markdown(f"### {c_icon} Candidate Memory")
                                st.markdown(f"**Title:** {candidate_mem.get('title') or 'N/A'}")
                                st.markdown(f"**Status:** {status_badge(candidate_mem.get('status', ''))}")
                                st.markdown(f"**Type:** {candidate_mem.get('type', 'N/A')} | **Scope:** {candidate_mem.get('scope', 'N/A')}")
                                if candidate_mem.get('summary'):
                                    st.markdown(f"**Summary:** {candidate_mem['summary']}")
                                st.text_area("Content", value=candidate_mem.get('content', ''), height=150, disabled=True, key=f"candidate_{item['id']}")

                        except Exception as e:
                            st.warning(f"Could not load memories for comparison: {e}")

                with col2:
                    if status_filter == "pending":
                        with st.form(key=f"resolve_form_{item['id']}"):
                            action = st.selectbox(
                                "Resolution Action",
                                options=["merge", "supersede", "archive_candidate", "keep_both", "promote_canonical"]
                            )
                            notes = st.text_input("Notes (Optional)")
                            submit = st.form_submit_button("✅ Resolve Item")

                            if submit:
                                try:
                                    api.resolve_review_item(item['id'], action, notes)
                                    st.success("Item resolved!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to resolve: {e}")
                    else:
                        st.success(f"Resolved At: {item.get('resolved_at', 'N/A')}")

elif page == "Scratch Memories":
    try:
        with st.spinner("Fetching scratch memories..."):
            scratch_memories = api.get_memories(limit=200, include_scratch=True)
            scratch_memories = [m for m in scratch_memories if m['status'] == 'scratch']
    except Exception as e:
        st.error(f"Failed to fetch scratch memories: {e}")
        scratch_memories = []

    if not scratch_memories:
        st.success("✅ No scratch memories pending review — all clean!")
    else:
        st.warning(f"⚠️ {len(scratch_memories)} scratch memories waiting for review")

        # Batch actions
        st.subheader("⚡ Batch Promote")
        bc1, bc2, bc3 = st.columns(3)
        batch_confirm = st.checkbox("⚠️ I confirm — apply batch action to ALL scratch memories", key="batch_confirm")
        with bc1:
            if st.button(f"✅ Promote ALL to Reviewed", type="primary", use_container_width=True, disabled=not batch_confirm):
                progress = st.progress(0, text="Promoting memories...")
                count = 0
                for i, mem in enumerate(scratch_memories):
                    try:
                        api.update_memory(mem['id'], {"status": "reviewed"})
                        count += 1
                    except Exception:
                        pass
                    progress.progress((i + 1) / len(scratch_memories), text=f"Promoted {i+1}/{len(scratch_memories)}")
                st.success(f"Promoted {count}/{len(scratch_memories)} memories to reviewed!")
                st.rerun()
        with bc2:
            if st.button(f"👑 Promote ALL to Canonical", use_container_width=True, disabled=not batch_confirm):
                progress = st.progress(0, text="Promoting memories...")
                count = 0
                for i, mem in enumerate(scratch_memories):
                    try:
                        api.update_memory(mem['id'], {"status": "canonical"})
                        count += 1
                    except Exception:
                        pass
                    progress.progress((i + 1) / len(scratch_memories), text=f"Promoted {i+1}/{len(scratch_memories)}")
                st.success(f"Promoted {count}/{len(scratch_memories)} memories to canonical!")
                st.rerun()
        with bc3:
            if st.button(f"📦 Archive ALL", disabled=not batch_confirm):
                progress = st.progress(0, text="Archiving memories...")
                count = 0
                for i, mem in enumerate(scratch_memories):
                    try:
                        api.archive_memory(mem['id'])
                        count += 1
                    except Exception:
                        pass
                    progress.progress((i + 1) / len(scratch_memories), text=f"Archived {i+1}/{len(scratch_memories)}")
                st.success(f"Archived {count}/{len(scratch_memories)} memories!")
                st.rerun()

        st.divider()

        for mem in scratch_memories:
            t_icon = TYPE_ICONS.get(mem.get('type', ''), '📄')
            with st.expander(f"{t_icon} ⚠️ {mem.get('title') or mem['id'][:8]} [{mem.get('type')} | {mem.get('scope')}]"):
                st.markdown(f"{status_badge(mem['status'])} **Type:** {mem.get('type')} | **Scope:** {mem.get('scope')}", unsafe_allow_html=True)
                st.write(mem['content'])

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"✅ Reviewed", key=f"review_{mem['id']}"):
                        try:
                            api.update_memory(mem['id'], {"status": "reviewed"})
                            st.success("Promoted to reviewed!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")
                with col2:
                    if st.button(f"👑 Canonical", key=f"canon_{mem['id']}"):
                        try:
                            api.update_memory(mem['id'], {"status": "canonical"})
                            st.success("Promoted to canonical!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")
                with col3:
                    if st.button(f"📦 Archive", key=f"archive_{mem['id']}"):
                        try:
                            api.archive_memory(mem['id'])
                            st.success("Archived!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")