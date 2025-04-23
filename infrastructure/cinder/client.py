from httpx import AsyncClient, Response

from common.envs import get_envs, Envs
from domain.volume.enum import VolumeStatus
from infrastructure.openstack_client import OpenStackClient

envs: Envs = get_envs()


class CinderClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _CINDER_PORT: int = envs.CINDER_PORT
    _CINDER_URL: str = f"{_OPEN_STACK_URL}:{_CINDER_PORT}"

    async def get_volume_status(
        self,
        client: AsyncClient,
        keystone_token: str,
        project_openstack_id: str,
        volume_openstack_id: str,
    ) -> VolumeStatus:
        response: Response = await self.request(
            client,
            method="GET",
            url=self._CINDER_URL + f"/v3/{project_openstack_id}/volumes/{volume_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
        )
        status: str = response.json().get("volume").get("status")
        return VolumeStatus.parse(status)

    async def create_volume(
        self,
        client: AsyncClient,
        keystone_token: str,
        project_openstack_id: str,
        volume_type_openstack_id: str,
        image_openstack_id: str,
        size: int,
    ) -> str:
        response: Response = await self.request(
            client,
            method="POST",
            url=self._CINDER_URL + f"/v3/{project_openstack_id}/volumes",
            headers={
                "Content-Type": "application/json",
                "X-Auth-Token": keystone_token,
            },
            json={
                "volume": {
                    "size": size,
                    "imageRef": image_openstack_id,
                    "volume_type": volume_type_openstack_id,
                }
            }
        )
        status_code = response.status_code
        print(f"response.status_code={status_code}")
        json = response.json()
        print(f"response.json()={json}")
        return response.json().get("volume").get("id")
