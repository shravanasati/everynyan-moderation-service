from abc import ABC, abstractmethod


class IModerationEngine(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def should_purge(self, text: str):
        pass
