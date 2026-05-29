from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Dict, List

# ── Backend imports (FastAPI router, models, services) ────────────────────────
_BACKEND_AVAILABLE = False
try:
    from fastapi import APIRouter, HTTPException, Depends
    from models import Agent, AgentCreate  # type: ignore[import]
    from datetime import datetime, timezone
    from services.audit_service import log_audit_event  # type: ignore[import]
    router = APIRouter()
    _BACKEND_AVAILABLE = True
except ImportError:
    # Runtime-only environment — backend deps not on path
    router = None  # type: ignore[assignment]


# ── Core runtime agent types and helpers ─────────────────────────────────────

@dataclass(frozen=True)
class AgentExecution:
    output: str
    metrics: Dict[str, int | str]


def implementation_module(agent_id: str) -> str:
    return agent_id.replace('-', '_')


def load_agent(agent_id: str):
    module = import_module(f'runtime.agent_impls.{implementation_module(agent_id)}')
    agent = module.Agent()
    if getattr(agent, 'id', None) != agent_id:
        raise ValueError(
            f"agent implementation id mismatch: "
            f"expected={agent_id}, actual={getattr(agent, 'id', None)}"
        )
    return agent


def implemented_agent_ids() -> set[str]:
    from pathlib import Path
    impl_dir = Path(__file__).parent / 'agent_impls'
    return {
        path.stem.replace('_', '-')
        for path in impl_dir.glob('*.py')
        if path.name != '__init__.py'
    }


# ── FastAPI CRUD routes (only registered when backend deps are available) ─────

if _BACKEND_AVAILABLE:
    async def _get_db():
        from server import db  # type: ignore[import]
        return db

    @router.post('/', response_model=Agent)  # type: ignore[union-attr]
    async def create_agent(agent: AgentCreate, db=Depends(_get_db)):
        """Create a new agent"""
        agent_obj = Agent(**agent.model_dump())
        doc = agent_obj.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        if doc.get('last_run'):
            doc['last_run'] = doc['last_run'].isoformat()
        await db.agents.insert_one(doc)
        await log_audit_event(db, 'agent.created', 'system', 'create', 'agent', agent_obj.id)
        return agent_obj

    @router.get('/', response_model=List[Agent])  # type: ignore[union-attr]
    async def list_agents(status: str = None, db=Depends(_get_db)):
        """List all agents"""
        query = {}
        if status:
            query['status'] = status
        agents = await db.agents.find(query, {'_id': 0}).to_list(1000)
        for agent in agents:
            if isinstance(agent.get('created_at'), str):
                agent['created_at'] = datetime.fromisoformat(agent['created_at'])
            if isinstance(agent.get('updated_at'), str):
                agent['updated_at'] = datetime.fromisoformat(agent['updated_at'])
            if agent.get('last_run') and isinstance(agent['last_run'], str):
                agent['last_run'] = datetime.fromisoformat(agent['last_run'])
        return agents

    @router.get('/{agent_id}', response_model=Agent)  # type: ignore[union-attr]
    async def get_agent(agent_id: str, db=Depends(_get_db)):
        """Get a specific agent"""
        agent = await db.agents.find_one({'id': agent_id}, {'_id': 0})
        if not agent:
            raise HTTPException(status_code=404, detail='Agent not found')
        if isinstance(agent.get('created_at'), str):
            agent['created_at'] = datetime.fromisoformat(agent['created_at'])
        if isinstance(agent.get('updated_at'), str):
            agent['updated_at'] = datetime.fromisoformat(agent['updated_at'])
        if agent.get('last_run') and isinstance(agent['last_run'], str):
            agent['last_run'] = datetime.fromisoformat(agent['last_run'])
        return agent

    @router.patch('/{agent_id}', response_model=Agent)  # type: ignore[union-attr]
    async def update_agent(agent_id: str, updates: dict, db=Depends(_get_db)):
        """Update an agent"""
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
        result = await db.agents.update_one({'id': agent_id}, {'$set': updates})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail='Agent not found')
        agent = await db.agents.find_one({'id': agent_id}, {'_id': 0})
        if isinstance(agent.get('created_at'), str):
            agent['created_at'] = datetime.fromisoformat(agent['created_at'])
        if isinstance(agent.get('updated_at'), str):
            agent['updated_at'] = datetime.fromisoformat(agent['updated_at'])
        if agent.get('last_run') and isinstance(agent['last_run'], str):
            agent['last_run'] = datetime.fromisoformat(agent['last_run'])
        await log_audit_event(db, 'agent.updated', 'system', 'update', 'agent', agent_id)
        return agent

    @router.post('/{agent_id}/execute')  # type: ignore[union-attr]
    async def execute_agent(agent_id: str, db=Depends(_get_db)):
        """Execute an agent action"""
        agent = await db.agents.find_one({'id': agent_id}, {'_id': 0})
        if not agent:
            raise HTTPException(status_code=404, detail='Agent not found')
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.agents.update_one(
            {'id': agent_id},
            {'$set': {'last_run': now_iso, 'updated_at': now_iso}, '$inc': {'run_count': 1}},
        )
        await log_audit_event(db, 'agent.executed', 'system', 'execute', 'agent', agent_id)
        return {'message': 'Agent execution started', 'agent_id': agent_id}
