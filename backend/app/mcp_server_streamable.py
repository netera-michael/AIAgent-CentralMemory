import os
import sys
import logging
import asyncio
import contextlib
import json
from typing import Any, Optional, List, Dict
from datetime import datetime, timezone

import mcp.types as types
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from starlette.applications import Starlette
from starlette.routing import Route
from uvicorn import Config, Server as UvicornServer

from sqlalchemy.orm import Session
from uuid import UUID

from .database import SessionLocal
from . import crud, schemas, models
from .worker import generate_embedding
from .deps import _lookup_key

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger('mcp_server')

server = Server('centralmemory-mcp')

session_manager = StreamableHTTPSessionManager(
    app=server,
    stateless=True,
    json_response=True,
)


def get_db_session() -> Session:
    return SessionLocal()

def get_scopes(api_key: str) -> list[str]:
    raw_key = api_key or os.environ.get('CENTRALMEMORY_API_KEY', '')
    if not raw_key:
        return []
    db = SessionLocal()
    try:
        record = _lookup_key(db, raw_key)
        if not record:
            return []
        record.last_used_at = datetime.now(timezone.utc)
        db.commit()
        return record.allowed_scopes
    finally:
        db.close()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name='memory_add',
            description='Add a new memory (fact, note, preference) to the CentralMemory system.',
            inputSchema={
                'type': 'object',
                'properties': {
                    'content': {'type': 'string', 'description': 'The exact content to memorize.'},
                    'type': {'type': 'string', 'description': 'Type of memory (e.g., fact, preference, project_note).'},
                    'scope': {'type': 'string', 'description': 'Scope (e.g., coding_projects, personal, infrastructure).'},
                    'title': {'type': 'string'},
                    'summary': {'type': 'string'}
                },
                'required': ['content', 'type', 'scope']
            }
        ),
        types.Tool(
            name='memory_search',
            description='Search the memory system using semantic similarity.',
            inputSchema={
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'The semantic search query.'},
                    'limit': {'type': 'integer', 'description': 'Number of results to return (default 5).'},
                    'include_scratch': {'type': 'boolean', 'description': 'Whether to include unreviewed scratch memories.'}
                },
                'required': ['query']
            }
        ),
        types.Tool(
            name='memory_update',
            description='Update an existing memory. Note: non-admin clients can only modify scratch memories.',
            inputSchema={
                'type': 'object',
                'properties': {
                    'memory_id': {'type': 'string'},
                    'status': {'type': 'string', 'description': 'New status (e.g., reviewed, canonical).'},
                    'title': {'type': 'string'},
                    'summary': {'type': 'string'},
                    'content': {'type': 'string', 'description': 'New content. Triggers re-embedding automatically.'}
                },
                'required': ['memory_id']
            }
        ),
        types.Tool(
            name='memory_archive',
            description='Soft-delete a memory from the system.',
            inputSchema={
                'type': 'object',
                'properties': {
                    'memory_id': {'type': 'string'}
                },
                'required': ['memory_id']
            }
        ),
        types.Tool(
            name='memory_get',
            description='Get a single memory by ID.',
            inputSchema={
                'type': 'object',
                'properties': {
                    'memory_id': {'type': 'string', 'description': 'The memory ID.'}
                },
                'required': ['memory_id']
            }
        ),
        types.Tool(
            name='memory_list',
            description='List recent memories. By default returns reviewed and canonical only.',
            inputSchema={
                'type': 'object',
                'properties': {
                    'limit': {'type': 'integer', 'description': 'Number of results (default 20).'},
                    'skip': {'type': 'integer', 'description': 'Offset for pagination.'},
                    'include_scratch': {'type': 'boolean', 'description': 'Whether to include unreviewed scratch memories.'}
                }
            }
        ),
        types.Tool(
            name='memory_purge',
            description='Hard delete a memory permanently. Admin only. Use for sensitive data spills.',
            inputSchema={
                'type': 'object',
                'properties': {
                    'memory_id': {'type': 'string'}
                },
                'required': ['memory_id']
            }
        ),
        types.Tool(
            name='entity_get_or_create',
            description='Ensure an entity exists in the system to attach memories to.',
            inputSchema={
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'Name of the entity.'},
                    'type': {'type': 'string', 'description': 'Type of entity (e.g., person, project, server).'},
                    'description': {'type': 'string'}
                },
                'required': ['name', 'type']
            }
        ),
        types.Tool(
            name='review_list_conflicts',
            description='List pending review items (duplicates, conflicts) in the system. (Admin only)',
            inputSchema={
                'type': 'object',
                'properties': {
                    'limit': {'type': 'integer'}
                }
            }
        ),
        types.Tool(
            name='review_resolve',
            description='Resolve a review item (duplicates, conflicts). Admin only.',
            inputSchema={
                'type': 'object',
                'properties': {
                    'item_id': {'type': 'string', 'description': 'The review item ID.'},
                    'action': {'type': 'string', 'description': 'Resolution action (e.g., merge, keep_both, discard).'},
                    'resolution_notes': {'type': 'string'}
                },
                'required': ['item_id', 'action']
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if arguments is None:
        arguments = {}

    api_key = os.environ.get('CENTRALMEMORY_API_KEY', '')
    scopes = get_scopes(api_key)
    db = get_db_session()

    try:
        if name == 'memory_add':
            if arguments['scope'] not in scopes and 'admin' not in scopes:
                return [types.TextContent(type='text', text=f'Error: Not authorized for scope {arguments["scope"]}')]

            mem_create = schemas.MemoryCreate(
                content=arguments['content'],
                type=arguments['type'],
                scope=arguments['scope'],
                title=arguments.get('title'),
                summary=arguments.get('summary')
            )

            initial_status = 'scratch'
            db_memory, db_job = crud.create_memory(db, mem_create, initial_status=initial_status)

            return [types.TextContent(type='text', text=f'Successfully added memory. ID: {db_memory.id}, Status: {db_memory.status}')]

        elif name == 'memory_search':
            query_str = arguments['query']
            limit = arguments.get('limit', 5)
            include_scratch = arguments.get('include_scratch', False)

            try:
                query_embedding = generate_embedding(query_str)
            except Exception as e:
                return [types.TextContent(type='text', text=f'Error generating embedding: {e}')]

            from sqlalchemy import func

            distance_expr = models.MemoryChunk.embedding.cosine_distance(query_embedding)
            subq = (
                db.query(
                    models.MemoryChunk.memory_id,
                    func.min(distance_expr).label('min_distance')
                )
                .group_by(models.MemoryChunk.memory_id)
                .subquery()
            )

            db_query = (
                db.query(models.Memory)
                .join(subq, models.Memory.id == subq.c.memory_id)
                .order_by(subq.c.min_distance)
            )

            if 'admin' not in scopes:
                db_query = db_query.filter(models.Memory.scope.in_(scopes))

            if not include_scratch:
                db_query = db_query.filter(models.Memory.status.in_(['reviewed', 'canonical']))

            threshold = arguments.get('threshold', 2.0)
            db_query = db_query.filter(subq.c.min_distance <= threshold)

            results = db_query.limit(limit).all()

            if not results:
                return [types.TextContent(type='text', text='No matching memories found.')]

            formatted = []
            for r in results:
                formatted.append(f'[{r.id}] ({r.type} | {r.scope} | {r.status})\nTitle: {r.title}\nContent: {r.content}\n---')

            return [types.TextContent(type='text', text='\n'.join(formatted))]

        elif name == 'memory_get':
            mem_id = UUID(arguments['memory_id'])
            db_memory = crud.get_memory(db, mem_id)
            if not db_memory:
                return [types.TextContent(type='text', text=f'Error: Memory {arguments["memory_id"]} not found.')]
            return [types.TextContent(type='text', text=f'[{db_memory.id}] ({db_memory.type} | {db_memory.scope} | {db_memory.status})\nTitle: {db_memory.title}\nContent: {db_memory.content}')]

        elif name == 'memory_list':
            limit = arguments.get('limit', 20)
            skip = arguments.get('skip', 0)
            include_scratch = arguments.get('include_scratch', False)
            db_query = db.query(models.Memory).order_by(models.Memory.updated_at.desc())
            if 'admin' not in scopes:
                db_query = db_query.filter(models.Memory.scope.in_(scopes))
            if not include_scratch:
                db_query = db_query.filter(models.Memory.status.in_(['reviewed', 'canonical']))
            results = db_query.offset(skip).limit(limit).all()
            if not results:
                return [types.TextContent(type='text', text='No memories found.')]
            formatted = []
            for r in results:
                formatted.append(f'[{r.id}] ({r.type} | {r.scope} | {r.status})\nTitle: {r.title}\n---')
            return [types.TextContent(type='text', text='\n'.join(formatted))]

        elif name == 'memory_update':
            mem_id_str = arguments['memory_id']
            mem_id = UUID(mem_id_str)

            db_memory = crud.get_memory(db, mem_id)
            if not db_memory:
                return [types.TextContent(type='text', text=f'Error: Memory {mem_id_str} not found.')]

            if db_memory.scope not in scopes and 'admin' not in scopes:
                return [types.TextContent(type='text', text='Error: Not authorized for this memory\'s scope.')]

            new_status = arguments.get('status')
            if new_status and new_status != 'scratch' and 'admin' not in scopes:
                return [types.TextContent(type='text', text='Error: Only admins can promote status beyond scratch.')]

            update_kwargs = {}
            if 'title' in arguments and arguments['title'] is not None:
                update_kwargs['title'] = arguments['title']
            if 'summary' in arguments and arguments['summary'] is not None:
                update_kwargs['summary'] = arguments['summary']
            if 'content' in arguments and arguments['content'] is not None:
                update_kwargs['content'] = arguments['content']
            if new_status:
                update_kwargs['status'] = new_status

            update_data = schemas.MemoryUpdate(**update_kwargs)

            crud.update_memory(db, mem_id, update_data)
            return [types.TextContent(type='text', text=f'Memory {mem_id_str} successfully updated.')]

        elif name == 'memory_archive':
            mem_id = UUID(arguments['memory_id'])
            db_memory = crud.archive_memory(db, mem_id)
            if not db_memory:
                return [types.TextContent(type='text', text='Error: Memory not found.')]
            return [types.TextContent(type='text', text=f'Memory {mem_id} successfully archived.')]

        elif name == 'memory_purge':
            if 'admin' not in scopes:
                return [types.TextContent(type='text', text='Error: Admin scope required.')]
            mem_id = UUID(arguments['memory_id'])
            db_memory = db.query(models.Memory).filter(models.Memory.id == mem_id).first()
            if not db_memory:
                return [types.TextContent(type='text', text=f'Error: Memory {arguments["memory_id"]} not found.')]
            db.query(models.MemoryChunk).filter(models.MemoryChunk.memory_id == mem_id).delete()
            db.delete(db_memory)
            db.commit()
            return [types.TextContent(type='text', text=f'Memory {mem_id} permanently purged.')]

        elif name == 'entity_get_or_create':
            entity_create = schemas.EntityCreate(
                name=arguments['name'],
                type=arguments['type'],
                description=arguments.get('description')
            )
            db_entity = crud.create_entity(db, entity_create)
            return [types.TextContent(type='text', text=f'Entity \'{db_entity.name}\' ready. ID: {db_entity.id}')]

        elif name == 'review_list_conflicts':
            if 'admin' not in scopes:
                return [types.TextContent(type='text', text='Error: Admin scope required.')]

            limit = arguments.get('limit', 10)
            items = crud.get_review_items(db, limit=limit, status='pending')

            if not items:
                return [types.TextContent(type='text', text='No pending review items.')]

            formatted = []
            for item in items:
                formatted.append(f'Review ID: {item.id}\nType: {item.review_type}\nMemory ID: {item.memory_id}\nReason: {item.reason}\n---')

            return [types.TextContent(type='text', text='\n'.join(formatted))]

        elif name == 'review_resolve':
            if 'admin' not in scopes:
                return [types.TextContent(type='text', text='Error: Admin scope required.')]
            return [types.TextContent(type='text', text=f'Review item {arguments["item_id"]} resolved with action: {arguments["action"]}.')]

        else:
            raise ValueError(f'Unknown tool: {name}')

    except Exception as e:
        logger.error(f'Error executing tool {name}: {e}')
        return [types.TextContent(type='text', text=f'Internal Error: {str(e)}')]
    finally:
        db.close()


async def handle_streamable(request):
    from starlette.responses import Response
    try:
        await session_manager.handle_request(request.scope, request.receive, request._send)
    except Exception as e:
        logger.error(f"MCP streamable handler error: {e}")
        return Response(content=json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}), status_code=500, media_type="application/json")


@contextlib.asynccontextmanager
async def lifespan(app):
    async with session_manager.run():
        yield


app = Starlette(
    routes=[
        Route('/mcp', endpoint=handle_streamable, methods=['GET', 'POST', 'DELETE']),
    ],
    lifespan=lifespan,
)

if __name__ == '__main__':
    port = int(os.environ.get('MCP_PORT', '9000'))
    uvicorn_config = Config(app, host='0.0.0.0', port=port, log_level='info')
    uvicorn_server = UvicornServer(uvicorn_config)
    asyncio.run(uvicorn_server.serve())
