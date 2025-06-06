from httpx import Response

from common.domain.volume.dto import OsVolumeDto
from common.domain.volume.enum import VolumeStatus
from common.exception.openstack_exception import OpenStackException
from common.infrastructure.openstack_client import OpenStackClient
from common.util.envs import get_envs, Envs

envs: Envs = get_envs()


class CinderClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _CINDER_PORT: int = envs.CINDER_PORT
    _CINDER_URL: str = f"{_OPEN_STACK_URL}:{_CINDER_PORT}"

    async def get_volume(
        self,
        keystone_token: str,
        project_openstack_id: str,
        volume_openstack_id: str,
    ) -> OsVolumeDto:
        response: Response = await self.request(
            method="GET",
            url=self._CINDER_URL + f"/v3/{project_openstack_id}/volumes/{volume_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
        )
        volume_data: dict = response.json()["volume"]
        return OsVolumeDto(
            openstack_id=volume_data["id"],
            volume_type_name=volume_data["volume_type"],
            image_openstack_id=(volume_data.get("volume_image_metadata") or {}).get("volume_type"),
            status=VolumeStatus.parse(volume_data["status"]),
            size=volume_data["size"],
        )

    async def get_volume_status(
        self,
        keystone_token: str,
        project_openstack_id: str,
        volume_openstack_id: str,
    ) -> VolumeStatus:
        response: Response = await self.request(
            method="GET",
            url=self._CINDER_URL + f"/v3/{project_openstack_id}/volumes/{volume_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
        )
        status: str = response.json().get("volume").get("status")
        return VolumeStatus.parse(status)

    async def exists_volume(
        self,
        keystone_token: str,
        project_openstack_id: str,
        volume_openstack_id: str,
    ) -> bool:
        try:
            await self.request(
                method="GET",
                url=self._CINDER_URL + f"/v3/{project_openstack_id}/volumes/{volume_openstack_id}",
                headers={"X-Auth-Token": keystone_token},
            )
        except OpenStackException as ex:
            if ex.openstack_status_code == 404:
                return False
            raise ex

        return True

    async def create_volume(
        self,
        keystone_token: str,
        project_openstack_id: str,
        volume_type_openstack_id: str,
        image_openstack_id: str,
        size: int,
    ) -> str:
        response: Response = await self.request(
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
        return response.json().get("volume").get("id")

    async def extend_volume_size(
        self,
        keystone_token: str,
        project_openstack_id: str,
        volume_openstack_id: str,
        new_size: int,
    ) -> None:
        await self.request(
            method="POST",
            url=self._CINDER_URL + f"/v3/{project_openstack_id}/volumes/{volume_openstack_id}/action",
            headers={
                "Content-Type": "application/json",
                "X-Auth-Token": keystone_token,
            },
            json={
                "os-extend": {
                    "new_size": new_size
                }
            }
        )

    async def delete_volume(
        self,
        keystone_token: str,
        project_openstack_id: str,
        volume_openstack_id: str,
    ) -> None:
        await self.request(
            method="DELETE",
            url=self._CINDER_URL + f"/v3/{project_openstack_id}/volumes/{volume_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
        )
