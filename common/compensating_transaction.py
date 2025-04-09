import inspect
import logging
from contextlib import asynccontextmanager
from typing import Callable, AsyncGenerator

logger = logging.getLogger(__name__)


class CompensationManager:
    def __init__(self):
        self._recovery_tasks: list[Callable] = []

    def add_task(self, task: Callable) -> None:
        self._recovery_tasks.append(task)

    async def rollback(self) -> None:
        for task in reversed(self._recovery_tasks):
            try:
                result = task()
                if inspect.isawaitable(result):
                    await result
            except Exception as ex:
                # TODO: 복구 로직 동작 실패에 대한 대응 작업 추가
                pass


@asynccontextmanager
async def compensating_transaction() -> AsyncGenerator[CompensationManager]:
    manager: CompensationManager = CompensationManager()
    try:
        yield manager
    except Exception:
        await manager.rollback()
        raise
