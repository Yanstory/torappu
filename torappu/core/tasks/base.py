import abc
from typing import ClassVar

from torappu.core.client import Client
from torappu.log import logger
from torappu.models import Diff


class BaseTask(abc.ABC):
    priority: ClassVar[int] = 1

    def __init__(self, client: Client) -> None:
        self.client = client

    @abc.abstractmethod
    def check(self, diff_list: list[Diff]) -> bool:
        raise NotImplementedError

    async def run(self):
        logger.info(f"Starting task {type(self).__name__}")
        await self.start()
        logger.info(f"Finished task {type(self).__name__}")

    @abc.abstractmethod
    async def start(self):
        raise NotImplementedError
