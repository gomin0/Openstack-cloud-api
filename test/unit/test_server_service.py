import pytest

from common.application.server.dto import CreateServerCommand
from common.application.server.response import ServerResponse, ServerDetailResponse, DeleteServerResponse
from common.application.server.service import ServerService
from common.domain.enum import SortOrder
from common.domain.network_interface.entity import NetworkInterface
from common.domain.project.entity import Project
from common.domain.server.dto import OsServerDto
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption
from common.domain.server.enum import ServerStatus
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus
from common.exception.security_group_exception import SecurityGroupAccessDeniedException
from common.exception.server_exception import (
    ServerDeletionFailedException
)
from common.exception.server_exception import ServerNotFoundException, ServerAccessPermissionDeniedException, \
    ServerUpdatePermissionDeniedException, ServerNameDuplicateException, VolumeDetachFailedException, \
    CannotDetachRootVolumeException
from common.exception.volume_exception import ServerNotMatchedException
from common.exception.volume_exception import VolumeAlreadyAttachedException, VolumeAttachmentFailedException
from test.util.factory import (
    create_network_interface_stub, create_volume_stub,
    create_network_interface, create_os_network_interface_dto, create_security_group, create_os_server_dto,
    create_server_stub, create_volume, create_project, create_server, create_os_volume_dto
)
from test.util.random import random_int, random_string


async def test_find_servers_details_success(
    mock_server_repository,
    server_service
):
    # given
    project = Project(id=1, name="project", openstack_id="pos", domain_id=1)
    volume1 = create_volume(
        volume_id=1, project_id=project.id, server_id=1, is_root_volume=True, image_openstack_id="123"
    )
    volume2 = create_volume(
        volume_id=2, project_id=project.id, server_id=2, is_root_volume=True, image_openstack_id="456"
    )
    network_interface1 = NetworkInterface(fixed_ip_address="123")
    network_interface2 = NetworkInterface(fixed_ip_address="456")
    mock_servers = [
        create_server_stub(
            server_id=1,
            project_id=project.id,
            volumes=[volume1],
            network_interfaces=[network_interface1],
        ),
        create_server_stub(
            server_id=2,
            project_id=project.id,
            volumes=[volume2],
            network_interfaces=[network_interface2],
        ),
    ]
    mock_server_repository.find_all_by_project_id.return_value = mock_servers

    # when
    response = await server_service.find_servers_details(
        id_=None,
        ids_contain=None,
        ids_exclude=None,
        name_eq=None,
        name_like=None,
        sort_by=ServerSortOption.CREATED_AT,
        order=SortOrder.ASC,
        project_id=project.id,
    )

    # then
    mock_server_repository.find_all_by_project_id.assert_called_once()
    assert len(response.servers) == 2


async def test_get_server_detail_success(
    mock_server_repository,
    server_service
):
    # given
    server_id = 1
    project_id = 1
    project = create_project(project_id=project_id, domain_id=1)
    volume = create_volume(
        volume_id=1, project_id=project.id, server_id=1, is_root_volume=True, image_openstack_id="123"
    )
    network_interface = NetworkInterface(fixed_ip_address="123")
    mock_server = create_server_stub(
        server_id=server_id,
        project_id=project.id,
        volumes=[volume],
        network_interfaces=[network_interface],
    )

    mock_server_repository.find_by_id.return_value = mock_server

    # when
    response = await server_service.get_server_detail(
        server_id=server_id,
        project_id=project_id
    )

    # then
    mock_server_repository.find_by_id.assert_called_once()
    assert response.id == mock_server.id


async def test_get_server_detail_fail_not_found(
    mock_server_repository,
    server_service
):
    # given
    server_id = 1
    project_id = 1
    mock_server_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(ServerNotFoundException):
        await server_service.get_server_detail(
            server_id=server_id,
            project_id=project_id
        )

    mock_server_repository.find_by_id.assert_called_once()


async def test_get_server_detail_fail_access_denied(
    mock_server_repository,
    server_service
):
    # given
    server_id = 1
    project_id = 1
    volume = create_volume(
        volume_id=1, project_id=2, server_id=1, is_root_volume=True, image_openstack_id="123"
    )
    network_interface = NetworkInterface(fixed_ip_address="123")
    mock_server = create_server_stub(
        server_id=server_id,
        project_id=2,
        volumes=[volume],
        network_interfaces=[network_interface],
    )
    mock_server_repository.find_by_id.return_value = mock_server

    # when & then
    with pytest.raises(ServerAccessPermissionDeniedException):
        await server_service.get_server_detail(
            server_id=server_id,
            project_id=project_id
        )

    mock_server_repository.find_by_id.assert_called_once()


async def test_update_server_info_success(mock_server_repository, server_service):
    # given
    new_name: str = "new_name"
    new_description: str = "new_description"
    server: Server = create_server()
    mock_server_repository.find_by_id.return_value = server
    mock_server_repository.exists_by_project_and_name.return_value = False

    # when
    result: ServerResponse = await server_service.update_server_info(
        current_project_id=server.project_id,
        server_id=server.id,
        name=new_name,
        description=new_description,
    )

    # then
    mock_server_repository.find_by_id.assert_called_once()
    mock_server_repository.exists_by_project_and_name.assert_called_once()
    assert result.id == server.id
    assert result.name == new_name
    assert result.description == new_description


async def test_update_server_info_fail_server_not_found(mock_server_repository, server_service):
    # given
    mock_server_repository.find_by_id.return_value = None

    # when and then
    with pytest.raises(ServerNotFoundException):
        await server_service.update_server_info(
            current_project_id=random_int(),
            server_id=random_int(),
            name=random_string(),
            description=random_string(),
        )
    mock_server_repository.find_by_id.assert_called_once()


async def test_update_server_info_fail_when_requester_has_not_update_permission(
    mock_server_repository,
    server_service
):
    # given
    project_id = 1
    requesting_project_id = 2
    new_name: str = "new_name"
    new_description: str = "new_description"
    server: Server = create_server(project_id=project_id)
    mock_server_repository.find_by_id.return_value = server

    # when and then
    with pytest.raises(ServerUpdatePermissionDeniedException):
        await server_service.update_server_info(
            current_project_id=requesting_project_id,
            server_id=server.id,
            name=new_name,
            description=new_description,
        )
    mock_server_repository.find_by_id.assert_called_once()


async def test_update_server_info_fail_new_name_is_duplicated(mock_server_repository, server_service):
    # given
    new_name: str = "new_name"
    new_description: str = "new_description"
    server: Server = create_server()
    mock_server_repository.find_by_id.return_value = server
    mock_server_repository.exists_by_project_and_name.return_value = True

    # when and then
    with pytest.raises(ServerNameDuplicateException):
        await server_service.update_server_info(
            current_project_id=server.project_id,
            server_id=server.id,
            name=new_name,
            description=new_description,
        )
    mock_server_repository.find_by_id.assert_called_once()
    mock_server_repository.exists_by_project_and_name.assert_called_once()


async def test_get_server_vnc_url_success(
    mock_server_repository,
    mock_nova_client,
    server_service
):
    # given
    server_id = 1
    project_id = 1
    keystone_token = "token"
    vnc_url = "vnc-url"

    volume = create_volume(
        volume_id=1, project_id=project_id, server_id=1, is_root_volume=True, image_openstack_id="123"
    )
    network_interface = NetworkInterface(fixed_ip_address="123")
    mock_server = create_server_stub(
        server_id=server_id,
        project_id=project_id,
        volumes=[volume],
        network_interfaces=[network_interface],
    )
    mock_server_repository.find_by_id.return_value = mock_server
    mock_nova_client.get_vnc_console.return_value = vnc_url

    # when
    server = await server_service.get_server(
        server_id=server_id,
        project_id=project_id,
    )
    response_url = await server_service.get_vnc_console(
        keystone_token=keystone_token,
        server_openstack_id=server.openstack_id
    )

    # then
    mock_server_repository.find_by_id.assert_called_once()
    mock_nova_client.get_vnc_console.assert_called_once()
    assert response_url == vnc_url


async def test_get_server_vnc_url_fail_not_found(
    mock_server_repository,
    server_service
):
    # given
    server_id = 1
    project_id = 1
    mock_server_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(ServerNotFoundException):
        await server_service.get_server(
            server_id=server_id,
            project_id=project_id,
        )

    mock_server_repository.find_by_id.assert_called_once()


async def test_create_server_success(
    mock_server_repository,
    mock_network_interface_repository,
    mock_security_group_repository,
    mock_nova_client,
    mock_neutron_client,
    mock_compensation_manager,
    server_service,
):
    # given
    command: CreateServerCommand = CreateServerCommand(
        keystone_token=random_string(),
        current_project_id=random_int(),
        current_project_openstack_id=random_string(),
        name=random_string(),
        description=random_string(),
        flavor_openstack_id=random_string(),
        network_openstack_id=random_string(),
        root_volume=CreateServerCommand.RootVolume(
            size=random_int(),
            image_openstack_id=random_string(),
        ),
        security_group_ids=[random_int()],
    )
    server_os_id: str = random_string()
    network_interface_os_id: str = random_string()
    expected_result: Server = create_server(project_id=command.current_project_id)
    mock_server_repository.exists_by_project_and_name.return_value = False
    mock_security_group_repository.find_all_by_ids.return_value = \
        [create_security_group(id_=command.security_group_ids[0], project_id=command.current_project_id)]
    mock_neutron_client.create_network_interface.return_value = \
        create_os_network_interface_dto(openstack_id=network_interface_os_id)
    mock_nova_client.create_server.return_value = server_os_id
    mock_server_repository.create.return_value = expected_result
    mock_network_interface_repository.create.return_value = create_network_interface()

    # when
    actual_result: ServerResponse = await server_service.create_server(
        compensating_tx=mock_compensation_manager,
        command=command,
    )

    # then
    mock_server_repository.exists_by_project_and_name.assert_called_once()
    mock_security_group_repository.find_all_by_ids.assert_called_once()
    mock_neutron_client.create_network_interface.assert_called_once()
    mock_nova_client.create_server.assert_called_once()
    mock_server_repository.create.assert_called_once()
    mock_network_interface_repository.create.assert_called_once()
    assert actual_result.id == expected_result.id


async def test_create_server_fail_server_name_duplicated(
    mock_server_repository,
    mock_compensation_manager,
    server_service,
):
    # given
    command: CreateServerCommand = CreateServerCommand(
        keystone_token=random_string(),
        current_project_id=random_int(),
        current_project_openstack_id=random_string(),
        name=random_string(),
        description=random_string(),
        flavor_openstack_id=random_string(),
        network_openstack_id=random_string(),
        root_volume=CreateServerCommand.RootVolume(
            size=random_int(),
            image_openstack_id=random_string(),
        ),
        security_group_ids=[random_int()],
    )
    mock_server_repository.exists_by_project_and_name.return_value = True

    # when and then
    with pytest.raises(ServerNameDuplicateException):
        await server_service.create_server(
            compensating_tx=mock_compensation_manager,
            command=command,
        )
    mock_server_repository.exists_by_project_and_name.assert_called_once()


async def test_create_server_fail_security_group_access_denied(
    mock_server_repository,
    mock_security_group_repository,
    mock_compensation_manager,
    server_service,
):
    # given
    command: CreateServerCommand = CreateServerCommand(
        keystone_token=random_string(),
        current_project_id=1,
        current_project_openstack_id=random_string(),
        name=random_string(),
        description=random_string(),
        flavor_openstack_id=random_string(),
        network_openstack_id=random_string(),
        root_volume=CreateServerCommand.RootVolume(
            size=random_int(),
            image_openstack_id=random_string(),
        ),
        security_group_ids=[random_int()],
    )
    mock_server_repository.exists_by_project_and_name.return_value = False
    mock_security_group_repository.find_all_by_ids.return_value = \
        [create_security_group(id_=command.security_group_ids[0], project_id=2)]

    # when and then
    with pytest.raises(SecurityGroupAccessDeniedException):
        await server_service.create_server(
            compensating_tx=mock_compensation_manager,
            command=command,
        )
    mock_server_repository.exists_by_project_and_name.assert_called_once()
    mock_security_group_repository.find_all_by_ids.assert_called_once()


async def test_finalize_server_creation_success(
    mock_server_repository,
    mock_volume_repository,
    mock_network_interface_repository,
    mock_security_group_repository,
    mock_nova_client,
    mock_neutron_client,
    mock_compensation_manager,
    server_service,
):
    # given
    server: Server = create_server(status=ServerStatus.BUILD)
    mock_nova_client.get_server.return_value = create_os_server_dto(status=ServerStatus.ACTIVE)
    mock_server_repository.find_by_openstack_id.return_value = server
    mock_volume_repository.create.return_value = create_volume()
    ServerService.CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION = 0

    # when
    await server_service.finalize_server_creation(
        server_openstack_id=random_string(),
        image_openstack_id=random_string(),
        root_volume_size=random_int(),
    )

    # then
    mock_nova_client.get_server.assert_called_once()
    mock_server_repository.find_by_openstack_id.assert_called_once()
    mock_volume_repository.create.assert_called_once()
    assert server.status == ServerStatus.ACTIVE


async def test_finalize_server_creation_fail(
    mock_server_repository,
    mock_volume_repository,
    mock_network_interface_repository,
    mock_security_group_repository,
    mock_nova_client,
    mock_neutron_client,
    mock_compensation_manager,
    server_service,
):
    # given
    server: Server = create_server(status=ServerStatus.BUILD)
    mock_nova_client.get_server.return_value = create_os_server_dto(status=ServerStatus.BUILD)
    mock_server_repository.find_by_openstack_id.return_value = server
    ServerService.MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION = 3
    ServerService.CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION = 0

    # when
    await server_service.finalize_server_creation(
        server_openstack_id=random_string(),
        image_openstack_id=random_string(),
        root_volume_size=random_int(),
    )

    # then
    assert mock_nova_client.get_server.call_count == ServerService.MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION
    mock_server_repository.find_by_openstack_id.assert_called_once()
    assert server.status == ServerStatus.ERROR


async def test_attach_volume_to_server_success(
    mock_nova_client,
    mock_cinder_client,
    mock_server_repository,
    mock_volume_repository,
    server_service
):
    # given
    project_id: int = random_int()
    server: Server = create_server(project_id=project_id)
    volume: Volume = create_volume(project_id=project_id, is_root_volume=True, image_openstack_id=random_string())
    mock_server_repository.find_by_id.return_value = server
    mock_volume_repository.find_by_id.return_value = volume
    mock_nova_client.attach_volume_to_server.return_value = None
    mock_cinder_client.get_volume.return_value = create_os_volume_dto(status=VolumeStatus.IN_USE)
    mock_server_repository.find_by_openstack_id.return_value = server
    mock_volume_repository.find_by_openstack_id.return_value = volume
    ServerService.CHECK_INTERVAL_SECONDS_FOR_VOLUME_ATTACHMENT = 0

    # when
    await server_service.attach_volume_to_server(
        keystone_token=random_string(),
        current_project_id=project_id,
        current_project_openstack_id=random_string(),
        server_id=server.id,
        volume_id=volume.id,
    )

    # then
    mock_server_repository.find_by_id.assert_called_once()
    mock_volume_repository.find_by_id.assert_called_once()
    mock_nova_client.attach_volume_to_server.assert_called_once()
    mock_cinder_client.get_volume.assert_called_once()
    mock_server_repository.find_by_openstack_id.assert_called_once()
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_attach_volume_to_server_fail_volume_is_already_attached(
    mock_server_repository,
    mock_volume_repository,
    server_service
):
    # given
    project_id: int = random_int()
    server: Server = create_server(project_id=project_id)
    volume: Volume = \
        create_volume(project_id=project_id, server=server, is_root_volume=True, image_openstack_id=random_string())
    mock_server_repository.find_by_id.return_value = server
    mock_volume_repository.find_by_id.return_value = volume

    # when and then
    with pytest.raises(VolumeAlreadyAttachedException):
        await server_service.attach_volume_to_server(
            keystone_token=random_string(),
            current_project_id=project_id,
            current_project_openstack_id=random_string(),
            server_id=server.id,
            volume_id=volume.id,
        )
    mock_server_repository.find_by_id.assert_called_once()
    mock_volume_repository.find_by_id.assert_called_once()


async def test_attach_volume_to_server_fail_when_os_volume_is_changed_to_unexpected_status(
    mock_nova_client,
    mock_cinder_client,
    mock_server_repository,
    mock_volume_repository,
    server_service
):
    # given
    project_id: int = random_int()
    unexpected_status: VolumeStatus = VolumeStatus.AVAILABLE
    server: Server = create_server(project_id=project_id)
    volume: Volume = create_volume(project_id=project_id, is_root_volume=True, image_openstack_id=random_string())
    mock_server_repository.find_by_id.return_value = server
    mock_volume_repository.find_by_id.return_value = volume
    mock_nova_client.attach_volume_to_server.return_value = None
    mock_cinder_client.get_volume.return_value = create_os_volume_dto(status=unexpected_status)
    ServerService.CHECK_INTERVAL_SECONDS_FOR_VOLUME_ATTACHMENT = 0

    # when and then
    with pytest.raises(VolumeAttachmentFailedException):
        await server_service.attach_volume_to_server(
            keystone_token=random_string(),
            current_project_id=project_id,
            current_project_openstack_id=random_string(),
            server_id=server.id,
            volume_id=volume.id,
        )
    mock_server_repository.find_by_id.assert_called_once()
    mock_volume_repository.find_by_id.assert_called_once()
    mock_nova_client.attach_volume_to_server.assert_called_once()
    mock_cinder_client.get_volume.assert_called_once()


async def test_attach_volume_to_server_fail_when_volume_is_not_attached_from_openstack(
    mock_nova_client,
    mock_cinder_client,
    mock_server_repository,
    mock_volume_repository,
    server_service
):
    # given
    project_id: int = random_int()
    unexpected_status: VolumeStatus = VolumeStatus.AVAILABLE
    server: Server = create_server(project_id=project_id)
    volume: Volume = create_volume(project_id=project_id, is_root_volume=True, image_openstack_id=random_string())
    mock_server_repository.find_by_id.return_value = server
    mock_volume_repository.find_by_id.return_value = volume
    mock_nova_client.attach_volume_to_server.return_value = None
    mock_cinder_client.get_volume.return_value = create_os_volume_dto(status=unexpected_status)
    mock_volume_repository.find_by_openstack_id.return_value = volume
    ServerService.MAX_CHECK_ATTEMPTS_FOR_VOLUME_ATTACHMENT = 3
    ServerService.CHECK_INTERVAL_SECONDS_FOR_VOLUME_ATTACHMENT = 0

    # when and then
    with pytest.raises(VolumeAttachmentFailedException):
        await server_service.attach_volume_to_server(
            keystone_token=random_string(),
            current_project_id=project_id,
            current_project_openstack_id=random_string(),
            server_id=server.id,
            volume_id=volume.id,
        )
    mock_server_repository.find_by_id.assert_called_once()
    mock_volume_repository.find_by_id.assert_called_once()
    mock_nova_client.attach_volume_to_server.assert_called_once()
    mock_cinder_client.get_volume.assert_called_once()
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_delete_server_success(
    mock_server_repository,
    mock_network_interface_repository,
    mock_volume_repository,
    mock_nova_client,
    server_service
):
    # given
    server_id = random_int()
    project_id = random_int()
    keystone_token = random_string()
    server_openstack_id = random_string()
    volume_id = random_int()
    network_interface_id = random_int()
    network_interface = create_network_interface_stub(
        server_id=server_id, project_id=project_id, network_interface_id=network_interface_id
    )
    volume = create_volume_stub(volume_id=volume_id, is_root_volume=True)
    server = create_server_stub(
        server_id=server_id,
        openstack_id=server_openstack_id,
        project_id=project_id,
        volumes=[volume],
        network_interfaces=[network_interface]
    )
    mock_server_repository.find_by_id.return_value = server
    mock_nova_client.delete_server.return_value = None
    response = DeleteServerResponse(
        server_id=server.id,
        volume_id=volume_id,
        network_interface_ids=[network_interface_id]
    )

    # when
    result = await server_service.delete_server(
        keystone_token=keystone_token,
        server_id=server_id,
        project_id=project_id
    )

    # then
    mock_server_repository.find_by_id.assert_called_once()
    mock_nova_client.delete_server.assert_called_once()
    assert result == response


async def test_delete_server_fail_server_not_found(
    mock_server_repository,
    mock_network_interface_repository,
    mock_volume_repository,
    mock_nova_client,
    server_service
):
    # given
    project_id = random_int()
    server_id = random_int()
    keystone_token = random_string()

    mock_server_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(ServerNotFoundException):
        await server_service.delete_server(
            keystone_token=keystone_token,
            server_id=server_id,
            project_id=project_id
        )
    mock_server_repository.find_by_id.assert_called_once()


async def test_delete_server_and_resources_success(
    mock_server_repository,
    mock_network_interface_repository,
    mock_volume_repository,
    mock_nova_client,
    mock_neutron_client,
    mock_network_interface_security_group_repository,
    server_service
):
    # given
    server_id = random_int()
    project_id = random_int()
    volume_id = random_int()
    keystone_token = random_string()
    network_interface_id = random_int()
    server_openstack_id = random_string()
    network_interface = create_network_interface_stub(
        server_id=server_id, project_id=project_id, network_interface_id=network_interface_id
    )
    volume = create_volume_stub(volume_id=volume_id, is_root_volume=True)
    server = create_server_stub(
        server_id=server_id,
        openstack_id=server_openstack_id,
        project_id=project_id,
        volumes=[volume],
        network_interfaces=[network_interface]
    )

    mock_server_repository.find_by_id.return_value = server
    mock_nova_client.exists_server.return_value = False
    mock_network_interface_repository.find_all_by_ids.return_value = [network_interface]
    mock_neutron_client.delete_network_interface.return_value = None

    # when
    await server_service.check_server_until_deleted_and_remove_resources(
        keystone_token=keystone_token,
        network_interface_ids=[network_interface_id],
        server_id=server_id
    )

    # then
    mock_network_interface_repository.find_all_by_ids.assert_called_once()
    mock_neutron_client.delete_network_interface.assert_called_once()
    mock_nova_client.exists_server.assert_called_once()
    assert mock_server_repository.find_by_id.call_count == 2


async def test_delete_server_and_resources_fail_server_not_found(
    mock_server_repository,
    mock_network_interface_repository,
    mock_volume_repository,
    mock_nova_client,
    mock_neutron_client,
    mock_network_interface_security_group_repository,
    server_service
):
    # given
    server_id = random_int()
    project_id = random_int()
    volume_id = random_int()
    keystone_token = random_string()
    network_interface_id = random_int()
    server_openstack_id = random_string()
    network_interface = create_network_interface_stub(
        server_id=server_id, project_id=project_id, network_interface_id=network_interface_id
    )
    volume = create_volume_stub(volume_id=volume_id, is_root_volume=True)
    server = create_server_stub(
        server_id=server_id,
        openstack_id=server_openstack_id,
        project_id=project_id,
        volumes=[volume],
        network_interfaces=[network_interface]
    )

    mock_server_repository.find_by_id.return_value = None

    # when
    with pytest.raises(ServerNotFoundException):
        await server_service.check_server_until_deleted_and_remove_resources(
            keystone_token=keystone_token,
            network_interface_ids=[network_interface_id],
            server_id=server_id
        )

    # then
    mock_server_repository.find_by_id.assert_called_once()


async def test_delete_server_and_resources_fail_timeout(
    mock_server_repository,
    mock_network_interface_repository,
    mock_volume_repository,
    mock_nova_client,
    mock_neutron_client,
    mock_network_interface_security_group_repository,
    server_service
):
    # given
    server_service.MAX_CHECK_ATTEMPTS_FOR_SERVER_DELETION = 1
    server_service.CHECK_INTERVAL_SECONDS_FOR_SERVER_DELETION = 0
    server_id = random_int()
    project_id = random_int()
    volume_id = random_int()
    keystone_token = random_string()
    network_interface_id = random_int()
    server_openstack_id = random_string()
    network_interface = create_network_interface_stub(
        server_id=server_id, project_id=project_id, network_interface_id=network_interface_id
    )
    volume = create_volume_stub(volume_id=volume_id, is_root_volume=True)
    server = create_server_stub(
        server_id=server_id,
        openstack_id=server_openstack_id,
        project_id=project_id,
        volumes=[volume],
        network_interfaces=[network_interface]
    )

    mock_server_repository.find_by_id.return_value = server
    mock_nova_client.get_server.return_value = None

    # when
    with pytest.raises(ServerDeletionFailedException):
        await server_service.check_server_until_deleted_and_remove_resources(
            keystone_token=keystone_token,
            network_interface_ids=[network_interface_id],
            server_id=server_id
        )

    # then
    mock_server_repository.find_by_id.assert_called()
    mock_nova_client.exists_server.assert_called_once()


async def test_start_server_success(
    mock_server_repository,
    mock_nova_client,
    server_service
):
    # given
    server_id = random_int()
    project_id = random_int()
    volume_id = random_int()
    network_interface_id = random_int()
    keystone_token = random_string()
    server_openstack_id = random_string()
    network_interface = create_network_interface_stub(
        server_id=server_id, project_id=project_id, network_interface_id=network_interface_id
    )
    volume = create_volume_stub(volume_id=volume_id, is_root_volume=True)
    server = create_server_stub(
        server_id=server_id,
        status=ServerStatus.SHUTOFF,
        openstack_id=server_openstack_id,
        project_id=project_id,
        volumes=[volume],
        network_interfaces=[network_interface]
    )

    mock_server_repository.find_by_id.return_value = server
    mock_nova_client.start_server.return_value = None

    # when
    await server_service.start_server(
        keystone_token=keystone_token,
        project_id=project_id,
        server_id=server_id,
    )

    # then
    mock_server_repository.find_by_id.assert_called_once()
    mock_nova_client.start_server.assert_called_once_with(
        keystone_token=keystone_token, server_openstack_id=server_openstack_id
    )


async def test_stop_server_success(
    mock_server_repository,
    mock_nova_client,
    server_service
):
    # given
    server_id = random_int()
    project_id = random_int()
    volume_id = random_int()
    network_interface_id = random_int()
    keystone_token = random_string()
    server_openstack_id = random_string()
    network_interface = create_network_interface_stub(
        server_id=server_id, project_id=project_id, network_interface_id=network_interface_id
    )
    volume = create_volume_stub(volume_id=volume_id, is_root_volume=True)
    server = create_server_stub(
        server_id=server_id,
        status=ServerStatus.ACTIVE,
        openstack_id=server_openstack_id,
        project_id=project_id,
        volumes=[volume],
        network_interfaces=[network_interface]
    )

    mock_server_repository.find_by_id.return_value = server
    mock_nova_client.stop_server.return_value = None

    # when
    await server_service.stop_server(
        keystone_token=keystone_token,
        project_id=project_id,
        server_id=server_id,
    )

    # then
    mock_server_repository.find_by_id.assert_called_once()
    mock_nova_client.stop_server.assert_called_once_with(
        keystone_token=keystone_token, server_openstack_id=server_openstack_id
    )


async def test_update_server_status_fail_server_not_found(
    mock_server_repository,
    mock_nova_client,
    server_service
):
    # given
    server_id = random_int()
    project_id = random_int()
    keystone_token = random_string()

    mock_server_repository.find_by_id.return_value = None

    # when
    with pytest.raises(ServerNotFoundException):
        await server_service.start_server(
            keystone_token=keystone_token,
            project_id=project_id,
            server_id=server_id,
        )

    # then
    mock_server_repository.find_by_id.assert_called_once()


async def test_wait_until_status_changed_success(
    mock_server_repository,
    mock_nova_client,
    server_service
):
    # given
    server_id = random_int()
    project_id = random_int()
    volume_id = random_int()
    network_interface_id = random_int()
    keystone_token = random_string()
    server_openstack_id = random_string()
    network_interface = create_network_interface_stub(
        server_id=server_id, project_id=project_id, network_interface_id=network_interface_id
    )
    volume = create_volume_stub(volume_id=volume_id, is_root_volume=True)
    server = create_server_stub(
        server_id=server_id,
        status=ServerStatus.SHUTOFF,
        openstack_id=server_openstack_id,
        project_id=project_id,
        volumes=[volume],
        network_interfaces=[network_interface]
    )
    mock_server = OsServerDto(
        openstack_id=server_openstack_id,
        project_openstack_id="project-openstack-id",
        status=ServerStatus.ACTIVE,
        volume_openstack_ids=["volume-openstack-id"]
    )

    mock_server_repository.find_by_openstack_id.return_value = server
    mock_nova_client.get_server.return_value = mock_server

    # when
    await server_service.wait_until_server_started(
        server_openstack_id=server_openstack_id,
    )

    # then
    mock_server_repository.find_by_openstack_id.assert_called_once()
    mock_nova_client.get_server.assert_called_once()


async def test_wait_until_status_changed_fail_server_not_found(
    mock_server_repository,
    mock_nova_client,
    server_service
):
    # given
    keystone_token = random_string()
    server_openstack_id = random_string()

    mock_server = OsServerDto(
        openstack_id=server_openstack_id,
        project_openstack_id="project-openstack-id",
        status=ServerStatus.ACTIVE,
        volume_openstack_ids=["volume-openstack-id"]
    )

    mock_server_repository.find_by_openstack_id.return_value = None
    mock_nova_client.get_server.return_value = mock_server

    # when
    with pytest.raises(ServerNotFoundException):
        await server_service.wait_until_server_started(
            server_openstack_id=server_openstack_id,
        )

    # then
    mock_server_repository.find_by_openstack_id.assert_called_once()


async def test_wait_until_status_changed_fail_time_out(
    mock_server_repository,
    mock_nova_client,
    server_service
):
    # given
    server_service.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE = 3
    server_service.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE = 0
    keystone_token = random_string()
    server_openstack_id = random_string()

    mock_server = OsServerDto(
        openstack_id=server_openstack_id,
        project_openstack_id="project-openstack-id",
        status=ServerStatus.SHUTOFF,
        volume_openstack_ids=["volume-openstack-id"]
    )

    mock_nova_client.get_server.return_value = mock_server

    # when
    await server_service.wait_until_server_started(
        server_openstack_id=server_openstack_id,
    )

    # then
    assert mock_nova_client.get_server.call_count == server_service.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE


async def test_detach_volume_from_server_success(
    mock_nova_client,
    mock_cinder_client,
    mock_server_repository,
    mock_volume_repository,
    server_service
):
    # given
    server_id = random_int()
    project_id = random_int()
    project_openstack_id = random_string()
    network_interface = NetworkInterface(fixed_ip_address="123")
    volume = create_volume(
        volume_id=2,
        openstack_id=random_string(),
        project_id=project_id,
        server_id=server_id,
        is_root_volume=False,
        image_openstack_id=random_string(),
        status=VolumeStatus.IN_USE
    )
    root_volume = create_volume(
        volume_id=1,
        openstack_id=random_string(),
        project_id=project_id,
        server_id=server_id,
        is_root_volume=True,
        image_openstack_id=random_string()
    )
    server = create_server_stub(
        project_id=project_id,
        server_id=server_id,
        volumes=[volume, root_volume],
        network_interfaces=[network_interface]
    )
    mock_volume_repository.find_by_id.return_value = volume
    mock_server_repository.find_by_id.return_value = server
    mock_nova_client.detach_volume_from_server.return_value = None
    mock_cinder_client.get_volume.return_value = create_os_volume_dto(status=VolumeStatus.AVAILABLE)
    mock_volume_repository.find_by_openstack_id.return_value = volume
    ServerService.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT = 0

    # when
    await server_service.detach_volume_from_server(
        keystone_token=random_string(),
        project_openstack_id=project_openstack_id,
        project_id=project_id,
        server_id=server.id,
        volume_id=volume.id,
    )

    # then
    mock_volume_repository.find_by_id.assert_called_once()
    mock_server_repository.find_by_id.assert_called_once()
    mock_nova_client.detach_volume_from_server.assert_called_once()
    mock_cinder_client.get_volume.assert_called_once()
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_detach_volume_from_server_fail_volume_is_not_attached_to_server(
    mock_nova_client,
    mock_cinder_client,
    mock_server_repository,
    mock_volume_repository,
    server_service
):
    # given
    project_id = random_int()
    project_openstack_id = random_string()
    server = create_server(project_id=project_id)
    root_volume = create_volume(
        volume_id=1, project_id=project_id, server_id=server.id, is_root_volume=True, image_openstack_id=random_string()
    )
    volume = create_volume(
        volume_id=2,
        project_id=project_id,
        server_id=random_int(),
        is_root_volume=True,
        image_openstack_id=random_string(),
        status=VolumeStatus.IN_USE
    )
    mock_volume_repository.find_by_id.return_value = volume

    # when
    with pytest.raises(ServerNotMatchedException):
        await server_service.detach_volume_from_server(
            keystone_token=random_string(),
            project_openstack_id=project_openstack_id,
            project_id=project_id,
            server_id=server.id,
            volume_id=volume.id,
        )

    # then
    mock_volume_repository.find_by_id.assert_called_once()


async def test_detach_volume_from_server_fail_cannot_detach_root_volume(
    mock_nova_client,
    mock_cinder_client,
    mock_server_repository,
    mock_volume_repository,
    server_service
):
    # given
    project_id = random_int()
    project_openstack_id = random_string()
    server = create_server(project_id=project_id)
    root_volume = create_volume(
        volume_id=1,
        project_id=project_id,
        server_id=server.id,
        is_root_volume=True,
        image_openstack_id=random_string(),
        status=VolumeStatus.IN_USE
    )
    mock_volume_repository.find_by_id.return_value = root_volume

    # when
    with pytest.raises(CannotDetachRootVolumeException):
        await server_service.detach_volume_from_server(
            keystone_token=random_string(),
            project_openstack_id=project_openstack_id,
            project_id=project_id,
            server_id=server.id,
            volume_id=root_volume.id,
        )

    # then
    mock_volume_repository.find_by_id.assert_called_once()


async def test_detach_volume_from_server_fail_time_out(
    mock_nova_client,
    mock_cinder_client,
    mock_server_repository,
    mock_volume_repository,
    server_service
):
    # given
    project_id = random_int()
    project_openstack_id = random_string()
    server = create_server(project_id=project_id)
    keystone_token = random_string()
    volume_openstack_id = random_string()
    root_volume = create_volume(
        volume_id=1, project_id=project_id, server_id=server.id, is_root_volume=True, image_openstack_id=random_string()
    )
    volume = create_volume(
        volume_id=2,
        openstack_id=volume_openstack_id,
        project_id=project_id,
        server_id=server.id,
        is_root_volume=False,
        image_openstack_id=random_string(),
        status=VolumeStatus.IN_USE
    )
    mock_volume_repository.find_by_id.return_value = volume
    mock_server_repository.find_by_id.return_value = server
    mock_nova_client.detach_volume_from_server.return_value = None
    mock_cinder_client.get_volume.return_value = create_os_volume_dto(status=VolumeStatus.IN_USE)
    ServerService.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT = 3
    ServerService.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT = 0

    # when
    with pytest.raises(VolumeDetachFailedException):
        await server_service.detach_volume_from_server(
            keystone_token=keystone_token,
            project_openstack_id=project_openstack_id,
            project_id=project_id,
            server_id=server.id,
            volume_id=volume.id,
        )

    # then
    mock_volume_repository.find_by_id.assert_called_once()
    mock_server_repository.find_by_id.assert_called_once()
    mock_nova_client.detach_volume_from_server.assert_called_once()
    assert mock_cinder_client.get_volume.call_count == ServerService.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT
