import inspect
import logging
from typing import Callable, Any, get_type_hints

from fastapi import BackgroundTasks
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.infrastructure.async_client import get_async_client
from common.infrastructure.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def _invoke_with_await_if_needed(func: Callable[..., Any], **kwargs) -> Any:
    if inspect.iscoroutinefunction(func):
        return await func(**kwargs)
    return func(**kwargs)


def _get_injectable_param_names(task: Callable[..., Any], expected_type: type) -> list[str]:
    signature = inspect.signature(task)
    type_hints = get_type_hints(task, globalns=globals(), localns=locals())
    return [param for param in signature.parameters if type_hints.get(param) == expected_type]


def run_background_task(background_task: BackgroundTasks, task: Callable[..., Any], **kwargs):
    """
    FastAPI BackgroundTasks에 함수를 등록하고, 필요한 의존성을 자동으로 주입합니다.

    이 함수는 주어진 함수(``task``)를 FastAPI의 background task로 등록하며,
    다음 타입의 파라미터를 자동으로 감지하여 주입합니다:

    - ``AsyncSession`` (SQLAlchemy 비동기 세션)
    - ``AsyncClient`` (httpx 비동기 클라이언트)

    :param background_task: FastAPI에서 주입되는 BackgroundTasks object
    :param task: 실행할 함수
    :param kwargs: 실행할 함수에 전달할 named parameters

    :raises ValueError: ``AsyncSession`` 타입의 파라미터가 두 개 이상 선언된 경우
    """
    kwargs = kwargs.copy()

    async def run_with_required_dependencies():
        # client
        client_param_names = _get_injectable_param_names(task, AsyncClient)
        if client_param_names:
            for param_name in client_param_names:
                logger.debug(
                    f"[background_task_runner] injecting AsyncClient into {task.__name__}({param_name})"
                )
                kwargs[param_name] = get_async_client()

        # session
        session_param_names = _get_injectable_param_names(task, AsyncSession)
        if len(session_param_names) > 1:
            raise ValueError(f"{task.__name__}()에서 AsyncSession 타입의 parameter는 하나만 선언할 수 있습니다.")
        if session_param_names:
            session_param_name = session_param_names[0]
            async with AsyncSessionLocal() as session:
                logger.debug(
                    f"[background_task_runner] injecting AsyncSession into {task.__name__}({session_param_name})"
                )
                kwargs[session_param_name] = session
                return await _invoke_with_await_if_needed(task, **kwargs)
        return await _invoke_with_await_if_needed(task, **kwargs)

    background_task.add_task(run_with_required_dependencies)
