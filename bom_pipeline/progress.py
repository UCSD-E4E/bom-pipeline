from abc import ABC, abstractmethod, abstractproperty


class Progress(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractproperty
    def progress(self) -> int:
        raise NotImplemented

    @progress.setter
    def progress(self, value: int):
        raise NotImplementedError

    @abstractproperty
    def total(self) -> int:
        raise NotImplementedError

    @total.setter
    def total(self, value: int):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError

    def increment(self):
        self.progress += 1

    @abstractmethod
    def write(self, s: str):
        raise NotImplementedError
