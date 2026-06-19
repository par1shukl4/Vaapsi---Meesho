from pydantic import BaseModel, Field

from backend.agents.base import Agent
from backend.models.domain import (
    BuyerIntent,
    Channel,
    FraudSignal,
    InteractionLog,
    Language,
    NDRCase,
    ResolutionAction,
    SentimentLabel,
)
from backend.tools.language import infer_language_from_pin
from backend.tools.sentiment_tool import SentimentAnalyzer
from backend.tools.voice_tool import VoiceClient
from backend.tools.whatsapp_tool import WhatsAppClient


class BuyerAgentResult(BaseModel):
    reached: bool
    language: Language
    channel: Channel
    intent: BuyerIntent
    sentiment_label: SentimentLabel | None = None
    updated_address_required: bool = False
    recommended_action: ResolutionAction | None = None
    interaction: InteractionLog
    fraud_signal: FraudSignal | None = None


class BuyerAgent(Agent[BuyerAgentResult]):
    name = "buyer_contact_agent"

    def __init__(
        self,
        whatsapp_client: WhatsAppClient | None = None,
        voice_client: VoiceClient | None = None,
        sentiment_analyzer: SentimentAnalyzer | None = None,
    ) -> None:
        self.whatsapp_client = whatsapp_client or WhatsAppClient()
        self.voice_client = voice_client or VoiceClient()
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()

    async def run(self, case: NDRCase) -> BuyerAgentResult:
        buyer = case.order.buyer
        language = buyer.language_preference or infer_language_from_pin(buyer.address.pin_code)
        whatsapp_result = await self.whatsapp_client.send_buyer_prompt(buyer, language, case.id)

        if whatsapp_result.delivered and whatsapp_result.response_text:
            text = whatsapp_result.response_text
            channel = whatsapp_result.channel
        else:
            voice_result = await self.voice_client.call_buyer(buyer, language)
            channel = voice_result.channel
            if not voice_result.connected or not voice_result.transcript:
                interaction = InteractionLog(
                    case_id=case.id,
                    actor=self.name,
                    channel=channel,
                    message="Buyer unreachable across WhatsApp and voice fallback.",
                    language=language,
                    metadata={"retry_count": case.retry_count},
                )
                return BuyerAgentResult(
                    reached=False,
                    language=language,
                    channel=channel,
                    intent=BuyerIntent.UNREACHABLE,
                    interaction=interaction,
                )
            text = voice_result.transcript

        sentiment = await self.sentiment_analyzer.analyze(text, language)
        intent = self._infer_intent(text, sentiment.label)
        interaction = InteractionLog(
            case_id=case.id,
            actor=self.name,
            channel=channel,
            message=text,
            language=language,
            sentiment=sentiment,
            metadata={"intent": intent},
        )
        fraud_signal = None
        if sentiment.label == SentimentLabel.SUSPICIOUS or intent == BuyerIntent.SUSPICIOUS:
            fraud_signal = FraudSignal(
                source=self.name,
                score=0.7,
                reason="Buyer response has suspicious markers.",
                evidence={"response": text, "sentiment": sentiment.label},
            )

        recommended_action = {
            BuyerIntent.ADDRESS_CORRECTION: ResolutionAction.ADDRESS_CORRECTION,
            BuyerIntent.REDELIVERY_REQUESTED: ResolutionAction.REDELIVERY,
            BuyerIntent.REFUND_REQUESTED: ResolutionAction.PARTIAL_REFUND,
            BuyerIntent.DENIES_ORDER: ResolutionAction.FRAUD_INVESTIGATION,
            BuyerIntent.SUSPICIOUS: ResolutionAction.FRAUD_INVESTIGATION,
        }.get(intent)

        return BuyerAgentResult(
            reached=True,
            language=language,
            channel=channel,
            intent=intent,
            sentiment_label=sentiment.label,
            updated_address_required=intent == BuyerIntent.ADDRESS_CORRECTION,
            recommended_action=recommended_action,
            interaction=interaction,
            fraud_signal=fraud_signal,
        )

    @staticmethod
    def _infer_intent(text: str, sentiment: SentimentLabel) -> BuyerIntent:
        normalized = text.lower()
        if sentiment == SentimentLabel.SUSPICIOUS:
            return BuyerIntent.SUSPICIOUS
        if "address" in normalized and ("wrong" in normalized or "change" in normalized):
            return BuyerIntent.ADDRESS_CORRECTION
        if "refund" in normalized:
            return BuyerIntent.REFUND_REQUESTED
        if "never ordered" in normalized or "did not order" in normalized:
            return BuyerIntent.DENIES_ORDER
        if "redeliver" in normalized or "available" in normalized or "tomorrow" in normalized:
            return BuyerIntent.REDELIVERY_REQUESTED
        return BuyerIntent.REDELIVERY_REQUESTED
