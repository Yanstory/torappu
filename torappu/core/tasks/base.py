import abc
from typing import ClassVar

from torappu.core.client import Client
from torappu.log import logger
from torappu.models import Diff


class BaseTask(abc.ABC):
    # The task's priority, lower number means higher priority.
    # Tasks will be executed in order of priority.
    priority: ClassVar[int] = 1
    # The task's name
    name: str | None = None

    def __init__(self, client: Client) -> None:
        self.client = client

    @abc.abstractmethod
    def check(self, diff_list: list[Diff]) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def start(self):
        raise NotImplementedError
