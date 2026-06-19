import unittest

from backend.memory import InMemoryEpisodicMemory
from backend.models.domain import (
    Address,
    Buyer,
    CaseStatus,
    DeliveryAgent,
    NDRCase,
    NDRReason,
    Order,
    ResolutionAction,
    Reseller,
)
from backend.orchestrator import Orchestrator


def build_case(
    *,
    buyer_score: float = 0.8,
    buyer_ndr_count: int = 0,
    reseller_consent: bool = True,
    attempt_offset: float = 0.0,
    false_scan_rate: float = 0.0,
) -> NDRCase:
    address = Address(
        line1="12 Bazaar Road",
        city="Kolkata",
        state="West Bengal",
        pin_code="700001",
        latitude=22.5726,
        longitude=88.3639,
    )
    buyer = Buyer(
        id="buyer-1",
        name="Ananya",
        phone="+919999999999",
        address=address,
        cod_reliability_score=buyer_score,
        historical_ndr_count=buyer_ndr_count,
    )
    reseller = Reseller(
        id="reseller-1",
        name="Priya",
        phone="+918888888888",
        trust_score=0.8,
        historical_resolution_rate=0.7,
        consent_for_social_context=reseller_consent,
    )
    agent = DeliveryAgent(
        id="da-1",
        name="Ravi",
        hub_id="hub-kol-1",
        historical_false_scan_rate=false_scan_rate,
    )
    order = Order(
        id="order-1",
        buyer=buyer,
        reseller=reseller,
        delivery_agent=agent,
        item_description="Cotton kurti",
        amount_inr=699,
    )
    return NDRCase(
        order=order,
        reason=NDRReason.BUYER_UNREACHABLE,
        attempt_latitude=22.5726 + attempt_offset,
        attempt_longitude=88.3639 + attempt_offset,
    )


class OrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolves_redelivery_when_logistics_valid_and_buyer_reachable(self) -> None:
        orchestrator = Orchestrator(memory=InMemoryEpisodicMemory())
        result = await orchestrator.resolve(build_case())

        self.assertEqual(result.final_action, ResolutionAction.REDELIVERY)
        self.assertEqual(result.case.status, CaseStatus.RESOLVED)
        self.assertGreaterEqual(len(result.case.interactions), 2)

    async def test_escalates_logistics_fraud_when_gps_mismatch(self) -> None:
        orchestrator = Orchestrator(memory=InMemoryEpisodicMemory())
        result = await orchestrator.resolve(build_case(attempt_offset=0.25))

        self.assertEqual(result.final_action, ResolutionAction.FRAUD_INVESTIGATION)
        self.assertEqual(result.case.status, CaseStatus.ESCALATED)
        self.assertEqual(len(result.case.fraud_signals), 1)

    async def test_uses_reseller_when_buyer_unreachable(self) -> None:
        orchestrator = Orchestrator(memory=InMemoryEpisodicMemory())
        result = await orchestrator.resolve(build_case(buyer_score=0.1))

        self.assertEqual(result.final_action, ResolutionAction.REDELIVERY)
        self.assertEqual(result.case.status, CaseStatus.RESOLVED)
        actors = {interaction.actor for interaction in result.case.interactions}
        self.assertIn("reseller_context_agent", actors)


if __name__ == "__main__":
    unittest.main()
