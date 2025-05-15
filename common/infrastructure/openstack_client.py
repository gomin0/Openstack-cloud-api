import logging
from typing import Any

from httpx import AsyncClient, Response, HTTPStatusError

from common.exception.openstack_exception import OpenStackException

logger = logging.getLogger(__name__)


class OpenStackClient:
    async def request(
        self,
        client: AsyncClient,
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Response:
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
            logger.error(
                f"Respond errors from OpenStack API. "
                f"Status code={status_code}, message={response.json() if response.content else 'Unknown Error'}"
            )
            raise OpenStackException(openstack_status_code=status_code)

        return response
