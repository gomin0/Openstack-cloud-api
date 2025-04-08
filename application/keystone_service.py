from datetime import datetime, timezone

from fastapi import Depends
from httpx import AsyncClient

from common.envs import get_envs, Envs
from domain.keystone.model import KeystoneToken
from exception.auth_exception import InvalidAuthException
from exception.openstack_exception import OpenStackException
from exception.project_exception import ProjectAccessDeniedException
from infrastructure.keystone.client import KeystoneClient

envs: Envs = get_envs()


class KeystoneService:
    def __init__(self, keystone_client: KeystoneClient = Depends()):
        self.keystone_client = keystone_client

    async def issue_keystone_token(
        self,
        client: AsyncClient,
        user_openstack_id: str,
        password: str,
        project_openstack_id: str,
    ) -> KeystoneToken:
        try:
            keystone_token, keystone_token_exp = await self.keystone_client.authenticate_with_scoped_auth(
                client=client,
                user_openstack_id=user_openstack_id,
                domain_openstack_id=envs.DEFAULT_DOMAIN_OPENSTACK_ID,
                password=password,
                project_openstack_id=project_openstack_id,
            )
        except OpenStackException as ex:
            if ex.openstack_status_code == 401:
                raise InvalidAuthException() from ex
            if ex.openstack_status_code == 403:
                raise ProjectAccessDeniedException() from ex
            raise ex

        return KeystoneToken(
            token=keystone_token,
            expires_at=datetime.strptime(
                keystone_token_exp, "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=timezone.utc),
        )
