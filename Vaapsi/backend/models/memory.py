from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.models.domain import FraudSignal, InteractionLog, ResolutionEvent, TrustGraph, utcnow


class MemorySnapshot(BaseModel):
    case_id: str
    interaction_count: int
    retry_count: int
    latest_interaction_at: datetime | None = None
    fraud_score: float = Field(ge=0, le=1)
    trust_graph: TrustGraph
    resolution_history: list[ResolutionEvent] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)


class MemoryUpdate(BaseModel):
    case_id: str
    interaction: InteractionLog | None = None
    fraud_signal: FraudSignal | None = None
    resolution_event: ResolutionEvent | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
