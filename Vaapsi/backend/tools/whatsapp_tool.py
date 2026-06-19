from dataclasses import dataclass

from backend.models.domain import Buyer, Channel, Language, Reseller


@dataclass(frozen=True)
class MessageResult:
    channel: Channel
    delivered: bool
    response_text: str | None = None
    provider_message_id: str | None = None


class WhatsAppClient:
    async def send_buyer_prompt(self, buyer: Buyer, language: Language, case_id: str) -> MessageResult:
        if buyer.historical_ndr_count >= 3:
            return MessageResult(Channel.WHATSAPP, True, "refund first then redeliver")
        if buyer.cod_reliability_score < 0.25:
            return MessageResult(Channel.WHATSAPP, False)
        return MessageResult(
            Channel.WHATSAPP,
            True,
            "yes please redeliver tomorrow, address is correct",
            f"wa-buyer-{case_id}",
        )

    async def send_reseller_prompt(
        self, reseller: Reseller, buyer_name: str, case_id: str
    ) -> MessageResult:
        if not reseller.consent_for_social_context:
            return MessageResult(Channel.RESELLER_PROXY, False)
        return MessageResult(
            Channel.RESELLER_PROXY,
            True,
            f"{buyer_name} is genuine and usually responds in evening",
            f"wa-reseller-{case_id}",
        )
