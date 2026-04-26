# CentralMemory

## When to use memory tools

CentralMemory tools are available via MCP (Streamable HTTP) or HTTP REST API. Tool names are prefixed with `centralmemory_`:

- **Recalling information**: Use `centralmemory_memory_search` before answering questions about anything that might be stored (server details, credentials, preferences, project decisions, facts, etc.)
- **Storing information**: Use `centralmemory_memory_add` whenever the user shares something worth remembering (new credentials, decisions, preferences, facts, server details, etc.)
- **Updating information**: Use `centralmemory_memory_update` when the user corrects or changes something already stored. Pass `content` to update the text — it will re-embed automatically.

Do NOT wait for the user to say "use memory_search" or "use memory_add". Proactively search memory when it could help answer their question. Proactively store anything the user tells you that seems like a fact, decision, or preference worth retaining.

## Memory scopes and types

When storing memories, use the correct scope and type:

**Scopes** (pick the best fit):
- `personal` — personal facts, preferences, health, family, vehicles, hobbies
- `personal_finance` — investments, crypto, properties, BNPL, budgeting, banks
- `biz_finance` — business finances, company details, revenue, banking
- `biz_projects` — business projects, venues, branding, clients
- `coding_projects` — software, infrastructure, AI tools, model choices, tech stack
- `infrastructure` — servers, backups, smart home, networking, hardware
- `social_media_clients` — social accounts, client details

**Types** (pick the best fit):
- `fact` — confirmed factual information
- `preference` — likes, dislikes, communication style, workflow choices
- `decision` — choices made, plans settled on, directions chosen
- `workflow` — processes, routing rules, procedures
- `project_note` — architecture, data models, project-level knowledge

**Status**:
- All agent-written memories start as `scratch` by default
- Only promote to `reviewed` or `canonical` if you are confident the user has confirmed it

## Memory quality rules

- Store concise facts (1-2 sentences), NOT full session transcripts or verbose logs
- Use `scope: personal` for personal facts, `scope: infrastructure` for server/deployment info, `scope: coding_projects` for project notes
- Use `type: fact` for facts, `type: decision` for architectural choices, `type: preference` for preferences
- Set `status: canonical` for critical truths, `status: reviewed` for verified info
- Archive outdated memories immediately — stale data pollutes search results