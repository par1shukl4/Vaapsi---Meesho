from backend.agents import BuyerAgent, LogisticsAgent, ResellerAgent
from backend.memory import InMemoryEpisodicMemory
from backend.orchestrator import Orchestrator


memory = InMemoryEpisodicMemory()
logistics_agent = LogisticsAgent()
buyer_agent = BuyerAgent()
reseller_agent = ResellerAgent()
orchestrator = Orchestrator(
    memory=memory,
    logistics_agent=logistics_agent,
    buyer_agent=buyer_agent,
    reseller_agent=reseller_agent,
)


def get_memory() -> InMemoryEpisodicMemory:
    return memory


def get_orchestrator() -> Orchestrator:
    return orchestrator


def get_logistics_agent() -> LogisticsAgent:
    return logistics_agent


def get_buyer_agent() -> BuyerAgent:
    return buyer_agent


def get_reseller_agent() -> ResellerAgent:
    return reseller_agent
