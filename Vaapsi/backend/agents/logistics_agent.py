from pydantic import BaseModel, Field

from backend.agents.base import Agent
from backend.core.config import get_settings
from backend.models.domain import FraudSignal, InteractionLog, NDRCase, Channel
from backend.tools.maps_tool import MapsClient


class LogisticsAgentResult(BaseModel):
    gps_validity_score: float = Field(ge=0, le=1)
    fraud_flag: bool
    recommendation: str
    interaction: InteractionLog
    fraud_signal: FraudSignal | None = None


class LogisticsAgent(Agent[LogisticsAgentResult]):
    name = "logistics_intel_agent"

    def __init__(self, maps_client: MapsClient | None = None) -> None:
        self.maps_client = maps_client or MapsClient()
        self.settings = get_settings()

    async def run(self, case: NDRCase) -> LogisticsAgentResult:
        result = await self.maps_client.validate_attempt(
            case.order.buyer.address,
            case.attempt_latitude,
            case.attempt_longitude,
            self.settings.gps_mismatch_threshold_meters,
        )
        agent_risk = case.order.delivery_agent.historical_false_scan_rate
        gps_score = 1.0 if result.distance_meters is None else max(
            0.0,
            1.0 - (result.distance_meters / max(self.settings.gps_mismatch_threshold_meters * 2, 1)),
        )
        fraud_flag = (not result.valid) or agent_risk >= 0.6
        fraud_signal = None
        recommendation = "Proceed to buyer contact."
        if fraud_flag:
            fraud_signal = FraudSignal(
                source=self.name,
                score=max(0.75, agent_risk),
                reason="Possible fake delivery attempt or high-risk delivery-agent history.",
                evidence={
                    "distance_meters": result.distance_meters,
                    "gps_reason": result.reason,
                    "delivery_agent_false_scan_rate": agent_risk,
                },
            )
            recommendation = "Escalate to logistics fraud review before buyer retries."

        interaction = InteractionLog(
            case_id=case.id,
            actor=self.name,
            channel=Channel.LOGISTICS_WEBHOOK,
            message=result.reason,
            metadata={"distance_meters": result.distance_meters, "fraud_flag": fraud_flag},
        )
        return LogisticsAgentResult(
            gps_validity_score=gps_score,
            fraud_flag=fraud_flag,
            recommendation=recommendation,
            interaction=interaction,
            fraud_signal=fraud_signal,
        )
