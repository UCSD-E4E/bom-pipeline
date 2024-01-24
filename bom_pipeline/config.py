from abc import ABC, abstractmethod
from typing import Dict


class Config(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def get_part(self, key: str) -> Dict:
        raise NotImplementedError
