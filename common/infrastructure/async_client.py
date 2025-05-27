from httpx import AsyncClient

_async_client: AsyncClient | None = None


def init_async_client() -> None:
    global _async_client
    if _async_client is not None:
        raise RuntimeError("Async client is already initialized")
    _async_client = AsyncClient(verify=False)


async def close_async_client() -> None:
    if _async_client is None:
        raise RuntimeError("Async client has not been initialized")
    await _async_client.aclose()


def get_async_client() -> AsyncClient:
    if _async_client is None:
        raise RuntimeError("Async client has not been initialized")
    return _async_client
