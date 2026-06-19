from pydantic import BaseModel, Field

from backend.agents.base import Agent
from backend.models.domain import Channel, FraudSignal, InteractionLog, NDRCase, ResolutionAction
from backend.tools.language import infer_language_from_pin
from backend.tools.whatsapp_tool import WhatsAppClient


class ResellerAgentResult(BaseModel):
    contacted: bool
    social_context: str | None = None
    trust_score: float = Field(ge=0, le=1)
    recommended_action: ResolutionAction
    interaction: InteractionLog
    fraud_signal: FraudSignal | None = None


class ResellerAgent(Agent[ResellerAgentResult]):
    name = "reseller_context_agent"

    def __init__(self, whatsapp_client: WhatsAppClient | None = None) -> None:
        self.whatsapp_client = whatsapp_client or WhatsAppClient()

    async def run(self, case: NDRCase) -> ResellerAgentResult:
        reseller = case.order.reseller
        language = reseller.preferred_language or infer_language_from_pin(case.order.buyer.address.pin_code)
        result = await self.whatsapp_client.send_reseller_prompt(
            reseller,
            case.order.buyer.name,
            case.id,
        )
        trust_score = self._score_reseller(case)
        recommended = ResolutionAction.REDELIVERY if trust_score >= 0.55 else ResolutionAction.ESCALATION
        fraud_signal = None
        if trust_score < 0.35:
            fraud_signal = FraudSignal(
                source=self.name,
                score=0.65,
                reason="Reseller trust score is low for social-proxy intervention.",
                evidence={
                    "reseller_trust": reseller.trust_score,
                    "historical_resolution_rate": reseller.historical_resolution_rate,
                    "consent": reseller.consent_for_social_context,
                },
            )
            recommended = ResolutionAction.FRAUD_INVESTIGATION

        message = result.response_text or "Reseller social proxy unavailable or consent missing."
        interaction = InteractionLog(
            case_id=case.id,
            actor=self.name,
            channel=Channel.RESELLER_PROXY,
            message=message,
            language=language,
            metadata={"trust_score": trust_score, "contacted": result.delivered},
        )
        return ResellerAgentResult(
            contacted=result.delivered,
            social_context=result.response_text,
            trust_score=trust_score,
            recommended_action=recommended,
            interaction=interaction,
            fraud_signal=fraud_signal,
        )

    @staticmethod
    def _score_reseller(case: NDRCase) -> float:
        reseller = case.order.reseller
        consent_bonus = 0.1 if reseller.consent_for_social_context else -0.15
        score = (
            reseller.trust_score * 0.55
            + reseller.historical_resolution_rate * 0.35
            + consent_bonus
        )
        return max(0.0, min(1.0, score))
