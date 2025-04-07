import logging
from typing import Any

from httpx import AsyncClient, Response

from exception.openstack_exception import OpenStackException

logger = logging.getLogger(__name__)


class OpenStackClient:
    async def request(
        self,
        client: AsyncClient,
        method: str,
        expected_status_code: int,
        url: str,
        json: dict[str, Any],
        headers: dict[str, Any] | None = None,
    ) -> Response:
        headers = headers or {"Content-Type": "application/json"}
        response: Response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
        )

        if response.status_code != expected_status_code:
            status_code: int = response.status_code
            try:
                error_message: str = response.json().get("error", {}).get("message", "Unknown error")
            except Exception:
                error_message: str = response.text
            logger.error(
                f"Respond errors from OpenStack API. "
                f"Status code={status_code}, message={error_message}"
            )
            raise OpenStackException(openstack_status_code=status_code)

        return response
