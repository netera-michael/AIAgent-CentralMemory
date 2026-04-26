import streamlit as st
import os
import plotly.graph_objects as go
from api_client import CentralMemoryAPI
from theme import apply_dark_theme, status_badge

API_URL = os.getenv("API_URL", "http://localhost:8000")
api = CentralMemoryAPI(API_URL)

st.set_page_config(page_title="Search & Graph | CentralMemory", page_icon="🔍", layout="wide")
apply_dark_theme()

tab_search, tab_graph = st.tabs(["🔍 Semantic Search", "🕸️ Memory Graph"])

SCOPES = [
    "personal",
    "personal_finance",
    "biz_finance",
    "biz_projects",
    "coding_projects",
    "infrastructure",
    "social_media_clients",
]

SCOPE_COLORS = {
    "personal": "#3fb950",
    "personal_finance": "#d29922",
    "biz_finance": "#f85149",
    "biz_projects": "#bc8cff",
    "coding_projects": "#58a6ff",
    "infrastructure": "#79c0ff",
    "social_media_clients": "#ff9bce",
}

# ========== SEMANTIC SEARCH TAB ==========
with tab_search:
    st.title("🔍 Semantic Search")
    st.caption("Search memories by meaning using vector embeddings")

    col_search, col_opts = st.columns([2, 1])

    with col_search:
        query = st.text_input("Search Query", placeholder="e.g., server IP address, deployment details, investment preferences...", key="search_query")

    with col_opts:
        include_scratch = st.checkbox("Include Scratch", value=False)
        limit = st.slider("Results Limit", 1, 50, value=10)
        threshold = st.slider("Similarity Threshold", 0.0, 2.0, value=2.0, step=0.05, help="Cosine distance (0=identical, 2=opposite). Lower = more precise, 2.0 = return all")

    with st.expander("⚙️ Advanced Filters", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            selected_scopes = st.multiselect("Scopes", SCOPES, default=[])
        with fc2:
            type_filter = st.selectbox("Type", ["", "fact", "preference", "decision", "workflow", "project_note"], index=0)
        with fc3:
            entity_id = st.text_input("Entity ID", placeholder="UUID (optional)")

    if st.button("🔍 Search", type="primary", use_container_width=True) or query:
        if not query:
            st.warning("Enter a search query first")
        else:
            with st.spinner("Searching..."):
                try:
                    results = api.semantic_search(
                        query=query,
                        scopes=selected_scopes if selected_scopes else None,
                        type=type_filter if type_filter else None,
                        entity_id=entity_id if entity_id else None,
                        include_scratch=include_scratch,
                        limit=limit,
                        threshold=threshold
                    )
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    results = []

            if not results:
                st.info("No results found. Try lowering the similarity threshold or adjusting filters.")
            else:
                st.success(f"Found {len(results)} result{'s' if len(results) != 1 else ''}")

                for i, mem in enumerate(results):
                    mem_id_short = str(mem.get('id', ''))[:8]
                    badge = status_badge(mem.get('status', 'unknown'))

                    with st.expander(
                        f"#{i+1} {mem.get('title') or mem_id_short} — {mem.get('type', '')} | {mem.get('scope', '')}",
                        expanded=(i < 3)
                    ):
                        st.markdown(f"{badge} | **Type:** {mem.get('type')} | **Scope:** {mem.get('scope')}", unsafe_allow_html=True)
                        if mem.get('summary'):
                            st.markdown(f"**Summary:** {mem['summary']}")
                        st.markdown(f"**Content:**")
                        st.code(mem.get('content', ''), language=None)
                        st.caption(f"ID: `{mem.get('id')}` | Created: {mem.get('created_at')} | Confidence: {mem.get('confidence', 'N/A')}")

# ========== MEMORY GRAPH TAB ==========
with tab_graph:
    st.title("🕸️ Memory Graph")
    st.caption("Visualize entity-memory relationships")

    with st.spinner("Loading graph data..."):
        try:
            all_mems = api.get_memories(limit=200, include_scratch=True)
        except Exception:
            all_mems = []
        try:
            all_entities = api.get_entities(limit=100)
        except Exception:
            all_entities = []

    if not all_mems:
        st.info("No memories to visualize.")
    else:
        entities_by_id = {str(e['id']): e for e in all_entities}
        entity_memories = {}
        for m in all_mems:
            eid = str(m.get('entity_id', '')) if m.get('entity_id') else None
            if eid:
                if eid not in entity_memories:
                    entity_memories[eid] = []
                entity_memories[eid].append(m)

        # Build nodes and edges
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        edge_x = []
        edge_y = []

        import math

        # Place entity nodes in a circle
        total_entity_nodes = len(entity_memories)
        for i, (eid, mems) in enumerate(entity_memories.items()):
            ent = entities_by_id.get(eid, {})
            angle = 2 * math.pi * i / max(total_entity_nodes, 1)
            cx, cy = math.cos(angle) * 3, math.sin(angle) * 3
            node_x.append(cx)
            node_y.append(cy)
            node_text.append(f"🏛️ {ent.get('name', eid[:8])}<br>{len(mems)} memories")
            node_color.append("#bc8cff")
            node_size.append(15 + len(mems) * 2)

            # Place memory nodes around the entity
            for j, mem in enumerate(mems):
                m_angle = angle + (2 * math.pi * (j + 1) / (len(mems) + 2))
                mx, my = cx + math.cos(m_angle) * 1.8, cy + math.sin(m_angle) * 1.8
                node_x.append(mx)
                node_y.append(my)
                scope = mem.get('scope', 'coding_projects')
                node_text.append(f"{mem.get('title', mem['id'][:8])}<br>{mem.get('type', '')} | {scope}")
                node_color.append(SCOPE_COLORS.get(scope, "#8b949e"))
                node_size.append(8)

                # Edge from entity to memory
                edge_x.extend([cx, mx, None])
                edge_y.extend([cy, my, None])

        # Add unlinked memories as scattered nodes
        linked_ids = set()
        for mems in entity_memories.values():
            for m in mems:
                linked_ids.add(m['id'])

        unlinked = [m for m in all_mems if m['id'] not in linked_ids]
        for i, m in enumerate(unlinked[:30]):
            angle = 2 * math.pi * i / max(len(unlinked), 1)
            x, y = math.cos(angle) * 6, math.sin(angle) * 6
            node_x.append(x)
            node_y.append(y)
            scope = m.get('scope', 'coding_projects')
            node_text.append(f"{m.get('title', m['id'][:8])}<br>{m.get('type', '')} | {scope} (unlinked)")
            node_color.append(SCOPE_COLORS.get(scope, "#8b949e"))
            node_size.append(6)

        # Build figure
        fig = go.Figure()

        # Edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=0.5, color='#30363d'),
            hoverinfo='none',
            showlegend=False
        ))

        # Nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=1, color='#0e1117')
            ),
            text=node_text,
            hoverinfo='text',
            textposition='top center',
            textfont=dict(size=8, color='#c9d1d9'),
            showlegend=False
        ))

        fig.update_layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=20, r=20, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
            height=600
        )

        fig.update_xaxes(range=[-9, 9])
        fig.update_yaxes(range=[-9, 9], scaleanchor='x', scaleratio=1)

        st.plotly_chart(fig, use_container_width=True)

        # Scope legend
        st.markdown("**Scope Colors:** ")
        legend_cols = st.columns(min(len(SCOPE_COLORS), 7))
        for i, (scope, color) in enumerate(SCOPE_COLORS.items()):
            if i < len(legend_cols):
                with legend_cols[i]:
                    st.markdown(f'<span style="color:{color};font-weight:700;">● {scope}</span>', unsafe_allow_html=True)

        st.caption(f"Showing {len(all_mems)} memories and {len(entity_memories)} entity clusters. Unlinked memories shown on outer ring.")