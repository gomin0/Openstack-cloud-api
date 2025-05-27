import logging
from typing import Any

from httpx import AsyncClient, Response, HTTPStatusError

from common.exception.openstack_exception import OpenStackException
from common.infrastructure.async_client import get_async_client

logger = logging.getLogger(__name__)


class OpenStackClient:
    async def request(
        self,
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Response:
        client: AsyncClient = get_async_client()
        headers = headers or {"Content-Type": "application/json"}
        response: Response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            params=params,
        )

        try:
            response.raise_for_status()
        except HTTPStatusError:
            status_code: int = response.status_code
            try:
                error_message: str = str(response.json())
            except Exception:
                error_message: str = response.text
            logger.error(
                f"Respond errors from OpenStack API. "
                f"Status code={status_code}, message={error_message}"
            )
            raise OpenStackException(openstack_status_code=status_code)

        return response
