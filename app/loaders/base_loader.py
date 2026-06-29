from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseLoader(ABC, Generic[T]):
    @abstractmethod
    def load(self) -> list[T]:
        ...

    @abstractmethod
    def reload(self) -> list[T]:
        ...
