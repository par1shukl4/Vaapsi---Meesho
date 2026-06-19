from abc import ABC, abstractmethod

from backend.models.domain import NDRCase
from backend.models.memory import MemorySnapshot, MemoryUpdate


class EpisodicMemory(ABC):
    @abstractmethod
    async def save_case(self, case: NDRCase) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_case(self, case_id: str) -> NDRCase | None:
        raise NotImplementedError

    @abstractmethod
    async def append(self, update: MemoryUpdate) -> MemorySnapshot:
        raise NotImplementedError

    @abstractmethod
    async def snapshot(self, case_id: str) -> MemorySnapshot | None:
        raise NotImplementedError


class InMemoryEpisodicMemory(EpisodicMemory):
    def __init__(self) -> None:
        self._cases: dict[str, NDRCase] = {}
        self._attributes: dict[str, dict[str, object]] = {}

    async def save_case(self, case: NDRCase) -> None:
        self._cases[case.id] = case

    async def get_case(self, case_id: str) -> NDRCase | None:
        return self._cases.get(case_id)

    async def append(self, update: MemoryUpdate) -> MemorySnapshot:
        case = self._cases[update.case_id]
        if update.interaction:
            case.add_interaction(update.interaction)
        if update.fraud_signal:
            case.add_fraud_signal(update.fraud_signal)
        if update.resolution_event:
            case.add_resolution(update.resolution_event)
        self._attributes.setdefault(update.case_id, {}).update(update.attributes)
        await self.save_case(case)
        snapshot = await self.snapshot(update.case_id)
        if snapshot is None:
            raise RuntimeError("snapshot unavailable after memory append")
        return snapshot

    async def snapshot(self, case_id: str) -> MemorySnapshot | None:
        case = self._cases.get(case_id)
        if case is None:
            return None
        latest = max((log.created_at for log in case.interactions), default=None)
        fraud_score = max((signal.score for signal in case.fraud_signals), default=0)
        notes = [
            str(value)
            for key, value in self._attributes.get(case_id, {}).items()
            if key.startswith("note")
        ]
        return MemorySnapshot(
            case_id=case.id,
            interaction_count=len(case.interactions),
            retry_count=case.retry_count,
            latest_interaction_at=latest,
            fraud_score=fraud_score,
            trust_graph=case.trust_graph,
            resolution_history=case.resolution_events,
            notes=notes,
        )
