import pytest

from common.application.server.response import ServerResponse
from common.domain.enum import SortOrder
from common.domain.network_interface.entity import NetworkInterface
from common.domain.project.entity import Project
from common.domain.server.dto import OsServerDto
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption, ServerStatus
from common.exception.server_exception import ServerNotFoundException, ServerAccessPermissionDeniedException, \
    ServerUpdatePermissionDeniedException, ServerNameDuplicateException
from test.util.factory import create_server_stub, create_volume, create_project, create_server, \
    create_network_interface_stub, create_volume_stub
from test.util.random import random_int, random_string


async def test_find_servers_details_success(
    mock_session,
    mock_async_client,
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
        session=mock_session,
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
    mock_server_repository.find_all_by_project_id.assert_called_once_with(
        session=mock_session,
        project_id=project.id,
        id_=None,
        ids_contain=None,
        ids_exclude=None,
        name_eq=None,
        name_like=None,
        sort_by=ServerSortOption.CREATED_AT,
        order=SortOrder.ASC,
        with_relations=True
    )
    assert len(response.servers) == 2


async def test_get_server_detail_success(
    mock_session,
    mock_async_client,
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
        session=mock_session,
        server_id=server_id,
        project_id=project_id
    )

    # then
    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        server_id=server_id,
        with_relations=True,
        with_deleted=False
    )
    assert response.id == mock_server.id


async def test_get_server_detail_fail_not_found(
    mock_session,
    mock_async_client,
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
            session=mock_session,
            server_id=server_id,
            project_id=project_id
        )

    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        server_id=server_id,
        with_relations=True,
        with_deleted=False
    )


async def test_get_server_detail_fail_access_denied(
    mock_session,
    mock_async_client,
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
            session=mock_session,
            server_id=server_id,
            project_id=project_id
        )

    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        server_id=server_id,
        with_relations=True,
        with_deleted=False
    )


async def test_update_server_info_success(mock_session, mock_server_repository, server_service):
    # given
    new_name: str = "new_name"
    new_description: str = "new_description"
    server: Server = create_server()
    mock_server_repository.find_by_id.return_value = server
    mock_server_repository.exists_by_project_and_name.return_value = False

    # when
    result: ServerResponse = await server_service.update_server_info(
        session=mock_session,
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


async def test_update_server_info_fail_server_not_found(mock_session, mock_server_repository, server_service):
    # given
    mock_server_repository.find_by_id.return_value = None

    # when and then
    with pytest.raises(ServerNotFoundException):
        await server_service.update_server_info(
            session=mock_session,
            current_project_id=random_int(),
            server_id=random_int(),
            name=random_string(),
            description=random_string(),
        )
    mock_server_repository.find_by_id.assert_called_once()


async def test_update_server_info_fail_when_requester_has_not_update_permission(
    mock_session,
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
            session=mock_session,
            current_project_id=requesting_project_id,
            server_id=server.id,
            name=new_name,
            description=new_description,
        )
    mock_server_repository.find_by_id.assert_called_once()


async def test_update_server_info_fail_new_name_is_duplicated(mock_session, mock_server_repository, server_service):
    # given
    new_name: str = "new_name"
    new_description: str = "new_description"
    server: Server = create_server()
    mock_server_repository.find_by_id.return_value = server
    mock_server_repository.exists_by_project_and_name.return_value = True

    # when and then
    with pytest.raises(ServerNameDuplicateException):
        await server_service.update_server_info(
            session=mock_session,
            current_project_id=server.project_id,
            server_id=server.id,
            name=new_name,
            description=new_description,
        )
    mock_server_repository.find_by_id.assert_called_once()
    mock_server_repository.exists_by_project_and_name.assert_called_once()


async def test_get_server_vnc_url_success(
    mock_session,
    mock_async_client,
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
        session=mock_session,
        server_id=server_id,
        project_id=project_id,
    )
    response_url = await server_service.get_vnc_console(
        client=mock_async_client,
        keystone_token=keystone_token,
        server_openstack_id=server.openstack_id
    )

    # then
    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        server_id=server_id
    )
    mock_nova_client.get_vnc_console.assert_called_once_with(
        client=mock_async_client,
        keystone_token=keystone_token,
        server_openstack_id=mock_server.openstack_id
    )
    assert response_url == vnc_url


async def test_get_server_vnc_url_fail_not_found(
    mock_session,
    mock_async_client,
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
            session=mock_session,
            server_id=server_id,
            project_id=project_id,
        )

    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        server_id=server_id,
    )


async def test_start_server_success(
    mock_session,
    mock_async_client,
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
        session=mock_session,
        client=mock_async_client,
        keystone_token=keystone_token,
        project_id=project_id,
        server_id=server_id,
    )

    # then
    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session, server_id=server_id, with_deleted=False, with_relations=False
    )
    mock_nova_client.start_server.assert_called_once_with(
        client=mock_async_client, keystone_token=keystone_token, server_openstack_id=server_openstack_id
    )


async def test_stop_server_success(
    mock_session,
    mock_async_client,
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
        session=mock_session,
        client=mock_async_client,
        keystone_token=keystone_token,
        project_id=project_id,
        server_id=server_id,
    )

    # then
    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session, server_id=server_id, with_deleted=False, with_relations=False
    )
    mock_nova_client.stop_server.assert_called_once_with(
        client=mock_async_client, keystone_token=keystone_token, server_openstack_id=server_openstack_id
    )


async def test_update_server_status_fail_server_not_found(
    mock_session,
    mock_async_client,
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
            session=mock_session,
            client=mock_async_client,
            keystone_token=keystone_token,
            project_id=project_id,
            server_id=server_id,
        )

    # then
    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session, server_id=server_id, with_deleted=False, with_relations=False
    )


async def test_wait_until_status_changed_success(
    mock_session,
    mock_async_client,
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
        session=mock_session,
        client=mock_async_client,
        keystone_token=keystone_token,
        server_openstack_id=server_openstack_id,
    )

    # then
    mock_server_repository.find_by_openstack_id.assert_called_once_with(
        session=mock_session, openstack_id=server_openstack_id, with_deleted=False
    )
    mock_nova_client.get_server.assert_called_once_with(
        client=mock_async_client, keystone_token=keystone_token, server_openstack_id=server_openstack_id
    )


async def test_wait_until_status_changed_fail_server_not_found(
    mock_session,
    mock_async_client,
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
            session=mock_session,
            client=mock_async_client,
            keystone_token=keystone_token,
            server_openstack_id=server_openstack_id,
        )

    # then
    mock_server_repository.find_by_openstack_id.assert_called_once_with(
        session=mock_session, openstack_id=server_openstack_id, with_deleted=False
    )


async def test_wait_until_status_changed_fail_time_out(
    mock_session,
    mock_async_client,
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
        session=mock_session,
        client=mock_async_client,
        keystone_token=keystone_token,
        server_openstack_id=server_openstack_id,
    )

    # then
    assert mock_nova_client.get_server.call_count == server_service.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE
