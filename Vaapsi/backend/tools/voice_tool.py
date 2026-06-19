from dataclasses import dataclass

from backend.models.domain import Buyer, Channel, Language


@dataclass(frozen=True)
class VoiceResult:
    channel: Channel
    connected: bool
    transcript: str | None = None
    recording_retention_hours: int = 24


class VoiceClient:
    async def call_buyer(self, buyer: Buyer, language: Language) -> VoiceResult:
        if buyer.cod_reliability_score < 0.2:
            return VoiceResult(Channel.IVR, False)
        return VoiceResult(Channel.VOICE, True, "I am available after 6 pm for delivery")
