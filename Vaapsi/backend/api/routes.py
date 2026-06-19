from fastapi import APIRouter, Depends, HTTPException

from backend.agents import BuyerAgent, LogisticsAgent, ResellerAgent
from backend.api.dependencies import (
    get_buyer_agent,
    get_logistics_agent,
    get_memory,
    get_orchestrator,
    get_reseller_agent,
)
from backend.memory import InMemoryEpisodicMemory
from backend.models.domain import NDRCase, ResolutionEvent
from backend.models.memory import MemorySnapshot, MemoryUpdate
from backend.orchestrator import Orchestrator, OrchestratorResult


router = APIRouter()


@router.post("/ndr/create", response_model=OrchestratorResult)
async def create_ndr_case(
    case: NDRCase,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> OrchestratorResult:
    return await orchestrator.resolve(case)


@router.post("/agent/logistics")
async def run_logistics_agent(
    case: NDRCase,
    agent: LogisticsAgent = Depends(get_logistics_agent),
):
    return await agent.run(case)


@router.post("/agent/buyer")
async def run_buyer_agent(case: NDRCase, agent: BuyerAgent = Depends(get_buyer_agent)):
    return await agent.run(case)


@router.post("/agent/reseller")
async def run_reseller_agent(case: NDRCase, agent: ResellerAgent = Depends(get_reseller_agent)):
    return await agent.run(case)


@router.post("/resolution", response_model=NDRCase)
async def post_resolution(
    case_id: str,
    resolution: ResolutionEvent,
    memory: InMemoryEpisodicMemory = Depends(get_memory),
) -> NDRCase:
    case = await memory.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    case.add_resolution(resolution)
    await memory.save_case(case)
    return case


@router.get("/case/{case_id}", response_model=NDRCase)
async def get_case(
    case_id: str,
    memory: InMemoryEpisodicMemory = Depends(get_memory),
) -> NDRCase:
    case = await memory.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    return case


@router.get("/history/{case_id}", response_model=MemorySnapshot)
async def get_history(
    case_id: str,
    memory: InMemoryEpisodicMemory = Depends(get_memory),
) -> MemorySnapshot:
    snapshot = await memory.snapshot(case_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="case not found")
    return snapshot


@router.post("/memory/update", response_model=MemorySnapshot)
async def update_memory(
    update: MemoryUpdate,
    memory: InMemoryEpisodicMemory = Depends(get_memory),
) -> MemorySnapshot:
    if await memory.get_case(update.case_id) is None:
        raise HTTPException(status_code=404, detail="case not found")
    return await memory.append(update)
