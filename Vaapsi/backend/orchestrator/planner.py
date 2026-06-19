from pydantic import BaseModel, Field

from backend.agents import BuyerAgent, LogisticsAgent, ResellerAgent
from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.memory import EpisodicMemory
from backend.models.domain import (
    CaseStatus,
    NDRCase,
    ResolutionAction,
    ResolutionEvent,
)
from backend.models.memory import MemoryUpdate
from backend.orchestrator.state_machine import CaseStateMachine


logger = get_logger(__name__)


class OrchestratorResult(BaseModel):
    case: NDRCase
    final_action: ResolutionAction
    steps: list[str] = Field(default_factory=list)


class Orchestrator:
    def __init__(
        self,
        memory: EpisodicMemory,
        logistics_agent: LogisticsAgent | None = None,
        buyer_agent: BuyerAgent | None = None,
        reseller_agent: ResellerAgent | None = None,
        state_machine: CaseStateMachine | None = None,
    ) -> None:
        self.memory = memory
        self.logistics_agent = logistics_agent or LogisticsAgent()
        self.buyer_agent = buyer_agent or BuyerAgent()
        self.reseller_agent = reseller_agent or ResellerAgent()
        self.state_machine = state_machine or CaseStateMachine()
        self.settings = get_settings()

    async def resolve(self, case: NDRCase) -> OrchestratorResult:
        steps: list[str] = []
        case.status = CaseStatus.IN_PROGRESS
        await self.memory.save_case(case)

        logistics = await self.logistics_agent.run(case)
        await self.memory.append(
            MemoryUpdate(
                case_id=case.id,
                interaction=logistics.interaction,
                fraud_signal=logistics.fraud_signal,
                attributes={"note_logistics": logistics.recommendation},
            )
        )
        steps.append(f"observe logistics: {logistics.recommendation}")
        logger.info("logistics observation case_id=%s fraud=%s", case.id, logistics.fraud_flag)

        if logistics.fraud_flag:
            event = ResolutionEvent(
                action=ResolutionAction.FRAUD_INVESTIGATION,
                reason="Logistics GPS or delivery-agent history indicates possible fake scan.",
                confidence=0.82,
            )
            case = self.state_machine.apply_resolution(case, event)
            await self.memory.append(MemoryUpdate(case_id=case.id, resolution_event=event))
            steps.append("act: route to logistics fraud investigation")
            return OrchestratorResult(case=case, final_action=event.action, steps=steps)

        buyer = await self.buyer_agent.run(case)
        await self.memory.append(
            MemoryUpdate(
                case_id=case.id,
                interaction=buyer.interaction,
                fraud_signal=buyer.fraud_signal,
                attributes={"note_buyer": f"intent={buyer.intent} channel={buyer.channel}"},
            )
        )
        steps.append(f"observe buyer: intent={buyer.intent} reached={buyer.reached}")

        if buyer.reached and buyer.recommended_action is not None:
            event = ResolutionEvent(
                action=buyer.recommended_action,
                reason=f"Buyer contact produced intent {buyer.intent}.",
                confidence=0.78,
                scheduled_slot="next_available_evening" if buyer.recommended_action == ResolutionAction.REDELIVERY else None,
            )
            case = self.state_machine.apply_resolution(case, event)
            await self.memory.append(MemoryUpdate(case_id=case.id, resolution_event=event))
            steps.append(f"act: {event.action}")
            return OrchestratorResult(case=case, final_action=event.action, steps=steps)

        reseller = await self.reseller_agent.run(case)
        await self.memory.append(
            MemoryUpdate(
                case_id=case.id,
                interaction=reseller.interaction,
                fraud_signal=reseller.fraud_signal,
                attributes={"note_reseller": f"trust_score={reseller.trust_score:.2f}"},
            )
        )
        steps.append(f"observe reseller: trust={reseller.trust_score:.2f}")

        event = ResolutionEvent(
            action=reseller.recommended_action,
            reason="Buyer unreachable; reseller social context selected as next best signal.",
            confidence=max(0.55, reseller.trust_score),
            scheduled_slot="buyer_confirmed_evening" if reseller.recommended_action == ResolutionAction.REDELIVERY else None,
        )
        case = self.state_machine.apply_resolution(case, event)
        await self.memory.append(MemoryUpdate(case_id=case.id, resolution_event=event))
        steps.append(f"act: {event.action}")
        return OrchestratorResult(case=case, final_action=event.action, steps=steps)
