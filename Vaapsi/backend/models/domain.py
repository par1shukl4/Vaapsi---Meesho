from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Language(StrEnum):
    HINDI = "hi"
    ENGLISH = "en"
    TAMIL = "ta"
    TELUGU = "te"
    BENGALI = "bn"
    MARATHI = "mr"
    KANNADA = "kn"


class Channel(StrEnum):
    WHATSAPP = "whatsapp"
    VOICE = "voice"
    IVR = "ivr"
    SMS = "sms"
    RESELLER_PROXY = "reseller_proxy"
    LOGISTICS_WEBHOOK = "logistics_webhook"


class SentimentLabel(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    SUSPICIOUS = "suspicious"


class BuyerIntent(StrEnum):
    REDELIVERY_REQUESTED = "redelivery_requested"
    ADDRESS_CORRECTION = "address_correction"
    UNREACHABLE = "unreachable"
    REFUND_REQUESTED = "refund_requested"
    DENIES_ORDER = "denies_order"
    SUSPICIOUS = "suspicious"


class NDRReason(StrEnum):
    BUYER_UNREACHABLE = "buyer_unreachable"
    ADDRESS_ISSUE = "address_issue"
    CUSTOMER_REFUSED = "customer_refused"
    CASH_UNAVAILABLE = "cash_unavailable"
    FAKE_ATTEMPT_SUSPECTED = "fake_attempt_suspected"
    OTHER = "other"


class CaseStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED_RTO = "closed_rto"


class ResolutionAction(StrEnum):
    REDELIVERY = "redelivery"
    ADDRESS_CORRECTION = "address_correction"
    PARTIAL_REFUND = "partial_refund"
    ESCALATION = "escalation"
    FRAUD_INVESTIGATION = "fraud_investigation"
    RTO_CLOSURE = "rto_closure"


class Address(BaseModel):
    line1: str
    line2: str | None = None
    city: str
    state: str
    pin_code: str = Field(min_length=6, max_length=6)
    landmark: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("pin_code")
    @classmethod
    def pin_code_digits(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("pin_code must contain exactly six digits")
        return value


class Buyer(BaseModel):
    id: str
    name: str
    phone: str
    address: Address
    language_preference: Language | None = None
    cod_reliability_score: float = Field(default=0.5, ge=0, le=1)
    historical_ndr_count: int = Field(default=0, ge=0)


class Reseller(BaseModel):
    id: str
    name: str
    phone: str
    preferred_language: Language | None = None
    trust_score: float = Field(default=0.7, ge=0, le=1)
    historical_resolution_rate: float = Field(default=0.5, ge=0, le=1)
    consent_for_social_context: bool = False


class DeliveryAgent(BaseModel):
    id: str
    name: str
    phone: str | None = None
    hub_id: str
    historical_false_scan_rate: float = Field(default=0, ge=0, le=1)


class Order(BaseModel):
    id: str
    buyer: Buyer
    reseller: Reseller
    delivery_agent: DeliveryAgent
    item_description: str
    amount_inr: float = Field(ge=0)
    is_cod: bool = True
    promised_delivery_slot: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class SentimentRecord(BaseModel):
    label: SentimentLabel
    score: float = Field(ge=0, le=1)
    language: Language
    rationale: str


class InteractionLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    actor: str
    channel: Channel
    message: str
    language: Language | None = None
    sentiment: SentimentRecord | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class FraudSignal(BaseModel):
    source: str
    score: float = Field(ge=0, le=1)
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class TrustGraph(BaseModel):
    buyer_trust: float = Field(default=0.5, ge=0, le=1)
    reseller_trust: float = Field(default=0.7, ge=0, le=1)
    logistics_trust: float = Field(default=0.5, ge=0, le=1)
    relationship_strength: float = Field(default=0.0, ge=0, le=1)
    notes: list[str] = Field(default_factory=list)


class ResolutionEvent(BaseModel):
    action: ResolutionAction
    reason: str
    confidence: float = Field(ge=0, le=1)
    scheduled_slot: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class NDRCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    order: Order
    reason: NDRReason
    attempt_latitude: float | None = Field(default=None, ge=-90, le=90)
    attempt_longitude: float | None = Field(default=None, ge=-180, le=180)
    attempt_timestamp: datetime = Field(default_factory=utcnow)
    retry_count: int = Field(default=0, ge=0)
    status: CaseStatus = CaseStatus.OPEN
    corrected_address: Address | None = None
    trust_graph: TrustGraph = Field(default_factory=TrustGraph)
    fraud_signals: list[FraudSignal] = Field(default_factory=list)
    interactions: list[InteractionLog] = Field(default_factory=list)
    resolution_events: list[ResolutionEvent] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utcnow)

    def add_interaction(self, interaction: InteractionLog) -> None:
        self.interactions.append(interaction)
        self.updated_at = utcnow()

    def add_fraud_signal(self, signal: FraudSignal) -> None:
        self.fraud_signals.append(signal)
        self.updated_at = utcnow()

    def add_resolution(self, event: ResolutionEvent) -> None:
        self.resolution_events.append(event)
        self.updated_at = utcnow()
