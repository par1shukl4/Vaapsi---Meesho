from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from backend.models.domain import NDRCase


ResultT = TypeVar("ResultT")


class Agent(ABC, Generic[ResultT]):
    name: str

    @abstractmethod
    async def run(self, case: NDRCase) -> ResultT:
        raise NotImplementedError
